"""测试套件优化 (v2.2)"""

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
