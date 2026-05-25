"""导出 — Step 7"""

import json, copy
import streamlit as st
from src.export.exporter_factory import ExporterFactory, ExportFormat


def render():
    st.title("导出")
    st.caption("Pytest 可运行脚本  /  JSON 结构化文档")

    all_d = {**st.session_state.test_suites, **st.session_state.get("custom_test_suites", {})}
    if not all_d:
        st.warning("请先生成测试用例…")
        return

    export = []
    for k, s in all_d.items():
        aids = st.session_state.get(f"active_{k}")
        if aids is not None:
            ac = [tc for tc in s.test_cases if tc.id in aids]
            if ac:
                es = copy.deepcopy(s)
                es.test_cases = ac
                export.append(es)
        else:
            export.append(s)

    if not export:
        st.warning("没有可导出的有效用例…")
        return

    at = sum(s.total_cases for s in export)
    tt = sum(s.total_cases for s in all_d.values())
    c1, c2, c3 = st.columns(3)
    c1.metric("套件", len(export))
    c2.metric("有效用例", at)
    c3.metric("全部用例", tt)

    st.divider()

    opts = {s.name: s for s in export}
    sel = st.multiselect("选择套件", list(opts.keys()), default=list(opts.keys()))
    if not sel:
        st.info("请选择套件…")
        return
    suites = [opts[n] for n in sel]

    fmt = st.radio("格式", ["Pytest (可运行)", "JSON (文档)"], horizontal=True)

    if st.button("导出", type="primary", use_container_width=True):
        with st.spinner("生成中…"):
            try:
                all_reqs = []
                all_maps = []
                for s in suites:
                    rid = s.requirement_id
                    rq = next((r for r in st.session_state.requirements if r.id == rid), None)
                    if rq:
                        all_reqs.append(rq)
                    m = st.session_state.get("req_code_mappings", {}).get(rid)
                    if m:
                        all_maps.append(m)
                rj = json.dumps([r.model_dump() for r in all_reqs], ensure_ascii=False, indent=2)
                mj = json.dumps([m.model_dump() for m in all_maps], ensure_ascii=False, indent=2)

                if fmt.startswith("Pytest"):
                    code = ExporterFactory.export(suites, ExportFormat.PYTEST, reqs_json=rj, mappings_json=mj)
                    st.download_button("下载", data=code, file_name="test_generated.py",
                                       mime="text/x-python", use_container_width=True)
                    st.success("导出完成")
                    st.code(code[:3000], language="python")
                else:
                    code = ExporterFactory.export(suites, ExportFormat.JSON)
                    st.download_button("下载", data=code, file_name="test_artifacts.json",
                                       mime="application/json", use_container_width=True)
                    st.success("导出完成")
                    st.code(code[:3000], language="json")
            except Exception as e:
                st.error(f"导出失败: {e}")
