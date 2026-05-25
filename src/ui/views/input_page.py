"""需求输入 (v2.2: CSV标准需求 / TXT文本需求 -> LLM生成需求-代码映射)"""

import streamlit as st
import os


def render():
    st.title("需求输入")
    st.markdown("选择代码仓库 + 导入需求 -> LLM 生成需求-代码映射")

    col1, col2 = st.columns(2)

    # ── 左侧: 代码仓库 (不变) ──
    with col1:
        st.subheader("代码仓库")
        folder_path = st.text_input(
            "文件夹路径",
            value=st.session_state.get("code_folder", "flask_app"),
            placeholder="例如: ./flask_app"
        )
        if folder_path:
            st.session_state["code_folder"] = folder_path
            if os.path.isdir(folder_path):
                py_count = sum(1 for f in os.listdir(folder_path) if f.endswith(".py"))
                st.success(f"{py_count} 个 .py 文件")
            else:
                st.error("文件夹不存在")

    # ── 右侧: 需求输入 (三种模式) ──
    with col2:
        st.subheader("需求导入")
        req_mode = st.radio(
            "选择导入方式",
            ["CSV 标准需求", "TXT 文本需求", "粘贴文本"],
            horizontal=True,
            key="req_mode"
        )

        if req_mode == "CSV 标准需求":
            _render_csv_mode()
        elif req_mode == "TXT 文本需求":
            _render_txt_mode()
        else:
            _render_paste_mode()

    # ── 统一生成按钮 ──
    st.divider()

    if st.button("生成标准需求与需求-代码映射", type="primary", use_container_width=True):
        folder = st.session_state.get("code_folder", "")
        if not folder or not os.path.isdir(folder):
            st.error("请输入有效的代码文件夹路径")
            return

        mode = st.session_state.get("req_mode", "TXT 文本需求")

        with st.spinner("LLM 正在分析需求与代码..."):
            try:
                from src.parser.ai_extractor import AIExtractor
                extractor = AIExtractor()

                if mode == "CSV 标准需求":
                    csv_content = st.session_state.get("csv_content", "")
                    if not csv_content.strip():
                        st.error("请先上传 CSV 文件")
                        return
                    requirements = extractor.parse_requirements_from_csv(csv_content)
                    if not requirements:
                        st.error("CSV 解析失败: 无有效需求行")
                        return
                    mappings = extractor.extract_mapping_from_csv(requirements, folder)
                    st.session_state.requirements = requirements

                else:
                    req_text = st.session_state.get("req_text", "")
                    if not req_text.strip():
                        st.error("请先输入需求文本")
                        return
                    result = extractor.extract_with_code(req_text, folder)
                    if not result:
                        st.error("LLM 返回空结果")
                        return
                    requirements, mappings = result
                    st.session_state.requirements = requirements

                if mappings:
                    st.session_state.req_code_mappings = {m.requirement_id: m for m in mappings}
                else:
                    st.error("LLM 未生成代码映射")
                    return

                st.success(
                    f"完成: {len(st.session_state.requirements)} 条需求"
                    f" + {len(st.session_state.req_code_mappings)} 个代码映射"
                )
                st.rerun()

            except Exception as e:
                st.error(f"生成失败: {e}")

    # ── 结果展示 ──
    if st.session_state.requirements and st.session_state.get("req_code_mappings"):
        st.divider()
        st.subheader(f"{len(st.session_state.requirements)} 条标准需求")
        for req in st.session_state.requirements:
            mapping = st.session_state.req_code_mappings.get(req.id)
            seg_count = len(mapping.code_segments) if mapping else 0
            with st.expander(f"{req.id}: {req.title} | 代码段: {seg_count}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**输入字段**")
                    for f in req.input_fields:
                        st.markdown(f"- `{f.name}` ({f.data_type}): {f.valid_range or 'N/A'}")
                        if f.constraints:
                            st.caption(f"  约束: {', '.join(f.constraints)}")
                with col_b:
                    st.markdown("**条件与行为**")
                    for c in req.conditions:
                        st.markdown(f"- {c.description}")
                    for b in req.expected_behaviors:
                        st.markdown(f"- [{b.condition}] -> {b.action}")
                if mapping and mapping.code_segments:
                    st.markdown("**关联代码**")
                    for seg in mapping.code_segments:
                        st.caption(
                            f"{seg.file_path} L{seg.start_line}-{seg.end_line} "
                            f"| {seg.function_name}() - {seg.description}"
                        )


def _render_csv_mode():
    """CSV 标准需求导入: 用户上传预定义好的标准化需求CSV，LLM仅生成映射"""
    st.caption("上传包含 id/title/description/input_fields/conditions/expected_behaviors 列的 CSV")
    uploaded = st.file_uploader("上传标准需求 CSV", type=["csv"], key="csv_upload")
    if uploaded:
        content = uploaded.getvalue().decode("utf-8")
        st.session_state["csv_content"] = content
        st.text_area("CSV 预览", content, height=150)

        if "csv_content" in st.session_state:
            try:
                from src.parser.ai_extractor import AIExtractor
                extractor = AIExtractor()
                reqs = extractor.parse_requirements_from_csv(content)
                if reqs:
                    st.success(f"解析到 {len(reqs)} 条标准需求: {', '.join(r.id for r in reqs)}")
                else:
                    st.warning("未能解析任何需求行")
            except Exception as e:
                st.error(f"预览解析失败: {e}")


def _render_txt_mode():
    """TXT 文本需求: 上传.txt文件, LLM生成标准需求+映射"""
    st.caption("上传 .txt 需求文档文件，LLM 将自动生成标准化需求条目")
    uploaded = st.file_uploader("上传需求文档", type=["txt"], key="txt_upload")
    if uploaded:
        content = uploaded.getvalue().decode("utf-8")
        st.session_state["req_text"] = content
        st.text_area("文件内容预览", content, height=180)
    elif st.session_state.get("req_text"):
        # 保留上次上传的内容
        st.info(f"已加载: {len(st.session_state['req_text'])} 字符")


def _render_paste_mode():
    """直接粘贴: 手动输入需求文本"""
    st.caption("直接在文本框中粘贴或输入需求描述")
    req_text = st.text_area(
        "需求描述",
        height=250,
        value=st.session_state.get("req_text", ""),
        placeholder="在此粘贴软件需求描述..."
    )
    if req_text:
        st.session_state["req_text"] = req_text
