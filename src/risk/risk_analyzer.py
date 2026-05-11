"""风险分析引擎 (v2.2: LLM输出risk_level + risk_factors)"""

import json
from src.models.risk import RiskAssessment
from src.models.requirement import StructuredRequirement
from src.ai.client import get_ai_client
from src.ai.prompts.risk_prompts import RISK_SYSTEM_PROMPT, RISK_USER_TEMPLATE
from src.utils.logger import logger


class RiskAnalyzer:
    """风险分析 — LLM评估每项需求的风险等级和因素"""

    def analyze_batch(self, reqs: list[StructuredRequirement]) -> list[RiskAssessment]:
        if not reqs:
            return []

        logger.info(f"LLM风险分析: {len(reqs)} 条需求")

        reqs_json = json.dumps(
            [{"id": r.id, "title": r.title, "description": r.description} for r in reqs],
            ensure_ascii=False, indent=2
        )

        try:
            ai_client = get_ai_client()
            result = ai_client.chat_with_json(
                system_prompt=RISK_SYSTEM_PROMPT,
                user_message=RISK_USER_TEMPLATE.format(requirements_json=reqs_json),
                temperature=0.1
            )

            assessments = []
            result_list = result.get("assessments", []) if result else []
            for a in result_list:
                assessments.append(RiskAssessment(
                    requirement_id=a.get("requirement_id", ""),
                    risk_level=a.get("risk_level", "Medium"),
                    risk_factors=a.get("risk_factors", [])
                ))

            # 补充LLM未返回的需求(默认Medium)
            existing_ids = {a.requirement_id for a in assessments}
            for r in reqs:
                if r.id not in existing_ids:
                    assessments.append(RiskAssessment(
                        requirement_id=r.id,
                        risk_level="Medium",
                        risk_factors=["LLM未返回，默认中风险"]
                    ))

            logger.info(f"风险分析完成: {len(assessments)} 项")
            return assessments

        except Exception as e:
            logger.error(f"风险分析失败: {e}")
            return [
                RiskAssessment(requirement_id=r.id, risk_level="Medium", risk_factors=["分析失败(默认)"])
                for r in reqs
            ]
