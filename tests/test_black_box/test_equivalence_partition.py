"""等价类划分生成器测试"""

import pytest
from src.test_design.black_box.equivalence_partition import EPGenerator


class TestEPGenerator:
    def test_name(self):
        gen = EPGenerator()
        assert gen.name == "Equivalence Partitioning"

    def test_generate_with_rule_engine(self, sample_requirement):
        gen = EPGenerator()
        cases = gen.generate(sample_requirement, use_ai=False)
        assert len(cases) > 0
        # 每个input_field应该有有效类和无效类
        valid_cases = [c for c in cases if c.category == "Valid"]
        invalid_cases = [c for c in cases if c.category == "Invalid"]
        assert len(valid_cases) > 0
        assert len(invalid_cases) > 0

    def test_generate_all_technique_tagged(self, sample_requirement):
        gen = EPGenerator()
        cases = gen.generate(sample_requirement, use_ai=False)
        for case in cases:
            assert case.technique == "Equivalence Partitioning"
            assert case.requirement_id == sample_requirement.id

    def test_generate_empty_fields(self):
        gen = EPGenerator()
        from src.models.requirement import StructuredRequirement
        req = StructuredRequirement(
            id="REQ-EMPTY",
            source="text",
            raw_text="无输入字段的需求",
            title="空需求",
            description="没有input_fields",
            domain="test"
        )
        cases = gen.generate(req, use_ai=False)
        assert cases == []
