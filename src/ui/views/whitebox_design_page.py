"""白盒测试设计 (v2.2: 路径覆盖 + 状态转换)"""

import streamlit as st
import pandas as pd
from src.test_design.white_box.whitebox_orchestrator import WhiteBoxOrchestrator
from src.models.testcase import TestSuite


def render():
    st.title("白盒测试设计")
    st.markdown("路径覆盖分析 / 状态转换建模 -> LLM 生成测试用例")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求")
        return

    req_options = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    selected_name = st.selectbox("选择标准需求", list(req_options.keys()))
    selected_req = req_options[selected_name]

    mapping = st.session_state.get("req_code_mappings", {}).get(selected_req.id)
    if not mapping:
        st.warning("该需求无代码映射，请先在「需求输入」生成")
        return

    # 读取源码
    sources = {}
    for seg in mapping.code_segments:
        fp = seg.file_path
        if fp not in sources:
            try:
                import os
                full = os.path.join(st.session_state.get("code_folder", "flask_app"), fp)
                with open(full, "r", encoding="utf-8") as f:
                    sources[fp] = f.read()
            except Exception:
                pass
    source_text = "\n\n".join(f"=== {p} ===\n{c}" for p, c in sources.items())

    # 技术选择
    techniques = st.multiselect(
        "选择白盒测试技术",
        ["PathCoverage (路径覆盖)", "StateTransition (状态转换)"],
        default=["PathCoverage (路径覆盖)", "StateTransition (状态转换)"]
    )
    tech_map = {"PathCoverage (路径覆盖)": "PathCoverage", "StateTransition (状态转换)": "State Transition"}
    enabled = [tech_map[t] for t in techniques]

    if st.button("LLM 白盒测试分析", type="primary", use_container_width=True):
        with st.spinner(f"LLM 分析中 ({', '.join(enabled)})..."):
            try:
                orch = WhiteBoxOrchestrator()
                suite, analysis = orch.generate_all(selected_req, mapping, source_text, enabled)
                st.session_state.test_suites[f"WB-{selected_req.id}"] = suite
                st.session_state[f"wb_analysis_{selected_req.id}"] = analysis
                st.success(f"生成 {suite.total_cases} 个测试用例")
                st.rerun()
            except Exception as e:
                st.error(f"生成失败: {e}")

    suite_id = f"WB-{selected_req.id}"
    suite = st.session_state.test_suites.get(suite_id)
    analysis = st.session_state.get(f"wb_analysis_{selected_req.id}", {})

    if not suite:
        st.info("点击按钮生成")
        return

    st.divider()
    st.metric("总用例数", suite.total_cases)

    pc = analysis.get("PathCoverage", {})
    st_data = analysis.get("State Transition", {})

    tabs = []
    if pc:
        tabs.append("路径覆盖")
    if st_data:
        tabs.append("状态转换")
    if not tabs:
        tabs = ["结果"]

    tab_objects = st.tabs(tabs)
    for i, tab_name in enumerate(tabs):
        with tab_objects[i]:
            if tab_name == "路径覆盖":
                _render_path_coverage(pc)
            elif tab_name == "状态转换":
                _render_state_transition(st_data, suite)


def _render_path_coverage(pc: dict):
    """渲染路径覆盖结果"""
    coverage = pc.get("coverage_report")
    tc_mappings = pc.get("tc_mappings", [])
    cases = pc.get("cases", [])

    if coverage:
        st.subheader("覆盖率报告")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总关联行数", coverage.total_lines)
        with col2:
            st.metric("已覆盖行数", coverage.covered_lines)
        with col3:
            st.metric("覆盖率", f"{coverage.coverage_pct}%")
        if coverage.uncovered_segments:
            st.warning(f"{len(coverage.uncovered_segments)} 个代码段未覆盖")
            for seg in coverage.uncovered_segments:
                st.caption(f"{seg.file_path} L{seg.start_line}-{seg.end_line} - {seg.description}")

    if tc_mappings:
        st.subheader("测试用例-覆盖代码图")
        for tcm in tc_mappings[:15]:
            with st.expander(f"{tcm.test_case_id}: {tcm.test_case_title}"):
                for seg in tcm.covered_segments:
                    st.caption(f"{seg.file_path} L{seg.start_line}-{seg.end_line} | {seg.function_name}() - {seg.description}")

    st.subheader(f"路径覆盖测试用例 ({len(cases)} 个)")
    for tc in cases[:20]:
        icon = "V" if tc.category == "Valid" else "X"
        with st.expander(f"[{icon}] {tc.id}: {tc.title}"):
            if tc.description:
                st.markdown(tc.description)
            if tc.test_steps:
                for s in tc.test_steps:
                    if s.action:
                        st.caption(f"路径: {s.action}")
                    st.json(s.input_data)
                    if s.expected_result:
                        st.info(f"预期: {s.expected_result}")


def _render_state_transition(st_data: dict, suite: TestSuite):
    """渲染状态转换结果"""
    sm = st_data.get("state_machine")
    all_states = st_data.get("all_states_paths", [])
    if sm:
        st.subheader("状态转换图")
        st.caption(f"{sm.state_count} 个状态, {sm.transition_count} 个转换")

        # 状态表
        state_rows = [{"ID": s.id, "名称": s.name, "描述": s.description, "初始": s.is_initial, "终止": s.is_final} for s in sm.states]
        st.dataframe(pd.DataFrame(state_rows), use_container_width=True, hide_index=True)

        # 转换表
        trans_rows = [{"ID": t.id, "从": t.from_state, "到": t.to_state, "触发": t.trigger, "守卫": t.guard or "-", "动作": t.action or "-"} for t in sm.transitions]
        st.dataframe(pd.DataFrame(trans_rows), use_container_width=True, hide_index=True)

    if all_states:
        st.subheader(f"All-States 覆盖路径 ({len(all_states)} 条)")
        for p in all_states:
            path_str = " -> ".join(p.get("path", []))
            st.markdown(f"- {path_str} | {p.get('description','')}")

    # 显示状态转换测试用例
    st_cases = suite.get_cases_by_technique("State Transition")
    if st_cases:
        st.subheader(f"状态转换测试用例 ({len(st_cases)} 个)")
        for tc in st_cases[:20]:
            with st.expander(f"{tc.id}: {tc.title}"):
                if tc.description:
                    st.markdown(tc.description)
                for s in tc.test_steps:
                    st.markdown(f"**步骤{s.step_number}**: {s.action}")
                    if s.input_data:
                        st.json(s.input_data)
                    if s.expected_result:
                        st.info(f"预期: {s.expected_result}")
