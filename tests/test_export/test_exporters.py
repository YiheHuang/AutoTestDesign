"""导出器测试"""

import json
import pytest
from src.export.json_exporter import JSONExporter
from src.export.csv_exporter import CSVExporter
from src.export.excel_exporter import ExcelExporter
from src.export.exporter_factory import ExporterFactory, ExportFormat


class TestJSONExporter:
    def test_export(self, sample_test_suite):
        exporter = JSONExporter()
        result = exporter.export(sample_test_suite)
        data = json.loads(result)

        assert "test_suite" in data
        assert data["test_suite"]["id"] == "TS-001"
        assert len(data["test_suite"]["test_cases"]) == sample_test_suite.total_cases

    def test_export_with_risk(self, sample_test_suite, sample_risk_assessment):
        exporter = JSONExporter()
        result = exporter.export(sample_test_suite, sample_risk_assessment)
        data = json.loads(result)

        assert "risk_assessment" in data
        assert data["risk_assessment"]["requirement_id"] == "REQ-001"


class TestCSVExporter:
    def test_export(self, sample_test_suite):
        exporter = CSVExporter()
        result = exporter.export(sample_test_suite)

        assert "id,title,requirement_id" in result
        assert "TC-EP-001" in result
        assert "TC-EP-002" in result


class TestExcelExporter:
    def test_export(self, sample_test_suite, sample_risk_assessment):
        exporter = ExcelExporter()
        result = exporter.export([sample_test_suite], [sample_risk_assessment])

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestExporterFactory:
    def test_create_json(self):
        exporter = ExporterFactory.create(ExportFormat.JSON)
        assert isinstance(exporter, JSONExporter)

    def test_create_csv(self):
        exporter = ExporterFactory.create(ExportFormat.CSV)
        assert isinstance(exporter, CSVExporter)

    def test_create_excel(self):
        exporter = ExporterFactory.create(ExportFormat.EXCEL)
        assert isinstance(exporter, ExcelExporter)

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            ExporterFactory.create("invalid")
