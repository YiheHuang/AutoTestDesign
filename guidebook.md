# AutoTestDesign — Guidebook

> AI-driven automated test design tool | Software Testing Final Project v2.2

---

## 1. Project Overview

AutoTestDesign is an AI-powered tool that automates the full test design lifecycle: from importing requirements and source code, through risk analysis, black-box and white-box test generation, oracle synthesis, suite optimization, to export of runnable pytest scripts. It targets the **Task Management Platform** (Flask + SQLite REST API) as the system under test.

### 1.1 Core Capabilities

- Extract standardized requirements and requirement-code mappings from requirement documents + code repositories
- LLM-based risk assessment (risk_level, test_priority, risk_factors) for each requirement
- Three ISO 29119-4 black-box techniques: Equivalence Partitioning, Boundary Value Analysis, Decision Table
- Two white-box techniques: Path Coverage (with coverage code map) and State Transition (All-States)
- Test oracle generation: fill test data -> LLM derives expected results -> save to custom suites
- Suite optimization: active/inactive zone management, risk-priority sort, duplicate merging, coverage minimization
- Export: runnable pytest (Flask test_client, no network) + JSON documents

### 1.2 Workflow

```
Step 1  Requirements Input  -> Code folder + reqs (CSV/TXT/Paste) -> LLM -> Standard REQs + Req-Code Map
Step 2  Risk Analysis       -> LLM -> risk_level, test_priority, risk_factors
Step 3  Black-Box Design    -> EP / BVA / DT -> LLM -> analysis tables + test cases
Step 4  White-Box Design    -> PathCoverage / StateTransition -> LLM -> cases + coverage map + coverage %
Step 5  Oracle Generation   -> Fill test data -> LLM -> expected result -> save to custom suite
Step 6  Suite Optimization  -> Active/Inactive zones, risk priority, merge, coverage minimization
Step 7  Export              -> Pytest (Flask test_client) / JSON
```

---

## 2. Target System Under Test

### Task Management Platform

A Flask + SQLite REST API with three functional modules:

| Module | Endpoints | Risk |
|--------|----------|------|
| User Auth | `/api/register`, `/api/login`, `/api/forgot-password`, `/api/reset-password`, `/api/logout` | High |
| Projects | `/api/projects` (CRUD), `/api/projects/<id>/stats` | Medium |
| Tasks | `/api/projects/<id>/tasks` (CRUD), `/api/tasks/<id>/assign`, `/api/users/<name>/tasks` | Medium/Low |

**Architecture**: App factory + Blueprints

```
flask_app/
  app.py                  create_app() factory
  config.py               Constants
  models/
    database.py           get_db, init_db, close_db
    project.py            Project CRUD
    task.py               Task CRUD, filter, user tasks
  routes/
    auth.py               /register, /login, /forgot-password, /reset-password, /logout
    projects.py           /projects CRUD + /stats
    tasks.py              /tasks CRUD + /assign + user tasks
  utils/
    validators.py         9 validation functions
```

### Planted Defects

The system contains 11 intentional deviations from the requirements (see `flask_app/planted_bugs.md`) to validate the test tool's defect-finding capability:

| Category | Count | Examples |
|----------|-------|---------|
| Auth | 3 | Token expiry minutes-vs-hours, login failure counter not cleared, password-equals-username accepted |
| Projects | 3 | No cascade delete, no duplicate name check, stats ignores project_id filter |
| Tasks | 3 | No assignee validation, done tasks deletable, past due_date accepted |
| Validators | 2 | Whitespace name passes, invalid status silently defaults |

---

## 3. Detailed Workflow

### 3.1 Requirements Input

Three import modes:

| Mode | Input | LLM Work |
|------|-------|---------|
| CSV | Upload pre-defined standardized requirements CSV | Mapping only (requirements already structured) |
| TXT | Upload .txt requirements document | Full extraction: requirements + mapping |
| Paste | Paste text directly | Full extraction: requirements + mapping |

**Code repository**: Enter a folder path; all `.py` files are read recursively and sent to LLM for requirement-code mapping.

### 3.2 Risk Analysis

LLM outputs per requirement:
- `risk_level`: High / Medium / Low
- `test_priority`: High / Medium / Low
- `risk_factors`: list of risk factor descriptions
- `priority_reason`: explanation for the priority assignment

### 3.3 Black-Box Test Design

For each selected requirement + technique, LLM generates both analysis tables and test cases:

**Equivalence Partitioning (EP)**: Valid/invalid classes per input field. Strategy: weak robust (one invalid field at a time).

**Boundary Value Analysis (BVA)**: 6 test points per boundary (lb-1, lb, lb+1, ub-1, ub, ub+1). Applied to fields with numeric/length ranges.

**Decision Table (DT)**: 2^n truth table from condition predicates, LLM simplifies to minimal rules.

### 3.4 White-Box Test Design

