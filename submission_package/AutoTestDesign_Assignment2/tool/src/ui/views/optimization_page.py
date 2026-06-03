"""套件优化 - Step 6"""

import copy
import json
from typing import Any

import pandas as pd
import streamlit as st

from src.models.testcase import TestStep
from src.optimization.coverage_optimizer import CoverageOptimizer


DEFAULT_CATEGORIES = ["Valid", "Invalid", "Boundary"]


def render():
    st.title("套件优化")
    st.caption("有效/无效区管理 · 风险优先级 · 合并 · 覆盖最小化")

    all_suites = {
        **st.session_state.test_suites,
        **st.session_state.get("custom_test_suites", {}),
    }
    if not all_suites:
        st.warning("请先生成测试用例。")
        return

    options = _suite_options(all_suites)
    selected = st.selectbox(
        "测试套件",
        options,
        format_func=lambda item: item["label"],
    )
    suite = selected["suite"]
    key = selected["key"]

    active_key = f"active_{key}"
    active_ids = _active_ids_for_suite(active_key, suite)
    active_cases = [tc for tc in suite.test_cases if tc.id in active_ids]
    inactive_cases = [tc for tc in suite.test_cases if tc.id not in active_ids]
    has_coverage = bool(
        suite.coverage_summary.get("tc_mappings")
        or suite.coverage_summary.get("coverage_report")
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("全部", suite.total_cases)
    col2.metric("有效", len(active_cases))
    col3.metric("无效", len(inactive_cases))

    st.divider()
    active_tab, inactive_tab = st.tabs([
        f"有效区 ({len(active_cases)})",
        f"无效区 ({len(inactive_cases)})",
    ])
    with active_tab:
        if active_cases:
            _case_zone(active_cases, key, active_key, "deactivate")
        else:
            st.caption("暂无有效用例")
    with inactive_tab:
        if inactive_cases:
            _case_zone(inactive_cases, key, active_key, "activate")
        else:
            st.caption("暂无无效用例")

    st.divider()
    st.subheader("测试用例审查与修改")
    _editable_cases(key, suite)

    st.divider()
    st.subheader("自动优化")
    risk_tab, merge_tab, coverage_tab = st.tabs([
        "风险优先级",
        "合并相同用例",
        "覆盖最小化",
    ])

    with risk_tab:
        if not st.session_state.risk_assessments:
            st.warning("请先在「风险分析」中完成评估。")
        else:
            budget = st.slider("保留比例", 0.1, 1.0, 1.0, 0.1, key="rb")
            min_risk_label = st.selectbox(
                "最低风险等级",
                ["全部", "Medium 及以上", "仅 High"],
                key="mr",
            )
            if st.button("执行", type="primary", key="btn_risk"):
                with st.spinner("按风险优先级排序中..."):
                    min_risk_map = {"全部": "", "Medium 及以上": "Medium", "仅 High": "High"}
                    active_suite = copy.deepcopy(suite)
                    active_suite.test_cases = active_cases
                    optimized = CoverageOptimizer().optimize_risk_priority(
                        active_suite,
                        st.session_state.risk_assessments,
                        budget=budget,
                        min_risk=min_risk_map[min_risk_label],
                    )
                    st.session_state[active_key] = {tc.id for tc in optimized.test_cases}
                    st.success(f"保留 {len(optimized.test_cases)} 条用例")
                    st.rerun()

    with merge_tab:
        st.caption("LLM 识别逻辑相同或高度相似的测试用例，并建议保留代表用例。")
        if st.button("执行", type="primary", key="btn_merge"):
            with st.spinner("LLM 分析中..."):
                try:
                    req = _find_requirement(suite.requirement_id)
                    requirement_json = req.model_dump_json(indent=2) if req else "{}"
                    active_suite = copy.deepcopy(suite)
                    active_suite.test_cases = active_cases
                    optimized = CoverageOptimizer().optimize_blackbox(active_suite, requirement_json)
                    st.session_state[active_key] = {tc.id for tc in optimized.test_cases}
                    _show_reasons(optimized.coverage_summary.get("deletion_reasons", {}))
                    st.success(f"保留 {len(optimized.test_cases)} 条用例")
                    st.rerun()
                except Exception as exc:
                    st.error(f"失败: {exc}")

    with coverage_tab:
        if not has_coverage:
            st.info("需要覆盖代码图，仅白盒套件支持。")
        else:
            target_pct = st.slider("目标覆盖率 (%)", 50, 100, 80, 5, key="ct")
            if st.button("执行", type="primary", key="btn_cov"):
                with st.spinner("LLM 分析中..."):
                    try:
                        summary = suite.coverage_summary
                        tc_mappings = summary.get("tc_mappings", [])
                        coverage_report = summary.get("coverage_report")
                        current_pct = coverage_report.coverage_pct if coverage_report else 100.0
                        req = _find_requirement(suite.requirement_id)
                        requirement_json = req.model_dump_json(indent=2) if req else "{}"
                        active_suite = copy.deepcopy(suite)
                        active_suite.test_cases = active_cases
                        active_mappings = [
                            item for item in tc_mappings
                            if item.test_case_id in active_ids
                        ]
                        optimized, _ = CoverageOptimizer().optimize_coverage(
                            active_suite,
                            active_mappings,
                            requirement_json,
                            target_pct,
                            current_pct,
                        )
                        st.session_state[active_key] = {tc.id for tc in optimized.test_cases}
                        _show_reasons(optimized.coverage_summary.get("deletion_reasons", {}))
                        st.success(f"保留 {len(optimized.test_cases)} 条用例")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"失败: {exc}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("全部恢复有效", type="secondary", use_container_width=True):
            st.session_state[active_key] = {tc.id for tc in suite.test_cases}
            st.success("已恢复")
            st.rerun()
    with col2:
        if st.button("清除状态记录", type="secondary", use_container_width=True):
            st.session_state.pop(active_key, None)
            st.success("已清除")
            st.rerun()


def _active_ids_for_suite(active_key, suite):
    suite_ids = {tc.id for tc in suite.test_cases}
    known_key = f"{active_key}_known_ids"
    if active_key not in st.session_state:
        st.session_state[active_key] = set(suite_ids)
    else:
        active_ids = set(st.session_state[active_key])
        active_ids &= suite_ids
        known_ids = set(st.session_state.get(known_key, suite_ids))
        active_ids |= suite_ids - known_ids
        st.session_state[active_key] = active_ids
    st.session_state[known_key] = set(suite_ids)
    return st.session_state[active_key]


def _suite_options(all_suites):
    options = []
    used_labels = set()
    for key, suite in all_suites.items():
        label = _clean_suite_name(key, suite)
        if label in used_labels:
            label = f"{label} ({key})"
        used_labels.add(label)
        options.append({"label": label, "key": key, "suite": suite})
    return options


def _clean_suite_name(key, suite):
    raw = _clean_text(suite.name or "")
    if raw and not _looks_mojibake(raw):
        return raw

    req = _find_requirement(suite.requirement_id)
    title = _clean_text(req.title if req else suite.requirement_id)
    suite_id = str(suite.id)
    key_text = str(key)
    if suite_id.startswith("TS-WB") or key_text.startswith("WB-"):
        prefix = "白盒测试套件"
    elif suite_id.startswith("TS-BB"):
        prefix = "黑盒测试套件"
    else:
        prefix = "测试套件"
    return f"{prefix} - {title}"


def _find_requirement(requirement_id):
    return next(
        (req for req in st.session_state.get("requirements", []) if req.id == requirement_id),
        None,
    )


def _case_zone(cases, key, active_key, action):
    for tc in cases:
        label = _case_label(tc)
        with st.expander(label):
            _render_case(tc)
            if action == "deactivate":
                if st.button("设为无效", key=f"de_{key}_{tc.id}"):
                    st.session_state[active_key].discard(tc.id)
                    st.rerun()
            else:
                if st.button("恢复有效", key=f"ac_{key}_{tc.id}"):
                    st.session_state[active_key].add(tc.id)
                    st.rerun()


def _case_label(tc):
    status = "[V]" if tc.category == "Valid" else "[X]"
    label = f"{status} {tc.id}  {_clean_text(tc.title)}  [{_clean_text(tc.technique)}]"
    if tc.category:
        label += f" ({_clean_text(tc.category)})"
    return label


def _render_case(tc):
    if tc.description:
        st.caption(_clean_text(tc.description))
    if tc.preconditions:
        st.markdown("**前置条件**")
        for item in tc.preconditions:
            st.caption(_clean_text(item))
    if tc.tags:
        st.caption("Tags: " + ", ".join(_clean_text(tag) for tag in tc.tags))
    if not tc.test_steps:
        st.caption("暂无测试步骤")
        return

    for step in tc.test_steps:
        st.markdown(f"**Step {step.step_number}**")
        if step.action:
            st.caption(_clean_text(step.action))
        st.json(_clean_json_value(step.input_data))
        if step.expected_result:
            st.info(_clean_text(step.expected_result))


def _editable_cases(key, suite):
    rows = [_case_row(tc) for tc in suite.test_cases]
    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "技术"],
        column_config={
            "类别": st.column_config.SelectboxColumn(
                "类别",
                options=_category_options(rows),
            ),
            "输入JSON": st.column_config.TextColumn("输入JSON", width="large"),
            "预期结果": st.column_config.TextColumn("预期结果", width="large"),
        },
        key=f"opt_editor_{key}",
    )

    ok = _apply_edits(key, suite, edited)
    if ok:
        _save_suite(key, suite)


