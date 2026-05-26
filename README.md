# AutoTestDesign — AI-driven automated test design tool

AutoTestDesign applies LLM to automate requirements analysis, risk assessment, and systematic test case generation following ISTQB and ISO/IEC/IEEE 29119-4.

## Target System Under Test

**Task Management Platform** — a Flask + SQLite REST API with three modules:

| Module | Endpoints | Risk |
|--------|----------|------|
| User Auth | `/api/register`, `/api/login`, `/api/forgot-password`, `/api/reset-password`, `/api/logout` | High |
| Projects | `/api/projects` (CRUD), `/api/projects/<id>/stats` | Medium |
| Tasks | `/api/projects/<id>/tasks` (CRUD), `/api/tasks/<id>/assign`, `/api/users/<name>/tasks` | Medium/Low |

The system intentionally contains 11 planted defects (see `flask_app/planted_bugs.md`) for test tool validation.

## Workflow — 7 Steps

```
1. Requirements Input  -> Code folder + requirements (CSV/TXT/Paste) -> Standardized REQs + Requirement-Code Map
2. Risk Analysis       -> LLM evaluates risk_level, test_priority, and risk_factors per requirement
3. Black-Box Design    -> EP / BVA / DT — LLM generates analysis tables + test cases
4. White-Box Design    -> Path Coverage + State Transition — LLM generates coverage map + computes coverage %
5. Oracle Generation   -> Fill test data -> LLM derives expected results -> Save to custom suite
6. Suite Optimization  -> Active/Inactive zones, risk priority, merge duplicates, coverage minimization
7. Export              -> Pytest (Flask test_client) / JSON
```

## Quick Start

```bash
cd final_project
pip install -r requirements.txt
cp .env.example .env   # edit: paste OPENAI_API_KEY

streamlit run src/ui/app.py
```

### Run Tests

```bash
# Unit tests for the tool itself
python -m pytest tests/ -v

# Generated end-to-end tests (after export via UI)
python -m pytest flask_app/tests/test_generated.py -v
```

## Project Structure

```
final_project/
|
|-- flask_app/                    # Target application (Task Management Platform)
|   |-- app.py                    #   create_app() factory
|   |-- config.py                 #   Constants
|   |-- models/                   #   database, project, task
|   |-- routes/                   #   auth, projects, tasks (Blueprints)
|   |-- utils/validators.py       #   9 validation functions
|   |-- planted_bugs.md           #   11 intentional defects
|   |-- tests/                    #   Generated pytest output
|
|-- src/
|   |-- models/                   # Pydantic data models
|   |-- parser/                   # Requirement extraction + code parsing
|   |-- risk/                     # LLM risk analysis
|   |-- test_design/
|   |   |-- black_box/            # EP, BVA, DT generators
|   |   |-- white_box/            # PathCoverage, StateTransition
|   |-- optimization/             # Suite optimization (risk/merge/coverage)
|   |-- export/                   # Pytest + JSON exporters
|   |-- ai/                       # OpenAI SDK client + prompts
|   |-- ui/                       # Streamlit (app.py + 7 views)
|   |-- utils/                    # Constants, logger
|
|-- docs/                         # Deliverables
|   |-- 01_risk_analysis_report.md
|   |-- 02_test_plan.md
|   |-- 03_detailed_test_design.md
|
|-- data/sample_input/            # Sample requirements (CSV + TXT)
|-- tests/                        # Tool unit tests
|-- guidebook.md                  # Reference manual
|-- README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| AI | OpenAI SDK -> yunwu.ai -> GPT-4o |
| UI | Streamlit |
| Data | Pydantic v2 |
| Target App | Flask 3.0 + SQLite |
| Testing | pytest + Flask test_client |

## Standards

- ISTQB Foundation Level (CTFL)
- ISO/IEC/IEEE 29119-4: Test Techniques
- ISO/IEC 25010: Software Quality Model
