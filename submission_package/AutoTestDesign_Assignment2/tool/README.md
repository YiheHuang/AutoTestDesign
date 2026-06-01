# AutoTestDesign 运行说明

## 1. 环境准备

建议使用 Python 3.11 或以上版本。

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量模板：

```bash
copy .env.example .env
```

在 `.env` 中填写可用的 API Key。

## 2. 启动方式

在 `tool/` 目录下运行：

```bash
streamlit run src/ui/app.py
```

启动后即可在浏览器中打开 Streamlit 界面。

## 3. 工具主要流程

1. 导入代码仓库与需求；
2. 生成标准需求和需求-代码映射；
3. 进行风险分析；
4. 生成黑盒测试用例；
5. 生成白盒测试用例；
6. 生成预期结果并保存到测试套件；
7. 进行套件优化与导出。

## 4. 目录说明

| 目录/文件 | 说明 |
|-----------|------|
| `src/` | 工具源码 |
| `prompts/` | 提示词文件 |
| `data/sample_input/` | 样例需求 |
| `tests/` | 工具自身单元测试 |
| `guidebook.md` | 工具使用手册 |

## 5. 说明

本工具用于辅助测试设计与测试脚本生成，自动生成结果在实际使用前仍建议进行人工校验。

如需运行工具当前的单元测试，可执行：

```bash
python -m pytest tests -q
```
