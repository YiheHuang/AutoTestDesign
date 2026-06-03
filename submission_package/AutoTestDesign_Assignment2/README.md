# 提交说明

本目录用于课程作业第二次提交，已按材料类别整理为可直接打包的结构。

## 目录说明

| 目录/文件 | 内容 |
|-----------|------|
| `docs/` | 三份课程文档：风险分析报告、测试计划、详细测试设计与执行文档 |
| `docs/english_reports/` | 三份英文 PDF 文档：风险分析报告、测试计划、详细测试设计与执行文档 |
| `presentation/软测_en.pptx` | 英文答辩 PPT |
| `tool/` | AutoTestDesign 自动化测试工具源码、提示词、样例需求、单元测试、运行说明 |
| `target_app/` | 被测应用源码（Task Management Platform）及缺陷记录 |
| `run_results/` | 任务管理模块 REQ-005、REQ-006、REQ-007 的真实运行结果 |
| `test_scripts/` | 三份测试脚本：原始自动脚本、人工校验后的自动脚本、人工编写脚本 |
| `course_materials/Assignment 2 Updated.pdf` | 作业要求原文 |

## 三份文档

1. `docs/01_risk_analysis_report.md`  
   对目标应用进行风险识别、风险分级和测试优先级分析。

2. `docs/02_test_plan.md`  
   说明整体测试范围、测试项、高级测试套件设计、组织方式、执行框架与成本估算。

3. `docs/03_detailed_test_design.md`  
   以任务管理模块为对象，给出详细测试设计、脚本组织、执行结果与异常现象解释。

对应英文 PDF 版本位于 `docs/english_reports/`。

答辩 PPT 位于 `presentation/软测_en.pptx`。

## 工具运行方式

工具源码位于 `tool/` 目录。建议使用以下步骤运行：

```bash
cd tool
pip install -r requirements.txt
copy .env.example .env
streamlit run src/ui/app.py
```

说明：

- `.env` 中需填写可用的 API Key；
- 工具界面支持需求导入、风险分析、黑盒/白盒测试设计、预言生成、套件优化与导出；

## 被测应用运行方式

被测应用源码位于 `target_app/flask_app/`。

```bash
cd target_app/flask_app
pip install -r requirements.txt
python app.py
```

如仅执行测试脚本，也可以直接使用 Flask `test_client()`，不必单独启动服务。

## 测试脚本执行方式

在项目根目录下执行：

```bash
python -m pytest test_scripts/test_generated.py -v --tb=short
python -m pytest test_scripts/test_generated_refined.py -v --tb=short
python -m pytest test_scripts/test_human.py -v --tb=short
```

其中：

- `test_generated.py` 用于保留原始自动导出脚本的基线状态；
- `test_generated_refined.py` 与 `test_human.py` 是本次详细测试设计与执行文档中的主要对比对象；
- `test_scripts/conftest.py` 已处理提交包内的导入路径，命令可直接执行。

若需要基于被测应用原始目录执行，也可以使用：

```bash
python -m pytest target_app/flask_app/tests/test_generated.py -v --tb=short
python -m pytest target_app/flask_app/tests/test_generated_refined.py -v --tb=short
python -m pytest target_app/flask_app/tests/test_human.py -v --tb=short
```

## 工具自测

自动测试工具自身的当前测试集可通过以下命令执行：

```bash
python -m pytest tool/tests -q
```

## 运行结果说明

`run_results/REQ005_006_007/` 中保存了本次详细测试相关的截图、CSV 导出结果和原始自动脚本，主要用于支撑 `03_detailed_test_design.md` 中的执行结果与异常现象解释。

## 已知缺陷记录

被测应用中故意植入的需求偏差记录位于：

`target_app/flask_app/planted_bugs.md`

其中与任务管理模块直接相关的是 BUG-7、BUG-8、BUG-9。
