"""AutoTestDesign - AI驱动的测试设计工具 主入口"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

st.set_page_config(
    page_title="AutoTestDesign",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("AutoTestDesign")
    st.markdown("AI驱动的自动化测试设计工具")
    st.divider()

page = st.sidebar.radio(
    "工作流程",
    [
        "1. 需求输入",
        "2. 风险分析",
        "3. 黑盒测试设计",
        "4. 白盒测试设计",
        "5. 预言生成",
        "6. 套件优化",
        "7. 导出"
    ],
    index=0
)

st.sidebar.divider()
st.sidebar.caption("v2.2 | ISTQB/ISO 29119-4")
st.sidebar.caption("期末项目 - 软件测试")

if "requirements" not in st.session_state:
    st.session_state.requirements = []
if "risk_assessments" not in st.session_state:
    st.session_state.risk_assessments = []
if "test_suites" not in st.session_state:
    st.session_state.test_suites = {}
if "optimized_suites" not in st.session_state:
    st.session_state.optimized_suites = {}
if "req_code_mappings" not in st.session_state:
    st.session_state.req_code_mappings = {}
if "code_folder" not in st.session_state:
    st.session_state.code_folder = "flask_app"
if "req_text" not in st.session_state:
    st.session_state.req_text = ""
if "custom_test_suites" not in st.session_state:
    st.session_state.custom_test_suites = {}

from src.ui.views import (
    input_page, risk_analysis_page, blackbox_design_page,
    whitebox_design_page, oracle_page,
    optimization_page, export_page
)

page_map = {
    "1. 需求输入": input_page.render,
    "2. 风险分析": risk_analysis_page.render,
    "3. 黑盒测试设计": blackbox_design_page.render,
    "4. 白盒测试设计": whitebox_design_page.render,
    "5. 预言生成": oracle_page.render,
    "6. 套件优化": optimization_page.render,
    "7. 导出": export_page.render,
}

page_map[page]()
