"""JSON格式导出器 - FR 6.0"""

import json
import datetime
from src.models.testcase import TestSuite
from src.models.risk import RiskAssessment
from src.utils.logger import logger


class JSONExporter:
    """导出为标准JSON格式

    格式符合ISTQB测试文档规范，可直接被测试管理工具解析。
    """

    def export(
        self,
        suite: TestSuite,
        risk: RiskAssessment | None = None,
        include_metadata: bool = True
    ) -> str:
        """导出测试套件为JSON字符串

        Args:
            suite: 测试套件
            risk: 相关风险评估
            include_metadata: 是否包含元数据

        Returns:
            格式化的JSON字符串
        """
        output = {
            "test_suite": {
                "id": suite.id,
                "name": suite.name,
                "requirement_id": suite.requirement_id,
                "test_cases": [tc.model_dump() for tc in suite.test_cases],
                "summary": {
                    "total_cases": suite.total_cases,
                    "techniques": self._summarize_techniques(suite),
                }
            }
        }

        if risk:
            output["risk_assessment"] = risk.model_dump()

        if include_metadata:
            output["metadata"] = {
                "generated_by": "AutoTestDesign v2.2",
                "generated_at": datetime.datetime.now().isoformat(),
                "standard": "ISO/IEC 29119-4",
                "techniques_used": list(
                    set(tc.technique for tc in suite.test_cases)
                )
            }

        logger.info(f"JSON导出: {suite.id}, {suite.total_cases}个用例")
        return json.dumps(output, ensure_ascii=False, indent=2)

    def export_multiple(
        self,
        suites: list[TestSuite],
        risks: list[RiskAssessment] | None = None
    ) -> str:
        """导出多个测试套件"""
        output = {
            "test_suites": []
        }

        risk_map = {}
        if risks:
            risk_map = {r.requirement_id: r for r in risks}

        for suite in suites:
            risk = risk_map.get(suite.requirement_id)
            suite_data = json.loads(self.export(suite, risk, include_metadata=False))
            output["test_suites"].append(suite_data["test_suite"])

        output["metadata"] = {
            "generated_by": "AutoTestDesign v2.2",
            "generated_at": datetime.datetime.now().isoformat(),
            "total_suites": len(suites),
            "total_cases": sum(s.total_cases for s in suites)
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    def _summarize_techniques(self, suite: TestSuite) -> dict:
        """统计各技术生成的用例数"""
        counts = {}
        for tc in suite.test_cases:
            counts[tc.technique] = counts.get(tc.technique, 0) + 1
        return counts
