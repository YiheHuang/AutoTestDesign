"""黑盒编排器 (v2.2)"""

import datetime
from src.models.requirement import StructuredRequirement
from src.models.testcase import TestSuite
from src.test_design.black_box.equivalence_partition import EPGenerator
from src.test_design.black_box.boundary_value import BVAGenerator
from src.test_design.black_box.decision_table import DTGenerator
from src.utils.constants import TECHNIQUE_EP, TECHNIQUE_BVA, TECHNIQUE_DT
from src.utils.logger import logger


class BlackBoxOrchestrator:
    def __init__(self):
        self.tech_map = {
            "EP": EPGenerator(),
            "BVA": BVAGenerator(),
            "DecisionTable": DTGenerator()
        }

    def generate_all(self, req: StructuredRequirement, enabled: list[str]):
        all_cases = []
        analysis = {}
        for tech_name in enabled:
            gen = self.tech_map.get(tech_name)
            if not gen:
                continue
            try:
                data, cases = gen.generate(req)
                all_cases.extend(cases)
                analysis[gen.name] = data
                logger.info(f"  {gen.name}: {len(cases)} 用例")
            except Exception as e:
                logger.error(f"  {tech_name} 失败: {e}")
                analysis[gen.name if gen else tech_name] = None

        suite = TestSuite(
            id=f"TS-BB-{req.id}",
            name=f"黑盒测试套件 - {req.title}",
            requirement_id=req.id,
            test_cases=all_cases,
            created_at=datetime.datetime.now().isoformat(),
            coverage_summary={"total_cases": len(all_cases), "techniques_used": enabled}
        )
        return suite, analysis
