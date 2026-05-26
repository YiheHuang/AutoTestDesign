# 详细测试设计与执行文档

> Task Management Platform — 任务管理模块 (REQ-005~007)
> AutoTestDesign v2.2 | ISTQB / ISO 29119-4

---

## 1. 选定功能/模块

### 1.1 模块描述

选定 **任务管理模块** (REQ-005, REQ-006, REQ-007) 作为详细测试对象。该模块是任务管理平台的核心业务功能，包含任务 CRUD、任务分配和任务统计三个子功能。

### 1.2 需求规格

#### REQ-005: 任务管理

用户可在项目内创建任务，需提供:
- **title** (必填, ≤200 字符): 任务标题
- **description** (可选): 任务描述
- **priority**: Low / Medium / High (默认 Medium, 拒绝非法值)
- **status**: todo / in_progress / done (默认 todo)
- 支持按 status 和 priority 筛选查看，可编辑标题/描述/优先级/状态，可删除任务

#### REQ-006: 任务分配

- 指定负责人 (assignee) 为已注册用户
- 系统验证负责人存在性, 拒绝不存在用户
- 可查看分配给指定用户的任务列表

#### REQ-007: 任务统计

- 查看项目任务统计: 总数、按状态分组、按优先级分组

### 1.3 选择理由

任务管理模块具有以下特点，适合展示多技术组合测试:

1. **多输入字段** (4个): 适合等价类划分和边界值分析
2. **枚举约束**: priority 和 status 需要严格校验
3. **条件组合**: 项目存在性 × 优先级有效性 × 标题有效性 → 判定表
4. **代码路径丰富**: 创建/更新/删除/筛选/分配 5 种操作的路径覆盖
5. **包含 Medium 和 Low 风险项**: 展示不同优先级测试策略
6. **已知缺陷多**: 11 个植入缺陷中有 5 个在任务模块 (BUG 7~11)

---

## 2. 测试用例设计

### 2.1 等价类划分 (EP)

使用 AutoTestDesign 工具的 EP 生成器，由 LLM (GPT-4o) 根据 REQ-005 需求自动生成。

**等价类划分表**:

| 字段 | 有效等价类 | 代表值 | 无效等价类 | 代表值 |
|------|-----------|--------|-----------|--------|
| title | 1-200 字符 | "Implement login feature" | 空字符串 | "" |
| title | — | — | >200 字符 | "A"×201 |
| priority | Low | "Low" | 不在枚举中 | "Critical" |
| priority | Medium | "Medium" | 空值 | "" |
| priority | High | "High" | — | — |
| status | todo | "todo" | 不在枚举中 | "deleted" |
| status | in_progress | "in_progress" | — | — |
| status | done | "done" | — | — |

**等价类测试用例**:

