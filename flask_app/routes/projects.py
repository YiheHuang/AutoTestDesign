"""项目管理路由 — Blueprint /api"""

from flask import Blueprint, request, jsonify, g
from flask_app.models.database import get_db
from flask_app.models.project import create_project, get_project, update_project, delete_project, list_projects
from flask_app.utils.validators import validate_project_name
import datetime

bp = Blueprint("projects", __name__, url_prefix="/api")


@bp.route("/projects", methods=["GET"])
def projects_list():
    db = get_db()
    projects = list_projects(db)
    return jsonify({"projects": [dict(p) for p in projects]}), 200


@bp.route("/projects", methods=["POST"])
def projects_create():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    name = data.get("name", "")
    valid, msg = validate_project_name(name)
    if not valid:
        return jsonify({"error": msg, "field": "name"}), 400

    description = data.get("description", "")
    # BUG #7: 缺少项目名称重复检查。需求规定应拒绝重复项目名，但此处直接创建
    project = create_project(get_db(), name, description)
    return jsonify({"message": "项目创建成功", "project": dict(project)}), 201


@bp.route("/projects/<int:project_id>", methods=["GET"])
def project_detail(project_id):
    db = get_db()
    project = get_project(db, project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404
    return jsonify({"project": dict(project)}), 200


@bp.route("/projects/<int:project_id>", methods=["PUT"])
def project_update(project_id):
    db = get_db()
    project = get_project(db, project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    if "name" in data:
        valid, msg = validate_project_name(data["name"])
        if not valid:
            return jsonify({"error": msg, "field": "name"}), 400

    update_project(db, project_id, data)
    updated = get_project(db, project_id)
    return jsonify({"message": "项目更新成功", "project": dict(updated)}), 200


@bp.route("/projects/<int:project_id>", methods=["DELETE"])
def project_delete(project_id):
    db = get_db()
    project = get_project(db, project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404

    name = project["name"]
    # BUG #2: 删除项目时没有级联删除其下的任务，只删了项目本身
    db.execute("DELETE FROM projects WHERE id=?", (project_id,))
    db.commit()
    return jsonify({"message": f"项目'{name}'已删除"}), 200


@bp.route("/projects/<int:project_id>/stats", methods=["GET"])
def project_stats(project_id):
    """任务统计 (REQ-007, Low risk)"""
    db = get_db()
    project = get_project(db, project_id)
    if not project:
        return jsonify({"error": "项目不存在"}), 404

    # BUG #10: 统计时忽略了project_id过滤，返回全部任务而非指定项目的任务
    tasks = db.execute("SELECT * FROM tasks").fetchall()
    total = len(tasks)
    by_status = {"todo": 0, "in_progress": 0, "done": 0}
    by_priority = {"Low": 0, "Medium": 0, "High": 0}
    for t in tasks:
        s = t["status"]
        if s in by_status:
            by_status[s] += 1
        p = t["priority"]
        if p in by_priority:
            by_priority[p] += 1

    return jsonify({
        "project_id": project_id,
        "total_tasks": total,
        "by_status": by_status,
        "by_priority": by_priority
    }), 200
