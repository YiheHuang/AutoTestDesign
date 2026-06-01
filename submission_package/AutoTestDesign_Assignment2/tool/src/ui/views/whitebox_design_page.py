"""白盒测试设计 — Step 4"""

import json
import streamlit as st
import pandas as pd
from src.test_design.white_box.whitebox_orchestrator import WhiteBoxOrchestrator
from src.models.testcase import TestStep


def render():
    st.title("白盒测试设计")
    st.caption("路径覆盖 & 状态转换 — LLM 分析代码生成测试用例")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求…")
        return

    opts = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    req = opts[st.selectbox("标准需求", list(opts.keys()))]
    mapping = st.session_state.get("req_code_mappings", {}).get(req.id)
    if not mapping:
        st.warning("该需求无代码映射，请先在「需求输入」生成…")
        return

    import os
    sources = {}
    for seg in mapping.code_segments:
        fp = seg.file_path
        if fp not in sources:
            try:
                full = os.path.join(st.session_state.get("code_folder", "flask_app"), fp)
                with open(full, encoding="utf-8") as f:
                    sources[fp] = f.read()
            except Exception:
                pass
    src_text = "\n\n".join(f"=== {p} ===\n{c}" for p, c in sources.items())

    techs = st.multiselect("测试技术", ["PathCoverage", "StateTransition"],
                           default=["PathCoverage", "StateTransition"])
    tmap = {"PathCoverage": "PathCoverage", "StateTransition": "State Transition"}
    enabled = [tmap[t] for t in techs]

    if st.button("生成测试用例", type="primary", use_container_width=True):
        with st.spinner("LLM 分析中…"):
            try:
                orch = WhiteBoxOrchestrator()
                suite, analysis = orch.generate_all(req, mapping, src_text, enabled)
                st.session_state.test_suites[f"WB-{req.id}"] = suite
                st.session_state[f"wb_analysis_{req.id}"] = analysis
                if suite.total_cases:
                    st.success(f"完成 — {suite.total_cases} 用例")
                else:
                    st.warning("未生成任何用例，请重试…")
                st.rerun()
            except Exception as e:
                st.error(f"失败: {e}")

    sid = f"WB-{req.id}"
    suite = st.session_state.test_suites.get(sid)
    analysis = st.session_state.get(f"wb_analysis_{req.id}", {})
    if not suite:
        st.info("点击上方按钮开始…")
        return

    st.caption(f"共 {suite.total_cases} 用例")
    pc = analysis.get("PathCoverage", {})
    st_data = analysis.get("State Transition", {})

    tabs = []
    if pc:
        tabs.append("路径覆盖")
    if st_data and (st_data.get("state_machine") or st_data.get("all_states_paths")):
        tabs.append("状态转换")
    if not tabs:
        tabs = ["结果"]

    tab_objs = st.tabs(tabs)
    for i, name in enumerate(tabs):
        with tab_objs[i]:
            if name == "路径覆盖":
                _pc(pc)
            elif name == "状态转换":
                _st(st_data, suite)

    st.divider()
    st.subheader("测试用例审查与修改")
    _editable_cases(sid, suite)


def _pc(pc):
    cov = pc.get("coverage_report")
    tcms = pc.get("tc_mappings", [])
    cases = pc.get("cases", [])
    if cov:
        st.subheader("覆盖率")
        c1, c2, c3 = st.columns(3)
        c1.metric("关联行", cov.total_lines)
        c2.metric("覆盖行", cov.covered_lines)
        c3.metric("覆盖率", f"{cov.coverage_pct}%")
        if cov.uncovered_segments:
            st.warning(f"{len(cov.uncovered_segments)} 代码段未覆盖")
            for s in cov.uncovered_segments:
                st.caption(f"{s.file_path} L{s.start_line}–{s.end_line}  {s.description}")
    if tcms:
        st.subheader("覆盖映射")
        for tcm in tcms[:15]:
            with st.expander(f"{tcm.test_case_id}  {tcm.test_case_title}"):
                for s in tcm.covered_segments:
                    st.caption(f"{s.file_path} L{s.start_line}–{s.end_line}  {s.function_name}()")
    st.subheader(f"用例 ({len(cases)})")
    for tc in cases[:20]:
        with st.expander(f"{tc.id}  {tc.title}"):
            if tc.description:
                st.caption(tc.description)
            if tc.test_steps:
                for s in tc.test_steps:
                    if s.action:
                        st.caption(s.action)
                    st.json(s.input_data)
                    if s.expected_result:
                        st.info(s.expected_result)


def _st(st_data, suite):
    sm = st_data.get("state_machine")
    paths = st_data.get("all_states_paths", [])
    if sm:
        st.subheader("状态转换图")
        st.caption(f"{sm.state_count} 状态, {sm.transition_count} 转换")
        st.dataframe(pd.DataFrame([{"ID": s.id, "名称": s.name, "初始": s.is_initial, "终止": s.is_final}
                                    for s in sm.states]), use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame([{"ID": t.id, "从": t.from_state, "到": t.to_state, "触发": t.trigger,
                                     "守卫": t.guard or "—", "动作": t.action or "—"}
                                    for t in sm.transitions]), use_container_width=True, hide_index=True)
    if paths:
        st.subheader(f"All-States 路径 ({len(paths)})")
        for p in paths:
            st.markdown(f"- {' → '.join(p.get('path',[]))}  |  {p.get('description','')}")
    st_cases = suite.get_cases_by_technique("State Transition")
    if st_cases:
        st.subheader(f"用例 ({len(st_cases)})")
        for tc in st_cases[:20]:
            with st.expander(f"{tc.id}  {tc.title}"):
                if tc.description:
                    st.caption(tc.description)
                for s in tc.test_steps:
                    st.markdown(f"**Step {s.step_number}**: {s.action}")
                    if s.input_data:
                        st.json(s.input_data)
                    if s.expected_result:
                        st.info(s.expected_result)


def _editable_cases(key, suite):
    rows = []
    for tc in suite.test_cases:
        step = tc.test_steps[0] if tc.test_steps else TestStep()
        rows.append({
            "ID": tc.id,
            "标题": tc.title,
            "描述": tc.description,
            "技术": tc.technique,
            "类别": tc.category,
            "输入JSON": json.dumps(step.input_data, ensure_ascii=False),
            "预期结果": step.expected_result,
        })

    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "技术"],
        column_config={
            "类别": st.column_config.SelectboxColumn("类别", options=["Valid", "Invalid", "Boundary"]),
        },
        key=f"wb_editor_{key}"
    )

    if st.button("保存白盒用例修改", use_container_width=True, key=f"save_wb_{key}"):
        by_id = {tc.id: tc for tc in suite.test_cases}
        for row in edited.to_dict("records"):
            tc = by_id[row["ID"]]
            tc.title = str(row["标题"])
            tc.description = str(row["描述"])
            tc.category = str(row["类别"])
            if not tc.test_steps:
                tc.test_steps = [TestStep()]
            try:
                tc.test_steps[0].input_data = json.loads(row["输入JSON"]) if str(row["输入JSON"]).strip() else {}
            except Exception:
                st.error(f"{tc.id} 的输入JSON格式无效")
                return
            tc.test_steps[0].expected_result = str(row["预期结果"])
        st.session_state.test_suites[key] = suite
        st.success("已保存白盒用例修改")
        st.rerun()
