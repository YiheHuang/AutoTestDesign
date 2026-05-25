"""导出 (v2.2: JSON + pytest, LLM纠正字段)"""

import json
import streamlit as st
from src.export.exporter_factory import ExporterFactory, ExportFormat


def render():
    st.title("导出")
    st.markdown("LLM 纠正字段错误 -> 生成可运行测试脚本或JSON文档")

    all_suites_dict = {**st.session_state.test_suites, **st.session_state.get("custom_test_suites", {})}
    if not all_suites_dict:
        st.warning("请先生成测试用例")
        return

    # 仅导出有效用例 (优化后失效的不导出)
    export_suites = []
    for key, s in all_suites_dict.items():
        active_ids = st.session_state.get(f"active_{key}")
        if active_ids is not None:
            active_cases = [tc for tc in s.test_cases if tc.id in active_ids]
            if active_cases:
                import copy
                es = copy.deepcopy(s)
                es.test_cases = active_cases
                export_suites.append(es)
        else:
            export_suites.append(s)

    if not export_suites:
        st.warning("没有可导出的有效用例")
        return

    active_total = sum(s.total_cases for s in export_suites)
    all_total = sum(s.total_cases for s in all_suites_dict.values())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("套件数", len(export_suites))
    with col2:
        st.metric("有效用例", active_total)
    with col3:
        st.metric("全部用例", all_total)

    st.divider()

    suite_options = {s.name: s for s in export_suites}
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
