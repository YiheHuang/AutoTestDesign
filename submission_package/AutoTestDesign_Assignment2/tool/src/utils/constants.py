"""全局常量定义 (v2.2)"""

# 测试技术名称
TECHNIQUE_EP = "Equivalence Partitioning"
TECHNIQUE_BVA = "Boundary Value Analysis"
TECHNIQUE_DT = "DecisionTable"
TECHNIQUE_PC = "PathCoverage"

# 技术短键映射
TECH_SHORT = {"EP": TECHNIQUE_EP, "BVA": TECHNIQUE_BVA, "DecisionTable": TECHNIQUE_DT}

# 测试用例类别
CATEGORY_VALID = "Valid"
CATEGORY_INVALID = "Invalid"
CATEGORY_BOUNDARY = "Boundary"

# 导出格式
FORMAT_JSON = "json"
FORMAT_PYTEST = "pytest"

# AI配置
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 4096
MAX_RETRIES = 3

# Flask API端点映射 (用于pytest导出fallback)
ENDPOINT_KEYWORDS = {
    "login": "/api/login",
    "forgot": "/api/forgot-password",
    "reset": "/api/reset-password",
    "logout": "/api/logout",
    "health": "/health",
    "project": "/api/projects",
    "task": "/api/projects/1/tasks",
    "统计": "/api/projects/1/stats",
    "分配": "/api/tasks/1/assign",
}
DEFAULT_ENDPOINT = "/api/register"

# 有效HTTP状态码
VALID_STATUS_CODES = [200, 201, 400, 401, 409, 423]
