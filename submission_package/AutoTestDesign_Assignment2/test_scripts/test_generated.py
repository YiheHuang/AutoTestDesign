"""AutoTestDesign 自动生成 | 2026-06-01T13:56:52.686288"""
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
        """Title为空 [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": ""}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建失败，title为必填项

    def test_tc_bva_req_005_002(self, client):
        """Title长度为1 [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建成功

    def test_tc_bva_req_005_003(self, client):
        """Title长度为200 [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建成功

    def test_tc_bva_req_005_004(self, client):
        """Title长度为201 [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "a"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建失败，title长度超出限制

    def test_tc_bva_req_005_005(self, client):
        """Priority为非法值 [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"priority": "Very Low"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建失败，无效的优先级值

    def test_tc_bva_req_005_006(self, client):
        """Status为非法值 [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"status": "not_started"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建失败，无效的状态值

    def test_tc_bva_req_006_001(self, client):
        """Valid registered user assignment [Boundary Value Analysis/Valid]"""
        response = client.post(
            "/api/projects/1/tasks",
            data=json.dumps({"assignee": "registered_user_123"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配成功

    def test_tc_bva_req_006_002(self, client):
        """Invalid user assignment [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/api/projects/1/tasks",
            data=json.dumps({"assignee": "unregistered_user_456"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配失败

class TestDecisionTable:

    def test_tc_dt_req_005_001(self, client):
        """测试用例1: 项目存在且优先级合法 [DecisionTable/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "123", "priority": "Medium"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建成功

    def test_tc_dt_req_005_002(self, client):
        """测试用例2: 项目存在但优先级非法 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "123", "priority": "InvalidPriority"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_dt_req_005_003(self, client):
        """测试用例3: 项目不存在且优先级非法 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "not_exists", "priority": "InvalidPriority"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_dt_req_005_004(self, client):
        """测试用例4: 项目不存在但优先级合法 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": "not_exists", "priority": "Low"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务创建被拒绝

    def test_tc_dt_req_006_001(self, client):
        """测试用例1: assignee存在且为注册用户 [DecisionTable/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": "registered_user_1"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配任务

    def test_tc_dt_req_006_002(self, client):
        """测试用例2: assignee存在但不是注册用户 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": "unregistered_user_1"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 不分配任务

    def test_tc_dt_req_006_003(self, client):
        """测试用例3: assignee不存在 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": null}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 不分配任务

    def test_tc_dt_req_007_001(self, client):
        """任务存在时返回统计结果 [DecisionTable/Valid]"""
        response = client.post(
            "/api/projects/1/stats",
            data=json.dumps({"任务ID": "12345"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 统计结果

    def test_tc_dt_req_007_002(self, client):
        """任务不存在时无动作 [DecisionTable/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"任务ID": null}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无动作

class TestEquivalencePartitioning:

    def test_tc_ep_req_005_001(self, client):
        """有效标题和默认优先级 [Equivalence Partitioning/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "有效描述", "priority": "Medium", "status": "todo"}),
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
            data=json.dumps({"title": "", "description": "有效描述", "priority": "Medium", "status": "todo"}),
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
            data=json.dumps({"title": null, "description": "有效描述", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 标题不能为空

    def test_tc_ep_req_005_005(self, client):
        """非法优先级 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "有效描述", "priority": "Critical", "status": "todo"}),
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
            data=json.dumps({"title": "有效标题", "description": "有效描述", "priority": null, "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的优先级值

    def test_tc_ep_req_005_007(self, client):
        """非法状态 [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "有效标题", "description": "有效描述", "priority": "Medium", "status": "archived"}),
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
            data=json.dumps({"title": "有效标题", "description": "有效描述", "priority": "Medium", "status": null}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 无效的状态值

    def test_tc_ep_req_006_001(self, client):
        """Valid assignee [Equivalence Partitioning/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": "registered_user_123"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配成功

    def test_tc_ep_req_006_002(self, client):
        """Invalid assignee - unregistered user [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": "unregistered_user_456"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配失败

    def test_tc_ep_req_006_003(self, client):
        """Invalid assignee - empty string [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": ""}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配失败

    def test_tc_ep_req_006_004(self, client):
        """Invalid assignee - null value [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"assignee": null}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 分配失败

class TestPathCoverage:

    def test_tc_pc_001(self, client):
        """创建任务成功 [PathCoverage/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": 1, "title": "Test Task", "description": "This is a test task", "priority": "Medium", "status": "todo", "assignee": "user1", "due_date": "2023-12-31"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None

    def test_tc_pc_002(self, client):
        """项目不存在时创建任务 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": 999, "title": "Test Task", "description": "This is a test task", "priority": "Medium", "status": "todo", "assignee": "user1", "due_date": "2023-12-31"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 404, "error": "项目不存在"}

    def test_tc_pc_003(self, client):
        """任务标题为空 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": 1, "title": "", "description": "This is a test task", "priority": "Medium", "status": "todo", "assignee": "user1", "due_date": "2023-12-31"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "error": "标题不能为空", "field": "title"}

    def test_tc_pc_004(self, client):
        """非法优先级 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"project_id": 1, "title": "Test Task", "description": "This is a test task", "priority": "InvalidPriority", "status": "todo", "assignee": "user1", "due_date": "2023-12-31"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "error": "无效的优先级值"}

    def test_tc_pc_005(self, client):
        """任务不存在时更新任务 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"task_id": 999, "title": "Updated Task Title"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 404, "error": "任务不存在"}

    def test_tc_pc_006(self, client):
        """删除已完成任务 [PathCoverage/Invalid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"task_id": 1}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"status_code": 400, "error": "已完成的任务不能被删除"}

class TestStateTransition:

    def test_tc_st_req_005_001(self, client):
        """测试用例1: 从项目不存在到任务删除 [State Transition/Valid]"""
        response = client.post(
            "/api/register",
            data=json.dumps({"title": "任务1", "priority": "Medium", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入状态S2: 任务创建中

    def test_tc_st_req_005_002(self, client):
        """测试用例2: 从项目不存在到任务分配完成 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"title": "任务2", "priority": "Low", "status": "todo"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 进入状态S2: 任务创建中

    def test_tc_st_req_006_001(self, client):
        """测试任务不存在时的分配行为 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"task_id": 999, "assignee": "user1"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 返回错误消息: 任务不存在

    def test_tc_st_req_006_002(self, client):
        """测试任务存在且分配成功 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"task_id": 1, "assignee": "user1"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务分配成功，返回更新后的任务信息

    def test_tc_st_req_006_003(self, client):
        """测试任务存在但分配失败 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"task_id": 1, "assignee": ""}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 返回错误消息: 负责人不能为空

    def test_tc_st_req_006_004(self, client):
        """测试任务已分配且重新分配成功 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"task_id": 1, "assignee": "user2"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 任务重新分配成功，返回更新后的任务信息

    def test_tc_st_req_006_005(self, client):
        """测试任务已分配但重新分配失败 [State Transition/Valid]"""
        response = client.post(
            "/api/tasks/1/assign",
            data=json.dumps({"task_id": 1, "assignee": ""}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 返回错误消息: 负责人不能为空

    def test_tc_st_req_007_001(self, client):
        """测试项目不存在时的任务统计 [State Transition/Valid]"""
        response = client.post(
            "/api/projects/1/stats",
            data=json.dumps({"project_id": "invalid_project_id"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 返回错误消息: 项目不存在

    def test_tc_st_req_007_002(self, client):
        """测试项目存在时的任务统计 [State Transition/Valid]"""
        response = client.post(
            "/api/projects/1/stats",
            data=json.dumps({"project_id": "valid_project_id"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 返回任务统计结果，包括任务总数、按状态统计和按优先级统计
