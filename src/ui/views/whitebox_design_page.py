"""白盒路径覆盖 (v2.2: LLM输出用例+覆盖代码图+覆盖率)"""

import streamlit as st
from src.test_design.white_box.path_coverage import PathCoverageGenerator
from src.models.testcase import TestSuite


def render():
    st.title("白盒测试设计 - 路径覆盖")
    st.markdown("LLM 分析代码路径 -> 生成测试用例 + 覆盖代码图 -> 计算覆盖率")

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

    if st.button("LLM 路径覆盖分析", type="primary", use_container_width=True):
        with st.spinner("LLM 分析代码路径 + 生成测试用例..."):
            try:
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

                gen = PathCoverageGenerator()
                cases, coverage, tc_mappings = gen.generate(selected_req, mapping, source_text)

                suite_id = f"WB-{selected_req.id}"
                suite = TestSuite(
                    id=suite_id, name=f"路径覆盖 - {selected_req.title}",
                    requirement_id=selected_req.id, test_cases=cases,
                    coverage_summary={"coverage_report": coverage, "tc_mappings": tc_mappings}
                )
                st.session_state.test_suites[suite_id] = suite
                st.success(f"生成 {len(cases)} 用例 | 覆盖率 {coverage.coverage_pct}%")
                st.rerun()
            except Exception as e:
                st.error(f"生成失败: {e}")

    suite_id = f"WB-{selected_req.id}"
    suite = st.session_state.test_suites.get(suite_id)
    coverage = suite.coverage_summary.get("coverage_report") if suite else None
    tc_mappings = suite.coverage_summary.get("tc_mappings", []) if suite else []

    if not suite:
        st.info("点击按钮生成")
        return

    if coverage:
        st.divider()
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
        st.divider()
        st.subheader("测试用例-覆盖代码图")
        for tcm in tc_mappings[:20]:
            with st.expander(f"{tcm.test_case_id}: {tcm.test_case_title}"):
                for seg in tcm.covered_segments:
                    st.caption(f"{seg.file_path} L{seg.start_line}-{seg.end_line} | {seg.function_name}() - {seg.description}")

    st.divider()
    st.subheader(f"路径覆盖测试用例 ({suite.total_cases} 个)")
    for tc in suite.test_cases[:30]:
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