def _case_row(tc):
    step = tc.test_steps[0] if tc.test_steps else TestStep()
    return {
        "ID": tc.id,
        "标题": _clean_text(tc.title),
        "描述": _clean_text(tc.description),
        "技术": _clean_text(tc.technique),
        "类别": _clean_text(tc.category),
        "操作": _clean_text(step.action),
        "输入JSON": json.dumps(_clean_json_value(step.input_data), ensure_ascii=False),
        "预期结果": _clean_text(step.expected_result),
    }


def _category_options(rows):
    values = [_cell_text(row.get("类别")) for row in rows]
    options = list(DEFAULT_CATEGORIES)
    for value in values:
        if value and value not in options:
            options.append(value)
    return options


def _apply_edits(key, suite, edited):
    if edited is None:
        return True

    by_id = {tc.id: tc for tc in suite.test_cases}
    for row in edited.to_dict("records"):
        tc_id = _cell_text(row.get("ID"))
        tc = by_id.get(tc_id)
        if tc is None:
            continue

        if not tc.test_steps:
            tc.test_steps = [TestStep()]
        step = tc.test_steps[0]

        input_text = _cell_text(row.get("输入JSON"))
        try:
            input_data = json.loads(input_text) if input_text.strip() else {}
        except json.JSONDecodeError as exc:
            st.error(f"{tc_id} 的输入JSON格式无效: {exc.msg}")
            return False
        if not isinstance(input_data, dict):
            st.error(f"{tc_id} 的输入JSON必须是对象。")
            return False

        tc.title = _clean_text(_cell_text(row.get("标题")))
        tc.description = _clean_text(_cell_text(row.get("描述")))
        tc.category = _clean_text(_cell_text(row.get("类别"))) or "Valid"
        step.action = _clean_text(_cell_text(row.get("操作")))
        step.input_data = _clean_json_value(input_data)
        step.expected_result = _clean_text(_cell_text(row.get("预期结果")))

    st.session_state[f"opt_last_edit_{key}"] = True
    return True


