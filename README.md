# AutoTestDesign - AI驱动的自动化测试设计工具

AutoTestDesign 是一款基于 AI 的软件测试设计工具，能够自动执行需求分析、风险评估和系统化测试用例生成，支持 ISTQB 测试理论和 ISO/IEC/IEEE 29119-4 标准。

## 功能特性

| 功能 | 说明 |
|------|------|
| 需求输入 | 代码仓库 + 需求文本 -> LLM 生成标准需求 (REQ-001~00N) + 需求-代码映射 |
| 风险分析 | LLM 评估每项需求的 risk_level (High/Medium/Low) 和风险因素 |
| 黑盒测试设计 | 等价类划分(EP) + 边界值分析(BVA) + 判定表(DT)，LLM 生成分析表与测试用例 |
| 白盒测试设计 | 路径覆盖: LLM 分析执行路径 -> 测试用例 + 覆盖代码图 + 覆盖率计算 |
| 套件优化 | 黑盒: LLM 合并逻辑相同用例 / 白盒: LLM 覆盖率优化 + 一键恢复原始套件 |
| 导出 | Pytest 可运行脚本 (Flask test_client, 不走网络) + JSON 结构化文档 |

## 快速开始

### 环境要求

- Python 3.11+
- yunwu.ai API Key

### 安装

```bash
cd final_project
pip install -r requirements.txt
pip install -r flask_app/requirements.txt
cp .env.example .env
# 编辑 .env: 填入 OPENAI_API_KEY
```

### .env 配置

```env
OPENAI_API_KEY=你的API_KEY
OPENAI_BASE_URL=https://yunwu.ai/v1
OPENAI_MODEL=gpt-4o
```

### 运行

```bash
# 启动 Web UI
streamlit run src/ui/app.py

# 运行单元测试
python -m pytest tests/ -v

# 运行生成的端到端测试
python -m pytest flask_app/tests/test_generated.py -v
```

浏览器打开 http://localhost:8501 即可使用。

## 工作流程 (6步)

```
1. 需求输入     -> 选择代码文件夹 + 粘贴需求文本 -> 生成标准需求 + 需求-代码图
2. 风险分析     -> LLM 评估 -> risk_level + risk_factors
3. 黑盒测试设计  -> 选需求 + 选技术 -> LLM 生成 EP/BVA/DT 分析表 + 测试用例
4. 白盒测试设计  -> 选需求 -> LLM 路径覆盖 -> 用例 + 覆盖代码图 + 覆盖率
5. 套件优化     -> 黑盒: LLM合并 / 白盒: LLM覆盖率优化 / 恢复原始套件
6. 导出         -> Pytest (Flask test_client) / JSON
```

## 项目结构

```
final_project/
├── flask_app/                 # 被测应用 (Flask 用户注册登录系统)
├── src/
│   ├── models/               # Pydantic 数据模型
│   ├── parser/               # 需求-代码映射 (LLM)
│   ├── risk/                 # 风险分析 (LLM)
│   ├── test_design/
│   │   ├── black_box/        # EP / BVA / DT
│   │   └── white_box/        # 路径覆盖
│   ├── optimization/         # LLM 套件优化
│   ├── export/               # Pytest / JSON 导出
│   ├── ai/                   # OpenAI SDK + 提示词模板
│   ├── ui/                   # Streamlit 界面
│   └── utils/                # 常量 / 日志
├── tests/                    # 单元测试
├── data/                     # 示例输入
├── guidebook.md              # 教学指南
└── README.md
```

## 技术栈

| 层次 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| AI | OpenAI SDK -> yunwu.ai -> GPT-4o |
| 界面 | Streamlit |
| 数据模型 | Pydantic v2 |
| 被测应用 | Flask + SQLite |
| 可视化 | plotly |
| 测试框架 | pytest |

## 参考标准

- ISTQB Foundation Level (CTFL)
- ISO/IEC/IEEE 29119-4: Test Techniques
- ISO/IEC 25010: Software Quality Model
