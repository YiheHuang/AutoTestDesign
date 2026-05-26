# 故意植入的破绽记录

本文档记录任务管理平台中故意植入的 11 个与需求不符合的破绽。

## 认证模块 (3 个)

| # | 文件 | 行 | 破绽 | 需求预期 | 实际行为 | 风险 |
|---|------|----|------|---------|---------|------|
| 1 | `routes/auth.py` | `reset_password` | Token 过期使用分钟替代小时 | REQ-003: 重置 token 1 小时有效 | `timedelta(minutes=RESET_TOKEN_EXPIRY_HOURS)` 实际只有 1 分钟即过期 | High |
| 2 | `routes/auth.py` | `login` | 登录成功后未清除失败记录 | REQ-002: 登录成功应重置失败计数器 | 旧的失败记录保留在 login_attempts 表, 用户可能被错误锁定 | High |
| 3 | `routes/auth.py` | `register` | 注册时允许密码与用户名相同 | REQ-001: 密码需包含至少 3 种字符类型 | 当用户名恰好满足密码复杂度时, 可用用户名作为密码 | Low |

## 项目管理模块 (3 个)

| # | 文件 | 行 | 破绽 | 需求预期 | 实际行为 | 风险 |
|---|------|----|------|---------|---------|------|
| 4 | `routes/projects.py` | `project_delete` | 删除项目不级联删除任务 | REQ-004: 删除项目时应同时删除其下任务 | 只删 projects 表, tasks 保留为孤儿数据 | Medium |
| 5 | `routes/projects.py` | `projects_create` | 缺少项目名称重复检查 | REQ-004: 应拒绝重复项目名 | 直接 INSERT, 同名的两个项目可共存 | Medium |
| 6 | `routes/projects.py` | `project_stats` | 统计忽略 project_id 过滤 | REQ-007: 统计指定项目的任务 | `SELECT * FROM tasks` 返回全部任务, 统计了所有项目的数据 | Low |

## 任务管理模块 (3 个)

| # | 文件 | 行 | 破绽 | 需求预期 | 实际行为 | 风险 |
|---|------|----|------|---------|---------|------|
| 7 | `routes/tasks.py` | `task_update`, `task_assign` | assignee 未做存在性检查 | REQ-006: 应验证负责人是否为已注册用户 | 接受任意用户名, 不查询 users 表 | Medium |
| 8 | `routes/tasks.py` | `task_delete` | 删除"done"状态任务时未禁止 | REQ-005: 已完成任务不应被删除 | 所有状态的任务均可直接删除 | Medium |
| 9 | `routes/tasks.py` | `tasks_create` | 任务创建时允许指定过去的 due_date | REQ-005: 截止日期不应早于当前时间 | 接受任意日期值, 包括 2020-01-01 | Low |

## 验证逻辑模块 (2 个)

| # | 文件 | 行 | 破绽 | 需求预期 | 实际行为 | 风险 |
|---|------|----|------|---------|---------|------|
| 10 | `utils/validators.py` | `validate_project_name` | 纯空格 "   " 通过名称验证 | REQ-004: 项目名称不能为空 | `isinstance(str)` + `>100` 检查, 但无 `strip()` 检查 | Low |
| 11 | `utils/validators.py` | `validate_task_status` | 非法状态值静默设为 todo | REQ-005: 应拒绝非法的状态值 | `not in TASK_STATUSES` 时返回 "todo", 不报错 | Low |

## 验证方法

| # | API 验证 | 预期状态码 | 实际状态码 |
|---|---------|-----------|-----------|
| 1 | 获取 token 后等待 1 分钟 → `POST /api/reset-password` | 200 | 400 "重置凭证已过期" |
| 2 | 失败 4 次 → 成功登录 1 次 → 再失败 1 次 → `/api/login` | 200 | 423 "账户已锁定" |
| 3 | `POST /api/register` 使用 `{"password": "Alice@123"}` (用户名为 Alice) | 400 | 201 (密码恰好满足复杂度) |
| 4 | `DELETE /api/projects/1` → `GET /api/tasks/1` | 404 | 200 (孤儿任务) |
| 5 | `POST /api/projects` 两次用同一名称 "Sprint1" | 409 | 201 (两个同名项目) |
| 6 | `GET /api/projects/1/stats` (project 1 有 3 tasks, project 2 有 2 tasks) | total=3 | total=5 (全部项目) |
| 7 | `POST /api/projects/1/tasks` with `{"assignee": "ghost"}` | 400 | 201 |
| 8 | `DELETE /api/tasks/3` (status="done") | 400 | 200 |
| 9 | `POST /api/projects/1/tasks` with `{"due_date": "2020-01-01"}` | 400 | 201 |
| 10 | `POST /api/projects` with `{"name": "   "}` | 400 | 201 |
| 11 | `POST /api/projects/1/tasks` with `{"status": "deleted"}` | 400 | 201 (任务 status="todo") |
