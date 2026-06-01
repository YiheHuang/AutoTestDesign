"""应用配置"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "data.db")

SECRET_KEY = "task-platform-secret-key-2024"

MAX_LOGIN_FAILURES = 5
LOCK_DURATION_MINUTES = 30
RESET_TOKEN_EXPIRY_HOURS = 1

TASK_PRIORITIES = ("Low", "Medium", "High")
TASK_STATUSES = ("todo", "in_progress", "done")
