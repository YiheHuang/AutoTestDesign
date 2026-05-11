"""导出 (v2.2: JSON + pytest, LLM纠正字段)"""

import json
import streamlit as st
from src.export.exporter_factory import ExporterFactory, ExportFormat


def render():
    st.title("导出")
    st.markdown("LLM 纠正字段错误 -> 生成可运行测试脚本或JSON文档")

    all_suites = list(st.session_state.test_suites.values())
    if not all_suites:
        st.warning("请先生成测试用例")
        return

    total_cases = sum(s.total_cases for s in all_suites)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("套件数", len(all_suites))
    with col2:
        st.metric("总用例数", total_cases)

    st.divider()

    suite_options = {s.name: s for s in all_suites}
    selected = st.multiselect("选择套件", list(suite_options.keys()), default=list(suite_options.keys()))
    if not selected:
        st.info("请选择套件")
        return
    suites = [suite_options[n] for n in selected]

    fmt = st.radio("导出格式", ["Pytest (可运行脚本)", "JSON (结构化文档)"], horizontal=True)

    if st.button("导出", type="primary", use_container_width=True):
        with st.spinner("LLM 纠正 + 生成..."):
            try:
                all_reqs = []
                all_mappings = []
                for s in suites:
                    rid = s.requirement_id
                    req = next((r for r in st.session_state.requirements if r.id == rid), None)
                    if req:
                        all_reqs.append(req)
                    m = st.session_state.get("req_code_mappings", {}).get(rid)
                    if m:
                        all_mappings.append(m)

                reqs_json = json.dumps([r.model_dump() for r in all_reqs], ensure_ascii=False, indent=2)
                mappings_json = json.dumps([m.model_dump() for m in all_mappings], ensure_ascii=False, indent=2)

                if fmt.startswith("Pytest"):
                    result = ExporterFactory.export(
                        suites, ExportFormat.PYTEST,
                        reqs_json=reqs_json, mappings_json=mappings_json
                    )
                    st.download_button("下载 pytest", data=result, file_name="test_generated.py", mime="text/x-python", use_container_width=True)
                    st.success("Pytest 导出完成")
                    st.code(result[:3000], language="python")
                else:
                    result = ExporterFactory.export(suites, ExportFormat.JSON)
                    st.download_button("下载 JSON", data=result, file_name="test_artifacts.json", mime="application/json", use_container_width=True)
                    st.success("JSON 导出完成")
                    st.code(result[:3000], language="json")
            except Exception as e:
                st.error(f"导出失败: {e}")
