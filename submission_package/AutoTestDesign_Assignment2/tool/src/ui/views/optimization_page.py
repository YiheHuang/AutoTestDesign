"""套件优化 — Step 6"""

import copy
import streamlit as st
from src.optimization.coverage_optimizer import CoverageOptimizer


def render():
    st.title("套件优化")
    st.caption("有效/无效区管理 · 风险优先级 · 合并 · 覆盖最小化")

    all_s = {**st.session_state.test_suites, **st.session_state.get("custom_test_suites", {})}
    if not all_s:
        st.warning("请先生成测试用例…")
        return

    opts = {s.name: (s, k) for k, s in all_s.items()}
    name = st.selectbox("测试套件", list(opts.keys()))
    suite, key = opts[name]

    ak = f"active_{key}"
    if ak not in st.session_state:
        st.session_state[ak] = {tc.id for tc in suite.test_cases}
    aids = st.session_state[ak]
    active = [tc for tc in suite.test_cases if tc.id in aids]
    inactive = [tc for tc in suite.test_cases if tc.id not in aids]
    has_cov = bool(suite.coverage_summary.get("tc_mappings") or suite.coverage_summary.get("coverage_report"))

    c1, c2, c3 = st.columns(3)
    c1.metric("全部", suite.total_cases)
    c2.metric("有效", len(active))
    c3.metric("无效", len(inactive))

    st.divider()
    st.subheader(f"有效区 ({len(active)})")
    if active:
        _zone(active, key, ak, "deactivate")
    else:
        st.caption("无有效用例")

    st.divider()
    st.subheader(f"无效区 ({len(inactive)})")
    if inactive:
        _zone(inactive, key, ak, "activate")
    else:
        st.caption("无失效用例")

    st.divider()
    st.subheader("自动优化")
    t1, t2, t3 = st.tabs(["风险优先级", "合并相同用例", "覆盖最小化"])

    with t1:
        if not st.session_state.risk_assessments:
            st.warning("请先在「风险分析」中完成评估…")
        else:
            budget = st.slider("保留比例", 0.1, 1.0, 1.0, 0.1, key="rb")
            mr = st.selectbox("最低风险等级", ["全部", "Medium 及以上", "仅 High"], key="mr")
            if st.button("执行", type="primary", key="btn_risk"):
                with st.spinner("排序中…"):
                    rm = {"全部": "", "Medium 及以上": "Medium", "仅 High": "High"}
                    opt = CoverageOptimizer()
                    as_ = copy.deepcopy(suite); as_.test_cases = active
                    r = opt.optimize_risk_priority(as_, st.session_state.risk_assessments, budget=budget, min_risk=rm[mr])
                    st.session_state[ak] = {tc.id for tc in r.test_cases}
                    st.success(f"保留 {len(r.test_cases)} 用例")
                    st.rerun()

    with t2:
        st.caption("LLM 识别逻辑相同用例并合并")
        if st.button("执行", type="primary", key="btn_merge"):
            with st.spinner("LLM 分析中…"):
                try:
                    rid = suite.requirement_id
                    rq = next((r for r in st.session_state.requirements if r.id == rid), None)
                    rj = rq.model_dump_json(indent=2) if rq else "{}"
                    opt = CoverageOptimizer()
                    as_ = copy.deepcopy(suite); as_.test_cases = active
                    r = opt.optimize_blackbox(as_, rj)
                    st.session_state[ak] = {tc.id for tc in r.test_cases}
                    reasons = r.coverage_summary.get("deletion_reasons", {})
                    for tid, reason in list(reasons.items())[:5]:
                        st.caption(f"{tid}: {reason}")
                    st.success(f"保留 {len(r.test_cases)} 用例")
                    st.rerun()
                except Exception as e:
                    st.error(f"失败: {e}")

    with t3:
        if not has_cov:
            st.info("需要覆盖代码图（仅白盒套件支持）…")
        else:
            tp = st.slider("目标覆盖率 (%)", 50, 100, 80, 5, key="ct")
            if st.button("执行", type="primary", key="btn_cov"):
                with st.spinner("LLM 分析中…"):
                    try:
                        cs = suite.coverage_summary
                        tcm = cs.get("tc_mappings", [])
                        cov = cs.get("coverage_report")
                        cp = cov.coverage_pct if cov else 100.0
                        rid = suite.requirement_id
                        rq = next((r for r in st.session_state.requirements if r.id == rid), None)
                        rj = rq.model_dump_json(indent=2) if rq else "{}"
                        opt = CoverageOptimizer()
                        as_ = copy.deepcopy(suite); as_.test_cases = active
                        am = [m for m in tcm if m.test_case_id in aids]
                        r, _ = opt.optimize_coverage(as_, am, rj, tp, cp)
                        st.session_state[ak] = {tc.id for tc in r.test_cases}
                        reasons = r.coverage_summary.get("deletion_reasons", {})
                        for tid, reason in list(reasons.items())[:5]:
                            st.caption(f"{tid}: {reason}")
                        st.success(f"保留 {len(r.test_cases)} 用例")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("全部恢复有效", type="secondary", use_container_width=True):
            st.session_state[ak] = {tc.id for tc in suite.test_cases}
            st.success("已恢复")
            st.rerun()
    with c2:
        if st.button("清除状态记录", type="secondary", use_container_width=True):
            st.session_state.pop(ak, None)
            st.success("已清除")
            st.rerun()


def _zone(cases, key, ak, action):
    for tc in cases:
        c1, c2 = st.columns([6, 1])
        lbl = f"{tc.id}  {tc.title}  [{tc.technique}]"
        if tc.category:
            lbl += f" ({tc.category})"
        c1.markdown(lbl)
        if tc.description:
            c1.caption(tc.description[:80])
        if action == "deactivate":
            if c2.button("失效", key=f"de_{key}_{tc.id}"):
                st.session_state[ak].discard(tc.id)
                st.rerun()
        else:
            if c2.button("激活", key=f"ac_{key}_{tc.id}"):
                st.session_state[ak].add(tc.id)
                st.rerun()
