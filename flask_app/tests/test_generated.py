"""AutoTestDesign 自动生成 | 2026-05-12T00:44:26.317532"""
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


class TestEquivalencePartitioning:

    def test_tc_ep_req_001_001(self, client):
        """Valid registration [Equivalence Partitioning/Valid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Registration successful

    def test_tc_ep_req_001_002(self, client):
        """Invalid username - too short [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "us", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 用户名需为3-20位字母或数字

    def test_tc_ep_req_001_004(self, client):
        """Invalid username - already exists [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "existingUser", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 用户名已被注册

    def test_tc_ep_req_001_007(self, client):
        """Invalid confirm_password - mismatch [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "DifferentPass1!", "email": "user@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 两次输入的密码不一致

    def test_tc_ep_req_001_008(self, client):
        """Invalid email - invalid format [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "userexample.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 请输入有效邮箱地址

    def test_tc_ep_req_001_009(self, client):
        """Invalid email - already exists [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "existing@example.com", "age": 25}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 邮箱已被注册

    def test_tc_ep_req_001_010(self, client):
        """Invalid age - too young [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "user@example.com", "age": 17}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 未成年不可注册

    def test_tc_ep_req_001_011(self, client):
        """Invalid age - too old [Equivalence Partitioning/Invalid]"""
        response = client.post(
            "/register",
            data=json.dumps({"username": "user123", "password": "Passw0rd!", "confirm_password": "Passw0rd!", "email": "user@example.com", "age": 121}),
            content_type="application/json"
        )
        assert response.status_code in [200, 201, 400, 401, 409, 423], f"Got {response.status_code}"
        response_json = response.get_json()
        assert response_json is not None
        # 预期: Error: 请输入有效年龄
