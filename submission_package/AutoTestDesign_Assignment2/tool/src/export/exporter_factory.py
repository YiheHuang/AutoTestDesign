"""导出工厂 (v2.2: 仅JSON+pytest)"""

from enum import Enum
from src.models.testcase import TestSuite
from src.export.json_exporter import JSONExporter
from src.export.pytest_exporter import PytestExporter
from src.utils.logger import logger


class ExportFormat(str, Enum):
    JSON = "json"
    PYTEST = "pytest"


class ExporterFactory:
    @classmethod
    def create(cls, fmt: ExportFormat):
        if fmt == ExportFormat.JSON:
            return JSONExporter()
        elif fmt == ExportFormat.PYTEST:
            return PytestExporter()
        raise ValueError(f"不支持的格式: {fmt}")

    @classmethod
    def export(cls, suites: list[TestSuite], fmt: ExportFormat,
               reqs_json: str = "[]", mappings_json: str = "[]",
               output_path: str = "flask_app/tests/test_generated.py") -> str:
        exporter = cls.create(fmt)
        if fmt == ExportFormat.PYTEST:
            return exporter.export(suites, reqs_json, mappings_json, output_path)
        else:
            if len(suites) == 1:
                return exporter.export(suites[0])
            return exporter.export_multiple(suites)

    @classmethod
    def get_available_formats(cls) -> list[str]:
        return ["json", "pytest"]
