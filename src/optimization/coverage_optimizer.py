"""测试套件优化 (v2.2: 风险优先级 + 合并 + 覆盖最小化)"""

import json
from src.models.requirement import TestCaseCodeMapping
from src.models.testcase import TestSuite
from src.ai.client import get_ai_client
from src.ai.prompts.optimization_prompts import OPTIMIZE_SYSTEM_PROMPT, OPTIMIZE_USER_TEMPLATE
from src.utils.logger import logger

MERGE_SYSTEM_PROMPT = """你是一名测试套件优化专家。

## 任务
给定黑盒测试套件(无覆盖代码图)，识别逻辑相同或高度相似的测试用例并合并:
- 两个用例如果测试相同的输入字段组合且预期结果相同，则视为重复
- 两个用例如果输入数据仅在非关键差异(如不同的有效用户名)上不同，可以合并为1个
- 边界值用例中 lb-1/lb+1 类型的测试往往与 lb 或 ub 点有逻辑重叠

## 输出JSON格式
{
  "deleted_test_case_ids": ["TC-EP-REQ-001-005"],
  "deletion_reasons": {"TC-EP-REQ-001-005": "与TC-EP-REQ-001-003逻辑相同"},
  "merged_groups": [{"kept": "TC-EP-001-001", "merged": ["TC-EP-001-002"], "reason": "..."}]
}
"""

MERGE_USER_TEMPLATE = """## 测试套件 (共{total}个用例)
{cases_json}

请识别逻辑相同或可合并的测试用例，输出删除的用例ID和原因。"""


