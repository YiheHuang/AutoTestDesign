"""AI响应解析与验证"""

import json
from typing import Any
from pydantic import BaseModel, ValidationError
from src.utils.logger import logger


def parse_and_validate(
    raw_response: dict[str, Any],
    model_class: type[BaseModel],
    fallback: Any = None
) -> Any:
    """解析AI响应并验证为Pydantic模型

    Args:
        raw_response: AI返回的原始JSON字典
        model_class: 目标Pydantic模型类
        fallback: 验证失败时的回退值

    Returns:
        验证通过的模型实例，或fallback
    """
    try:
        return model_class(**raw_response)
    except ValidationError as e:
        logger.error(f"模型验证失败 [{model_class.__name__}]: {e}")
        return fallback


def safe_json_parse(text: str) -> dict[str, Any]:
    """安全地解析JSON字符串，处理常见格式问题"""
    text = text.strip()
    # 移除markdown包裹
    if text.startswith("```"):
        lines = text.split("\n")
        # 移除首行```json或```
        if lines[0].startswith("```"):
            lines = lines[1:]
        # 移除末行```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def extract_list_from_response(raw: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """从AI响应中提取列表字段"""
    if key in raw and isinstance(raw[key], list):
        return raw[key]
    # 尝试在嵌套结构中查找
    for k, v in raw.items():
        if isinstance(v, dict):
            result = extract_list_from_response(v, key)
            if result:
                return result
        if isinstance(v, list) and k in ("results", "data", "items", "test_cases", key):
            return v
    return raw.get(key, [])
