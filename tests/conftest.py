"""pytest fixtures and configuration"""

import pytest
from unittest.mock import MagicMock, patch
from src.models.requirement import (
    StructuredRequirement, InputField, Condition, SystemBehavior, SourceType
)
from src.models.testcase import TestCase, TestSuite, TestStep
from src.models.risk import RiskAssessment
from src.models.state_machine import StateMachine, State, Transition


@pytest.fixture
def sample_requirement():
    """创建示例结构化需求（用户注册表单）"""
    return StructuredRequirement(
        id="REQ-001",
        source=SourceType.TEXT,
        raw_text="用户注册页面要求输入用户名(3-20字符)、密码(8-32位)...",
        title="用户注册表单验证",
        description="用户注册时对输入字段进行验证",
        input_fields=[
            InputField(name="username", data_type="string", valid_range="3-20",
                       constraints=["required", "min_length:3", "max_length:20", "alphanumeric"]),
            InputField(name="password", data_type="string", valid_range="8-32",
                       constraints=["required", "min_length:8", "max_length:32",
                                    "pattern:uppercase", "pattern:lowercase", "pattern:digit"]),
            InputField(name="age", data_type="integer", valid_range="18-120",
                       constraints=["required", "min:18", "max:120"]),
            InputField(name="email", data_type="string", valid_range="valid email",
                       constraints=["required", "format:email"]),
        ],
        conditions=[
            Condition(description="用户名已存在", field="username", operator="==", value="exists_in_db"),
            Condition(description="年龄小于18", field="age", operator="<", value="18"),
            Condition(description="所有输入有效", field=None, operator=None, value=None),
        ],
        expected_behaviors=[
            SystemBehavior(condition="用户名已存在", action="显示错误", expected_output="用户名已被注册"),
            SystemBehavior(condition="年龄<18", action="显示错误", expected_output="未成年不可注册"),
            SystemBehavior(condition="所有有效", action="创建账号", expected_output="注册成功"),
        ],
        domain="web_application"
    )


@pytest.fixture
def sample_login_requirement():
    """创建示例登录需求"""
    return StructuredRequirement(
        id="REQ-002",
        source=SourceType.TEXT,
        raw_text="用户登录: 用户名+密码验证，5次失败锁定30分钟",
        title="用户登录验证",
        description="验证用户名和密码，处理锁定逻辑",
        input_fields=[
            InputField(name="username", data_type="string", constraints=["required"]),
            InputField(name="password", data_type="string", constraints=["required"]),
        ],
        conditions=[
            Condition(description="用户名正确", field="username", operator="==", value="valid"),
            Condition(description="密码正确", field="password", operator="==", value="valid"),
            Condition(description="账户已锁定", field="account", operator="==", value="locked"),
        ],
        expected_behaviors=[
            SystemBehavior(condition="用户名+密码正确且未锁定", action="登录成功", expected_output="跳转主页"),
            SystemBehavior(condition="用户名或密码错误", action="登录失败", expected_output="用户名或密码错误"),
            SystemBehavior(condition="账户锁定", action="拒绝登录", expected_output="账户已锁定"),
        ],
        domain="web_application"
    )


@pytest.fixture
def sample_test_case():
    """创建示例测试用例"""
    return TestCase(
        id="TC-EP-001",
        requirement_id="REQ-001",
        title="有效年龄输入",
        technique="Equivalence Partitioning",
        category="Valid",
        priority="Medium",
        risk_score=0.5,
        test_steps=[
            TestStep(
                step_number=1,
                action="输入年龄30",
                input_data={"age": "30"},
                expected_result="输入验证通过"
            )
        ],
        tags=["equivalence_partitioning", "valid"]
    )


@pytest.fixture
def sample_test_suite(sample_requirement, sample_test_case):
    """创建示例测试套件"""
    return TestSuite(
        id="TS-001",
        name="测试套件示例",
        requirement_id="REQ-001",
        test_cases=[sample_test_case, TestCase(
            id="TC-EP-002",
            requirement_id="REQ-001",
            title="无效年龄（小于最小值）",
            technique="Equivalence Partitioning",
            category="Invalid",
            priority="High",
            risk_score=0.7,
            test_steps=[TestStep(step_number=1, action="输入年龄10", input_data={"age": "10"}, expected_result="显示错误")],
            tags=["equivalence_partitioning", "invalid"]
        )],
    )


@pytest.fixture
def sample_risk_assessment():
    """创建示例风险评估"""
    return RiskAssessment(
        requirement_id="REQ-001",
        likelihood=0.6,
        impact=0.8,
        risk_factors=["多字段输入", "含密码字段"],
        mitigation_suggestions=["EP+BVA覆盖", "安全测试"]
    )


@pytest.fixture
def sample_state_machine():
    """创建登录状态机"""
    return StateMachine(
        id="SM-LOGIN",
        name="登录状态机",
        states=[
            State(id="S1", name="未登录", description="初始状态", is_initial=True),
            State(id="S2", name="登录中", description="验证凭据"),
            State(id="S3", name="已登录", description="登录成功"),
            State(id="S4", name="已锁定", description="错误锁定", is_final=True),
        ],
        transitions=[
            Transition(id="T1", from_state="S1", to_state="S2", trigger="提交登录", action="验证凭据"),
            Transition(id="T2", from_state="S2", to_state="S3", trigger="验证成功", guard="凭据正确"),
            Transition(id="T3", from_state="S2", to_state="S2", trigger="验证失败", guard="次数<5", action="计数+1"),
            Transition(id="T4", from_state="S2", to_state="S4", trigger="验证失败", guard="次数=5", action="锁定30min"),
            Transition(id="T5", from_state="S3", to_state="S1", trigger="登出", action="清除会话"),
        ]
    )


@pytest.fixture
def mock_ai_client():
    """Mock AI客户端，返回固定响应"""
    with patch("src.ai.client.AIClient") as mock:
        client = MagicMock()
        client.chat.return_value = '{"title": "测试", "description": "测试"}'
        client.chat_with_json.return_value = {"title": "测试", "test_cases": []}
        client.structured_output.return_value = {"title": "测试"}
        mock.return_value = client
        yield client
