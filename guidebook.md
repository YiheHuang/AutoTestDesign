# AutoTestDesign - 教学指南 (Guidebook)

> AI驱动的自动化测试设计工具 | 软件测试课程期末项目 v2.2

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [被测应用](#3-被测应用)
4. [工作流程详解](#4-工作流程详解)
5. [AI集成与提示词工程](#5-ai集成与提示词工程)
6. [测试技术详解](#6-测试技术详解)
7. [安装与运行](#7-安装与运行)
8. [项目结构](#8-项目结构)

---

## 1. 项目概述

### 1.1 项目目标

AutoTestDesign 是一款 AI 驱动的自动化测试设计工具，基于 ISTQB 测试理论和 ISO/IEC/IEEE 29119-4 标准，实现从需求分析到可运行测试脚本的完整自动化流程。

### 1.2 核心能力

- 从需求文档和代码仓库自动提取标准化需求条目，并建立需求-代码映射
- LLM 评估每项需求的测试风险等级 (High/Medium/Low)
- 应用等价类划分(EP)、边界值分析(BVA)、判定表(DT)三种黑盒技术生成测试用例及分析表
- 应用路径覆盖白盒技术，生成测试用例-覆盖代码图并计算覆盖率
- LLM 驱动的测试套件优化: 黑盒合并逻辑相同用例 / 白盒基于覆盖率删除冗余
- 纯本地生成可运行 pytest 测试脚本 (Flask test_client, 不依赖网络)

### 1.3 工作流概览 (6步)

```
Step 1 需求输入:     代码仓库 + 需求文本 -> LLM -> 标准需求 + 需求-代码图
Step 2 风险分析:     标准需求 -> LLM -> risk_level + risk_factors
Step 3 黑盒测试设计: 标准需求 -> LLM -> EP/BVA/DT 分析表 + 测试用例
Step 4 白盒测试设计: 标准需求 + 需求-代码图 + 源码 -> LLM -> 路径覆盖用例 + 覆盖代码图 + 覆盖率
Step 5 套件优化:     黑盒: LLM合并相同用例 / 白盒: LLM覆盖率优化 + 一键恢复
Step 6 导出:         本地生成 pytest (Flask test_client) + JSON 文档
```

---

## 2. 系统架构

### 2.1 分层架构

```
Streamlit UI (6页面)
    |
Core Engine:
    Parser -> Risk Analyzer -> Test Design -> Optimization -> Export
    |
AI Service Layer:
    OpenAI SDK -> yunwu.ai -> GPT-4o
    提示词模板库 x 5
    |
Data Model Layer:
    Pydantic v2 (StructuredRequirement, TestCase, TestSuite,
                 RequirementCodeMapping, TestCaseCodeMapping, CoverageReport)
```

### 2.2 数据流

```
需求文本 + 代码文件夹
    -> AIExtractor.extract_with_code()
    -> [StructuredRequirement[], RequirementCodeMapping[]]

StructuredRequirement[]
    -> RiskAnalyzer.analyze_batch()
    -> [RiskAssessment]  (risk_level + risk_factors)

StructuredRequirement (选一)
    -> BlackBoxOrchestrator.generate_all()
        -> EPGenerator / BVAGenerator / DTGenerator (LLM)
    -> TestSuite + 分析表 (等价类/边界值/判定表)

StructuredRequirement + RequirementCodeMapping + 源码
    -> PathCoverageGenerator.generate()
    -> TestSuite + [TestCaseCodeMapping] + CoverageReport

TestSuite
    -> CoverageOptimizer.optimize_blackbox()   (黑盒: LLM合并)
    -> CoverageOptimizer.optimize_coverage()   (白盒: LLM覆盖率优化)
    -> 优化后的 TestSuite + 恢复功能

TestSuite[]
    -> PytestExporter.export()  (纯本地生成, 无LLM)
    -> test_generated.py (Flask test_client)
```

---

## 3. 被测应用

### 3.1 概述

被测应用是基于 Flask 的用户注册登录 Web API，作为 AutoTestDesign 的测试对象。

### 3.2 API 端点

| 端点 | 方法 | 功能 | 关键验证 |
|------|------|------|---------|
| /register | POST | 用户注册 | username(3-20字母数字), password(8-32位/至少3种字符类型), confirm_password, email(有效格式/唯一), age(18-120) |
| /login | POST | 用户登录 | 密码验证 + 5次失败锁定30分钟 |
| /forgot-password | POST | 忘记密码 | 邮箱验证 + 生成重置token |
| /reset-password | POST | 重置密码 | token验证 + 新密码设置 |
| /logout | GET | 登出 | - |
| /health | GET | 健康检查 | - |

### 3.3 数据库

```sql
users (id, username UNIQUE, password_hash, email UNIQUE, age, created_at)
login_attempts (id, username, attempt_time, success, ip_address)
reset_tokens (id, email, token UNIQUE, created_at, used)
```

---

## 4. 工作流程详解

### 4.1 需求输入

**输入**: 代码仓库路径 + 需求文本

**处理**: LLM 接收需求文本 + 全部源码，输出标准化需求条目 (REQ-001 ~ REQ-00N) 和需求-代码映射。

**LLM 输出**:
```json
{
  "requirements": [{
    "id": "REQ-001", "title": "用户注册",
    "input_fields": [{"name":"username","data_type":"string","valid_range":"3-20",...}],
    "conditions": [...], "expected_behaviors": [...]
  }],
  "mappings": [{
    "requirement_id": "REQ-001",
    "code_segments": [{
      "file_path": "app.py", "start_line": 83, "end_line": 93,
      "function_name": "validate_username", "description": "用户名验证逻辑"
    }]
  }]
}
```

**核心文件**: `src/parser/ai_extractor.py`, `src/ai/prompts/requirement_mapping_prompts.py`

### 4.2 风险分析

**输入**: 标准化需求列表

**LLM 输出**: 每项需求的 risk_level (High/Medium/Low) 和 risk_factors

**风险等级参考**:
- High: 核心功能、安全认证、敏感数据
- Medium: 一般业务功能
- Low: 辅助功能

**核心文件**: `src/risk/risk_analyzer.py`, `src/ai/prompts/risk_prompts.py`

### 4.3 黑盒测试设计

**输入**: 选择一条标准需求 + 选择技术 (EP/BVA/DT)

#### 等价类划分 (EP)
LLM 为每个输入字段划分有效/无效等价类，生成等价类划分表 + 测试用例。策略: 弱健壮 (每次只测1个无效值)。

#### 边界值分析 (BVA)
LLM 识别数值/长度边界，每个边界生成6点测试 (lb-1, lb, lb+1, ub-1, ub, ub+1)，输出边界值分析表 + 测试用例。

#### 判定表 (DT)
LLM 从条件逻辑组合构建判定表 (2^n 规则)，化简后生成测试用例。输出: 条件列表 + 动作列表 + 化简规则表 + 测试用例。

**核心文件**: `src/test_design/black_box/`, `src/ai/prompts/blackbox_prompts.py`

### 4.4 白盒测试设计 - 路径覆盖

**输入**: 标准需求 + 需求-代码图 + 源码

**处理**:
1. LLM 分析代码执行路径，为每条关键路径生成测试用例
2. 每个测试用例标注覆盖的代码段 (file_path + start_line + end_line)
3. 系统聚合所有覆盖代码段，计算覆盖率 = 覆盖行数 / 总关联行数

**UI 展示**: 覆盖率报告 (总行数/已覆盖行数/覆盖率百分比) + 未覆盖代码段 + 测试用例-覆盖代码图 + 路径测试用例

**核心文件**: `src/test_design/white_box/path_coverage.py`, `src/ai/prompts/path_coverage_prompts.py`

### 4.5 套件优化

**两种模式**:

| 套件类型 | 优化方式 | 说明 |
|---------|---------|------|
| 黑盒 | LLM 合并逻辑相同用例 | 无覆盖代码图，LLM 识别重复/高度相似用例并合并 |
| 白盒 | LLM 覆盖率优化 | 基于覆盖代码图，在保持目标覆盖率前提下删除冗余 |

**恢复功能**: 优化前自动备份原始套件，可一键恢复。

**核心文件**: `src/optimization/coverage_optimizer.py`, `src/ai/prompts/optimization_prompts.py`

### 4.6 导出

**两种格式**: Pytest (可运行脚本) / JSON (结构化文档)

**Pytest 导出**: 纯本地生成，不调用 LLM。生成文件使用 Flask test_client 进行进程内测试，不依赖网络连接。特性:
- 按技术分 TestClass 组织
- 自动推断端点 (基于用例标题/描述关键词)
- 自动推断 HTTP 方法
- 自动数据库清理 fixture
- 状态码断言

**核心文件**: `src/export/pytest_exporter.py`, `src/export/exporter_factory.py`

---

## 5. AI集成与提示词工程

### 5.1 AI 调用架构

```
OpenAI SDK -> yunwu.ai -> GPT-4o
```

### 5.2 提示词设计原则

每个提示词遵循统一结构:
1. 角色定义 - "你是一名 ISTQB/ISO 29119-4 测试专家..."
2. 任务描述 - 明确要做什么
3. 输出 JSON Schema - 精确的字段定义
4. Few-shot 示例 - 使用真实场景的完整示例
5. 约束条件 - 必须遵守的规则

### 5.3 提示词清单

| 文件 | 用途 | 调用者 |
|------|------|--------|
| `requirement_mapping_prompts.py` | 需求-代码映射 | AIExtractor |
| `risk_prompts.py` | 风险等级分析 | RiskAnalyzer |
| `blackbox_prompts.py` | EP/BVA/DT 测试生成 | EP/BVA/DT Generator |
| `path_coverage_prompts.py` | 路径覆盖 + 覆盖代码图 | PathCoverageGenerator |
| `optimization_prompts.py` | 用例合并/覆盖率优化 | CoverageOptimizer |

---

## 6. 测试技术详解

### 6.1 黑盒测试

| 技术 | 策略 | 覆盖目标 |
|------|------|---------|
| 等价类划分 (EP) | 弱健壮: 每次只测1个无效值 | 每个字段的有效类 + 无效类 |
| 边界值分析 (BVA) | 6点测试: lb-1, lb, lb+1, ub-1, ub, ub+1 | 每个数值/长度边界 |
| 判定表 (DT) | 2^n 真值表 + LLM 化简 | 每个化简后的规则 |

### 6.2 白盒测试

| 技术 | 策略 | 覆盖目标 |
|------|------|---------|
| 路径覆盖 | LLM 分析执行路径 | 每个 return 路径 + 业务流程路径 |

### 6.3 覆盖率计算

```
覆盖率 = 测试用例覆盖的代码行数 / 需求关联的总代码行数 * 100%
```

- 需求关联代码行数: 需求-代码图中所有 code_segments 的行数总和 (去重)
- 覆盖行数: 测试用例-覆盖代码图中不重复的 (file_path, line) 对数量

---

## 7. 安装与运行

### 7.1 环境要求

- Python 3.11+
- yunwu.ai API Key

### 7.2 安装

```bash
cd final_project
pip install -r requirements.txt
pip install -r flask_app/requirements.txt
cp .env.example .env
# 编辑 .env: 填入 OPENAI_API_KEY
```

### 7.3 .env 配置

```env
OPENAI_API_KEY=你的API_KEY
OPENAI_BASE_URL=https://yunwu.ai/v1
OPENAI_MODEL=gpt-4o
```

### 7.4 运行

```bash
# 启动 Web UI
streamlit run src/ui/app.py

# 运行单元测试
python -m pytest tests/ -v

# 运行生成的端到端测试
python -m pytest flask_app/tests/test_generated.py -v
```

### 7.5 工作流演示

```
1. 浏览器打开 http://localhost:8501
2. 侧边栏: 1. 需求输入
   -> 输入代码文件夹路径 (如 ./flask_app) + 粘贴需求文本
   -> 点击"生成标准需求与需求-代码映射"
3. 2. 风险分析
   -> 点击"LLM 风险分析"
4. 3. 黑盒测试设计
   -> 选择需求 + 技术 -> 点击"LLM 生成黑盒测试"
   -> 查看等价类划分/边界值分析/判定表 tab
5. 4. 白盒测试设计 (路径覆盖)
   -> 选择需求 -> 点击"LLM 路径覆盖分析"
   -> 查看覆盖率报告 + 覆盖代码图 + 测试用例
6. 5. 套件优化
   -> 选择套件 -> 黑盒: LLM合并 / 白盒: 覆盖率优化
   -> 可点击"恢复原始套件"回退
7. 6. 导出
   -> 选择套件 + 格式 -> 点击"导出"
   -> 下载 pytest 脚本或 JSON 文档
```

---

## 8. 项目结构

```
final_project/
|
|-- flask_app/                    # 被测应用
|   |-- app.py                    # Flask API (6端点 + 验证函数)
|   |-- models.py                 # 数据模型与验证常量
|   |-- requirements.txt
|   |-- tests/                    # 生成的pytest输出目录
|
|-- src/
|   |-- models/                   # Pydantic 数据模型
|   |   |-- requirement.py        #   StructuredRequirement, CodeSegment,
|   |   |                         #   RequirementCodeMapping, TestCaseCodeMapping,
|   |   |                         #   CoverageReport
|   |   |-- testcase.py           #   TestCase, TestStep, TestSuite
|   |   |-- risk.py               #   RiskAssessment (risk_level, risk_factors)
|   |
|   |-- parser/
|   |   |-- ai_extractor.py       #   需求-代码映射 (LLM)
|   |   |-- code_parser.py        #   Python AST 代码结构分析
|   |
|   |-- risk/
|   |   |-- risk_analyzer.py      #   风险分析 (LLM)
|   |
|   |-- test_design/
|   |   |-- black_box/            #   黑盒测试
|   |   |   |-- equivalence_partition.py
|   |   |   |-- boundary_value.py
|   |   |   |-- decision_table.py
|   |   |   |-- orchestrator.py
|   |   |-- white_box/
|   |   |   |-- path_coverage.py  #   路径覆盖 + 覆盖率计算
|   |
|   |-- optimization/
|   |   |-- coverage_optimizer.py #   LLM优化 (黑盒合并 + 白盒覆盖)
|   |
|   |-- export/
|   |   |-- pytest_exporter.py    #   纯本地生成 pytest (Flask test_client)
|   |   |-- json_exporter.py      #   JSON 导出
|   |   |-- exporter_factory.py
|   |
|   |-- ai/                       #   AI 服务层
|   |   |-- client.py             #   OpenAI SDK 封装 (yunwu.ai)
|   |   |-- prompts/              #   提示词模板 (5个)
|   |       |-- requirement_mapping_prompts.py
|   |       |-- risk_prompts.py
|   |       |-- blackbox_prompts.py   (EP + BVA + DT)
|   |       |-- path_coverage_prompts.py
|   |       |-- optimization_prompts.py
|   |
|   |-- ui/
|   |   |-- app.py                #   Streamlit 主入口
|   |   |-- views/                #   6个功能页面
|   |       |-- input_page.py
|   |       |-- risk_analysis_page.py
|   |       |-- blackbox_design_page.py
|   |       |-- whitebox_design_page.py
|   |       |-- optimization_page.py
|   |       |-- export_page.py
|   |
|   |-- utils/
|       |-- constants.py          #   全局常量 (技术名/端点映射/状态码)
|       |-- logger.py
|
|-- tests/                        #   单元测试
|-- data/sample_input/            #   示例输入
|-- guidebook.md                  #   本文件
|-- README.md
|-- requirements.txt
|-- .env.example
```

---

> 本项目遵循 ISTQB Foundation Level 和 ISO/IEC/IEEE 29119-4 标准。
> AutoTestDesign v2.2
