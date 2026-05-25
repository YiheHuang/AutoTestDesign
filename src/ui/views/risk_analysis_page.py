"""风险分析 (v2.2: risk_level + test_priority + reasons)"""

import streamlit as st
import pandas as pd
from src.risk.risk_analyzer import RiskAnalyzer


def render():
    st.title("风险分析")
    st.markdown("LLM 评估每项需求的风险等级与测试优先级")

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

    # 统计
    risk_high = sum(1 for x in a if x.risk_level == "High")
    risk_med = sum(1 for x in a if x.risk_level == "Medium")
    risk_low = sum(1 for x in a if x.risk_level == "Low")
    pri_high = sum(1 for x in a if x.test_priority == "High")
    pri_med = sum(1 for x in a if x.test_priority == "Medium")
    pri_low = sum(1 for x in a if x.test_priority == "Low")

    st.subheader("风险等级分布")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High 风险", risk_high)
    with col2:
        st.metric("Medium 风险", risk_med)
    with col3:
        st.metric("Low 风险", risk_low)

    st.subheader("测试优先级分布")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High 优先", pri_high)
    with col2:
        st.metric("Medium 优先", pri_med)
    with col3:
        st.metric("Low 优先", pri_low)

    st.divider()

    # 详细表格
    rows = [{
        "需求ID": x.requirement_id,
        "风险等级": x.risk_level,
        "风险因素": "; ".join(x.risk_factors),
        "测试优先级": x.test_priority,
        "优先级原因": x.priority_reason
    } for x in a]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 逐条展开详情
    for x in a:
        with st.expander(f"{x.requirement_id}: 风险={x.risk_level} | 优先级={x.test_priority}"):
            st.markdown(f"**风险因素**: {'; '.join(x.risk_factors) if x.risk_factors else '无'}")
            st.markdown(f"**优先级原因**: {x.priority_reason or '无'}")