class CoverageOptimizer:
    def optimize_risk_priority(
        self,
        suite: TestSuite,
        risk_assessments: list,
        budget: float = 1.0,
        min_risk: str = ""
    ) -> TestSuite:
        """基于风险的优先级排序与筛选

        Args:
            suite: 待优化套件
            risk_assessments: 风险评估列表 (RiskAssessment对象)
            budget: 保留比例 (1.0=全部, 0.5=前50%)
            min_risk: 最低风险等级 ('High'=仅保留High, 'Medium'=High+Medium, ''=全部)
        """
        logger.info(f"风险优化: {suite.id}, budget={budget}, min_risk={min_risk}")

        risk_map = {}
        for ra in risk_assessments:
            score = {"High": 3, "Medium": 2, "Low": 1}.get(ra.risk_level, 2)
            risk_map[ra.requirement_id] = (ra.risk_level, score)

        for tc in suite.test_cases:
            level, score = risk_map.get(tc.requirement_id, ("Medium", 2))
            tc.tags = [t for t in tc.tags if not t.startswith("risk:")]
            tc.tags.append(f"risk:{level}")
            tc.tags.append(f"risk_score:{score}")

        # 按风险分数降序排列
        sorted_cases = sorted(
            suite.test_cases,
            key=lambda tc: risk_map.get(tc.requirement_id, ("Medium", 2))[1],
            reverse=True
        )

        # 筛选最低风险等级
        if min_risk == "High":
            sorted_cases = [tc for tc in sorted_cases if risk_map.get(tc.requirement_id, ("Medium",))[0] == "High"]
        elif min_risk == "Medium":
            sorted_cases = [tc for tc in sorted_cases if risk_map.get(tc.requirement_id, ("Medium",))[0] in ("High", "Medium")]

        # 预算裁剪
        if budget < 1.0:
            cutoff = max(1, int(len(sorted_cases) * budget))
            sorted_cases = sorted_cases[:cutoff]

        return TestSuite(
            id=suite.id, name=f"{suite.name} (Risk-Prioritized)",
            requirement_id=suite.requirement_id,
            test_cases=sorted_cases,
            coverage_summary={
                **suite.coverage_summary,
                "original_cases": suite.total_cases,
                "optimized_cases": len(sorted_cases),
                "deleted_cases": suite.total_cases - len(sorted_cases),
                "opt_mode": "risk_priority",
                "budget": budget,
                "min_risk": min_risk or "All"
            }
        )

    def optimize_blackbox(self, suite: TestSuite, requirements_json: str = "{}") -> TestSuite:
        """黑盒优化: LLM合并逻辑相同的用例"""
        logger.info(f"黑盒优化: {suite.id}, {suite.total_cases} 用例")

        cases_data = [{
            "id": tc.id, "title": tc.title, "technique": tc.technique,
            "category": tc.category,
            "input_data": tc.test_steps[0].input_data if tc.test_steps else {},
            "expected_result": tc.test_steps[0].expected_result if tc.test_steps else ""
        } for tc in suite.test_cases]

        try:
            ai_client = get_ai_client()
            result = ai_client.chat_with_json(
                system_prompt=MERGE_SYSTEM_PROMPT,
                user_message=MERGE_USER_TEMPLATE.format(
                    total=suite.total_cases,
                    cases_json=json.dumps(cases_data, ensure_ascii=False, indent=2)
                ),
                temperature=0.1
            )

            if not result:
                logger.warning("LLM合并返回空")
                return suite

            deleted_ids = set(result.get("deleted_test_case_ids", []))
            reasons = result.get("deletion_reasons", {})

            kept_cases = [tc for tc in suite.test_cases if tc.id not in deleted_ids]
            return TestSuite(
                id=suite.id, name=f"{suite.name} (Optimized)",
                requirement_id=suite.requirement_id,
                test_cases=kept_cases,
                coverage_summary={
                    **suite.coverage_summary,
                    "original_cases": suite.total_cases,
                    "optimized_cases": len(kept_cases),
                    "deleted_cases": len(deleted_ids),
                    "deletion_reasons": reasons,
                    "opt_mode": "blackbox_merge"
                }
            )
        except Exception as e:
            logger.error(f"黑盒优化失败: {e}")
            return suite

    def optimize_coverage(
        self,
        suite: TestSuite,
        tc_mappings: list[TestCaseCodeMapping],
        req_json: str,
        target_pct: float = 80.0,
        current_pct: float = 100.0
    ) -> tuple[TestSuite, list[TestCaseCodeMapping]]:
        """白盒覆盖优化: LLM删除冗余用例保持覆盖率"""
        logger.info(f"覆盖优化: {suite.id}, 目标={target_pct}%")

        tc_json = json.dumps([tm.model_dump() for tm in tc_mappings], ensure_ascii=False, indent=2)

        try:
            ai_client = get_ai_client()
            result = ai_client.chat_with_json(
                system_prompt=OPTIMIZE_SYSTEM_PROMPT,
                user_message=OPTIMIZE_USER_TEMPLATE.format(
                    target_pct=target_pct, current_pct=current_pct,
                    tc_mapping_json=tc_json, requirement_json=req_json
                ),
                temperature=0.1
            )

            if not result:
                return suite, tc_mappings

            deleted_ids = set(result.get("deleted_test_case_ids", []))
            reasons = result.get("deletion_reasons", {})

            kept_cases = [tc for tc in suite.test_cases if tc.id not in deleted_ids]
            optimized = TestSuite(
                id=suite.id, name=f"{suite.name} (Optimized, {target_pct}%)",
                requirement_id=suite.requirement_id,
                test_cases=kept_cases,
                coverage_summary={
                    **suite.coverage_summary,
                    "original_cases": suite.total_cases,
                    "optimized_cases": len(kept_cases),
                    "deleted_cases": len(deleted_ids),
                    "target_coverage_pct": target_pct,
                    "deletion_reasons": reasons,
                    "opt_mode": "coverage"
                }
            )
            kept_mappings = [tm for tm in tc_mappings if tm.test_case_id not in deleted_ids]
            return optimized, kept_mappings
        except Exception as e:
            logger.error(f"覆盖优化失败: {e}")
            return suite, tc_mappings