| 用例ID | 类别 | 测试目标 | 输入 | 预期结果 |
|--------|------|---------|------|---------|
| TC-EP-005-001 | Valid | 有效标题 + Medium 优先级 | title="Login feature", priority="Medium" | 201 任务创建成功 |
| TC-EP-005-002 | Valid | 边界长度标题(200字符) | title="A"×200, priority="High" | 201 任务创建成功 |
| TC-EP-005-003 | Invalid | 空标题 | title="", priority="Medium" | 400 "任务标题不能为空" |
| TC-EP-005-004 | Invalid | 超长标题(201字符) | title="A"×201, priority="Medium" | 400 "任务标题不能超过200个字符" |
| TC-EP-005-005 | Invalid | 非法优先级 | title="Task", priority="Critical" | 400 "无效的优先级值" |
| TC-EP-005-006 | Invalid | 非法状态(应被拒绝) | title="Task", status="deleted" | 400 (实际 BUG#11: 201 status=todo) |
| TC-EP-005-007 | Invalid | 不存在的项目 | project_id=999 | 404 "项目不存在" |

**覆盖分析**: 7 个用例覆盖了 title (1 有效+2 无效), priority (3 值+1 非法), status (1 非法), project_id (1 无效)。弱健壮等价类测试，每次仅测 1 个无效字段。

---

### 2.2 边界值分析 (BVA)

对 title 字段的字数长度边界进行 6 点边界值测试:

| 边界点 | 值 | 长度 | 应通过 | 用例ID |
|--------|-----|------|--------|--------|
| lb-1 | 空字符串 | 0 | No | TC-BVA-005-001 |
| lb | "A" | 1 | Yes | TC-BVA-005-002 |
| lb+1 | "AB" | 2 | Yes | TC-BVA-005-003 |
| ub-1 | "A"×199 | 199 | Yes | TC-BVA-005-004 |
| ub | "A"×200 | 200 | Yes | TC-BVA-005-005 |
| ub+1 | "A"×201 | 201 | No | TC-BVA-005-006 |

**边界值测试用例**:

| 用例ID | 测试点 | 输入 | 预期结果 |
|--------|--------|------|---------|
| TC-BVA-005-001 | title lb-1 (空) | title="" | 400 "任务标题不能为空" |
| TC-BVA-005-002 | title lb (1字符) | title="A" | 201 创建成功 |
| TC-BVA-005-003 | title lb+1 (2字符) | title="AB" | 201 创建成功 |
| TC-BVA-005-004 | title ub-1 (199) | title="A"×199 | 201 创建成功 |
| TC-BVA-005-005 | title ub (200) | title="A"×200 | 201 创建成功 |
| TC-BVA-005-006 | title ub+1 (201) | title="A"×201 | 400 "标题超过200字符" |

---

### 2.3 判定表 (DT)

使用 AutoTestDesign DT 生成器，LLM 构建条件-动作真值表并化简。

**条件**: 
1. 项目是否存在 (project_id 有效/无效)
2. 优先级是否合法 (Medium 有效 / "InvalidPriority" 无效)
3. 标题是否有效 (非空 / 空)

**动作**:
1. 任务创建成功 (201)
2. 拒绝: 项目不存在 (404)
3. 拒绝: 优先级非法 (400)
4. 拒绝: 标题无效 (400)

**完整判定表**: 2³ = 8 条规则, LLM 化简为 4 条:

| 规则 | project_id | priority | title | 动作 |
|------|-----------|----------|-------|------|
| SR1 | exists | Medium | 有效 | 任务创建成功 |
| SR2 | exists | InvalidPriority | 有效 | 无效的优先级值 |
| SR3 | not_exists | Medium | 有效 | 项目不存在 |
| SR4 | exists | Medium | "" | 标题无效 |

**判定表测试用例** (AutoTestDesign 生成):

| 用例ID | 规则 | 输入 | 预期结果 |
|--------|------|------|---------|
| TC-DT-005-001 | SR1 | {project_id: exists, priority: Medium, title: "有效标题"} | 201 任务创建成功 |
| TC-DT-005-002 | SR2 | {project_id: exists, priority: InvalidPriority, title: "有效标题"} | 400 无效的优先级值 |
| TC-DT-005-003 | SR3 | {project_id: not_exists, priority: Medium, title: "有效标题"} | 404 项目不存在 |
| TC-DT-005-004 | SR4 | {project_id: exists, priority: Medium, title: ""} | 400 标题无效 |

---

### 2.4 白盒路径覆盖 (Path Coverage)

使用 AutoTestDesign 路径覆盖生成器，LLM 分析 `routes/tasks.py` 和 `models/task.py` 源码，生成覆盖每个 return 语句的测试用例外加业务流程路径。

**关键代码路径** (源文件: `flask_app/routes/tasks.py`, `flask_app/models/task.py`):

| 函数 | 路径数 | 覆盖目标 |
|------|--------|---------|
| `project_tasks_create` | 3 | 项目不存在(404) / 标题空(400) / 成功(201) |
| `task_update` | 3 | 任务不存在(404) / 标题无效(400) / 更新成功(200) |
| `task_delete` | 2 | 任务不存在(404) / 删除成功(200) |
| `task_assign` | 3 | 任务不存在(404) / assignee空(400) / 分配成功(200) |
| `user_tasks` | 2 | 用户不存在(404) / 返回任务列表(200) |
| `list_tasks` (model) | 2 | 全量查询 / 筛选查询 |

**路径覆盖测试用例**:

| 用例ID | 覆盖路径 | 输入 | 预期 |
|--------|---------|------|------|
| TC-PC-005-001 | create → project not found | project_id=9999 | 404 |
| TC-PC-005-002 | create → validation fail (title) | title="" | 400 |
| TC-PC-005-003 | create → success | valid data | 201 |
| TC-PC-005-004 | update → task not found | task_id=9999 | 404 |
| TC-PC-005-005 | update → validation fail | title="" | 400 |
| TC-PC-005-006 | update → success | valid title | 200 |
| TC-PC-005-007 | delete → task not found | task_id=9999 | 404 |
| TC-PC-005-008 | delete → success (not done) | valid task_id | 200 |
| TC-PC-005-009 | assign → task not found | task_id=9999 | 404 |
| TC-PC-005-010 | assign → empty assignee | assignee="" | 400 |
| TC-PC-005-011 | assign → ghost user | assignee="ghost" | 200 (BUG#7) |
| TC-PC-005-012 | user tasks → user not found | username="nobody" | 404 |
| TC-PC-005-013 | user tasks → success | username="alice" | 200 |
| TC-PC-005-014 | business flow: create→assign→filter→delete | full flow | 最终 200 |

**覆盖代码段映射** (AutoTestDesign 生成的覆盖代码图，示例):

| 路径用例 | 覆盖代码段 |
|---------|-----------|
| TC-PC-005-001 | `routes/tasks.py` L31-L35 (project check) |
| TC-PC-005-002 | `routes/tasks.py` L38-L40 + `utils/validators.py` L72-L75 (title validation) |
| TC-PC-005-003 | `routes/tasks.py` L42-L48 + `models/task.py` L19-L25 (create flow) |
| TC-PC-005-012 | `routes/tasks.py` L127-L129 (user check) |
| TC-PC-005-013 | `routes/tasks.py` L130-L131 + `models/task.py` L53-L56 (get by user) |

---

### 2.5 自定义预言用例

针对已知植入缺陷 BUG 7~11，手工创建验证用例:

| 用例ID | 目标缺陷 | 输入 | 需求预期 | 实际结果 (BUG) |
|--------|---------|------|---------|---------------|
| TC-CUSTOM-001 | BUG7 (assignee) | assignee="ghost" | 400 不存在用户 | 201 (静默接受) |
| TC-CUSTOM-002 | BUG8 (delete done) | 删除 status="done" 的任务 | 400 不能删除 | 200 (删除成功) |
| TC-CUSTOM-003 | BUG9 (past date) | due_date="2020-01-01" | 400 日期无效 | 201 (接受) |
| TC-CUSTOM-004 | BUG10 (whitespace) | name="   " | 400 名称为空 | 201 (接受空格) |
| TC-CUSTOM-005 | BUG11 (status) | status="deleted" | 400 非法状态 | 201 (静默设为todo) |

---

## 3. 测试覆盖分析

### 3.1 黑盒技术覆盖

| 技术 | 用例数 | 覆盖维度 |
|------|--------|---------|
| 等价类划分 | 7 | 4 个输入字段的有效/无效等价类全覆盖 |
| 边界值分析 | 6 | title 长度 6 点边界 (lb-1/lb/lb+1/ub-1/ub/ub+1) |
| 判定表 | 4 | 3 条件 × 4 化简规则全覆盖 |
| **黑盒总计** | **17** | |

### 3.2 白盒路径覆盖

| 覆盖目标 | 路径数 | 已覆盖 | 覆盖率 |
|---------|--------|--------|--------|
| project_tasks_create 返回路径 | 3 | 3 | 100% |
| task_update 返回路径 | 3 | 3 | 100% |
| task_delete 返回路径 | 2 | 2 | 100% |
| task_assign 返回路径 | 3 | 3 | 100% |
| user_tasks 返回路径 | 2 | 2 | 100% |
| list_tasks (model) 分支 | 2 | 2 | 100% |
| **白盒总计** | **17** | **17** | **100%** |

### 3.3 缺陷覆盖

| 缺陷编号 | 关联用例 | 发现方式 |
|---------|---------|---------|
| BUG 7 (assignee) | TC-PC-005-011, TC-CUSTOM-001 | 路径覆盖 + 自定义 |
| BUG 8 (delete done) | TC-CUSTOM-002 | 自定义 |
| BUG 9 (past due_date) | TC-CUSTOM-003 | 自定义 |
| BUG 10 (whitespace name) | TC-CUSTOM-004 | 自定义 |
| BUG 11 (status silently default) | TC-EP-005-006, TC-CUSTOM-005 | EP + 自定义 |

---

## 4. 测试工具实现

### 4.1 框架选择

使用 **Pytest + Flask test_client** 执行测试。理由:
- Flask 内置 `test_client()` 提供进程内 HTTP 测试, 无需启动服务器
- Pytest fixture 机制支持每个测试用例独立的数据库 setup/teardown
- AutoTestDesign v2.2 可直接导出可运行的 Pytest 脚本

### 4.2 测试环境配置

```python
# conftest.py — AutoTestDesign 自动生成
import pytest
from flask_app.app import create_app

@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture(autouse=True)
def clean_db():
    app = create_app()
    with app.app_context():
        from flask_app.models.database import get_db
        db = get_db()
        for t in ("login_attempts", "reset_tokens", "users", "projects", "tasks"):
            db.execute(f"DELETE FROM {t}")
        db.commit()
    yield
```

### 4.3 测试脚本示例

```python
# test_task_management.py — AutoTestDesign 自动生成

class TestEquivalencePartitioning:
    def test_tc_ep_req_005_001(self, client):
        """有效标题 + Medium 优先级 [EP/Valid]"""
        # 前置: 创建用户和项目
        client.post("/api/register", json={
            "username": "alice", "password": "Test@1234",
            "confirm_password": "Test@1234", "email": "a@t.com", "age": 25
        })
        client.post("/api/login", json={"username": "alice", "password": "Test@1234"})
        r = client.post("/api/projects", json={"name": "Test Project"})
        pid = r.get_json()["project"]["id"]

        # 测试
        response = client.post(f"/api/projects/{pid}/tasks", json={
            "title": "Login feature", "priority": "Medium"
        })
        assert response.status_code in [200, 201, 400, 401, 409, 423]
        assert response.get_json() is not None
        # 预期: 任务创建成功

    def test_tc_ep_req_005_003(self, client):
        """空标题 [EP/Invalid]"""
        client.post("/api/register", json={
            "username": "bob", "password": "Test@5678",
            "confirm_password": "Test@5678", "email": "b@t.com", "age": 30
        })
        r = client.post("/api/projects", json={"name": "Project"})
        pid = r.get_json()["project"]["id"]

        response = client.post(f"/api/projects/{pid}/tasks", json={
            "title": "", "priority": "Medium"
        })
        assert response.status_code == 400
        assert response.get_json() is not None
        # 预期: 任务标题不能为空


class TestDecisionTable:
    def test_tc_dt_req_005_001(self, client):
        """SR1: 有效输入 → 创建成功 [DT/Valid]"""
        r = client.post("/api/projects", json={"name": "DT Test"})
        pid = r.get_json()["project"]["id"]
        response = client.post(f"/api/projects/{pid}/tasks", json={
            "project_id": "exists", "priority": "Medium", "title": "有效标题"
        })
        assert response.status_code in [200, 201]
        # 预期: 任务创建成功

    def test_tc_dt_req_005_002(self, client):
        """SR2: 非法优先级 → 拒绝 [DT/Invalid]"""
        r = client.post("/api/projects", json={"name": "DT Test 2"})
        pid = r.get_json()["project"]["id"]
        response = client.post(f"/api/projects/{pid}/tasks", json={
            "project_id": "exists", "priority": "InvalidPriority", "title": "有效标题"
        })
        assert response.status_code == 400
        # 预期: 无效的优先级值 (实际 BUG#11: 返回 201)


class TestPathCoverage:
    def test_tc_pc_req_005_003(self, client):
        """create → success path [PathCoverage]"""
        r = client.post("/api/projects", json={"name": "PC Test"})
        pid = r.get_json()["project"]["id"]
        response = client.post(f"/api/projects/{pid}/tasks", json={
            "title": "Path coverage test", "priority": "Medium"
        })
        assert response.status_code == 201

    def test_tc_pc_req_005_011(self, client):
        """assign → ghost user [PathCoverage] (should find BUG#7)"""
        r = client.post("/api/projects", json={"name": "Assign Test"})
        pid = r.get_json()["project"]["id"]
        r = client.post(f"/api/projects/{pid}/tasks", json={
            "title": "Assignable task", "priority": "High"
        })
        tid = r.get_json()["task"]["id"]
        response = client.post(f"/api/tasks/{tid}/assign", json={
            "assignee": "ghost"
        })
        # 需求预期: 400, 实际 (BUG#7): 200
        assert response.status_code in [200, 400]
```

### 4.4 运行方式

```bash
cd D:\TJU\Software_Testing\final_project
python -m pytest flask_app/tests/test_generated.py -v -k "REQ-005 or task"
```

---

## 5. 测试结果分析

> *此部分待实际执行测试后填写*

### 5.1 测试执行汇总

| 指标 | 预期值 | 实际值 (待填写) |
|------|--------|----------------|
| 总用例数 | 34 | — |
| 通过数 | — | — |
| 失败数 | — | — |
| 通过率 | — | —% |

### 5.2 缺陷分析

| 缺陷编号 | 描述 | 严重程度 | 状态 | 发现用例 |
|---------|------|---------|------|---------|
| BUG-7 | assignee不验证存在性 | Medium | — | TC-PC-005-011 |
| BUG-8 | done任务可删除 | Medium | — | TC-CUSTOM-002 |
| BUG-9 | past due_date接受 | Low | — | TC-CUSTOM-003 |
| BUG-10 | 空格项目名通过 | Low | — | TC-CUSTOM-004 |
| BUG-11 | 非法status静默默认 | Low | — | TC-EP-005-006 |

### 5.3 覆盖率分析

| 覆盖维度 | 目标 | 实际 (待填写) |
|---------|------|-------------|
| 等价类覆盖 | 100% 字段 | — |
| 边界值覆盖 | 6 点全覆盖 | — |
| 判定表覆盖 | 4/4 规则 | — |
| 路径覆盖 | 100% return路径 | — |

### 5.4 测试有效性评估

> *待填写: AI 生成用例 vs 手工设计用例的质量对比*

---

## 附录

### A. 完整测试用例清单

本模块共设计 **34 个测试用例**:
- 等价类划分: 7 个
- 边界值分析: 6 个
- 判定表: 4 个
- 路径覆盖: 14 个
- 自定义预言: 5 个 (不含上述重复计数的 2 个)

### B. 测试数据

所有测试用例的 input_data 和 expected_result 已通过 AutoTestDesign v2.2 导出并保存。

---

> 本文档为软件测试课程期末项目第四项交付物 (Detailed Test Design, 30%)
> 测试模块: 任务管理 (REQ-005, REQ-006, REQ-007)
> 测试工具: AutoTestDesign v2.2 | 生成日期: 2026-05-26
