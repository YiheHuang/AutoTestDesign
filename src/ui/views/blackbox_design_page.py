"""黑盒测试设计 (v2.2: LLM生成EP/BVA/DT分析表+用例)"""

import streamlit as st
import pandas as pd
from src.test_design.black_box.orchestrator import BlackBoxOrchestrator
from src.utils.constants import TECHNIQUE_EP, TECHNIQUE_BVA, TECHNIQUE_DT


def render():
    st.title("黑盒测试设计")
    st.markdown("选择标准需求 + 测试技术 -> LLM 生成分析表与测试用例")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求")
        return

    req_options = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    selected_name = st.selectbox("选择标准需求", list(req_options.keys()))
    selected_req = req_options[selected_name]

    techniques = st.multiselect(
        "选择技术",
        ["EP (等价类划分)", "BVA (边界值分析)", "DT (判定表)"],
        default=["EP (等价类划分)", "BVA (边界值分析)", "DT (判定表)"]
    )
    tech_map = {"EP (等价类划分)": "EP", "BVA (边界值分析)": "BVA", "DT (判定表)": "DecisionTable"}
    enabled = [tech_map[t] for t in techniques]

    if st.button("LLM 生成黑盒测试", type="primary", use_container_width=True):
        with st.spinner(f"LLM 生成中 ({', '.join(enabled)})..."):
            orch = BlackBoxOrchestrator()
            suite, analysis = orch.generate_all(selected_req, enabled)
            st.session_state.test_suites[selected_req.id] = suite
            st.session_state[f"analysis_{selected_req.id}"] = analysis
            st.success(f"生成 {suite.total_cases} 个测试用例")
            st.rerun()

    suite = st.session_state.test_suites.get(selected_req.id)
    analysis = st.session_state.get(f"analysis_{selected_req.id}", {})
    if not suite or not suite.test_cases:
        st.info("点击按钮生成")
        return

    st.divider()
    st.metric("总用例数", suite.total_cases)

    tabs = st.tabs(["等价类划分", "边界值分析", "判定表", "全部用例"])

    with tabs[0]:
        ep_data = analysis.get(TECHNIQUE_EP)
        if ep_data:
            st.subheader("等价类划分表")
            for fd in ep_data:
                st.markdown(f"**字段: `{fd.get('field','?')}`**")
                rows = [{"类型": c["type"], "描述": c["description"], "代表值": str(c.get("representative_value",""))} for c in fd.get("classes",[])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        ep_cases = suite.get_cases_by_technique(TECHNIQUE_EP)
        st.subheader(f"等价类测试用例 ({len(ep_cases)} 个)")
        _cases(ep_cases)

    with tabs[1]:
        ba_data = analysis.get(TECHNIQUE_BVA)
        if ba_data:
            st.subheader("边界值分析表")
            for fd in ba_data:
                st.markdown(f"**字段: `{fd.get('field','?')}`** (范围: {fd.get('valid_range','?')})")
                rows = [{"边界点": bp["point"], "值": str(bp["value"]), "应通过": "YES" if bp.get("should_pass") else "NO"} for bp in fd.get("boundary_points",[])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        bva_cases = suite.get_cases_by_technique(TECHNIQUE_BVA)
        st.subheader(f"边界值测试用例 ({len(bva_cases)} 个)")
        _cases(bva_cases)

    with tabs[2]:
        dt_data = analysis.get(TECHNIQUE_DT)
        if dt_data:
            st.subheader("判定表")
            st.caption(f"条件: {', '.join(dt_data.get('conditions',[]))}")
            st.caption(f"动作: {', '.join(dt_data.get('actions',[]))}")
            rules = dt_data.get("simplified_rules", dt_data.get("decision_table", []))
            if rules:
                rows = [{"规则": r.get("rule_id",""), "条件": str(r.get("values","")), "动作": r.get("expected_action",""), "说明": r.get("description","")} for r in rules]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        dt_cases = suite.get_cases_by_technique(TECHNIQUE_DT)
        st.subheader(f"判定表测试用例 ({len(dt_cases)} 个)")
        _cases(dt_cases)

    with tabs[3]:
        _cases(suite.test_cases)


def _cases(cases):
    for tc in cases[:40]:
        icon = "V" if tc.category == "Valid" else "X"
        with st.expander(f"[{icon}] {tc.id}: {tc.title} [{tc.technique}]"):
            if tc.description:
                st.markdown(tc.description)
            if tc.test_steps:
                for s in tc.test_steps:
                    st.json(s.input_data)
                    if s.expected_result:
                        st.info(f"预期: {s.expected_result}")
