"""需求输入 — Step 1"""

import streamlit as st
import os


def render():
    st.title("需求输入")
    st.caption("代码仓库 + 需求文档 → 标准需求 & 需求-代码映射")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("代码仓库")
        fp = st.text_input(
            "路径",
            value=st.session_state.get("code_folder", "flask_app"),
            placeholder="./flask_app"
        )
        if fp:
            st.session_state["code_folder"] = fp
            if os.path.isdir(fp):
                import os as _os
                n = sum(1 for r, ds, fs in _os.walk(fp) for f in fs if f.endswith(".py") and f != "__init__.py")
                st.caption(f"{n} 个 .py 文件")
            else:
                st.error("路径不存在")

    with col2:
        st.subheader("需求文档")
        mode = st.radio("导入方式", ["CSV 标准需求", "TXT 文本需求", "粘贴文本"], horizontal=True, key="req_mode")
        if mode == "CSV 标准需求":
            _csv()
        elif mode == "TXT 文本需求":
            _txt()
        else:
            _paste()

    if st.button("生成标准需求与需求-代码映射", type="primary", use_container_width=True):
        folder = st.session_state.get("code_folder", "")
        if not folder or not os.path.isdir(folder):
            st.error("请输入有效的代码文件夹路径")
            return
        mode = st.session_state.get("req_mode", "TXT 文本需求")
        with st.spinner("LLM 分析中…"):
            try:
                from src.parser.ai_extractor import AIExtractor
                ex = AIExtractor()
                if mode == "CSV 标准需求":
                    csv = st.session_state.get("csv_content", "")
                    if not csv.strip():
                        st.error("请先上传 CSV 文件")
                        return
                    reqs = ex.parse_requirements_from_csv(csv)
                    if not reqs:
                        st.error("CSV 解析失败")
                        return
                    mappings = ex.extract_mapping_from_csv(reqs, folder)
                    st.session_state.requirements = reqs
                else:
                    txt = st.session_state.get("req_text", "")
                    if not txt.strip():
                        st.error("请先输入需求文本")
                        return
                    r = ex.extract_with_code(txt, folder)
                    if not r:
                        st.error("LLM 返回空结果，请重试…")
                        return
                    reqs, mappings = r
                    st.session_state.requirements = reqs
                if mappings:
                    st.session_state.req_code_mappings = {m.requirement_id: m for m in mappings}
                else:
                    st.error("LLM 未生成代码映射，请重试…")
                    return
                n_reqs = len(st.session_state.requirements)
                n_maps = len(st.session_state.req_code_mappings)
                st.success(f"完成 — {n_reqs} 条需求, {n_maps} 个代码映射")
                st.rerun()
            except Exception as e:
                st.error(f"失败: {e}")

    if st.session_state.requirements and st.session_state.get("req_code_mappings"):
        st.divider()
        st.subheader(f"标准需求 ({len(st.session_state.requirements)})")
        for req in st.session_state.requirements:
            m = st.session_state.req_code_mappings.get(req.id)
            seg = len(m.code_segments) if m else 0
            with st.expander(f"{req.id}  {req.title}  ·  {seg} 代码段"):
                ca, cb = st.columns(2)
                with ca:
                    st.caption("输入字段")
                    for f in req.input_fields:
                        st.markdown(f"- `{f.name}` ({f.data_type}): {f.valid_range or '—'}")
                        if f.constraints:
                            st.caption(f"  {', '.join(f.constraints)}")
                with cb:
                    st.caption("条件 & 行为")
                    for c in req.conditions:
                        st.markdown(f"- {c.description}")
                    for b in req.expected_behaviors:
                        st.markdown(f"- [{b.condition}] → {b.action}")
                if m and m.code_segments:
                    st.caption("关联代码")
                    for s in m.code_segments:
                        st.caption(f"{s.file_path} L{s.start_line}–{s.end_line}  |  {s.function_name}()")


def _csv():
    st.caption("上传预定义的标准需求 CSV")
    u = st.file_uploader("CSV 文件", type=["csv"], key="csv_upload", label_visibility="collapsed")
    if u:
        c = u.getvalue().decode("utf-8")
        st.session_state["csv_content"] = c
        st.text_area("预览", c, height=140, label_visibility="collapsed")
        try:
            from src.parser.ai_extractor import AIExtractor
            reqs = AIExtractor().parse_requirements_from_csv(c)
            if reqs:
                st.caption(f"解析到 {len(reqs)} 条需求: {', '.join(r.id for r in reqs)}")
        except Exception as e:
            st.error(f"预览失败: {e}")


def _txt():
    st.caption("上传 .txt 需求文档")
    u = st.file_uploader("TXT 文件", type=["txt"], key="txt_upload", label_visibility="collapsed")
    if u:
        c = u.getvalue().decode("utf-8")
        st.session_state["req_text"] = c
        st.text_area("预览", c, height=180, label_visibility="collapsed")
    elif st.session_state.get("req_text"):
        st.caption(f"已加载 {len(st.session_state['req_text'])} 字符")


def _paste():
    st.caption("直接粘贴需求描述")
    t = st.text_area("内容", height=250, value=st.session_state.get("req_text", ""),
                     placeholder="在此粘贴软件需求描述…", label_visibility="collapsed")
    if t:
        st.session_state["req_text"] = t
