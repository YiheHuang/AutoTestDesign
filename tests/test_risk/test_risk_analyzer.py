"""风险分析器测试"""

import pytest
from src.risk.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzer:
    def test_heuristic_analyze(self, sample_requirement):
        analyzer = RiskAnalyzer()
        result = analyzer._heuristic_analyze(sample_requirement)

        assert result.requirement_id == "REQ-001"
        assert 0 <= result.likelihood <= 1
        assert 0 <= result.impact <= 1
        assert result.risk_score == pytest.approx(result.likelihood * result.impact, abs=0.01)
        assert result.priority in ("High", "Medium", "Low")

    def test_password_keyword_high_impact(self):
        analyzer = RiskAnalyzer()
        from src.models.requirement import StructuredRequirement
        req = StructuredRequirement(
            id="REQ-PWD",
            source="text",
            raw_text="password reset",
            title="密码重置",
            description="用户修改密码 password authentication",
            domain="web_application"
        )
        result = analyzer._heuristic_analyze(req)
        # 含password关键词应该高impact
        assert result.impact >= 0.8

    def test_get_summary(self, sample_risk_assessment):
        analyzer = RiskAnalyzer()
        summary = analyzer.get_summary([sample_risk_assessment])
        assert summary["total"] == 1
        assert "avg_risk_score" in summary
        assert "high_count" in summary

    def test_empty_summary(self):
        analyzer = RiskAnalyzer()
        summary = analyzer.get_summary([])
        assert summary == {}
