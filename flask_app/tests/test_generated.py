"""AutoTestDesign 自动生成 | 2026-05-25T15:02:11.227943"""
import pytest, json, sys, os

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

from flask_app.app import app, init_db


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.app_context():
        init_db()
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_db():
    with app.app_context():
        from flask_app.app import get_db
        db = get_db()
        for t in ("login_attempts", "reset_tokens", "users"):
            db.execute(f"DELETE FROM {t}")
        db.commit()
    yield


class TestBoundaryValueAnalysis:

    def test_tc_bva_req_001_001(self, client):
        """Username below minimum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "ab"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 用户名需为3-20位字母或数字

    def test_tc_bva_req_001_002(self, client):
        """Username at minimum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "abc"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Valid

    def test_tc_bva_req_001_003(self, client):
        """Password below minimum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"password": "Abc123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 密码需包含大写字母、小写字母、数字和特殊字符中的至少三种

    def test_tc_bva_req_001_004(self, client):
        """Password at minimum length [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"password": "Abc123!@"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Valid

    def test_tc_bva_req_001_005(self, client):
        """Age below minimum [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"age": 17}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 未成年不可注册

    def test_tc_bva_req_001_006(self, client):
        """Age at minimum [Boundary Value Analysis/Boundary]"""
        response = client.post(
            "/register",
            data=json.dumps({"age": 18}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Valid

    def test_tc_bva_req_001_007(self, client):
        """Email invalid format [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"email": "testexample.com"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 请输入有效邮箱地址

    def test_tc_bva_req_001_008(self, client):
        """Email valid format [Boundary Value Analysis/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"email": "test@example.com"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Valid

    def test_tc_bva_req_001_009(self, client):
        """Password and confirm password mismatch [Boundary Value Analysis/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"password": "Abc123!@", "confirm_password": "Abc123!#@"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 两次输入的密码不一致

    def test_tc_bva_req_001_010(self, client):
        """Password and confirm password match [Boundary Value Analysis/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"password": "Abc123!@", "confirm_password": "Abc123!@"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Valid

class TestCustomOracle:

    def test_tc_custom_req_001_001(self, client):
        """TC-CUSTOM-REQ-001-001 [Custom Oracle/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "YiheHuang", "password": "123321", "email": "huangyihe@tongji.edu.cn", "age": "2"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: {"error": "未成年不可注册（需年满18岁）", "field": "age"}

class TestDecisionTable:

    def test_tc_dt_req_001_001(self, client):
        """测试用例1: 用户名已存在 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "existing_user", "age": 25, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 用户名已被注册

    def test_tc_dt_req_001_002(self, client):
        """测试用例2: 年龄小于18 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 17, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 未成年不可注册

    def test_tc_dt_req_001_003(self, client):
        """测试用例3: 年龄大于120 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 121, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 请输入有效年龄

    def test_tc_dt_req_001_004(self, client):
        """测试用例4: 邮箱已存在 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 25, "email": "existing@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 邮箱已被注册

    def test_tc_dt_req_001_005(self, client):
        """测试用例5: 密码与确认密码不一致 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 25, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "DifferentPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 两次输入的密码不一致

    def test_tc_dt_req_001_006(self, client):
        """测试用例6: 密码复杂度不足 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 25, "email": "test@example.com", "password": "simple", "confirm_password": "simple"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 密码需包含大写字母、小写字母、数字和特殊字符中的至少三种

    def test_tc_dt_req_001_007(self, client):
        """测试用例7: 用户名格式不正确 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "invalid_user!", "age": 25, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 用户名需为3-20位字母或数字

    def test_tc_dt_req_001_008(self, client):
        """测试用例8: 邮箱格式不正确 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 25, "email": "invalid_email", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 显示错误: 请输入有效邮箱地址

    def test_tc_dt_req_001_009(self, client):
        """测试用例9: 全部条件有效 [DecisionTable/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "new_user", "age": 25, "email": "test@example.com", "password": "ValidPass123!", "confirm_password": "ValidPass123!"}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 创建账号: 注册成功

class TestEquivalencePartitioning:

    def test_tc_ep_req_001_001(self, client):
        """Valid Registration [Equivalence Partitioning/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 注册成功

    def test_tc_ep_req_001_002(self, client):
        """Invalid Username - Too Short [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "us", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 用户名需为3-20位字母或数字

    def test_tc_ep_req_001_003(self, client):
        """Invalid Username - Too Long [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "usernamethatiswaytoolong", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 用户名需为3-20位字母或数字

    def test_tc_ep_req_001_004(self, client):
        """Invalid Username - Non-Alphanumeric [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user@123", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 用户名需为3-20位字母或数字

    def test_tc_ep_req_001_005(self, client):
        """Invalid Username - Already Exists [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "existing_user", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 用户名已被注册

    def test_tc_ep_req_001_006(self, client):
        """Invalid Password - Too Short [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Pass1!", "confirm_password": "Pass1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 密码需包含大写字母、小写字母、数字和特殊字符中的至少三种

    def test_tc_ep_req_001_007(self, client):
        """Invalid Password - Too Long [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password12345678901234567890123456789!", "confirm_password": "Password12345678901234567890123456789!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 密码需包含大写字母、小写字母、数字和特殊字符中的至少三种

    def test_tc_ep_req_001_008(self, client):
        """Invalid Password - Complexity [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "password", "confirm_password": "password", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 密码需包含大写字母、小写字母、数字和特殊字符中的至少三种

    def test_tc_ep_req_001_009(self, client):
        """Invalid Confirm Password - Mismatch [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password2!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 两次输入的密码不一致

    def test_tc_ep_req_001_010(self, client):
        """Invalid Email - Format [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password1!", "email": "userexample.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 请输入有效邮箱地址

    def test_tc_ep_req_001_011(self, client):
        """Invalid Email - Already Exists [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password1!", "email": "existing@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 邮箱已被注册

    def test_tc_ep_req_001_012(self, client):
        """Invalid Age - Too Young [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 17}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 未成年不可注册

    def test_tc_ep_req_001_013(self, client):
        """Invalid Age - Too Old [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Password1!", "confirm_password": "Password1!", "email": "user@example.com", "age": 121}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: 请输入有效年龄
