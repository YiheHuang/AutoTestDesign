"""白盒编排器 (v2.2: 路径覆盖 + 状态转换)"""

import datetime
from src.models.requirement import StructuredRequirement, RequirementCodeMapping
from src.models.testcase import TestSuite
from src.test_design.white_box.path_coverage import PathCoverageGenerator
from src.test_design.white_box.state_transition import StateTransitionGenerator
from src.utils.logger import logger


class WhiteBoxOrchestrator:

    def __init__(self):
        self.path_gen = PathCoverageGenerator()
        self.state_gen = StateTransitionGenerator()

    def generate_all(
        self,
        req: StructuredRequirement,
        req_code_mapping: RequirementCodeMapping,
        source_code: str,
        enabled: list[str]
    ) -> tuple[TestSuite, dict]:
        """生成启用的白盒测试技术

        Args:
            enabled: ["PathCoverage"] 或 ["State Transition"] 或两者
        """
        all_cases = []
        analysis = {}

        if "PathCoverage" in enabled:
            try:
                cases, coverage, tc_mappings = self.path_gen.generate(req, req_code_mapping, source_code)
                all_cases.extend(cases)
                analysis["PathCoverage"] = {
                    "coverage_report": coverage,
                    "tc_mappings": tc_mappings,
                    "cases": cases
                }
                logger.info(f"  路径覆盖: {len(cases)} 用例, 覆盖率 {coverage.coverage_pct}%")
            except Exception as e:
                logger.error(f"  路径覆盖失败: {e}")

        if "State Transition" in enabled:
            try:
                st_data, st_cases = self.state_gen.generate(req, req_code_mapping, source_code)
                all_cases.extend(st_cases)
                analysis["State Transition"] = st_data
                logger.info(f"  状态转换: {len(st_cases)} 用例")
            except Exception as e:
                logger.error(f"  状态转换失败: {e}")

        suite = TestSuite(
            id=f"TS-WB-{req.id}",
            name=f"白盒测试套件 - {req.title}",
            requirement_id=req.id,
            test_cases=all_cases,
            created_at=datetime.datetime.now().isoformat(),
            coverage_summary={
                "total_cases": len(all_cases),
                "techniques_used": enabled,
                **({"tc_mappings": analysis.get("PathCoverage", {}).get("tc_mappings", [])} if "PathCoverage" in analysis else {}),
                **({"coverage_report": analysis.get("PathCoverage", {}).get("coverage_report")} if "PathCoverage" in analysis else {})
            }
        )
        return suite, analysis
