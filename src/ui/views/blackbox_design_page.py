"""黑盒测试设计 — Step 3"""

import streamlit as st
import pandas as pd
from src.test_design.black_box.orchestrator import BlackBoxOrchestrator
from src.utils.constants import TECHNIQUE_EP, TECHNIQUE_BVA, TECHNIQUE_DT


def render():
    st.title("黑盒测试设计")
    st.caption("EP · BVA · DT — LLM 生成分析表 & 测试用例")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求…")
        return

    opts = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    req = opts[st.selectbox("标准需求", list(opts.keys()))]
    techs = st.multiselect("测试技术", ["EP", "BVA", "DT"], default=["EP", "BVA", "DT"])
    tmap = {"EP": "EP", "BVA": "BVA", "DT": "DecisionTable"}
    enabled = [tmap[t] for t in techs]

    if st.button("生成测试用例", type="primary", use_container_width=True):
        with st.spinner("LLM 生成中…"):
            orch = BlackBoxOrchestrator()
            suite, analysis = orch.generate_all(req, enabled)
            st.session_state.test_suites[req.id] = suite
            st.session_state[f"analysis_{req.id}"] = analysis
            if suite.total_cases:
                st.success(f"完成 — {suite.total_cases} 用例")
            else:
                st.warning("未生成任何用例，请重试…")
            st.rerun()

    suite = st.session_state.test_suites.get(req.id)
    analysis = st.session_state.get(f"analysis_{req.id}", {})
    if not suite or not suite.test_cases:
        st.info("点击上方按钮开始…")
        return

    st.caption(f"共 {suite.total_cases} 用例")
    tabs = st.tabs(["等价类划分", "边界值分析", "判定表", "全部用例"])

    with tabs[0]:
        ep = analysis.get(TECHNIQUE_EP)
        if ep:
            st.caption("等价类划分表")
            for fd in ep:
                st.markdown(f"**`{fd.get('field','?')}`**")
                rows = [{"类型": c["type"], "描述": c["description"], "代表值": str(c.get("representative_value",""))}
                        for c in fd.get("classes", [])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        ep_c = suite.get_cases_by_technique(TECHNIQUE_EP)
        st.caption(f"等价类用例 ({len(ep_c)})")
        _cases(ep_c)

    with tabs[1]:
        ba = analysis.get(TECHNIQUE_BVA)
        if ba:
            st.caption("边界值分析表")
            for fd in ba:
                st.markdown(f"**`{fd.get('field','?')}`**  ({fd.get('valid_range','?')})")
                rows = [{"边界点": bp["point"], "值": str(bp["value"]), "通过": "Yes" if bp.get("should_pass") else "No"}
                        for bp in fd.get("boundary_points", [])]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        bv_c = suite.get_cases_by_technique(TECHNIQUE_BVA)
        st.caption(f"边界值用例 ({len(bv_c)})")
        _cases(bv_c)

    with tabs[2]:
        dt = analysis.get(TECHNIQUE_DT)
        if dt:
            st.caption("判定表")
            st.caption(f"条件: {', '.join(dt.get('conditions',[]))}")
            st.caption(f"动作: {', '.join(dt.get('actions',[]))}")
            rules = dt.get("simplified_rules", dt.get("decision_table", []))
            if rules:
                rows = [{"规则": r.get("rule_id",""), "条件": str(r.get("values","")),
                         "动作": r.get("expected_action",""), "说明": r.get("description","")} for r in rules]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        dt_c = suite.get_cases_by_technique(TECHNIQUE_DT)
        st.caption(f"判定表用例 ({len(dt_c)})")
        _cases(dt_c)

    with tabs[3]:
        _cases(suite.test_cases)


def _cases(cases):
    for tc in cases[:40]:
        lbl = f"{'[V]' if tc.category == 'Valid' else '[X]'} {tc.id}  {tc.title}  [{tc.technique}]"
        with st.expander(lbl):
            if tc.description:
                st.caption(tc.description)
            if tc.test_steps:
                for s in tc.test_steps:
                    st.json(s.input_data)
                    if s.expected_result:
                        st.info(s.expected_result)
