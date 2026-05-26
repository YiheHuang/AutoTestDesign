"""AI服务客户端 - OpenAI SDK → yunwu.ai 中转站"""

import json
import os
import time
from functools import lru_cache
from typing import Optional, Any

from openai import OpenAI
from dotenv import load_dotenv

from src.utils.constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, MAX_RETRIES
from src.utils.logger import logger

load_dotenv()


class AIClient:
    """OpenAI兼容API客户端（yunwu.ai中转站）"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://yunwu.ai/v1")
        self.model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

        if not api_key:
            raise ValueError("请在 .env 文件中设置 OPENAI_API_KEY")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"AI客户端初始化完成: base_url={base_url}, model={self.model}")

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ) -> str:
        """通用对话接口"""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content or ""

    def structured_output(
        self,
        system_prompt: str,
        user_message: str,
        output_schema: Optional[dict[str, Any]] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = MAX_RETRIES
    ) -> dict[str, Any]:
        """结构化JSON输出

        使用OpenAI的response_format强制JSON输出。
        含自动重试机制: JSON解析失败时最多重试max_retries次。
        """
        # 在system prompt中追加JSON格式要求
        if output_schema:
            schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)
            system_prompt = f"{system_prompt}\n\n## 输出要求\n你必须严格按照以下JSON Schema输出，不要输出任何其他内容:\n```json\n{schema_str}\n```"

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                content = response.choices[0].message.content or "{}"
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self._repair_json(content)

            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON解析失败 (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(1 * (attempt + 1))  # 指数退避
            except Exception as e:
                last_error = e
                logger.error(f"AI调用失败 (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 * (attempt + 1))

        logger.error(f"AI调用全部重试失败: {last_error}")
        return {}

    def _repair_json(self, text: str) -> dict[str, Any]:
        """尝试修复 LLM 返回的常见 JSON 格式问题"""
        import re
        text = text.strip()

        # 1. 提取 markdown 代码块
        if "```json" in text:
            s = text.index("```json") + 7
            e = text.index("```", s) if "```" in text[s:] else len(text)
            text = text[s:e].strip()
        elif "```" in text:
            s = text.index("```") + 3
            e = text.index("```", s) if "```" in text[s:] else len(text)
            text = text[s:e].strip()

        # 2. 清理
        text = text.lstrip("﻿")
        text = re.sub(r',\s*([}\]])', r'\1', text)  # 尾随逗号

        # 3. 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 4. 单引号→双引号 (LLM偶尔输出Python dict风格)
        try:
            return json.loads(text.replace("'", '"'))
        except json.JSONDecodeError:
            pass

        # 5. 缺失逗号修复
        fixed = text
        fixed = re.sub(r'"\s+(?=")', r'", ', fixed)          # "a" "b" -> "a", "b"
        fixed = re.sub(r'("\s*)\n(\s*")', r'\1,\n\2', fixed) # "a"\n"b" -> "a",\n"b"
        fixed = re.sub(r'(\d)\s+(")', r'\1, \2', fixed)      # 123 "k"
        fixed = re.sub(r'([}\]])\s+(")', r'\1, \2', fixed)   # } "k"
        fixed = re.sub(r'("[^"]*")\s+(\{)', r'\1, \2', fixed)# "v" {

        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # 6. 截断到最后一个完整的顶级对象
        depth = 0
        in_str = False
        last = 0
        for i, ch in enumerate(fixed):
            if ch == '"' and (i == 0 or fixed[i-1] != '\\'):
                in_str = not in_str
            if not in_str:
                if ch in '{[': depth += 1
                elif ch in '}]':
                    depth -= 1
                    if depth == 0:
                        last = i + 1
        if last > 0:
            try:
                return json.loads(fixed[:last])
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("All repair strategies failed", text, 0)

    def chat_with_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = MAX_RETRIES
    ) -> dict[str, Any]:
        """JSON对话（优先使用JSON mode，失败后plain text+修复）"""
        last_error = None
        for attempt in range(max_retries):
            try:
                # 优先使用 JSON mode (强制合法JSON)
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    max_tokens=DEFAULT_MAX_TOKENS,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                text = response.choices[0].message.content or "{}"
                return self._repair_json(text)
            except Exception as e:
                last_error = e
                logger.warning(f"JSON mode失败 (attempt {attempt + 1}/{max_retries}): {e}, 尝试plain text")
                try:
                    text = self.chat(system_prompt, user_message, temperature)
                    return self._repair_json(text)
                except Exception as e2:
                    last_error = e2
                    logger.warning(f"Plain text也失败 (attempt {attempt + 1}/{max_retries}): {e2}")
                time.sleep(1 * (attempt + 1))

        logger.error(f"AI调用全部重试失败: {last_error}")
        return {}


@lru_cache()
def get_ai_client() -> AIClient:
    """获取AI客户端单例"""
    return AIClient()
