"""用户注册登录系统 - Flask 被测应用

此应用作为 AutoTestDesign 工具的测试对象，包含：
- 用户注册（5字段验证 + 唯一性检查）
- 用户登录（验证 + 5次锁定30分钟）
- 密码重置（邮箱验证 → token → 新密码）
- 登出
"""

import re
import secrets
import datetime
import sqlite3
from functools import wraps
from flask import Flask, request, jsonify, g

import os
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(_BASE_DIR, "data.db")

# ──────────────────────────────────────────────
# 数据库
# ──────────────────────────────────────────────


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                attempt_time TEXT NOT NULL,
                success INTEGER NOT NULL,
                ip_address TEXT DEFAULT ''
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                used INTEGER DEFAULT 0
            )
        """)
        db.commit()


# ──────────────────────────────────────────────
# 验证工具函数（被测对象的核心业务逻辑）
# ──────────────────────────────────────────────


def validate_username(username):
    """验证用户名：3-20字符，仅字母和数字"""
    if not username or not isinstance(username, str):
        return False, "用户名不能为空"
    if len(username) < 3:
        return False, "用户名长度不能少于3个字符"
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False, "用户名只能包含字母和数字"
    return True, ""


def validate_password(password):
    """验证密码：8-32位，至少包含大小写字母、数字、特殊字符中的3种"""
    if not password or not isinstance(password, str):
        return False, "密码不能为空"
    if len(password) < 8:
        return False, "密码长度不能少于8个字符"
    if len(password) > 32:
        return False, "密码长度不能超过32个字符"

    categories = 0
    if re.search(r'[A-Z]', password):
        categories += 1
    if re.search(r'[a-z]', password):
        categories += 1
    if re.search(r'[0-9]', password):
        categories += 1
    if re.search(r'[^a-zA-Z0-9]', password):
        categories += 1

    if categories < 3:
        return False, "密码需包含大写字母、小写字母、数字和特殊字符中的至少三种"
    return True, ""


def validate_email(email):
    """验证邮箱格式"""
    if not email or not isinstance(email, str):
        return False, "邮箱不能为空"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "请输入有效的邮箱地址"
    return True, ""


def validate_age(age):
    """验证年龄：18-120"""
    if age is None:
        return False, "年龄不能为空"
    try:
        age_int = int(age)
    except (ValueError, TypeError):
        return False, "年龄必须为整数"
    if age_int < 18:
        return False, "未成年不可注册（需年满18岁）"
    if age_int > 120:
        return False, "请输入有效年龄（18-120）"
    return True, ""


def hash_password(password):
    """密码哈希（简化版，生产环境应使用 bcrypt）"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def check_login_locked(username):
    """检查账户是否被锁定（最近30分钟内是否达到5次失败）"""
    db = get_db()
    cutoff = (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat()
    failures = db.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts "
        "WHERE username = ? AND success = 0 AND attempt_time > ?",
        (username, cutoff)
    ).fetchone()
    return failures["cnt"] >= 5


def get_remaining_lock_time(username):
    """获取剩余锁定时间（秒）"""
    db = get_db()
    cutoff = (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat()
    last_failure = db.execute(
        "SELECT attempt_time FROM login_attempts "
        "WHERE username = ? AND success = 0 AND attempt_time > ? "
        "ORDER BY attempt_time ASC LIMIT 1",
        (username, cutoff)
    ).fetchone()
    if not last_failure:
        return 0
    lock_until = datetime.datetime.fromisoformat(last_failure["attempt_time"]) + datetime.timedelta(minutes=30)
    remaining = (lock_until - datetime.datetime.now()).total_seconds()
    return max(0, int(remaining))


# ──────────────────────────────────────────────
# API 端点
# ──────────────────────────────────────────────


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "timestamp": datetime.datetime.now().isoformat()})


