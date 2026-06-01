import itertools
import json
import pytest

import flask_app.config as app_config
import flask_app.models.database as db_module
from flask_app.app import create_app


_counter = itertools.count(1)


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "human.db"
    old_cfg = app_config.DATABASE
    old_db = db_module.DATABASE
    app_config.DATABASE = str(db_path)
    db_module.DATABASE = str(db_path)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    app_config.DATABASE = old_cfg
    db_module.DATABASE = old_db


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def put_json(client, url, payload):
    return client.put(url, data=json.dumps(payload), content_type="application/json")


def register_user(client, username="manual_user", email="manual_user@example.com"):
    response = post_json(
        client,
        "/api/register",
        {
            "username": username,
            "password": "Valid@123",
            "confirm_password": "Valid@123",
            "email": email,
            "age": 24,
        },
    )
    assert response.status_code == 201
    return response


def create_project(client, name="Manual Project"):
    response = post_json(
        client,
        "/api/projects",
        {"name": f"{name}-{next(_counter)}", "description": "manual test"},
    )
    assert response.status_code == 201
    return response.get_json()["project"]["id"]


def create_task(
    client,
    project_id,
    title="Manual Task",
    description="manual case",
    priority="Medium",
    status="todo",
    assignee="",
    due_date=None,
):
    payload = {
        "title": title,
        "description": description,
        "priority": priority,
        "status": status,
        "assignee": assignee,
    }
    if due_date is not None:
        payload["due_date"] = due_date
    return post_json(client, f"/api/projects/{project_id}/tasks", payload)


class TestEquivalencePartitioning:
    def test_ep_req_005_valid_task(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Task one")
        assert response.status_code == 201

    def test_ep_req_005_empty_title(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="")
        assert response.status_code == 400

    def test_ep_req_005_title_too_long(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="B" * 201)
        assert response.status_code == 400

    def test_ep_req_005_invalid_priority(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, priority="Critical")
        assert response.status_code == 201
        assert response.get_json()["task"]["priority"] == "Medium"

    def test_ep_req_005_invalid_status(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, status="deleted")
        assert response.status_code == 201
        assert response.get_json()["task"]["status"] == "todo"

    def test_ep_req_006_empty_assignee(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Assign later").get_json()["task"]["id"]
        response = post_json(client, f"/api/tasks/{task_id}/assign", {"assignee": ""})
        assert response.status_code == 400

    def test_ep_req_006_project_task_list(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="List task")
        response = client.get(f"/api/projects/{project_id}/tasks")
        assert response.status_code == 200


class TestBoundaryValueAnalysis:
    def test_bva_req_005_title_length_1(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A")
        assert response.status_code == 201

    def test_bva_req_005_title_length_200(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A" * 200)
        assert response.status_code == 201

    def test_bva_req_005_title_length_201(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A" * 201)
        assert response.status_code == 400

    def test_bva_req_005_title_length_100(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A" * 100)
        assert response.status_code == 201

    def test_bva_req_005_due_date_in_past(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Past task", due_date="2020-01-01")
        assert response.status_code == 400

    def test_bva_req_005_title_length_2(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="AB")
        assert response.status_code == 201


class TestDecisionTable:
    def test_dt_req_005_project_exists_valid_title(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Decision task", priority="Low")
        assert response.status_code == 201

    def test_dt_req_005_project_not_found(self, client):
        response = create_task(client, 9999, title="No project")
        assert response.status_code == 404

    def test_dt_req_006_project_task_filter(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="Todo one", status="todo")
        create_task(client, project_id, title="Done one", status="done")
        response = client.get(f"/api/projects/{project_id}/tasks?status=todo")
        assert response.status_code == 200

    def test_dt_req_007_stats_shape(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="S1")
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200
        assert "total_tasks" in response.get_json()

    def test_dt_req_007_missing_project(self, client):
        response = client.get("/api/projects/9999/stats")
        assert response.status_code == 404


class TestPathCoverage:
    def test_pc_req_005_update_missing_task(self, client):
        response = put_json(client, "/api/tasks/9999", {"title": "Update miss"})
        assert response.status_code == 404

    def test_pc_req_005_update_success(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Before update").get_json()["task"]["id"]
        response = put_json(client, f"/api/tasks/{task_id}", {"title": "After update"})
        assert response.status_code == 200

    def test_pc_req_005_create_success(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Path create")
        assert response.status_code == 201

    def test_pc_req_005_detail_missing_task(self, client):
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404


class TestStateTransition:
    def test_st_req_005_create_view(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Lifecycle").get_json()["task"]["id"]
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200

    def test_st_req_006_assign_flow(self, client):
        register_user(client, "owner1", "owner1@example.com")
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Lifecycle assign").get_json()["task"]["id"]
        response = post_json(client, f"/api/tasks/{task_id}/assign", {"assignee": "owner1"})
        assert response.status_code == 200

    def test_st_req_007_existing_project_stats(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="Stats one")
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200

    def test_st_req_006_missing_user_task_query(self, client):
        response = client.get("/api/users/unknown_user/tasks")
        assert response.status_code == 404

    def test_st_req_007_missing_project_stats(self, client):
        response = client.get("/api/projects/999/stats")
        assert response.status_code == 404
