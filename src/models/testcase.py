"""测试用例数据模型 (v2.2)"""

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class TestStep(BaseModel):
    step_number: int = Field(default=1)
    action: str = Field(default="")
    input_data: dict[str, Any] = Field(default_factory=dict)
    expected_result: str = Field(default="")

    @field_validator("expected_result", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        if isinstance(v, dict):
            import json
            return json.dumps(v, ensure_ascii=False)
        return str(v) if v is not None else ""


class TestCase(BaseModel):
    id: str
    requirement_id: str
    title: str
    description: str = Field(default="")
    technique: str = Field(default="")
    category: str = Field(default="Valid")
    preconditions: list[str] = Field(default_factory=list)
    test_steps: list[TestStep] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    id: str
    name: str
    requirement_id: str
    test_cases: list[TestCase] = Field(default_factory=list)
    created_at: str = Field(default="")
    coverage_summary: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_cases(self) -> int:
        return len(self.test_cases)

    def get_cases_by_technique(self, technique: str) -> list[TestCase]:
        return [tc for tc in self.test_cases if tc.technique == technique]
