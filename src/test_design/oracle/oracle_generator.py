"""测试预言生成与校验 - FR 5.0 (重写)

三步流程:
1. 合理性校验: LLM 评估测试用例是否合理
2. 丢弃不合理: 移除不合理的用例
3. 生成预期结果: 为合理用例生成精确的 HTTP 预期
"""

import json
from src.models.requirement import StructuredRequirement
from src.models.testcase import TestCase, TestSuite, TestStep
from src.parser.code_parser import CodeStructure
from src.ai.client import get_ai_client
from src.ai.prompts.oracle_prompts import ORACLE_SYSTEM_PROMPT, ORACLE_USER_TEMPLATE
from src.ai.prompts.oracle_validate_prompts import (
    ORACLE_VALIDATE_SYSTEM_PROMPT,
    ORACLE_VALIDATE_USER_TEMPLATE
)
from src.utils.logger import logger


class OracleGenerator:
    """测试预言生成器 — 校验 + 丢弃 + 生成预期"""

    def __init__(self):
        self.validation_log = []

    def generate_suite(
        self,
        suite: TestSuite,
        req: StructuredRequirement,
        code_structure: CodeStructure | None = None,
        risk_json: str = "{}",
        validate: bool = True
    ) -> TestSuite:
        """为套件中所有用例校验并生成预期结果

        Args:
            suite: 测试套件
            req: 需求规格
            code_structure: 代码结构（用于白盒校验）
            risk_json: 风险分析JSON
            validate: 是否进行合理性校验

        Returns:
            处理后的测试套件（已移除不合理用例）
        """
        logger.info(f"预言生成: {suite.id}, {len(suite.test_cases)} 用例, 校验={validate}")

        if not suite.test_cases:
            return suite

        if validate:
            suite = self._validate_and_filter(suite, req, code_structure, risk_json)

        # 为保留的用例生成预期结果
        for i, tc in enumerate(suite.test_cases):
            suite.test_cases[i] = self._fill_expected(tc, req)

        return suite

    def _validate_and_filter(
        self,
        suite: TestSuite,
        req: StructuredRequirement,
        code_structure: CodeStructure | None = None,
        risk_json: str = "{}"
    ) -> TestSuite:
        """校验合理性并过滤"""
        logger.info(f"校验 {len(suite.test_cases)} 个用例的合理性")

        # 1. 规则引擎快速校验
        kept_cases = []
        discarded = []

        for tc in suite.test_cases:
            reason = self._rule_validate(tc, req)
            if reason:
                discarded.append((tc.id, reason))
                logger.info(f"  丢弃 {tc.id}: {reason}")
            else:
                kept_cases.append(tc)

        # 2. AI深度校验（如果用例数量较多）
        if len(kept_cases) > 5:
            try:
                kept_cases, ai_discarded = self._ai_validate(
                    kept_cases, req, code_structure, risk_json
                )
                discarded.extend(ai_discarded)
            except Exception as e:
                logger.warning(f"AI校验失败，仅使用规则校验: {e}")

        self.validation_log = discarded

        logger.info(f"校验结果: 保留 {len(kept_cases)}/{len(suite.test_cases)}, "
                    f"丢弃 {len(discarded)}")

        return TestSuite(
            id=suite.id,
            name=f"{suite.name} (Validated)",
            requirement_id=suite.requirement_id,
            test_cases=kept_cases,
            created_at=suite.created_at,
            coverage_summary={
                **suite.coverage_summary,
                "original_cases": len(suite.test_cases),
                "validated_cases": len(kept_cases),
                "discarded_cases": len(discarded),
                "discard_reasons": [{"id": d[0], "reason": d[1]} for d in discarded]
            }
        )

    def _rule_validate(self, tc: TestCase, req: StructuredRequirement) -> str:
        """规则引擎快速校验

        Returns:
            空字符串表示通过，非空表示不通过的原因
        """
        if not tc.test_steps:
            return "缺少测试步骤"

        step = tc.test_steps[0]
        input_data = step.input_data
        expected = step.expected_result.lower()

        # 检查字段值与预期是否矛盾
        if input_data:
            age = input_data.get("age")
            if age is not None:
                try:
                    age_int = int(age)
                    if age_int < 18 and "注册成功" in expected:
                        return f"年龄{age_int}<18但预期注册成功，逻辑矛盾"
                    if age_int >= 18 and age_int <= 120 and "未成年" in expected:
                        return f"年龄{age_int}在有效范围内但预期'未成年'，逻辑矛盾"
                except (ValueError, TypeError):
                    pass

            username = input_data.get("username", "")
            if isinstance(username, str):
                if len(username) < 3 and "注册成功" in expected:
                    return f"用户名长度{len(username)}<3但预期注册成功"
                if len(username) > 20 and "注册成功" in expected:
                    return f"用户名长度{len(username)}>20但预期注册成功"

            password = input_data.get("password", "")
            if isinstance(password, str):
                if len(password) < 8 and "登录成功" in expected:
                    return f"密码长度{len(password)}<8但预期成功"
                if len(password) > 32 and "登录成功" in expected:
                    return f"密码长度{len(password)}>32但预期成功"

        return ""

    def _ai_validate(
        self,
        cases: list[TestCase],
        req: StructuredRequirement,
        code_structure: CodeStructure | None = None,
        risk_json: str = "{}"
    ) -> tuple[list[TestCase], list[tuple[str, str]]]:
        """AI深度校验"""
        ai_client = get_ai_client()

        code_ctx = ""
        if code_structure:
            from src.parser.code_parser import CodeParser
            parser = CodeParser()
            code_ctx = parser.to_context_for_llm(code_structure)

        cases_json = json.dumps(
            [{
                "id": tc.id,
                "title": tc.title,
                "technique": tc.technique,
                "endpoint": tc.test_steps[0].action if tc.test_steps else "",
                "input_data": tc.test_steps[0].input_data if tc.test_steps else {},
                "expected": tc.test_steps[0].expected_result if tc.test_steps else ""
            } for tc in cases],
            ensure_ascii=False, indent=2
        )

        user_message = ORACLE_VALIDATE_USER_TEMPLATE.format(
            requirement_json=req.model_dump_json(indent=2),
            code_structure=code_ctx,
            risk_json=risk_json,
            test_cases_json=cases_json
        )

        result = ai_client.chat_with_json(
            system_prompt=ORACLE_VALIDATE_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.1
        )

        # 处理校验结果
        valid_map = {}
        discarded = []
        for vr in result.get("validation_results", []):
            tc_id = vr.get("test_case_id", "")
            if vr.get("action") == "discard":
                discarded.append((tc_id, vr.get("reason", "AI判定不合理")))
            else:
                valid_map[tc_id] = vr

        # 过滤保留的用例并更新预期
        kept = []
        for tc in cases:
            if tc.id in valid_map:
                vr = valid_map[tc.id]
                if tc.test_steps:
                    tc.test_steps[0].expected_result = vr.get("expected_response_body", {}).get("message", "")
                kept.append(tc)
            elif not any(d[0] == tc.id for d in discarded):
                kept.append(tc)  # AI未明确丢弃，保留

        return kept, discarded

    def _fill_expected(self, tc: TestCase, req: StructuredRequirement) -> TestCase:
        """填充预期结果"""
        if not tc.test_steps:
            return tc

        step = tc.test_steps[0]
        input_data = step.input_data

        # 尝试从需求的expected_behaviors匹配
        for behavior in req.expected_behaviors:
            condition = behavior.condition.lower()
            if self._match_condition(condition, input_data):
                tc.test_steps[0].expected_result = behavior.expected_output or behavior.action
                return tc

        # 规则推导
        if input_data:
            age = input_data.get("age")
            if age is not None:
                try:
                    age_int = int(age)
                    if age_int < 18:
                        tc.test_steps[0].expected_result = "未成年不可注册（需年满18岁）"
                        return tc
                    if age_int > 120:
                        tc.test_steps[0].expected_result = "请输入有效年龄（18-120）"
                        return tc
                except (ValueError, TypeError):
                    tc.test_steps[0].expected_result = "年龄必须为整数"
                    return tc

            username = input_data.get("username", "")
            if isinstance(username, str) and (len(username) < 3 or len(username) > 20):
                tc.test_steps[0].expected_result = f"用户名长度需为3-20字符"
                return tc

        return tc

    def _match_condition(self, condition: str, input_data: dict) -> bool:
        """简单条件匹配"""
        for key, value in input_data.items():
            str_val = str(value).lower()
            if key.lower() in condition or str_val in condition:
                return True
        return False

    def generate_for_risk_priority(self, test_case: TestCase, priority: str) -> TestCase:
        """根据风险优先级标记用例"""
        test_case.priority = priority
        if priority == "High":
            test_case.risk_score = 0.8
        elif priority == "Medium":
            test_case.risk_score = 0.5
        else:
            test_case.risk_score = 0.2
        return test_case

    def get_validation_log(self) -> list[tuple[str, str]]:
        """获取校验日志（被丢弃的用例及原因）"""
        return self.validation_log
