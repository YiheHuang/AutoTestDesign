"""风险分析器测试"""

from unittest.mock import MagicMock, patch

from src.risk.risk_analyzer import RiskAnalyzer


class TestRiskAnalyzer:
    def test_default_score_mapping(self):
        analyzer = RiskAnalyzer()
        assert analyzer._default_score("High") == 85
        assert analyzer._default_score("Medium") == 60
        assert analyzer._default_score("Low") == 30

    def test_analyze_batch_with_mock_llm(self, sample_requirement, sample_login_requirement):
        analyzer = RiskAnalyzer()
        mock_client = MagicMock()
        mock_client.chat_with_json.return_value = {
            "assessments": [
                {
                    "requirement_id": "REQ-001",
                    "risk_score": 90,
                    "risk_level": "High",
                    "risk_factors": ["涉及密码字段"],
                    "test_priority": "High",
                    "priority_reason": "核心注册流程"
                }
            ]
        }

        with patch("src.risk.risk_analyzer.get_ai_client", return_value=mock_client):
            result = analyzer.analyze_batch([sample_requirement, sample_login_requirement])

        assert len(result) == 2
        first = next(x for x in result if x.requirement_id == "REQ-001")
        second = next(x for x in result if x.requirement_id == "REQ-002")
        assert first.risk_score == 90
        assert first.risk_level == "High"
        assert second.risk_score == 60
        assert second.risk_level == "Medium"

    def test_analyze_batch_fallback(self, sample_requirement):
        analyzer = RiskAnalyzer()
        with patch("src.risk.risk_analyzer.get_ai_client", side_effect=RuntimeError("boom")):
            result = analyzer.analyze_batch([sample_requirement])

        assert len(result) == 1
        assert result[0].risk_score == 60
        assert result[0].test_priority == "Medium"
