import itertools
import json
import pytest

import flask_app.config as app_config
import flask_app.models.database as db_module
from flask_app.app import create_app


_counter = itertools.count(1)


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "generated_refined.db"
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


def register_user(client, username="alice", email="alice@example.com"):
    response = post_json(
        client,
        "/api/register",
        {
            "username": username,
            "password": "Valid@123",
            "confirm_password": "Valid@123",
            "email": email,
            "age": 25,
        },
    )
    assert response.status_code == 201
    return response


def create_project(client, name="Project A", description="task project"):
    unique_name = f"{name}-{next(_counter)}"
    response = post_json(client, "/api/projects", {"name": unique_name, "description": description})
    assert response.status_code == 201
    return response.get_json()["project"]["id"]


def create_task(
    client,
    project_id,
    title="Task Alpha",
    description="demo task",
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
    def test_ep_req_005_valid_title_and_priority(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Implement login", priority="Medium")
        assert response.status_code == 201

    def test_ep_req_005_empty_title(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="")
        assert response.status_code == 400
        assert response.get_json()["field"] == "title"

    def test_ep_req_005_title_too_long(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A" * 201)
        assert response.status_code == 400

    def test_ep_req_005_invalid_priority_defaults(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, priority="Critical")
        assert response.status_code == 201
        assert response.get_json()["task"]["priority"] == "Medium"

    def test_ep_req_005_invalid_status_defaults(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, status="archived")
        assert response.status_code == 201
        assert response.get_json()["task"]["status"] == "todo"

    def test_ep_req_006_empty_assignee(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Need owner").get_json()["task"]["id"]
        response = post_json(client, f"/api/tasks/{task_id}/assign", {"assignee": ""})
        assert response.status_code == 400
        assert response.get_json()["field"] == "assignee"

    def test_ep_req_006_unregistered_assignee(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Assign check").get_json()["task"]["id"]
        response = put_json(client, f"/api/tasks/{task_id}", {"assignee": "ghost_user"})
        assert response.status_code == 400

    def test_ep_req_006_project_task_list(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="Listable task")
        response = client.get(f"/api/projects/{project_id}/tasks")
        assert response.status_code == 200
        assert len(response.get_json()["tasks"]) == 1


class TestBoundaryValueAnalysis:
    def test_bva_req_005_title_length_1(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A")
        assert response.status_code == 201

    def test_bva_req_005_title_length_2(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="AB")
        assert response.status_code == 201

    def test_bva_req_005_title_length_199(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="A" * 199)
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


class TestDecisionTable:
    def test_dt_req_005_project_exists_valid_priority(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Table case", priority="Low")
        assert response.status_code == 201

    def test_dt_req_005_project_not_found(self, client):
        response = create_task(client, 9999, title="Ghost task", priority="Medium")
        assert response.status_code == 404

    def test_dt_req_005_project_exists_invalid_priority(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Invalid priority case", priority="InvalidPriority")
        assert response.status_code == 201
        assert response.get_json()["task"]["priority"] == "Medium"

    def test_dt_req_006_project_task_list_with_filter(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="Todo task", status="todo")
        create_task(client, project_id, title="Done task", status="done")
        response = client.get(f"/api/projects/{project_id}/tasks?status=todo")
        assert response.status_code == 200
        assert len(response.get_json()["tasks"]) >= 1

    def test_dt_req_007_stats_response_shape(self, client):
        project_id = create_project(client)
        create_task(client, project_id, title="T1", priority="Low", status="todo")
        create_task(client, project_id, title="T2", priority="High", status="done")
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert set(data.keys()) == {"project_id", "total_tasks", "by_status", "by_priority"}

    def test_dt_req_007_missing_project(self, client):
        response = client.get("/api/projects/9999/stats")
        assert response.status_code == 404


class TestPathCoverage:
    def test_pc_req_005_create_success_path(self, client):
        project_id = create_project(client)
        response = create_task(client, project_id, title="Path success")
        assert response.status_code == 201

    def test_pc_req_005_update_missing_task(self, client):
        response = put_json(client, "/api/tasks/9999", {"title": "Updated title"})
        assert response.status_code == 404

    def test_pc_req_005_update_invalid_title(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Task before update").get_json()["task"]["id"]
        response = put_json(client, f"/api/tasks/{task_id}", {"title": ""})
        assert response.status_code == 400

    def test_pc_req_005_detail_missing_task(self, client):
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404

    def test_pc_req_005_delete_todo_task(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Delete me", status="todo").get_json()["task"]["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200

    def test_pc_req_005_delete_done_task(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Completed task", status="done").get_json()["task"]["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 400


class TestStateTransition:
    def test_st_req_005_create_view_update(self, client):
        project_id = create_project(client)
        task_id = create_task(client, project_id, title="Lifecycle task").get_json()["task"]["id"]
        detail = client.get(f"/api/tasks/{task_id}")
        assert detail.status_code == 200
        update = put_json(client, f"/api/tasks/{task_id}", {"title": "Lifecycle updated"})
        assert update.status_code == 200
        assert update.get_json()["task"]["title"] == "Lifecycle updated"

    def test_st_req_006_query_missing_user_tasks(self, client):
        response = client.get("/api/users/unknown_user/tasks")
        assert response.status_code == 404

    def test_st_req_006_query_existing_user_without_tasks(self, client):
        register_user(client, "bob", "bob@example.com")
        response = client.get("/api/users/bob/tasks")
        assert response.status_code == 200
        assert response.get_json()["tasks"] == []

    def test_st_req_007_stats_single_project(self, client):
        project_id = create_project(client, "Stats Project A")
        create_task(client, project_id, title="S1", status="todo", priority="Low")
        create_task(client, project_id, title="S2", status="done", priority="High")
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert data["project_id"] == project_id
        assert isinstance(data["by_status"], dict)
        assert isinstance(data["by_priority"], dict)

    def test_st_req_007_stats_request(self, client):
        project_id = create_project(client, "Stats Project B")
        response = client.get(f"/api/projects/{project_id}/stats")
        assert response.status_code == 200
