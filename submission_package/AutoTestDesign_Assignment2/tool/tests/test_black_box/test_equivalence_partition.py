"""等价类划分生成器测试"""

from unittest.mock import MagicMock, patch

from src.test_design.black_box.equivalence_partition import EPGenerator


class TestEPGenerator:
    def test_name(self):
        gen = EPGenerator()
        assert gen.name == "Equivalence Partitioning"

    def test_generate_with_mock_llm(self, sample_requirement):
        gen = EPGenerator()
        mock_client = MagicMock()
        mock_client.chat_with_json.return_value = {
            "equivalence_classes": [
                {
                    "field": "age",
                    "classes": [
                        {"type": "Valid", "description": "18-120", "representative_value": 30},
                        {"type": "Invalid", "description": "<18", "representative_value": 10},
                    ]
                }
            ],
            "test_cases": [
                {"title": "有效年龄", "description": "年龄有效", "category": "Valid", "input_data": {"age": 30}, "expected_result": "通过"},
                {"title": "无效年龄", "description": "年龄过小", "category": "Invalid", "input_data": {"age": 10}, "expected_result": "拒绝"},
            ]
        }

        with patch("src.test_design.black_box.equivalence_partition.get_ai_client", return_value=mock_client):
            analysis, cases = gen.generate(sample_requirement)

        assert len(analysis) == 1
        assert len(cases) == 2
        assert {c.category for c in cases} == {"Valid", "Invalid"}
        assert all(c.technique == "Equivalence Partitioning" for c in cases)
