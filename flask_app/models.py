"""数据模型定义（与 app.py 中的 SQLite schema 对应）"""

# users 表
USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,      -- 用户名 3-20 字母数字
    password_hash TEXT NOT NULL,        -- SHA256 密码哈希
    email TEXT UNIQUE NOT NULL,         -- 邮箱
    age INTEGER NOT NULL,               -- 年龄 18-120
    created_at TEXT NOT NULL            -- 创建时间 ISO格式
)
"""

# login_attempts 表
LOGIN_ATTEMPTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,             -- 尝试登录的用户名
    attempt_time TEXT NOT NULL,         -- 尝试时间 ISO格式
    success INTEGER NOT NULL,           -- 0=失败, 1=成功
    ip_address TEXT DEFAULT ''         -- 客户端IP
)
"""

# reset_tokens 表
RESET_TOKENS_SCHEMA = """
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,                -- 用户邮箱
    token TEXT UNIQUE NOT NULL,         -- 重置令牌
    created_at TEXT NOT NULL,           -- 创建时间
    used INTEGER DEFAULT 0             -- 0=未使用, 1=已使用
)
"""

# 验证规则常量
VALIDATION_RULES = {
    "username": {
        "type": "string",
        "min_length": 3,
        "max_length": 20,
        "pattern": r'^[a-zA-Z0-9]+$',
        "description": "3-20字符，仅字母和数字"
    },
    "password": {
        "type": "string",
        "min_length": 8,
        "max_length": 32,
        "min_categories": 3,
        "categories": ["uppercase", "lowercase", "digit", "special_char"],
        "description": "8-32位，至少包含大小写字母、数字、特殊字符中的3种"
    },
    "email": {
        "type": "string",
        "pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        "description": "有效邮箱格式"
    },
    "age": {
        "type": "integer",
        "min": 18,
        "max": 120,
        "description": "18-120岁"
    }
}

# 登录配置
LOGIN_CONFIG = {
    "max_failed_attempts": 5,           # 最大失败次数
    "lock_duration_minutes": 30,        # 锁定持续时间
    "reset_token_expiry_hours": 1       # 重置令牌有效期
}
