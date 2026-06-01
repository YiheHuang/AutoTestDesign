"""状态转换 (v2.2: LLM生成状态机+测试序列)"""

from src.models.requirement import StructuredRequirement, RequirementCodeMapping
from src.models.state_machine import StateMachine, State, Transition
from src.models.testcase import TestCase, TestStep
from src.ai.client import get_ai_client
from src.ai.prompts.state_transition_prompts import ST_SYSTEM_PROMPT, ST_USER_TEMPLATE
from src.utils.logger import logger


class StateTransitionGenerator:
    name = "State Transition"

    def generate(
        self,
        req: StructuredRequirement,
        req_code_mapping: RequirementCodeMapping,
        source_code: str
    ) -> tuple[dict, list[TestCase]]:
        """LLM生成状态机 + 测试序列

        Returns:
            (st_data: {state_machine, all_states_paths}, test_cases)
        """
        logger.info(f"LLM状态转换: {req.id}")

        ai_client = get_ai_client()
        result = ai_client.chat_with_json(
            system_prompt=ST_SYSTEM_PROMPT,
            user_message=ST_USER_TEMPLATE.format(
                requirement_json=req.model_dump_json(indent=2),
                req_code_mapping_json=req_code_mapping.model_dump_json(indent=2),
                source_code=source_code
            ),
            temperature=0.1
        )

        if not result:
            logger.warning("LLM状态转换返回空")
            return {"state_machine": None, "all_states_paths": []}, []

        # 解析状态机
        sm_data = result.get("state_machine", {})
        state_machine = _parse_state_machine(sm_data) if sm_data else None

        # 解析测试用例
        test_cases = _build_test_cases(result, req.id)

        if not test_cases:
            raise RuntimeError("状态转换: LLM返回了空的test_cases，请重试")

        st_data = {
            "state_machine": state_machine,
            "all_states_paths": result.get("all_states_paths", [])
        }

        logger.info(f"状态转换完成: {len(test_cases)} 用例")
        return st_data, test_cases


def _parse_state_machine(data: dict) -> StateMachine | None:
    try:
        states = [State(**s) for s in data.get("states", [])]
        transitions = [Transition(**t) for t in data.get("transitions", [])]
        return StateMachine(
            id="SM-001",
            name=data.get("name", "状态机"),
            states=states,
            transitions=transitions
        )
    except Exception as e:
        logger.error(f"解析状态机失败: {e}")
        return None


def _build_test_cases(result: dict, req_id: str) -> list[TestCase]:
    cases = []
    for i, tc in enumerate(result.get("test_cases", [])):
        steps = [
            TestStep(
                step_number=s.get("step_number", j + 1),
                action=s.get("action", ""),
                input_data=s.get("input_data", {}),
                expected_result=s.get("expected_result", "")
            )
            for j, s in enumerate(tc.get("test_steps", []))
        ]
        if not steps:
            steps = [TestStep(step_number=1, action=tc.get("description", ""), input_data={}, expected_result="")]

        cases.append(TestCase(
            id=f"TC-ST-{req_id}-{i + 1:03d}",
            requirement_id=req_id,
            title=tc.get("title", ""),
            description=tc.get("description", ""),
            technique="State Transition",
            category=tc.get("category", "Valid"),
            test_steps=steps,
            tags=[tc.get("coverage_type", "state_transition")]
        ))
    return cases
