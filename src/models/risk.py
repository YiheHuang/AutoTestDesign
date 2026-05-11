"""风险分析数据模型 (v2.2 简化版)"""

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    """风险评估 — 仅保留风险等级和因素"""
    requirement_id: str = Field(description="关联需求ID")
    risk_level: str = Field(default="Medium", description="风险等级: High, Medium, Low")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素列表")
