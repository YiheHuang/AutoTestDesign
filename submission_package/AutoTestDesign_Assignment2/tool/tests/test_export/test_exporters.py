"""导出器测试"""

import json

import pytest

from src.export.exporter_factory import ExporterFactory, ExportFormat
from src.export.json_exporter import JSONExporter
from src.export.pytest_exporter import PytestExporter


class TestJSONExporter:
    def test_export_single_suite(self, sample_test_suite, sample_risk_assessment):
        exporter = JSONExporter()
        result = exporter.export(sample_test_suite, sample_risk_assessment)
        data = json.loads(result)

        assert data["test_suite"]["id"] == "TS-001"
        assert data["test_suite"]["summary"]["total_cases"] == sample_test_suite.total_cases
        assert data["risk_assessment"]["risk_score"] == 85

    def test_export_multiple_suites(self, sample_test_suite):
        exporter = JSONExporter()
        result = exporter.export_multiple([sample_test_suite])
        data = json.loads(result)

        assert data["metadata"]["total_suites"] == 1
        assert data["metadata"]["total_cases"] == sample_test_suite.total_cases


class TestPytestExporter:
    def test_export_pytest_file(self, sample_test_suite, tmp_path):
        exporter = PytestExporter()
        output = tmp_path / "test_generated.py"
        code = exporter.export([sample_test_suite], output_path=str(output))

        assert output.exists()
        assert "from flask_app.app import create_app" in code
        assert "def client()" in code


class TestExporterFactory:
    def test_create_json(self):
        exporter = ExporterFactory.create(ExportFormat.JSON)
        assert isinstance(exporter, JSONExporter)

    def test_create_pytest(self):
        exporter = ExporterFactory.create(ExportFormat.PYTEST)
        assert isinstance(exporter, PytestExporter)

    def test_available_formats(self):
        assert ExporterFactory.get_available_formats() == ["json", "pytest"]

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            ExporterFactory.create("invalid")
