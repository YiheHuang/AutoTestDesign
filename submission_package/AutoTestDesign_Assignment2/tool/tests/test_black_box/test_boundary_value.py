"""边界值分析生成器测试"""

from unittest.mock import MagicMock, patch

from src.test_design.black_box.boundary_value import BVAGenerator


class TestBVAGenerator:
    def test_name(self):
        gen = BVAGenerator()
        assert gen.name == "Boundary Value Analysis"

    def test_generate_with_mock_llm(self, sample_requirement):
        gen = BVAGenerator()
        mock_client = MagicMock()
        mock_client.chat_with_json.return_value = {
            "boundary_analysis": [
                {
                    "field": "age",
                    "valid_range": "18-120",
                    "boundary_points": [
                        {"point": "lb", "value": 18, "should_pass": True},
                        {"point": "lb-1", "value": 17, "should_pass": False},
                    ]
                }
            ],
            "test_cases": [
                {"title": "年龄下界", "description": "年龄等于18", "category": "Boundary", "input_data": {"age": 18}, "expected_result": "通过"},
                {"title": "年龄下界外", "description": "年龄等于17", "category": "Boundary", "input_data": {"age": 17}, "expected_result": "拒绝"},
            ]
        }

        with patch("src.test_design.black_box.boundary_value.get_ai_client", return_value=mock_client):
            analysis, cases = gen.generate(sample_requirement)

        assert len(analysis) == 1
        assert len(cases) == 2
        assert all(c.technique == "Boundary Value Analysis" for c in cases)
