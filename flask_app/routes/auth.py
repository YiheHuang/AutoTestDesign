"""用户认证路由 — Blueprint /api"""

import hashlib
import secrets
import datetime
from flask import Blueprint, request, jsonify, g
from flask_app.models.database import get_db
from flask_app.utils.validators import validate_username, validate_password, validate_email, validate_age
from flask_app.config import MAX_LOGIN_FAILURES, LOCK_DURATION_MINUTES, RESET_TOKEN_EXPIRY_HOURS

bp = Blueprint("auth", __name__, url_prefix="/api")


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def check_login_locked(username):
    db = get_db()
    since = (datetime.datetime.now() - datetime.timedelta(minutes=LOCK_DURATION_MINUTES)).isoformat()
    failures = db.execute(
        "SELECT COUNT(*) as cnt FROM login_attempts WHERE username=? AND success=0 AND attempt_time>?",
        (username, since)
    ).fetchone()
    return failures["cnt"] >= MAX_LOGIN_FAILURES


def get_remaining_lock_time(username):
    db = get_db()
    since = (datetime.datetime.now() - datetime.timedelta(minutes=LOCK_DURATION_MINUTES)).isoformat()
    last = db.execute(
        "SELECT attempt_time FROM login_attempts WHERE username=? AND success=0 AND attempt_time>? ORDER BY attempt_time DESC LIMIT 1",
        (username, since)
    ).fetchone()
    if not last:
        return 0
    elapsed = (datetime.datetime.now() - datetime.datetime.fromisoformat(last["attempt_time"])).total_seconds()
    return max(0, int(LOCK_DURATION_MINUTES * 60 - elapsed))


# ─── /register ───

@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    username = data.get("username", "")
    valid, msg = validate_username(username)
    if not valid:
        return jsonify({"error": msg, "field": "username"}), 400

    password = data.get("password", "")
    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"error": msg, "field": "password"}), 400

    confirm = data.get("confirm_password", "")
    if password != confirm:
        return jsonify({"error": "两次输入的密码不一致", "field": "confirm_password"}), 400

    email = data.get("email", "")
    valid, msg = validate_email(email)
    if not valid:
        return jsonify({"error": msg, "field": "email"}), 400

    age = data.get("age")
    valid, msg = validate_age(age)
    if not valid:
        return jsonify({"error": msg, "field": "age"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        return jsonify({"error": "用户名已被注册", "field": "username"}), 409

    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "邮箱已被注册", "field": "email"}), 409

    db.execute(
        "INSERT INTO users (username, password_hash, email, age, created_at) VALUES (?,?,?,?,?)",
        (username, hash_password(password), email, int(age), datetime.datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"message": "注册成功", "user": {"username": username, "email": email}}), 201


# ─── /login ───

@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    username = data.get("username", "")
    password = data.get("password", "")
    remember_me = data.get("remember_me", False)

    db = get_db()
    if check_login_locked(username):
        remaining = get_remaining_lock_time(username)
        return jsonify({
            "error": f"账户已锁定，请{remaining // 60}分{remaining % 60}秒后重试",
            "locked": True,
            "remaining_seconds": remaining
        }), 423

    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user or user["password_hash"] != hash_password(password):
        db.execute(
            "INSERT INTO login_attempts (username, attempt_time, success, ip_address) VALUES (?,?,0,?)",
            (username, datetime.datetime.now().isoformat(), request.remote_addr or "")
        )
        db.commit()
        if check_login_locked(username):
            remaining = get_remaining_lock_time(username)
            return jsonify({
                "error": f"账户已锁定，请{remaining // 60}分{remaining % 60}秒后重试",
                "locked": True,
                "remaining_seconds": remaining
            }), 423
        return jsonify({"error": "用户名或密码错误"}), 401

    # BUG #6: 登录成功后没有清除之前的失败记录，导致即使成功登录后，旧失败计数仍累积
    # 按需求，登录成功后应重置失败计数器，但此处未执行 DELETE
    db.execute(
        "INSERT INTO login_attempts (username, attempt_time, success, ip_address) VALUES (?,?,1,?)",
        (username, datetime.datetime.now().isoformat(), request.remote_addr or "")
    )
    db.commit()
    return jsonify({
        "message": "登录成功",
        "user": {"username": user["username"], "email": user["email"], "age": user["age"]},
        "remember_me": remember_me
    }), 200


# ─── /forgot-password ───

@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    email = data.get("email", "")
    valid, msg = validate_email(email)
    if not valid:
        return jsonify({"error": msg, "field": "email"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not user:
        return jsonify({"message": "如果该邮箱已注册，重置邮件已发送"}), 200

    token = secrets.token_urlsafe(32)
    db.execute(
        "INSERT INTO reset_tokens (email, token, created_at, used) VALUES (?,?,?,0)",
        (email, token, datetime.datetime.now().isoformat())
    )
    db.commit()
    return jsonify({"message": "如果该邮箱已注册，重置邮件已发送", "reset_token": token}), 200


# ─── /reset-password ───

@bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "请求体需为JSON格式"}), 400

    token = data.get("token", "")
    new_password = data.get("new_password", "")
    confirm = data.get("confirm_password", "")

    if not token:
        return jsonify({"error": "重置凭证不能为空", "field": "token"}), 400

    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({"error": msg, "field": "new_password"}), 400

    if new_password != confirm:
        return jsonify({"error": "两次输入的密码不一致", "field": "confirm_password"}), 400

    db = get_db()
    reset_entry = db.execute(
        "SELECT * FROM reset_tokens WHERE token=? AND used=0", (token,)
    ).fetchone()
    if not reset_entry:
        return jsonify({"error": "无效的重置凭证", "field": "token"}), 400

    created = datetime.datetime.fromisoformat(reset_entry["created_at"])
    # BUG #3: 应该是 hours=RESET_TOKEN_EXPIRY_HOURS，这里误写成了 minutes
    if datetime.datetime.now() - created > datetime.timedelta(minutes=RESET_TOKEN_EXPIRY_HOURS):
        return jsonify({"error": "重置凭证已过期", "field": "token"}), 400

    db.execute("UPDATE users SET password_hash=? WHERE email=?",
               (hash_password(new_password), reset_entry["email"]))
    db.execute("UPDATE reset_tokens SET used=1 WHERE id=?", (reset_entry["id"],))
    db.commit()
    return jsonify({"message": "密码重置成功"}), 200


# ─── /logout ───

@bp.route("/logout", methods=["GET"])
def logout():
    return jsonify({"message": "登出成功"}), 200
