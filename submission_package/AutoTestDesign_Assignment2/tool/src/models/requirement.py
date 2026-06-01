"""需求数据模型 (v2.2: 新增需求-代码映射、测试用例-代码映射、覆盖率报告)"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    TEXT = "text"
    DIRECT = "direct"


class InputField(BaseModel):
    name: str
    data_type: str
    valid_range: Optional[str] = Field(default=None)
    constraints: list[str] = Field(default_factory=list)

    @field_validator("constraints", mode="before")
    @classmethod
    def coerce_constraints(cls, v):
        return [str(x) for x in v] if v else []


class Condition(BaseModel):
    description: str
    field: Optional[str] = Field(default=None)
    operator: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)

    @field_validator("value", "field", "operator", mode="before")
    @classmethod
    def coerce_to_str(cls, v):
        return str(v) if v is not None else None


class SystemBehavior(BaseModel):
    condition: str
    action: str
    expected_output: Optional[str] = Field(default=None)


class StructuredRequirement(BaseModel):
    id: str
    source: SourceType = Field(default=SourceType.TEXT)
    raw_text: str
    title: str
    description: str
    input_fields: list[InputField] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    expected_behaviors: list[SystemBehavior] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    domain: str = Field(default="")

    def get_field_names(self) -> list[str]:
        return [f.name for f in self.input_fields]

    def get_numeric_fields(self) -> list[InputField]:
        return [f for f in self.input_fields if f.data_type in ("integer", "float")]

    def get_condition_count(self) -> int:
        return len(self.conditions)


# ── v2.2 新增模型 ──

class CodeSegment(BaseModel):
    """代码片段 — 描述一段代码的位置"""
    file_path: str = Field(description="文件相对路径")
    start_line: int = Field(description="起始行号")
    end_line: int = Field(description="结束行号")
    function_name: str = Field(default="", description="所属函数名")
    description: str = Field(default="", description="此代码片段与需求的关系")


class RequirementCodeMapping(BaseModel):
    """需求-代码映射 — 一个需求对应哪些代码片段"""
    requirement_id: str
    requirement_title: str = Field(default="")
    code_segments: list[CodeSegment] = Field(default_factory=list)


class TestCaseCodeMapping(BaseModel):
    """测试用例-代码覆盖映射 — 一个测试用例覆盖哪些代码片段"""
    test_case_id: str
    test_case_title: str = Field(default="")
    covered_segments: list[CodeSegment] = Field(default_factory=list)


class CoverageReport(BaseModel):
    """覆盖率报告"""
    total_lines: int = Field(default=0)
    covered_lines: int = Field(default=0)
    coverage_pct: float = Field(default=0.0)
    uncovered_segments: list[CodeSegment] = Field(default_factory=list)
    total_segments: int = Field(default=0)
    covered_segments: list[CodeSegment] = Field(default_factory=list)
