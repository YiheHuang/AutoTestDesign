"""套件优化 (v2.2: LLM合并/覆盖优化 + 恢复)"""

import copy
import streamlit as st
from src.optimization.coverage_optimizer import CoverageOptimizer


def render():
    st.title("套件优化")
    st.markdown("LLM 优化测试套件: 合并逻辑相同的用例 / 基于覆盖率删除冗余")

    if not st.session_state.test_suites:
        st.warning("请先生成测试用例")
        return

    suite_options = {s.name: (s, k) for k, s in st.session_state.test_suites.items()}
    selected_name = st.selectbox("选择测试套件", list(suite_options.keys()))
    suite, suite_key = suite_options[selected_name]

    # 保存原始套件用于恢复
    orig_key = f"{suite_key}_original"
    if orig_key not in st.session_state:
        st.session_state[orig_key] = copy.deepcopy(suite)

    original = st.session_state[orig_key]

    # 判断套件类型
    has_coverage = bool(suite.coverage_summary.get("tc_mappings") or suite.coverage_summary.get("coverage_report"))
    suite_type = "白盒 (路径覆盖)" if has_coverage else "黑盒"

    st.caption(f"套件类型: {suite_type}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("当前用例数", suite.total_cases)
    with col2:
        st.metric("原始用例数", original.total_cases,
                  delta=f"{suite.total_cases - original.total_cases}" if suite.total_cases != original.total_cases else None)

    st.divider()

    if has_coverage:
        # 白盒: 覆盖率优化
        target_pct = st.slider("目标覆盖率 (%)", 50, 100, 80, 5)
        if st.button("LLM 覆盖优化", type="primary", use_container_width=True):
            with st.spinner("LLM 分析冗余用例..."):
                try:
                    cs = suite.coverage_summary
                    tc_mappings = cs.get("tc_mappings", [])
                    coverage = cs.get("coverage_report")
                    current_pct = coverage.coverage_pct if coverage else 100.0

                    req_id = suite.requirement_id
                    req = next((r for r in st.session_state.requirements if r.id == req_id), None)
                    req_json = req.model_dump_json(indent=2) if req else "{}"

                    optimizer = CoverageOptimizer()
                    optimized, _ = optimizer.optimize_coverage(
                        suite, tc_mappings, req_json, target_pct, current_pct
                    )
                    st.session_state.test_suites[suite_key] = optimized

                    deleted = suite.total_cases - optimized.total_cases
                    st.success(f"优化完成: {suite.total_cases} -> {optimized.total_cases} (删除 {deleted})")
                    st.rerun()
                except Exception as e:
                    st.error(f"优化失败: {e}")
    else:
        # 黑盒: 合并逻辑相同用例
        if st.button("LLM 合并相同用例", type="primary", use_container_width=True):
            with st.spinner("LLM 分析相同用例..."):
                try:
                    req_id = suite.requirement_id
                    req = next((r for r in st.session_state.requirements if r.id == req_id), None)
                    req_json = req.model_dump_json(indent=2) if req else "{}"

                    optimizer = CoverageOptimizer()
                    optimized = optimizer.optimize_blackbox(suite, req_json)
                    st.session_state.test_suites[suite_key] = optimized

                    deleted = suite.total_cases - optimized.total_cases
                    st.success(f"合并完成: {suite.total_cases} -> {optimized.total_cases} (删除 {deleted})")
                    st.rerun()
                except Exception as e:
                    st.error(f"合并失败: {e}")

    # --- 显示优化结果 ---
    if suite.coverage_summary.get("deletion_reasons"):
        st.divider()
        st.subheader(f"优化结果: {suite.total_cases} 个用例")
        reasons = suite.coverage_summary["deletion_reasons"]
        for tc_id, reason in reasons.items():
            st.caption(f"[已删除] {tc_id}: {reason}")

    # --- 恢复按钮 ---
    st.divider()
    if st.button("恢复原始套件", type="secondary", use_container_width=True):
        st.session_state.test_suites[suite_key] = copy.deepcopy(original)
        st.session_state.pop(orig_key, None)
        st.success(f"已恢复原始套件 ({original.total_cases} 个用例)")
        st.rerun()
