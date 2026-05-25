"""边界值分析 (v2.2)"""

from src.models.requirement import StructuredRequirement
from src.models.testcase import TestCase, TestStep
from src.ai.client import get_ai_client
from src.ai.prompts.blackbox_prompts import BVA_SYSTEM_PROMPT, BVA_USER_TEMPLATE
from src.utils.constants import TECHNIQUE_BVA, CATEGORY_BOUNDARY
from src.utils.logger import logger


class BVAGenerator:
    name = TECHNIQUE_BVA

    def generate(self, req: StructuredRequirement) -> tuple[list[dict], list[TestCase]]:
        logger.info(f"LLM BVA: {req.id}")
        ai_client = get_ai_client()
        result = ai_client.chat_with_json(
            system_prompt=BVA_SYSTEM_PROMPT,
            user_message=BVA_USER_TEMPLATE.format(requirement_json=req.model_dump_json(indent=2)),
            temperature=0.1
        )

        ba_data = result.get("boundary_analysis", []) if result else []
        test_cases = self._build_cases(result, req.id)
        if not test_cases:
            logger.warning("BVA: LLM返回了空的test_cases，请重试")
        return ba_data, test_cases

    @staticmethod
    def _build_cases(result: dict | None, req_id: str) -> list[TestCase]:
        cases = []
        for i, tc in enumerate(result.get("test_cases", []) if result else []):
            cases.append(TestCase(
                id=f"TC-BVA-{req_id}-{i + 1:03d}",
                requirement_id=req_id,
                title=tc.get("title", ""),
                description=tc.get("description", ""),
                technique=TECHNIQUE_BVA,
                category=tc.get("category", CATEGORY_BOUNDARY),
                test_steps=[TestStep(
                    step_number=1,
                    input_data=tc.get("input_data", {}),
                    expected_result=tc.get("expected_result", "")
                )],
                tags=["boundary_value_analysis"]
            ))
        return cases
