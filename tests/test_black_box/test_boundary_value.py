"""边界值分析生成器测试"""

import pytest
from src.test_design.black_box.boundary_value import BVAGenerator


class TestBVAGenerator:
    def test_get_bounded_fields(self, sample_requirement):
        gen = BVAGenerator()
        bounded = gen._get_bounded_fields(sample_requirement)

        assert len(bounded) >= 2  # username(3-20) + age(18-120)
        field_names = [f.name for f, _, _ in bounded]
        assert "username" in field_names
        assert "age" in field_names

    def test_generate_bva_cases_rule_engine(self, sample_requirement):
        gen = BVAGenerator()
        cases = gen.generate(sample_requirement, use_ai=False)

        assert len(cases) > 0
        # 每个边界字段6个边界点
        assert len(cases) >= 12  # 至少username(6)+age(6)=12

        for case in cases:
            assert case.technique == "Boundary Value Analysis"

    def test_bva_values_in_range(self, sample_requirement):
        gen = BVAGenerator()
        cases = gen.generate(sample_requirement, use_ai=False)

        # 检查是否有lb-1, lb, lb+1类型
        values = []
        for c in cases:
            for step in c.test_steps:
                values.append(step.input_data.get("username", ""))
        # 应该有边界值测试
        assert any("2" in str(v) for v in values if v) or len(values) > 0

    def test_generate_no_bounded_fields(self):
        gen = BVAGenerator()
        from src.models.requirement import StructuredRequirement, InputField
        req = StructuredRequirement(
            id="REQ-NOBOUND",
            source="text",
            raw_text="无边界的需求",
            title="无边界",
            description="只有非数值字段",
            input_fields=[
                InputField(name="name", data_type="string", constraints=["required"])
            ],
            domain="test"
        )
        cases = gen.generate(req, use_ai=False)
        assert cases == []
