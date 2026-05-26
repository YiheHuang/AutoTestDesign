"""任务数据模型"""

import datetime


def list_tasks(db, project_id, status_filter=None, priority_filter=None):
    query = "SELECT * FROM tasks WHERE project_id=?"
    params = [project_id]
    if status_filter:
        # BUG #5: 使用 LIKE 而非精确匹配
        query += " AND status LIKE ?"
        params.append(f"%{status_filter}%")
    if priority_filter:
        query += " AND priority=?"
        params.append(priority_filter)
    query += " ORDER BY created_at DESC"
    return db.execute(query, params).fetchall()


def get_task(db, task_id):
    return db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()


def create_task(db, project_id, title, description="", priority="Medium", status="todo", assignee="", due_date=None):
    now = datetime.datetime.now().isoformat()
    db.execute(
        "INSERT INTO tasks (project_id, title, description, priority, status, assignee, due_date, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (project_id, title, description, priority, status, assignee, due_date, now, now)
    )
    db.commit()
    return db.execute("SELECT * FROM tasks WHERE id=last_insert_rowid()").fetchone()


def update_task(db, task_id, data):
    fields = []
    values = []
    for k in ("title", "description", "priority", "status", "assignee", "due_date"):
        if k in data:
            fields.append(f"{k}=?")
            values.append(data[k])
    if fields:
        fields.append("updated_at=?")
        values.append(datetime.datetime.now().isoformat())
        values.append(task_id)
        db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", values)
        db.commit()


def delete_task(db, task_id):
    db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    db.commit()


def get_tasks_by_user(db, username):
    return db.execute(
        "SELECT * FROM tasks WHERE assignee=? ORDER BY created_at DESC", (username,)
    ).fetchall()
