"""风险分析数据模型 (v2.2)"""

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    requirement_id: str = Field(description="关联需求ID")
    risk_level: str = Field(default="Medium", description="风险等级: High, Medium, Low")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")
    test_priority: str = Field(default="Medium", description="测试优先级: High, Medium, Low")
    priority_reason: str = Field(default="", description="优先级判定原因")
