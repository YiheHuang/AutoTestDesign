"""Pytest导出 (v2.2: 纯本地生成, 无LLM)"""

import json
import os
import datetime
from src.models.testcase import TestSuite
from src.utils.constants import ENDPOINT_KEYWORDS, DEFAULT_ENDPOINT, VALID_STATUS_CODES
from src.utils.logger import logger


class PytestExporter:

    def export(
        self,
        suites: list[TestSuite],
        requirements_json: str = "[]",
        mappings_json: str = "[]",
        output_path: str = "flask_app/tests/test_generated.py"
    ) -> str:
        all_cases = []
        for s in suites:
            all_cases.extend(s.test_cases)

        seen = set()
        unique_cases = []
        for tc in all_cases:
            if tc.id not in seen:
                seen.add(tc.id)
                unique_cases.append(tc)

        code = _generate_pytest(unique_cases, output_path)
        logger.info(f"Pytest导出: {len(unique_cases)} 用例, {len(code)} 字符")
        return code


def _generate_pytest(cases: list, output_path: str) -> str:
    """本地生成完整pytest文件 — 使用Flask test_client, 不走网络"""
    lines = [
        '"""AutoTestDesign 自动生成 | ' + datetime.datetime.now().isoformat() + '"""',
        'import pytest, json, sys, os',
        '',
        '_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))',
        'sys.path.insert(0, _root)',
        '',
        'from flask_app.app import app, init_db',
        '',
        '',
        '@pytest.fixture(scope="module")',
        'def client():',
        '    app.config["TESTING"] = True',
        '    with app.app_context():',
        '        init_db()',
        '    with app.test_client() as client:',
        '        yield client',
        '',
        '',
        '@pytest.fixture(autouse=True)',
        'def clean_db():',
        '    with app.app_context():',
        '        from flask_app.app import get_db',
        '        db = get_db()',
        '        for t in ("login_attempts", "reset_tokens", "users"):',
        '            db.execute(f"DELETE FROM {t}")',
        '        db.commit()',
        '    yield',
        '',
        '',
    ]

    groups = {}
    for tc in cases:
        tech = tc.technique.replace(" ", "").replace("(", "").replace(")", "")
        groups.setdefault(tech, []).append(tc)

    for tech, tech_cases in sorted(groups.items()):
        class_name = f"Test{tech}"
        lines.append(f'class {class_name}:')
        lines.append('')

        for tc in tech_cases:
            safe_name = tc.id.lower().replace("-", "_").replace(".", "_")[:60]
            title_escaped = tc.title.replace('"', "'")
            lines.append(f'    def test_{safe_name}(self, client):')
            lines.append(f'        """{title_escaped} [{tc.technique}/{tc.category}]"""')

            if not tc.test_steps:
                lines.append('        pass')
                lines.append('')
                continue

            step = tc.test_steps[0]
            data = step.input_data

            endpoint = DEFAULT_ENDPOINT
            text = (tc.title + tc.description + " ".join(tc.tags)).lower()
            for kw, ep in ENDPOINT_KEYWORDS.items():
                if kw in text:
                    endpoint = ep
                    break

            http_method = "get" if endpoint in ("/logout", "/health") else "post"

            if http_method == "get":
                lines.append(f'        response = client.{http_method}("{endpoint}")')
            else:
                data_str = json.dumps(data, ensure_ascii=False)
                lines.append(f'        response = client.{http_method}(')
                lines.append(f'            "{endpoint}",')
                lines.append(f'            data=json.dumps({data_str}),')
                lines.append(f'            content_type="application/json"')
                lines.append(f'        )')

            lines.append(f'        assert response.status_code in {VALID_STATUS_CODES}, f"Got {{response.status_code}}"')
            lines.append(f'        response_json = response.get_json()')
            lines.append(f'        assert response_json is not None')

            expected = step.expected_result
            if expected and len(expected) < 100:
                lines.append(f'        # 预期: {expected}')
            lines.append('')

    code = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    return code
