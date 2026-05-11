"""优化器测试"""

import pytest
from src.optimization.risk_based_optimizer import RiskBasedOptimizer
from src.optimization.coverage_optimizer import CoverageBasedMinimizer


class TestRiskBasedOptimizer:
    def test_optimize_full_budget(self, sample_test_suite):
        optimizer = RiskBasedOptimizer()
        result = optimizer.optimize(sample_test_suite, budget=1.0)
        assert result.total_cases == sample_test_suite.total_cases

    def test_optimize_partial_budget(self, sample_test_suite):
        optimizer = RiskBasedOptimizer()
        result = optimizer.optimize(sample_test_suite, budget=0.5)
        assert result.total_cases <= sample_test_suite.total_cases

    def test_optimize_sorted_by_risk(self, sample_test_suite):
        optimizer = RiskBasedOptimizer()
        result = optimizer.optimize(sample_test_suite)
        # 验证按风险降序排列
        scores = [tc.risk_score for tc in result.test_cases]
        assert scores == sorted(scores, reverse=True)


class TestCoverageBasedMinimizer:
    def test_optimize(self, sample_test_suite):
        optimizer = CoverageBasedMinimizer()
        result = optimizer.optimize(sample_test_suite, min_coverage=1.0)
        assert result.total_cases <= sample_test_suite.total_cases

    def test_optimize_single_case(self):
        from src.models.testcase import TestSuite, TestCase, TestStep
        single = TestSuite(
            id="TS-SINGLE",
            name="单用例套件",
            requirement_id="REQ-001",
            test_cases=[TestCase(
                id="TC-001",
                requirement_id="REQ-001",
                title="单用例",
                technique="EP",
                category="Valid",
                test_steps=[TestStep(step_number=1, action="test", input_data={"a": "1"}, expected_result="")]
            )]
        )
        optimizer = CoverageBasedMinimizer()
        result = optimizer.optimize(single)
        assert result.total_cases == 1
