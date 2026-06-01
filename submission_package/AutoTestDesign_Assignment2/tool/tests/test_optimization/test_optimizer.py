"""优化器测试"""

from src.optimization.coverage_optimizer import CoverageOptimizer


class DummyRisk:
    def __init__(self, requirement_id, risk_level):
        self.requirement_id = requirement_id
        self.risk_level = risk_level


class TestCoverageOptimizer:
    def test_optimize_risk_priority_full_budget(self, sample_test_suite):
        optimizer = CoverageOptimizer()
        result = optimizer.optimize_risk_priority(
            sample_test_suite,
            [DummyRisk("REQ-001", "High")],
            budget=1.0
        )
        assert result.total_cases == sample_test_suite.total_cases

    def test_optimize_risk_priority_partial_budget(self, sample_test_suite):
        optimizer = CoverageOptimizer()
        result = optimizer.optimize_risk_priority(
            sample_test_suite,
            [DummyRisk("REQ-001", "High")],
            budget=0.5
        )
        assert 1 <= result.total_cases <= sample_test_suite.total_cases

    def test_optimize_risk_priority_tags_score(self, sample_test_suite):
        optimizer = CoverageOptimizer()
        result = optimizer.optimize_risk_priority(
            sample_test_suite,
            [DummyRisk("REQ-001", "Medium")]
        )
        assert any("risk:Medium" in tc.tags for tc in result.test_cases)
        assert any("risk_score:2" in tc.tags for tc in result.test_cases)
