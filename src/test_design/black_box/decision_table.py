"""判定表 (v2.2)"""

from src.models.requirement import StructuredRequirement
from src.models.testcase import TestCase, TestStep
from src.ai.client import get_ai_client
from src.ai.prompts.blackbox_prompts import DT_SYSTEM_PROMPT, DT_USER_TEMPLATE
from src.utils.constants import TECHNIQUE_DT, CATEGORY_VALID
from src.utils.logger import logger


class DTGenerator:
    name = TECHNIQUE_DT

    def generate(self, req: StructuredRequirement) -> tuple[dict, list[TestCase]]:
        logger.info(f"LLM DT: {req.id}")
        ai_client = get_ai_client()
        result = ai_client.chat_with_json(
            system_prompt=DT_SYSTEM_PROMPT,
            user_message=DT_USER_TEMPLATE.format(requirement_json=req.model_dump_json(indent=2)),
            temperature=0.1
        )

        dt_data = result if result else {"conditions": [], "actions": [], "simplified_rules": []}
        test_cases = self._build_cases(result, req.id)
        return dt_data, test_cases

    @staticmethod
    def _build_cases(result: dict | None, req_id: str) -> list[TestCase]:
        cases = []
        for i, tc in enumerate(result.get("test_cases", []) if result else []):
            cases.append(TestCase(
                id=f"TC-DT-{req_id}-{i + 1:03d}",
                requirement_id=req_id,
                title=tc.get("title", ""),
                description=tc.get("description", ""),
                technique=TECHNIQUE_DT,
                category=tc.get("category", CATEGORY_VALID),
                test_steps=[TestStep(
                    step_number=1,
                    input_data=tc.get("input_data", {}),
                    expected_result=tc.get("expected_result", "")
                )],
                tags=["decision_table"]
            ))
        return cases
