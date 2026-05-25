"""套件优化 (v2.2: 有效/无效区 + 风险优先级 + 合并 + 覆盖最小化)"""

import copy
import streamlit as st
from src.optimization.coverage_optimizer import CoverageOptimizer


def render():
    st.title("套件优化")
    st.markdown("管理测试用例的有效/无效状态，三种自动优化策略")

    all_suites = {**st.session_state.test_suites, **st.session_state.get("custom_test_suites", {})}
    if not all_suites:
        st.warning("请先生成测试用例")
        return

    suite_options = {s.name: (s, k) for k, s in all_suites.items()}
    selected_name = st.selectbox("选择测试套件", list(suite_options.keys()))
    suite, suite_key = suite_options[selected_name]

    # ── 初始化有效用例集合 (首次进入默认全部有效) ──
    active_key = f"active_{suite_key}"
    if active_key not in st.session_state:
        st.session_state[active_key] = {tc.id for tc in suite.test_cases}
    active_ids = st.session_state[active_key]

    active_cases = [tc for tc in suite.test_cases if tc.id in active_ids]
    inactive_cases = [tc for tc in suite.test_cases if tc.id not in active_ids]

    has_coverage = bool(suite.coverage_summary.get("tc_mappings") or suite.coverage_summary.get("coverage_report"))

    # ── 概览 ──
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("全部用例", suite.total_cases)
    with col2:
        st.metric("有效", len(active_cases))
    with col3:
        st.metric("无效", len(inactive_cases))

    st.divider()

    # ── 有效区 ──
    st.subheader(f"有效区 ({len(active_cases)} 用例)")
    if active_cases:
        _render_zone(active_cases, suite_key, active_key, "deactivate")
    else:
        st.info("所有用例均已失效")

    st.divider()

    # ── 无效区 ──
    st.subheader(f"无效区 ({len(inactive_cases)} 用例)")
    if inactive_cases:
        _render_zone(inactive_cases, suite_key, active_key, "activate")
    else:
        st.info("无失效用例")

    st.divider()

    # ── 三种优化策略 (针对有效区) ──
    st.subheader("自动优化 (针对有效区)")
    tab1, tab2, tab3 = st.tabs(["风险优先级", "合并相同用例", "覆盖率最小化"])

    with tab1:
        if not st.session_state.risk_assessments:
            st.warning("请先在「风险分析」中完成评估")
        else:
            budget = st.slider("保留比例", 0.1, 1.0, 1.0, 0.1, key="risk_budget")
            min_risk = st.selectbox("最低风险等级", ["全部", "Medium及以上", "仅High"], key="min_risk")
            if st.button("执行", type="primary", key="btn_risk"):
                with st.spinner("排序中..."):
                    risk_map = {"全部": "", "Medium及以上": "Medium", "仅High": "High"}
                    optimizer = CoverageOptimizer()
                    active_suite = copy.deepcopy(suite)
                    active_suite.test_cases = active_cases
                    result = optimizer.optimize_risk_priority(
                        active_suite, st.session_state.risk_assessments,
                        budget=budget, min_risk=risk_map[min_risk]
                    )
                    kept_ids = {tc.id for tc in result.test_cases}
                    removed = active_ids - kept_ids
                    st.session_state[active_key] = kept_ids
                    st.success(f"移除 {len(removed)} 个用例到无效区")
                    st.rerun()

    with tab2:
        st.caption("LLM 识别输入相同、逻辑相同的用例，合并到无效区")
        if st.button("执行", type="primary", key="btn_merge"):
            with st.spinner("LLM 分析..."):
                try:
                    req_id = suite.requirement_id
                    req = next((r for r in st.session_state.requirements if r.id == req_id), None)
                    req_json = req.model_dump_json(indent=2) if req else "{}"
                    optimizer = CoverageOptimizer()
                    active_suite = copy.deepcopy(suite)
                    active_suite.test_cases = active_cases
                    result = optimizer.optimize_blackbox(active_suite, req_json)
                    kept_ids = {tc.id for tc in result.test_cases}
                    removed = active_ids - kept_ids
                    st.session_state[active_key] = kept_ids
                    reasons = result.coverage_summary.get("deletion_reasons", {})
                    if reasons:
                        for tc_id, reason in list(reasons.items())[:5]:
                            st.caption(f"{tc_id}: {reason}")
                    st.success(f"移除 {len(removed)} 个用例到无效区")
                    st.rerun()
                except Exception as e:
                    st.error(f"失败: {e}")

    with tab3:
        if not has_coverage:
            st.info("需要测试用例-覆盖代码图（仅白盒套件支持）")
        else:
            target_pct = st.slider("目标覆盖率 (%)", 50, 100, 80, 5, key="cov_target")
            if st.button("执行", type="primary", key="btn_cov"):
                with st.spinner("LLM 分析..."):
                    try:
                        cs = suite.coverage_summary
                        tc_mappings = cs.get("tc_mappings", [])
                        coverage = cs.get("coverage_report")
                        current_pct = coverage.coverage_pct if coverage else 100.0
                        req_id = suite.requirement_id
                        req = next((r for r in st.session_state.requirements if r.id == req_id), None)
                        req_json = req.model_dump_json(indent=2) if req else "{}"
                        optimizer = CoverageOptimizer()
                        active_suite = copy.deepcopy(suite)
                        active_suite.test_cases = active_cases
                        active_mappings = [m for m in tc_mappings if m.test_case_id in active_ids]
                        result, _ = optimizer.optimize_coverage(
                            active_suite, active_mappings, req_json, target_pct, current_pct
                        )
                        kept_ids = {tc.id for tc in result.test_cases}
                        removed = active_ids - kept_ids
                        st.session_state[active_key] = kept_ids
                        reasons = result.coverage_summary.get("deletion_reasons", {})
                        if reasons:
                            for tc_id, reason in list(reasons.items())[:5]:
                                st.caption(f"{tc_id}: {reason}")
                        st.success(f"移除 {len(removed)} 个用例到无效区")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    # ── 恢复 ──
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("全部恢复有效", type="secondary", use_container_width=True):
            st.session_state[active_key] = {tc.id for tc in suite.test_cases}
            st.success("已全部恢复到有效区")
            st.rerun()
    with col2:
        if st.button("清除状态记录", type="secondary", use_container_width=True):
            st.session_state.pop(active_key, None)
            st.success("已清除")
            st.rerun()


def _render_zone(cases, suite_key, active_key, action):
    """渲染用例区域，支持手动切换"""
    for tc in cases:
        col1, col2 = st.columns([6, 1])
        with col1:
            label = f"{tc.id}: {tc.title}  [{tc.technique}]"
            if tc.category:
                label += f" ({tc.category})"
            st.markdown(label)
            if tc.description:
                st.caption(tc.description[:80])
        with col2:
            if action == "deactivate":
                if st.button("失效", key=f"deact_{suite_key}_{tc.id}"):
                    st.session_state[active_key].discard(tc.id)
                    st.rerun()
            else:
                if st.button("激活", key=f"act_{suite_key}_{tc.id}"):
                    st.session_state[active_key].add(tc.id)
                    st.rerun()
