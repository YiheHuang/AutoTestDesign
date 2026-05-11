"""自然语言文本解析器 - FR 1.0"""

import re
from src.models.requirement import StructuredRequirement
from src.parser.ai_extractor import AIExtractor
from src.utils.logger import logger


class TextParser:
    """解析自然语言文本需求

    按空行或编号(如 1., 1), REQ-xxx)将文本分段，
    每段作为一个独立需求进行AI提取。
    """

    # 需求分隔模式
    SEPARATOR_PATTERNS = [
        re.compile(r'\n\s*\n'),  # 空行
        re.compile(r'\n(?=(?:REQ-|FR-|F-)?\d+[\.\)])'),  # 编号开头
        re.compile(r'\n(?=REQ-)'),  # REQ-开头
    ]

    def __init__(self):
        self.extractor = AIExtractor()

    def can_handle(self, source: str) -> bool:
        """文本格式总是可以处理（除了纯CSV）"""
        return not (source.strip().startswith("id,") or source.strip().endswith(".csv"))

    def parse(self, text: str) -> list[StructuredRequirement]:
        """
        解析文本格式需求

        Args:
            text: 自然语言需求文本

        Returns:
            结构化需求列表
        """
        # 尝试分段
        segments = self._split_into_segments(text)

        logger.info(f"文本解析: 分为{len(segments)}个需求段落")

        requirements = []
        for i, segment in enumerate(segments):
            segment = segment.strip()
            if not segment or len(segment) < 10:
                continue

            try:
                req = self.extractor.extract(segment, f"REQ-{i + 1:03d}")
                requirements.append(req)
            except Exception as e:
                logger.error(f"解析段落{i + 1}失败: {e}")

        logger.info(f"文本解析完成: 成功解析{len(requirements)}条需求")
        return requirements

    def _split_into_segments(self, text: str) -> list[str]:
        """将文本分割为独立的需求段落"""
        segments = []

        # 先尝试按空行分割
        parts = re.split(r'\n\s*\n', text)
        if len(parts) > 1:
            # 过滤太短的段落和仅标题的段落
            return [p.strip() for p in parts if len(p.strip()) > 20]

        # 如果只有单个大段落，按编号分割
        lines = text.strip().split("\n")
        current_segment = []
        for line in lines:
            stripped = line.strip()
            # 检测编号行如 "1. ", "REQ-001: ", "FR-1 "
            if re.match(r'^(REQ-|FR-|F-)?\d+[\.\):：]', stripped):
                if current_segment:
                    segments.append("\n".join(current_segment))
                current_segment = [stripped]
            else:
                current_segment.append(stripped)

        if current_segment:
            segments.append("\n".join(current_segment))

        return segments if segments else [text]
