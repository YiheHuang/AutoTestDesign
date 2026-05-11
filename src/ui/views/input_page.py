"""需求输入 (v2.2: 代码文件夹+需求文本 -> LLM输出标准需求+需求-代码图)"""

import streamlit as st
import os


def render():
    st.title("需求输入")
    st.markdown("选择代码仓库 + 粘贴需求文本 -> LLM 生成标准需求与需求-代码映射")

    col1, col2 = st.columns(2)

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
                st.success(f"{py_count} 个.py文件")
            else:
                st.error("文件夹不存在")

    with col2:
        st.subheader("需求文本")
        req_text = st.text_area(
            "粘贴需求文档",
            height=300,
            value=st.session_state.get("req_text", ""),
            placeholder="在此粘贴软件需求描述..."
        )
        if req_text:
            st.session_state["req_text"] = req_text

    st.divider()
    if st.button("生成标准需求与需求-代码映射", type="primary", use_container_width=True):
        if not folder_path or not os.path.isdir(folder_path):
            st.error("请输入有效的代码文件夹路径")
            return
        if not req_text.strip():
            st.error("请粘贴需求文本")
            return
        with st.spinner("LLM 正在分析需求与代码..."):
            try:
                from src.parser.ai_extractor import AIExtractor
                extractor = AIExtractor()
                result = extractor.extract_with_code(req_text, folder_path)
                if result:
                    requirements, mappings = result
                    st.session_state.requirements = requirements
                    st.session_state.req_code_mappings = {m.requirement_id: m for m in mappings}
                    st.success(f"生成 {len(requirements)} 条标准需求 + {len(mappings)} 个代码映射")
                    st.rerun()
                else:
                    st.error("LLM 返回空结果")
            except Exception as e:
                st.error(f"生成失败: {e}")

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