@app.route("/register", methods=["POST"])
def register():
    """用户注册

    请求体 JSON:
    {
        "username": "string (3-20, 仅字母数字)",
        "password": "string (8-32, 至少3种字符类型)",
        "confirm_password": "string (必须与password一致)",
        "email": "string (有效邮箱格式)",
        "age": "integer (18-120)"
    }

    响应:
    201: 注册成功
    400: 输入验证失败
    409: 用户名或邮箱已存在
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体必须为JSON格式"}), 400

    username = data.get("username", "")
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    email = data.get("email", "")
    age = data.get("age")

    # 逐字段验证
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({"error": msg, "field": "username"}), 400

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"error": msg, "field": "password"}), 400

    if password != confirm_password:
        return jsonify({"error": "两次输入的密码不一致", "field": "confirm_password"}), 400

    valid, msg = validate_email(email)
    if not valid:
        return jsonify({"error": msg, "field": "email"}), 400

    valid, msg = validate_age(age)
    if not valid:
        return jsonify({"error": msg, "field": "age"}), 400

    # 唯一性检查
    db = get_db()
    existing_user = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing_user:
        return jsonify({"error": "用户名已被注册", "field": "username"}), 409

    existing_email = db.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing_email:
        return jsonify({"error": "邮箱已被注册", "field": "email"}), 409

    # 创建用户
    db.execute(
        "INSERT INTO users (username, password_hash, email, age, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, hash_password(password), email, int(age), datetime.datetime.now().isoformat())
    )
    db.commit()

    return jsonify({
        "message": "注册成功",
        "user": {"username": username, "email": email}
    }), 201


@app.route("/login", methods=["POST"])
def login():
    """用户登录

    请求体 JSON:
    {
        "username": "string",
        "password": "string",
        "remember_me": "boolean (可选，默认false)"
    }

    响应:
    200: 登录成功
    401: 用户名或密码错误
    423: 账户已锁定
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体必须为JSON格式"}), 400

    username = data.get("username", "")
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)
    now = datetime.datetime.now().isoformat()
    ip = request.remote_addr or ""

    # 检查是否锁定
    if check_login_locked(username):
        remaining = get_remaining_lock_time(username)
        db = get_db()
        db.execute(
            "INSERT INTO login_attempts (username, attempt_time, success, ip_address) VALUES (?, ?, 0, ?)",
            (username, now, ip)
        )
        db.commit()
        return jsonify({
            "error": f"账户已锁定，请{remaining // 60}分{remaining % 60}秒后重试",
            "locked": True,
            "remaining_seconds": remaining
        }), 423

    # 查找用户
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if not user or user["password_hash"] != hash_password(password):
        # 登录失败
        db.execute(
            "INSERT INTO login_attempts (username, attempt_time, success, ip_address) VALUES (?, ?, 0, ?)",
            (username, now, ip)
        )
        db.commit()

        # 检查失败后是否触发锁定
        if check_login_locked(username):
            remaining = get_remaining_lock_time(username)
            return jsonify({
                "error": f"账户已锁定，请{remaining // 60}分{remaining % 60}秒后重试",
                "locked": True,
                "remaining_seconds": remaining
            }), 423

        return jsonify({"error": "用户名或密码错误"}), 401

    # 登录成功
    db.execute(
        "INSERT INTO login_attempts (username, attempt_time, success, ip_address) VALUES (?, ?, 1, ?)",
        (username, now, ip)
    )
    db.commit()

    return jsonify({
        "message": "登录成功",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "age": user["age"]
        },
        "remember_me": remember_me
    }), 200


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    """忘记密码 - 发送重置链接

    请求体 JSON:
    {
        "email": "string"
    }

    响应:
    200: 如果邮箱已注册，生成重置token（不会泄露是否存在）
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体必须为JSON格式"}), 400

    email = data.get("email", "")

    valid, msg = validate_email(email)
    if not valid:
        return jsonify({"error": msg, "field": "email"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        # 安全考虑：不暴露邮箱是否注册，统一返回成功
        return jsonify({"message": "如果该邮箱已注册，重置链接已发送"}), 200

    # 生成重置token
    token = secrets.token_urlsafe(32)
    db.execute(
        "INSERT INTO reset_tokens (email, token, created_at) VALUES (?, ?, ?)",
        (email, token, datetime.datetime.now().isoformat())
    )
    db.commit()

    return jsonify({
        "message": "如果该邮箱已注册，重置链接已发送",
        "reset_token": token  # 实际应用中通过邮件发送，这里直接返回用于测试
    }), 200


@app.route("/reset-password", methods=["POST"])
def reset_password():
    """重置密码

    请求体 JSON:
    {
        "token": "string (重置令牌)",
        "new_password": "string (8-32位, 至少3种字符类型)",
        "confirm_password": "string (必须与new_password一致)"
    }

    响应:
    200: 重置成功
    400: 输入验证失败或token无效
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体必须为JSON格式"}), 400

    token = data.get("token", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if not token:
        return jsonify({"error": "重置令牌不能为空", "field": "token"}), 400

    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({"error": msg, "field": "new_password"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "两次输入的密码不一致", "field": "confirm_password"}), 400

    db = get_db()
    reset_entry = db.execute(
        "SELECT * FROM reset_tokens WHERE token = ? AND used = 0", (token,)
    ).fetchone()

    if not reset_entry:
        return jsonify({"error": "无效的重置令牌", "field": "token"}), 400

    # 检查token是否过期（1小时内有效）
    created = datetime.datetime.fromisoformat(reset_entry["created_at"])
    if datetime.datetime.now() - created > datetime.timedelta(hours=1):
        return jsonify({"error": "重置令牌已过期", "field": "token"}), 400

    # 更新密码
    db.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (hash_password(new_password), reset_entry["email"])
    )
    db.execute("UPDATE reset_tokens SET used = 1 WHERE id = ?", (reset_entry["id"],))
    db.commit()

    return jsonify({"message": "密码重置成功"}), 200


@app.route("/logout", methods=["GET"])
def logout():
    """登出"""
    return jsonify({"message": "登出成功"}), 200


# ──────────────────────────────────────────────
# 启动
# ──────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
