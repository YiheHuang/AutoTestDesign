"""需求-代码映射提取器 (v2.2: LLM输出标准需求+需求-代码图)"""

import json
import os
from src.models.requirement import (
    StructuredRequirement, InputField, Condition, SystemBehavior, SourceType,
    RequirementCodeMapping, CodeSegment
)
from src.ai.client import get_ai_client
from src.ai.prompts.requirement_mapping_prompts import (
    REQ_MAPPING_SYSTEM_PROMPT, REQ_MAPPING_USER_TEMPLATE,
    MAPPING_ONLY_SYSTEM_PROMPT, MAPPING_ONLY_USER_TEMPLATE
)
from src.utils.logger import logger


class AIExtractor:
    """需求-代码映射提取器

    输入: 需求文本 + 代码文件夹路径
    输出: 标准化需求列表 + 需求-代码映射表
    """

    def extract_with_code(
        self,
        requirement_text: str,
        code_folder: str
    ) -> tuple[list[StructuredRequirement], list[RequirementCodeMapping]] | None:
        """提取标准需求 + 需求-代码映射

        Args:
            requirement_text: 原始需求文档
            code_folder: 包含.py源码的文件夹路径

        Returns:
            (requirements列表, mappings列表) 或 None(失败时)
        """
        # 1. 读取所有.py源文件
        sources = self._read_sources(code_folder)
        if not sources:
            logger.error(f"文件夹 {code_folder} 中未找到.py文件")
            return None

        source_text = "\n\n".join(
            f"=== {path} ===\n{code}" for path, code in sources.items()
        )

        # 2. 调用LLM
        logger.info(f"LLM需求-代码映射: {len(sources)} 个源文件, {sum(len(c) for c in sources.values())} 行代码")
        ai_client = get_ai_client()
        user_message = REQ_MAPPING_USER_TEMPLATE.format(
            requirement_text=requirement_text,
            source_code=source_text
        )

        result = ai_client.chat_with_json(
            system_prompt=REQ_MAPPING_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.1
        )

        if not result:
            logger.error("LLM返回空结果")
            return None

        # 3. 解析需求
        requirements = []
        for req_data in result.get("requirements", []):
            try:
                req = StructuredRequirement(
                    id=req_data.get("id", ""),
                    source=SourceType.TEXT,
                    raw_text=requirement_text,
                    title=req_data.get("title", ""),
                    description=req_data.get("description", ""),
                    input_fields=[InputField(**f) for f in req_data.get("input_fields", [])],
                    conditions=[Condition(**c) for c in req_data.get("conditions", [])],
                    expected_behaviors=[SystemBehavior(**b) for b in req_data.get("expected_behaviors", [])],
                    dependencies=req_data.get("dependencies", []),
                    constraints=req_data.get("constraints", []),
                    domain=req_data.get("domain", "")
                )
                requirements.append(req)
            except Exception as e:
                logger.error(f"解析需求 {req_data.get('id', '?')} 失败: {e}")

        # 4. 解析映射
        mappings = []
        for m_data in result.get("mappings", []):
            try:
                segments = [CodeSegment(**s) for s in m_data.get("code_segments", [])]
                mappings.append(RequirementCodeMapping(
                    requirement_id=m_data.get("requirement_id", ""),
                    requirement_title=m_data.get("requirement_title", ""),
                    code_segments=segments
                ))
            except Exception as e:
                logger.error(f"解析映射失败: {e}")

        logger.info(f"完成: {len(requirements)} 条需求, {len(mappings)} 个映射")
        return requirements, mappings

    def extract_mapping_from_csv(
        self,
        requirements: list[StructuredRequirement],
        code_folder: str
    ) -> list[RequirementCodeMapping] | None:
        """从CSV标准需求 + 代码文件夹 -> LLM仅生成需求-代码映射

        Args:
            requirements: 已从CSV解析的标准需求列表
            code_folder: 代码文件夹路径

        Returns:
            mappings列表 或 None
        """
        sources = self._read_sources(code_folder)
        if not sources:
            logger.error(f"文件夹 {code_folder} 中未找到.py文件")
            return None

        source_text = "\n\n".join(
            f"=== {path} ===\n{code}" for path, code in sources.items()
        )

        reqs_json = json.dumps(
            [{
                "id": r.id, "title": r.title, "description": r.description,
                "input_fields": [f.model_dump() for f in r.input_fields],
                "conditions": [c.model_dump() for c in r.conditions],
                "expected_behaviors": [b.model_dump() for b in r.expected_behaviors]
            } for r in requirements],
            ensure_ascii=False, indent=2
        )

        logger.info(f"LLM映射生成: {len(requirements)} 条已有需求 -> {code_folder}")
        ai_client = get_ai_client()
        result = ai_client.chat_with_json(
            system_prompt=MAPPING_ONLY_SYSTEM_PROMPT,
            user_message=MAPPING_ONLY_USER_TEMPLATE.format(
                requirements_json=reqs_json,
                source_code=source_text
            ),
            temperature=0.1
        )

        if not result:
            logger.error("LLM返回空结果")
            return None

        mappings = []
        for m_data in result.get("mappings", []):
            try:
                segments = [CodeSegment(**s) for s in m_data.get("code_segments", [])]
                mappings.append(RequirementCodeMapping(
                    requirement_id=m_data.get("requirement_id", ""),
                    requirement_title=m_data.get("requirement_title", ""),
                    code_segments=segments
                ))
            except Exception as e:
                logger.error(f"解析映射失败: {e}")

        logger.info(f"映射完成: {len(mappings)} 个")
        return mappings

    def parse_requirements_from_csv(self, csv_content: str) -> list[StructuredRequirement]:
        """从CSV文本解析标准需求列表 (LLM不参与)

        CSV列: id, title, description, input_fields(JSON数组), conditions(JSON数组),
               expected_behaviors(JSON数组), domain
        """
        import io, csv as csv_mod
        reader = csv_mod.DictReader(io.StringIO(csv_content))
        requirements = []
        for row in reader:
            try:
                req = StructuredRequirement(
                    id=row.get("id", "").strip(),
                    source=SourceType.TEXT,
                    raw_text=row.get("description", ""),
                    title=row.get("title", "").strip(),
                    description=row.get("description", "").strip(),
                    input_fields=[InputField(**f) for f in json.loads(row.get("input_fields", "[]"))],
                    conditions=[Condition(**c) for c in json.loads(row.get("conditions", "[]"))],
                    expected_behaviors=[SystemBehavior(**b) for b in json.loads(row.get("expected_behaviors", "[]"))],
                    domain=row.get("domain", "").strip()
                )
                requirements.append(req)
            except Exception as e:
                logger.error(f"CSV行解析失败 [{row.get('id', '?')}]: {e}")
        return requirements

    def _read_sources(self, folder: str) -> dict[str, str]:
        """读取文件夹下所有.py文件"""
        sources = {}
        if not os.path.isdir(folder):
            return sources
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in ("venv", ".venv", "__pycache__", ".git", "node_modules")]
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, folder)
                    try:
                        with open(full_path, "r", encoding="utf-8") as fh:
                            sources[rel_path] = fh.read()
                    except Exception:
                        pass
            if len(sources) >= 10:
                break
        return sources