def _save_suite(key, suite):
    if key in st.session_state.test_suites:
        st.session_state.test_suites[key] = suite
    if key in st.session_state.get("custom_test_suites", {}):
        st.session_state.custom_test_suites[key] = suite


def _show_reasons(reasons):
    for test_case_id, reason in list(reasons.items())[:5]:
        st.caption(f"{test_case_id}: {_clean_text(reason)}")


def _cell_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value)


def _clean_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, list):
        return [_clean_json_value(item) for item in value]
    if isinstance(value, dict):
        return {
            _clean_text(str(key)): _clean_json_value(item)
            for key, item in value.items()
        }
    return value


def _clean_text(value):
    text = _cell_text(value)
    if not text or not _looks_mojibake(text):
        return text

    candidates = []
    for encoding in ("gbk", "cp936", "latin1"):
        try:
            candidates.append(text.encode(encoding, errors="strict").decode("utf-8"))
        except UnicodeError:
            continue

    best = min(candidates, key=_mojibake_score, default=text)
    return best if _mojibake_score(best) < _mojibake_score(text) else text


def _looks_mojibake(text):
    markers = (
        "濂", "鐧", "榛", "娴", "绛", "杈", "鍒", "瑕", "椋", "浼",
        "鍏", "鏃", "℃", "€", "锛", "鈥", "搟", "", "", "",
    )
    return any(marker in text for marker in markers)


def _mojibake_score(text):
    return sum(text.count(marker) for marker in (
        "濂", "鐧", "榛", "娴", "绛", "杈", "鍒", "瑕", "椋", "浼",
        "鍏", "鏃", "€", "锛", "鈥", "搟", "�", "", "", "",
    ))
