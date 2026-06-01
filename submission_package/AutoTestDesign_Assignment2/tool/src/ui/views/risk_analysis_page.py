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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("High", r_hi)
    c2.metric("Medium", r_md)
    c3.metric("Low", r_lo)
    c4.metric("平均分", f"{round(sum(x.risk_score for x in a) / max(1, len(a)), 1)}")

    st.subheader("测试优先级")
    c1, c2, c3 = st.columns(3)
    c1.metric("High", p_hi)
    c2.metric("Medium", p_md)
    c3.metric("Low", p_lo)

    st.divider()
    rows = [{"需求": x.requirement_id, "风险分数": x.risk_score, "风险": x.risk_level, "优先级": x.test_priority,
             "风险因素": "; ".join(x.risk_factors), "原因": x.priority_reason} for x in a]
    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        disabled=["需求"],
        column_config={
            "风险分数": st.column_config.NumberColumn("风险分数", min_value=0, max_value=100, step=1),
            "风险": st.column_config.SelectboxColumn("风险", options=["High", "Medium", "Low"]),
            "优先级": st.column_config.SelectboxColumn("优先级", options=["High", "Medium", "Low"]),
        }
    )
    if st.button("保存修改", use_container_width=True):
        by_id = {x.requirement_id: x for x in a}
        for row in edited.to_dict("records"):
            rid = row["需求"]
            item = by_id.get(rid)
            if item:
                item.risk_score = int(row["风险分数"])
                item.risk_level = row["风险"]
                item.test_priority = row["优先级"]
                item.risk_factors = [s.strip() for s in str(row["风险因素"]).split(";") if s.strip()]
                item.priority_reason = str(row["原因"])
        st.session_state.risk_assessments = list(by_id.values())
        st.success("已保存风险分析修改")
        st.rerun()
