"""状态转换生成器测试"""

import pytest
from src.test_design.white_box.state_transition import StateTransitionGenerator
from src.test_design.white_box.state_coverage import CoverageCalculator


class TestStateTransitionGenerator:
    def test_build_from_dict(self, sample_state_machine):
        gen = StateTransitionGenerator()
        data = {
            "states": [
                {"id": "S1", "name": "未登录", "is_initial": True},
                {"id": "S2", "name": "已登录"},
            ],
            "transitions": [
                {"id": "T1", "from_state": "S1", "to_state": "S2", "trigger": "登录", "guard": None, "action": None}
            ]
        }
        sm = gen.build_model_from_dict(data, "TEST")
        assert sm.id == "SM-TEST"
        assert len(sm.states) == 2
        assert len(sm.transitions) == 1

    def test_find_path(self, sample_state_machine):
        gen = StateTransitionGenerator()
        path = gen._find_path_to_state(sample_state_machine, "S1", "S3")
        assert path == ["S1", "S2", "S3"]

    def test_all_states_paths(self, sample_state_machine):
        gen = StateTransitionGenerator()
        paths = gen._generate_all_states_paths(sample_state_machine)
        assert len(paths) > 0
        path = paths[0]["path"]
        # 应该覆盖所有4个状态
        assert all(sid in path for sid in ["S1", "S2", "S3", "S4"])

    def test_all_transitions_paths(self, sample_state_machine):
        gen = StateTransitionGenerator()
        paths = gen._generate_all_transitions_paths(sample_state_machine)
        assert len(paths) > 0


class TestCoverageCalculator:
    def test_compute_full_coverage(self, sample_state_machine):
        calc = CoverageCalculator()
        # 执行覆盖所有状态的路径
        paths = [
            ["S1", "S2", "S3", "S1", "S2", "S4"]
        ]
        result = calc.compute(sample_state_machine, paths)

        assert result["state_coverage"] == 1.0
        assert result["total_states"] == 4
        assert result["covered_states"] == 4

    def test_compute_partial_coverage(self, sample_state_machine):
        calc = CoverageCalculator()
        paths = [["S1", "S2"]]
        result = calc.compute(sample_state_machine, paths)

        assert result["state_coverage"] < 1.0
        assert result["covered_states"] < result["total_states"]
