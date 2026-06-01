"""等价类划分 (v2.2)"""

from src.models.requirement import StructuredRequirement
from src.models.testcase import TestCase, TestStep
from src.ai.client import get_ai_client
from src.ai.prompts.blackbox_prompts import EP_SYSTEM_PROMPT, EP_USER_TEMPLATE
from src.utils.constants import TECHNIQUE_EP, CATEGORY_VALID
from src.utils.logger import logger


class EPGenerator:
    name = TECHNIQUE_EP

    def generate(self, req: StructuredRequirement) -> tuple[list[dict], list[TestCase]]:
        logger.info(f"LLM EP: {req.id}")
        ai_client = get_ai_client()
        result = ai_client.chat_with_json(
            system_prompt=EP_SYSTEM_PROMPT,
            user_message=EP_USER_TEMPLATE.format(requirement_json=req.model_dump_json(indent=2)),
            temperature=0.1
        )

        ec_data = result.get("equivalence_classes", []) if result else []
        test_cases = self._build_cases(result, req.id)
        if not test_cases:
            logger.warning("EP: LLM返回了空的test_cases，请重试")
        return ec_data, test_cases

    @staticmethod
    def _build_cases(result: dict | None, req_id: str) -> list[TestCase]:
        cases = []
        for i, tc in enumerate(result.get("test_cases", []) if result else []):
            cases.append(TestCase(
                id=f"TC-EP-{req_id}-{i + 1:03d}",
                requirement_id=req_id,
                title=tc.get("title", ""),
                description=tc.get("description", ""),
                technique=TECHNIQUE_EP,
                category=tc.get("category", CATEGORY_VALID),
                test_steps=[TestStep(
                    step_number=1,
                    input_data=tc.get("input_data", {}),
                    expected_result=tc.get("expected_result", "")
                )],
                tags=["equivalence_partitioning"]
            ))
        return cases
