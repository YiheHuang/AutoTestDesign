"""路径覆盖 (v2.2: LLM输出用例+覆盖代码图+覆盖率计算)"""

import json
from src.models.requirement import (
    StructuredRequirement, RequirementCodeMapping,
    TestCaseCodeMapping, CodeSegment, CoverageReport
)
from src.models.testcase import TestCase, TestStep
from src.ai.client import get_ai_client
from src.ai.prompts.path_coverage_prompts import (
    PATH_COVERAGE_SYSTEM_PROMPT, PATH_COVERAGE_USER_TEMPLATE
)
from src.utils.logger import logger


class PathCoverageGenerator:
    name = "PathCoverage"

    def generate(
        self,
        req: StructuredRequirement,
        req_code_mapping: RequirementCodeMapping,
        source_code: str
    ) -> tuple[list[TestCase], CoverageReport, list[TestCaseCodeMapping]]:
        """生成路径覆盖测试用例 + 覆盖率报告

        Returns:
            (test_cases, coverage_report, tc_code_mappings)
        """
        logger.info(f"LLM路径覆盖: {req.id}")

        ai_client = get_ai_client()
        mapping_json = req_code_mapping.model_dump_json(indent=2)

        user_message = PATH_COVERAGE_USER_TEMPLATE.format(
            requirement_json=req.model_dump_json(indent=2),
            req_code_mapping=mapping_json,
            source_code=source_code
        )

        result = ai_client.chat_with_json(
            system_prompt=PATH_COVERAGE_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.1
        )

        if not result:
            logger.warning("LLM路径覆盖返回空")
            return [], CoverageReport(), []

        # 解析测试用例
        test_cases = []
        tc_mappings = []

        for i, tc_data in enumerate(result.get("test_cases", [])):
            tc_id = tc_data.get("id", f"TC-PC-{req.id}-{i + 1:03d}")
            tc = TestCase(
                id=tc_id,
                requirement_id=req.id,
                title=tc_data.get("title", ""),
                description=tc_data.get("description", ""),
                technique=self.name,
                category=tc_data.get("category", "Valid"),
                test_steps=[TestStep(
                    step_number=1,
                    action=tc_data.get("path_description", ""),
                    input_data=tc_data.get("input_data", {}),
                    expected_result=tc_data.get("expected_result", "")
                )],
                tags=["path_coverage"]
            )
            test_cases.append(tc)

            # 解析覆盖代码段
            segments = []
            for cl in tc_data.get("covered_lines", []):
                try:
                    segments.append(CodeSegment(
                        file_path=cl.get("file_path", ""),
                        start_line=int(cl.get("start_line", 0)),
                        end_line=int(cl.get("end_line", 0)),
                        function_name=cl.get("function_name", ""),
                        description=cl.get("description", "")
                    ))
                except Exception:
                    pass

            if segments:
                tc_mappings.append(TestCaseCodeMapping(
                    test_case_id=tc_id,
                    test_case_title=tc.title,
                    covered_segments=segments
                ))

        # 计算覆盖率
        coverage = self._compute_coverage(req_code_mapping, tc_mappings)
        logger.info(f"路径覆盖完成: {len(test_cases)} 用例, 覆盖率 {coverage.coverage_pct}%")
        return test_cases, coverage, tc_mappings

    def _compute_coverage(
        self,
        req_mapping: RequirementCodeMapping,
        tc_mappings: list[TestCaseCodeMapping]
    ) -> CoverageReport:
        all_segments = req_mapping.code_segments
        all_lines = {(seg.file_path, ln)
                     for seg in all_segments
                     for ln in range(seg.start_line, seg.end_line + 1)}
        total_lines = len(all_lines)

        covered = set()
        covered_segs = []
        for tcm in tc_mappings:
            for seg in tcm.covered_segments:
                for ln in range(seg.start_line, seg.end_line + 1):
                    covered.add((seg.file_path, ln))
                if seg not in covered_segs:
                    covered_segs.append(seg)

        covered_lines = len(covered)
        pct = round(covered_lines / max(1, total_lines) * 100, 1)

        uncovered = [seg for seg in all_segments
                     if not any((seg.file_path, ln) in covered
                                for ln in range(seg.start_line, seg.end_line + 1))]

        return CoverageReport(
            total_lines=total_lines,
            covered_lines=covered_lines,
            coverage_pct=pct,
            uncovered_segments=uncovered,
            total_segments=len(all_segments),
            covered_segments=covered_segs
        )
