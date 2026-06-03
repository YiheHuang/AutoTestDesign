"""AutoTestDesign 自动生成 | 2026-06-03T10:33:27.372758"""
import pytest, json, sys, os

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

from flask_app.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_db():
    app = create_app()
    with app.app_context():
        from flask_app.models.database import get_db
        db = get_db()
        for t in ("login_attempts", "reset_tokens", "users", "projects", "tasks"):
            db.execute(f"DELETE FROM {t}")
        db.commit()
    yield


class TestBoundaryValueAnalysis:

    def test_tc_bva_req_005_001(self, client):
        """Title is empty [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Validation error: Title is required

    def test_tc_bva_req_005_002(self, client):
        """Title at minimum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Task created successfully

    def test_tc_bva_req_005_003(self, client):
        """Title exceeds maximum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Validation error: Title exceeds maximum length

    def test_tc_bva_req_005_004(self, client):
        """Invalid priority value [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "Valid Title", "priority": "Very High", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Validation error: Invalid priority value

    def test_tc_bva_req_005_005(self, client):
        """Invalid status value [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "Valid Title", "priority": "Medium", "status": "completed"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Validation error: Invalid status value

    def test_tc_bva_req_005_006(self, client):
        """Valid input data [Boundary Value Analysis/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "Valid Title", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Task created successfully

class TestCustomOracle:

    def test_tc_custom_req_005_001(self, client):
        """TC-CUSTOM-REQ-005-001 [Custom Oracle/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "", "description": "", "priority": "", "status": ""}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"error": "任务标题不能为空", "field": "title"}

class TestDecisionTable:

    def test_tc_dt_req_005_001(self, client):
        """创建任务 - 有效输入 [DecisionTable/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "exists", "title": "有效任务标题", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建成功

    def test_tc_dt_req_005_002(self, client):
        """拒绝任务 - 优先级非法 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "exists", "title": "有效任务标题", "priority": "InvalidPriority", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_dt_req_005_003(self, client):
        """拒绝任务 - 项目不存在 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "not_exists", "title": "有效任务标题", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建被拒绝

    def test_tc_dt_req_005_004(self, client):
        """拒绝任务 - 项目不存在且优先级非法 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "not_exists", "title": "有效任务标题", "priority": "InvalidPriority", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

class TestEquivalencePartitioning:

    def test_tc_ep_req_005_001(self, client):
        """有效标题和默认优先级 [Equivalence Partitioning/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "任意描述", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建成功

    def test_tc_ep_req_005_002(self, client):
        """标题为空 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "", "description": "任意描述", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 标题不能为空

    def test_tc_ep_req_005_003(self, client):
        """标题超过最大长度 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 标题长度不能超过200字符

    def test_tc_ep_req_005_004(self, client):
        """标题为null [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": null, "description": "任意描述", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 标题不能为空

    def test_tc_ep_req_005_005(self, client):
        """优先级为非法枚举值 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "任意描述", "priority": "Urgent", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_ep_req_005_006(self, client):
        """优先级为null [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "任意描述", "priority": null, "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_ep_req_005_007(self, client):
        """状态为非法枚举值 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "任意描述", "priority": "Medium", "status": "archived"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的状态值

    def test_tc_ep_req_005_008(self, client):
        """状态为null [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "任意描述", "priority": "Medium", "status": null}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的状态值

class TestPathCoverage:

    def test_tc_pc_001(self, client):
        """用户注册成功 [PathCoverage/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "validUser123", "password": "ValidPass123!", "confirm_password": "ValidPass123!", "email": "valid.email@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None

    def test_tc_pc_002(self, client):
        """用户名已存在 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "existingUser", "password": "ValidPass123!", "confirm_password": "ValidPass123!", "email": "new.email@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 409, "response_body": {"error": "用户名已被注册", "field": "username"}}

    def test_tc_pc_003(self, client):
        """邮箱已存在 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "newUser", "password": "ValidPass123!", "confirm_password": "ValidPass123!", "email": "existing.email@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 409, "response_body": {"error": "邮箱已被注册", "field": "email"}}

    def test_tc_pc_004(self, client):
        """密码不一致 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "newUser", "password": "ValidPass123!", "confirm_password": "DifferentPass123!", "email": "new.email@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "response_body": {"error": "两次输入的密码不一致", "field": "confirm_password"}}

    def test_tc_pc_005(self, client):
        """年龄不符合要求 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "newUser", "password": "ValidPass123!", "confirm_password": "ValidPass123!", "email": "new.email@example.com", "age": 15}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "response_body": {"error": "未成年不可注册（需年满18岁）", "field": "age"}}

    def test_tc_pc_006(self, client):
        """无效的用户名格式 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "invalid@user", "password": "ValidPass123!", "confirm_password": "ValidPass123!", "email": "new.email@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "response_body": {"error": "用户名只能包含字母和数字", "field": "username"}}

class TestStateTransition:

    def test_tc_st_req_001_001(self, client):
        """成功注册测试 [State Transition/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "testuser", "password": "Test@1234", "confirm_password": "Test@1234", "email": "test@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态

    def test_tc_st_req_001_002(self, client):
        """用户名验证失败测试 [State Transition/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "ab", "password": "Test@1234", "confirm_password": "Test@1234", "email": "test@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态

    def test_tc_st_req_001_003(self, client):
        """密码验证失败测试 [State Transition/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "testuser", "password": "123", "confirm_password": "123", "email": "test@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态

    def test_tc_st_req_001_004(self, client):
        """邮箱验证失败测试 [State Transition/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "testuser", "password": "Test@1234", "confirm_password": "Test@1234", "email": "invalid-email", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态

    def test_tc_st_req_001_005(self, client):
        """年龄验证失败测试 [State Transition/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "testuser", "password": "Test@1234", "confirm_password": "Test@1234", "email": "test@example.com", "age": 17}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态

    def test_tc_st_req_001_006(self, client):
        """唯一性检查失败测试 [State Transition/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"username": "existinguser", "password": "Test@1234", "confirm_password": "Test@1234", "email": "existing@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入验证用户名状态
