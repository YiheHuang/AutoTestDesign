"""风险分析 — Step 2"""

import streamlit as st
import pandas as pd
from src.risk.risk_analyzer import RiskAnalyzer


def render():
    st.title("风险分析")
    st.caption("LLM 评估每项需求的风险等级 & 测试优先级")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求…")
        return

    if st.button("开始风险分析", type="primary", use_container_width=True):
        with st.spinner("LLM 评估中…"):
            a = RiskAnalyzer().analyze_batch(st.session_state.requirements)
            st.session_state.risk_assessments = a
            st.success(f"完成 — {len(a)} 项")
            st.rerun()

    if not st.session_state.risk_assessments:
        st.info("点击上方按钮开始…")
        return

    a = st.session_state.risk_assessments
    r_hi = sum(1 for x in a if x.risk_level == "High")
    r_md = sum(1 for x in a if x.risk_level == "Medium")
    r_lo = sum(1 for x in a if x.risk_level == "Low")
    p_hi = sum(1 for x in a if x.test_priority == "High")
    p_md = sum(1 for x in a if x.test_priority == "Medium")
    p_lo = sum(1 for x in a if x.test_priority == "Low")

    st.subheader("风险等级")
    c1, c2, c3 = st.columns(3)
    c1.metric("High", r_hi)
    c2.metric("Medium", r_md)
    c3.metric("Low", r_lo)

    st.subheader("测试优先级")
    c1, c2, c3 = st.columns(3)
    c1.metric("High", p_hi)
    c2.metric("Medium", p_md)
    c3.metric("Low", p_lo)

    st.divider()
    rows = [{"需求": x.requirement_id, "风险": x.risk_level, "优先级": x.test_priority,
             "风险因素": "; ".join(x.risk_factors), "原因": x.priority_reason} for x in a]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
