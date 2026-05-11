"""CSV解析器测试"""

import pytest
from src.parser.csv_parser import CSVParser


class TestCSVParser:
    def test_can_handle_csv_extension(self):
        parser = CSVParser()
        assert parser.can_handle("test.csv") is True

    def test_can_handle_csv_content(self):
        parser = CSVParser()
        assert parser.can_handle("id,title,description\n1,测试,描述") is True

    def test_can_handle_non_csv(self):
        parser = CSVParser()
        assert parser.can_handle("这是纯文本需求") is False

    def test_parse_empty_csv(self):
        parser = CSVParser()
        csv_content = "id,title,description\n"
        results = parser.parse(csv_content)
        assert results == []

    def test_missing_required_columns_raises_error(self):
        parser = CSVParser()
        csv_content = "title,description\n测试,某功能"
        with pytest.raises(ValueError, match="缺少必要列"):
            parser.parse(csv_content)
