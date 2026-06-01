"""任务管理路由 — Blueprint /api"""

from flask import Blueprint, request, jsonify, g
from flask_app.models.database import get_db
from flask_app.models.task import create_task, get_task, update_task, delete_task, list_tasks, get_tasks_by_user
from flask_app.utils.validators import validate_task_title, validate_task_priority, validate_task_status
import datetime

bp = Blueprint("tasks", __name__, url_prefix="/api")


@bp.route("/projects/<int:project_id>/tasks", methods=["GET"])
def project_tasks_list(project_id):
    db = get_db()
    proj = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        return jsonify({"error": "项目不存在"}), 404

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    tasks = list_tasks(db, project_id, status_filter, priority_filter)
    return jsonify({"tasks": [dict(t) for t in tasks]}), 200


@bp.route("/projects/<int:project_id>/tasks", methods=["POST"])
def project_tasks_create(project_id):
    db = get_db()
    proj = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not proj:
        return jsonify({"error": "项目不存在"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    title = data.get("title", "")
    valid, msg = validate_task_title(title)
    if not valid:
        return jsonify({"error": msg, "field": "title"}), 400

    description = data.get("description", "")
    priority = validate_task_priority(data.get("priority", "Medium"))
    status = validate_task_status(data.get("status", "todo"))
    assignee = data.get("assignee", "")
    due_date = data.get("due_date")

    task = create_task(db, project_id, title, description, priority, status, assignee, due_date)
    return jsonify({"message": "任务创建成功", "task": dict(task)}), 201


@bp.route("/tasks/<int:task_id>", methods=["GET"])
def task_detail(task_id):
    db = get_db()
    task = get_task(db, task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify({"task": dict(task)}), 200


@bp.route("/tasks/<int:task_id>", methods=["PUT"])
def task_update(task_id):
    db = get_db()
    task = get_task(db, task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    if "title" in data:
        valid, msg = validate_task_title(data["title"])
        if not valid:
            return jsonify({"error": msg, "field": "title"}), 400

    priority = data.get("priority")
    if priority is not None:
        data["priority"] = validate_task_priority(priority)

    if "status" in data:
        data["status"] = validate_task_status(data["status"])

    # BUG #1: 没有检查 assignee 是否存在
    assignee = data.get("assignee")
    if assignee is not None:
        data["assignee"] = assignee

    update_task(db, task_id, data)
    updated = get_task(db, task_id)
    return jsonify({"message": "任务更新成功", "task": dict(updated)}), 200


@bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def task_delete(task_id):
    db = get_db()
    task = get_task(db, task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    # BUG #8: 未检查任务状态。需求规定已完成(done)的任务不应被删除
    delete_task(db, task_id)
    return jsonify({"message": "任务已删除"}), 200


@bp.route("/tasks/<int:task_id>/assign", methods=["POST"])
def task_assign(task_id):
    db = get_db()
    task = get_task(db, task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    assignee = data.get("assignee", "")
    if not assignee:
        return jsonify({"error": "负责人不能为空", "field": "assignee"}), 400

    # BUG #1 (also here): 不检查 assignee 是否存在于 users 表
    db.execute("UPDATE tasks SET assignee=?, updated_at=? WHERE id=?",
               (assignee, datetime.datetime.now().isoformat(), task_id))
    db.commit()
    updated = get_task(db, task_id)
    return jsonify({"message": "分配成功", "task": dict(updated)}), 200


@bp.route("/users/<username>/tasks", methods=["GET"])
def user_tasks(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    tasks = get_tasks_by_user(db, username)
    return jsonify({"tasks": [dict(t) for t in tasks]}), 200
