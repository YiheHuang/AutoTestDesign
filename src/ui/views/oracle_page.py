"""预言生成 (v2.2: 用户填充测试数据 -> LLM生成预期结果 -> 保存到自定义套件)"""

import json
import os
import streamlit as st
import pandas as pd
from src.models.testcase import TestCase, TestStep, TestSuite
from src.ai.client import get_ai_client
import datetime

ORACLE_SYSTEM_PROMPT = """你是一名测试预言(Test Oracle)专家。给定标准需求、相关源代码和用户填写的测试输入数据，推导出系统应该产生的精确预期结果。

## 任务
分析输入的测试数据，根据需求和代码逻辑，推导出:
1. 预期HTTP状态码
2. 预期响应体(JSON格式)
3. 推导依据(简要说明)

## 输出JSON格式
{
  "expected_status": 200,
  "expected_response": {"message": "..."},
  "reasoning": "根据需求REQ-001中'所有输入有效时创建账号'的规则，以及代码中register函数的return语句..."
}
"""

ORACLE_USER_TEMPLATE = """## 标准需求
{requirement_json}

## 需求-代码映射
{mapping_json}

## 源代码
{source_code}

## 用户填写的测试数据
{test_data_json}

请推导预期结果。"""


def render():
    st.title("预言生成")
    st.markdown("选择需求 -> 填写测试数据 -> LLM 生成预期结果 -> 保存到自定义测试套件")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求")
        return

    # ── 选择需求 ──
    req_options = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    selected_name = st.selectbox("选择标准需求", list(req_options.keys()))
    selected_req = req_options[selected_name]

    mapping = st.session_state.get("req_code_mappings", {}).get(selected_req.id)

    # ── 自动生成模板 ──
    st.divider()
    st.subheader("测试数据")

    # 从需求的input_fields构建模板
    template = {}
    for field in selected_req.input_fields:
        default_val = ""
        if field.data_type == "integer":
            default_val = "0"
        elif field.data_type == "boolean":
            default_val = False
        template[field.name] = default_val

    # 让用户编辑
    st.caption("根据需求字段填写具体测试值，可增删字段")
    template_json = st.text_area(
        "测试数据 (JSON格式)",
        value=json.dumps(template, indent=2, ensure_ascii=False),
        height=200,
        key="oracle_template"
    )

    # ── LLM生成按钮 ──
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LLM 生成预期结果", type="primary", use_container_width=True):
            try:
                test_data = json.loads(template_json)
            except json.JSONDecodeError:
                st.error("JSON格式无效")
                return

            with st.spinner("LLM 推导预期结果..."):
                # 读取源码
                sources = {}
                if mapping:
                    for seg in mapping.code_segments:
                        fp = seg.file_path
                        if fp not in sources:
                            try:
                                full = os.path.join(st.session_state.get("code_folder", "flask_app"), fp)
                                with open(full, "r", encoding="utf-8") as f:
                                    sources[fp] = f.read()
                            except Exception:
                                pass
                source_text = "\n\n".join(f"=== {p} ===\n{c}" for p, c in sources.items())

                try:
                    ai_client = get_ai_client()
                    result = ai_client.chat_with_json(
                        system_prompt=ORACLE_SYSTEM_PROMPT,
                        user_message=ORACLE_USER_TEMPLATE.format(
                            requirement_json=selected_req.model_dump_json(indent=2),
                            mapping_json=mapping.model_dump_json(indent=2) if mapping else "{}",
                            source_code=source_text,
                            test_data_json=json.dumps(test_data, ensure_ascii=False, indent=2)
                        ),
                        temperature=0.1
                    )

                    if result:
                        st.session_state["oracle_result"] = result
                        st.session_state["oracle_data"] = test_data
                        st.success("预期结果已生成")
                        st.rerun()
                    else:
                        st.error("LLM 返回空结果")
                except Exception as e:
                    st.error(f"LLM 调用失败: {e}")

    # ── 显示结果 ──
    oracle_result = st.session_state.get("oracle_result")
    oracle_data = st.session_state.get("oracle_data")

    if oracle_result:
        status = oracle_result.get("expected_status", "?")
        response = oracle_result.get("expected_response", {})
        reasoning = oracle_result.get("reasoning", "")

        st.divider()
        st.subheader("LLM 预期结果")
        st.metric("预期状态码", status)
        st.json(response)
        if reasoning:
            st.info(f"推导依据: {reasoning}")

        # ── 保存到自定义套件 ──
        st.divider()
        tc_name = st.text_input("测试用例名称", f"TC-CUSTOM-{selected_req.id}-{len(st.session_state.custom_test_suites)+1:03d}")
        if st.button("保存到自定义测试套件", type="primary", use_container_width=True):
            tc = TestCase(
                id=tc_name,
                requirement_id=selected_req.id,
                title=tc_name,
                description=f"手动创建的测试用例 - {selected_req.title}",
                technique="Custom Oracle",
                category="Valid" if str(status).startswith("2") else "Invalid",
                test_steps=[TestStep(
                    step_number=1,
                    action=f"输入: {oracle_data}",
                    input_data=oracle_data,
                    expected_result=json.dumps(response, ensure_ascii=False) if response else str(status)
                )],
                tags=["custom", "oracle_generated"]
            )

            suite_id = f"CUSTOM-{selected_req.id}"
            if suite_id in st.session_state.custom_test_suites:
                st.session_state.custom_test_suites[suite_id].test_cases.append(tc)
            else:
                st.session_state.custom_test_suites[suite_id] = TestSuite(
                    id=suite_id,
                    name=f"自定义测试套件 - {selected_req.title}",
                    requirement_id=selected_req.id,
                    test_cases=[tc],
                    created_at=datetime.datetime.now().isoformat()
                )
            # 同时写入主test_suites，使优化/导出页面可直接使用
            st.session_state.test_suites[suite_id] = st.session_state.custom_test_suites[suite_id]
            st.success(f"已保存: {tc_name}")
            st.rerun()

    # ── 显示已有自定义套件 ──
    if st.session_state.custom_test_suites:
        st.divider()
        st.subheader("自定义测试套件")
        for key, suite in st.session_state.custom_test_suites.items():
            with st.expander(f"{suite.name} ({suite.total_cases} 用例)"):
                for tc in suite.test_cases:
                    st.markdown(f"- **{tc.id}**: {tc.title}")
                    if tc.test_steps:
                        s = tc.test_steps[0]
                        st.caption(f"  输入: {s.input_data}")
                        st.caption(f"  预期: {s.expected_result}")

    st.caption("保存后自动同步到主测试套件，可在优化和导出页面直接使用")
