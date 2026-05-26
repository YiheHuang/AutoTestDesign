"""项目数据模型"""

import datetime


def list_projects(db):
    return db.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()


def get_project(db, project_id):
    return db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()


def create_project(db, name, description=""):
    now = datetime.datetime.now().isoformat()
    db.execute(
        "INSERT INTO projects (name, description, created_at, updated_at) VALUES (?,?,?,?)",
        (name, description, now, now)
    )
    db.commit()
    return db.execute("SELECT * FROM projects WHERE id=last_insert_rowid()").fetchone()


def update_project(db, project_id, data):
    fields = []
    values = []
    for k in ("name", "description"):
        if k in data:
            fields.append(f"{k}=?")
            values.append(data[k])
    if fields:
        fields.append("updated_at=?")
        values.append(datetime.datetime.now().isoformat())
        values.append(project_id)
        db.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id=?", values)
        db.commit()


def delete_project(db, project_id):
    db.execute("DELETE FROM projects WHERE id=?", (project_id,))
    db.commit()
