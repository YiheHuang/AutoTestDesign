"""风险分析 (v2.2: risk_level + risk_factors)"""

import streamlit as st
import pandas as pd
from src.risk.risk_analyzer import RiskAnalyzer


def render():
    st.title("风险分析")
    st.markdown("LLM 评估每项需求的风险等级与风险因素")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求")
        return

    if st.button("LLM 风险分析", type="primary", use_container_width=True):
        with st.spinner("LLM 评估中..."):
            assessments = RiskAnalyzer().analyze_batch(st.session_state.requirements)
            st.session_state.risk_assessments = assessments
            st.success(f"完成 {len(assessments)} 项")
            st.rerun()

    if not st.session_state.risk_assessments:
        st.info("点击上方按钮启动")
        return

    a = st.session_state.risk_assessments
    high = sum(1 for x in a if x.risk_level == "High")
    med = sum(1 for x in a if x.risk_level == "Medium")
    low = sum(1 for x in a if x.risk_level == "Low")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High", high)
    with col2:
        st.metric("Medium", med)
    with col3:
        st.metric("Low", low)

    st.divider()
    rows = [{"需求ID": x.requirement_id, "风险等级": x.risk_level, "风险因素": "; ".join(x.risk_factors)} for x in a]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