**Path Coverage**: LLM analyzes code execution paths, generates test cases with covered code segments (file_path + line range). System computes coverage = covered_lines / total_associated_lines.

**State Transition**: LLM identifies system states and transitions, models them as a state machine, and generates All-States coverage test sequences.

### 3.5 Oracle Generation

1. Select a requirement -> auto-generated JSON template from its input_fields
2. User fills in specific test values
3. LLM receives requirement + code + test data -> derives expected HTTP status, response body, and reasoning
4. Save to custom test suite (automatically synced to main test_suites)

### 3.6 Suite Optimization

**Active/Inactive zones**: Every test case has an active/inactive toggle. Optimization strategies operate on the active zone, moving removed cases to inactive.

Three strategies:
- **Risk Priority**: Sort + filter by risk level (budget slider + minimum risk threshold)
- **Merge Duplicates**: LLM identifies logically identical cases
- **Coverage Minimization**: LLM deletes redundant cases while maintaining target coverage (white-box only)

**Restore**: One-click restore to original suite.

### 3.7 Export

- **Pytest**: Pure local generation using Flask test_client (no network dependency). Test cases grouped by technique into classes, with auto DB setup/teardown fixtures.
- **JSON**: Structured ISTQB-compatible JSON document.

---

## 4. AI Integration

### 4.1 Architecture

```
OpenAI SDK -> yunwu.ai proxy -> GPT-4o
```

### 4.2 Reliability

- JSON mode: `response_format={"type": "json_object"}` forces valid JSON
- JSON repair: 7 repair strategies for malformed LLM output (trailing commas, missing commas, single quotes, markdown wrapping, BOM, truncation)
- Retry: 3 attempts with exponential backoff
- Pydantic validation: field_validator coercions (int->str, dict->JSON string)

### 4.3 Prompt Templates

| Prompt File | Purpose | Caller |
|-------------|---------|--------|
| `requirement_mapping_prompts.py` | Req-code mapping | AIExtractor |
| `risk_prompts.py` | Risk analysis | RiskAnalyzer |
| `blackbox_prompts.py` | EP, BVA, DT | EP/BVA/DT Generator |
| `path_coverage_prompts.py` | Path coverage + code map | PathCoverageGenerator |
| `state_transition_prompts.py` | State machine + test sequences | StateTransitionGenerator |
| `optimization_prompts.py` | Duplicate merge | CoverageOptimizer |

---

## 5. Test Techniques Summary

### Black-Box

| Technique | Strategy | Coverage Target |
|-----------|---------|----------------|
| EP | Weak robust: 1 invalid field at a time | Every valid + invalid class per field |
| BVA | 6-point: lb-1, lb, lb+1, ub-1, ub, ub+1 | Every numeric/length boundary |
| DT | 2^n truth table + LLM simplification | Every simplified rule |

### White-Box

| Technique | Strategy | Coverage Target |
|-----------|---------|----------------|
| Path Coverage | LLM analyzes execution paths | Every return statement + business flow |
| State Transition | All-States | Every state visited at least once |

---

## 6. Project Structure

```
final_project/
|
|-- flask_app/                    # Target application
|   |-- app.py                    #   create_app() factory
|   |-- config.py                 #   Constants
|   |-- models/                   #   database.py, project.py, task.py
|   |-- routes/                   #   auth.py, projects.py, tasks.py
|   |-- utils/validators.py       #   9 validation functions
|   |-- planted_bugs.md           #   11 intentional defects
|   |-- tests/                    #   Generated pytest output
|
|-- src/
|   |-- models/                   # Pydantic: requirement, testcase, risk, state_machine
|   |-- parser/                   # ai_extractor, code_parser
|   |-- risk/                     # risk_analyzer
|   |-- test_design/
|   |   |-- black_box/            # EP, BVA, DT generators + orchestrator
|   |   |-- white_box/            # path_coverage, state_transition, whitebox_orchestrator
|   |-- optimization/             # coverage_optimizer (risk/merge/coverage)
|   |-- export/                   # pytest_exporter, json_exporter, exporter_factory
|   |-- ai/                       # client.py + prompts/
|   |-- ui/                       # app.py + views/ (7 pages)
|   |-- utils/                    # constants, logger
|
|-- docs/                         # Deliverables
|   |-- 01_risk_analysis_report.md
|   |-- 02_test_plan.md
|   |-- 03_detailed_test_design.md
|
|-- data/sample_input/            # Sample requirements (CSV + TXT)
|-- tests/                        # Tool unit tests
|-- guidebook.md
|-- README.md
```

---

## 7. Running

```bash
# Start
streamlit run src/ui/app.py

# Unit tests
python -m pytest tests/ -v

# Generated tests (after export)
python -m pytest flask_app/tests/test_generated.py -v
```

## 8. Standards

- ISTQB Foundation Level (CTFL)
- ISO/IEC/IEEE 29119-4: Test Techniques
- ISO/IEC 25010: Software Quality Model

---

> AutoTestDesign v2.2
