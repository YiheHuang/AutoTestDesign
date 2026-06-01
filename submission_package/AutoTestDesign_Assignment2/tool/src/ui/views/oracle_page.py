"""预言生成 — Step 5"""

import json, os, datetime
import streamlit as st
from src.models.testcase import TestCase, TestStep, TestSuite
from src.ai.client import get_ai_client

ORACLE_SYSTEM_PROMPT = """你是一名测试预言(Test Oracle)专家。

## 任务
给定标准需求、相关源代码和用户填写的测试输入数据，推导系统应产生的精确预期结果。

## 输出JSON格式
{
  "expected_status": 200,
  "expected_response": {"message": "..."},
  "reasoning": "根据需求中'所有输入有效时创建账号'的规则…"
}
"""

ORACLE_USER_TEMPLATE = """## 标准需求
{requirement_json}

## 需求-代码映射
{mapping_json}

## 源代码
{source_code}

## 测试数据
{test_data_json}

请推导预期结果。"""


def render():
    st.title("预言生成")
    st.caption("填写测试数据 → LLM 推导预期结果 → 保存到自定义套件")

    if not st.session_state.requirements:
        st.warning("请先生成标准需求…")
        return

    opts = {f"{r.id}: {r.title}": r for r in st.session_state.requirements}
    req = opts[st.selectbox("标准需求", list(opts.keys()))]
    mapping = st.session_state.get("req_code_mappings", {}).get(req.id)

    st.divider()
    st.subheader("测试数据")

    template = {}
    for f in req.input_fields:
        template[f.name] = "" if f.data_type != "integer" else 0

    data_json = st.text_area("数据 (JSON)", value=json.dumps(template, indent=2, ensure_ascii=False),
                             height=180, key="oracle_template")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("生成预期结果", type="primary", use_container_width=True):
            try:
                td = json.loads(data_json)
            except json.JSONDecodeError:
                st.error("JSON 格式无效")
                return
            with st.spinner("LLM 推导中…"):
                sources = {}
                if mapping:
                    for seg in mapping.code_segments:
                        fp = seg.file_path
                        if fp not in sources:
                            try:
                                full = os.path.join(st.session_state.get("code_folder", "flask_app"), fp)
                                with open(full, encoding="utf-8") as f:
                                    sources[fp] = f.read()
                            except Exception:
                                pass
                src = "\n\n".join(f"=== {p} ===\n{c}" for p, c in sources.items())
                try:
                    ai = get_ai_client()
                    r = ai.chat_with_json(
                        system_prompt=ORACLE_SYSTEM_PROMPT,
                        user_message=ORACLE_USER_TEMPLATE.format(
                            requirement_json=req.model_dump_json(indent=2),
                            mapping_json=mapping.model_dump_json(indent=2) if mapping else "{}",
                            source_code=src,
                            test_data_json=json.dumps(td, ensure_ascii=False, indent=2)
                        ),
                        temperature=0.1
                    )
                    if r:
                        st.session_state["oracle_result"] = r
                        st.session_state["oracle_data"] = td
                        st.success("已生成")
                        st.rerun()
                    else:
                        st.error("LLM 返回空结果，请重试…")
                except Exception as e:
                    st.error(f"LLM 调用失败: {e}")

    r = st.session_state.get("oracle_result")
    od = st.session_state.get("oracle_data")
    if r:
        st.divider()
        st.subheader("预期结果")
        st.metric("状态码", r.get("expected_status", "?"))
        st.json(r.get("expected_response", {}))
        if r.get("reasoning"):
            st.info(r["reasoning"])

        name = st.text_input("用例名称", f"TC-CUSTOM-{req.id}-{len(st.session_state.custom_test_suites)+1:03d}")
        if st.button("保存到自定义套件", type="primary", use_container_width=True):
            tc = TestCase(
                id=name, requirement_id=req.id, title=name,
                description=f"手动创建 — {req.title}",
                technique="Custom Oracle",
                category="Valid" if str(r.get("expected_status","")).startswith("2") else "Invalid",
                test_steps=[TestStep(step_number=1, input_data=od,
                                     expected_result=json.dumps(r.get("expected_response",{}), ensure_ascii=False))],
                tags=["custom", "oracle"]
            )
            sid = f"CUSTOM-{req.id}"
            if sid in st.session_state.custom_test_suites:
                st.session_state.custom_test_suites[sid].test_cases.append(tc)
            else:
                st.session_state.custom_test_suites[sid] = TestSuite(
                    id=sid, name=f"自定义套件 — {req.title}",
                    requirement_id=req.id, test_cases=[tc],
                    created_at=datetime.datetime.now().isoformat()
                )
            st.session_state.test_suites[sid] = st.session_state.custom_test_suites[sid]
            st.success(f"已保存: {name}")
            st.rerun()

    if st.session_state.custom_test_suites:
        st.divider()
        st.subheader("自定义套件")
        for k, s in st.session_state.custom_test_suites.items():
            with st.expander(f"{s.name} ({s.total_cases})"):
                for tc in s.test_cases:
                    st.markdown(f"- **{tc.id}**  {tc.title}")
                    if tc.test_steps:
                        st.caption(f"  输入: {tc.test_steps[0].input_data}")
                        st.caption(f"  预期: {tc.test_steps[0].expected_result}")
