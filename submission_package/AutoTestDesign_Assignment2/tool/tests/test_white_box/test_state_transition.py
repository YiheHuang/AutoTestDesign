"""状态转换生成器测试"""

from unittest.mock import MagicMock, patch

from src.models.requirement import CodeSegment, RequirementCodeMapping
from src.test_design.white_box.state_transition import StateTransitionGenerator


class TestStateTransitionGenerator:
    def test_generate_returns_state_machine_and_cases(self, sample_requirement):
        generator = StateTransitionGenerator()
        mapping = RequirementCodeMapping(
            requirement_id=sample_requirement.id,
            requirement_title=sample_requirement.title,
            code_segments=[
                CodeSegment(file_path="flask_app/routes/tasks.py", start_line=1, end_line=20, function_name="task_assign")
            ]
        )
        mock_client = MagicMock()
        mock_client.chat_with_json.return_value = {
            "state_machine": {
                "name": "任务分配状态机",
                "states": [
                    {"id": "S1", "name": "未分配", "is_initial": True},
                    {"id": "S2", "name": "已分配", "is_final": True},
                ],
                "transitions": [
                    {"id": "T1", "from_state": "S1", "to_state": "S2", "trigger": "assign"}
                ]
            },
            "all_states_paths": [
                {"path": ["S1", "S2"], "description": "覆盖全部状态"}
            ],
            "test_cases": [
                {
                    "title": "任务从未分配进入已分配",
                    "description": "验证正常分配流程",
                    "category": "Valid",
                    "coverage_type": "all_states",
                    "test_steps": [
                        {
                            "step_number": 1,
                            "action": "分配任务",
                            "input_data": {"assignee": "alice"},
                            "expected_result": "分配成功"
                        }
                    ]
                }
            ]
        }

        with patch("src.test_design.white_box.state_transition.get_ai_client", return_value=mock_client):
            data, cases = generator.generate(sample_requirement, mapping, "def task_assign(): pass")

        assert data["state_machine"].state_count == 2
        assert len(data["all_states_paths"]) == 1
        assert len(cases) == 1
        assert cases[0].technique == "State Transition"

    def test_generate_empty_cases_raise(self, sample_requirement):
        generator = StateTransitionGenerator()
        mapping = RequirementCodeMapping(
            requirement_id=sample_requirement.id,
            requirement_title=sample_requirement.title,
            code_segments=[]
        )
        mock_client = MagicMock()
        mock_client.chat_with_json.return_value = {
            "state_machine": {},
            "all_states_paths": [],
            "test_cases": []
        }

        with patch("src.test_design.white_box.state_transition.get_ai_client", return_value=mock_client):
            try:
                generator.generate(sample_requirement, mapping, "")
            except RuntimeError as exc:
                assert "空的test_cases" in str(exc)
            else:
                raise AssertionError("应抛出 RuntimeError")
