"""CSV文件解析器 - FR 1.0"""

import io
import pandas as pd
from src.models.requirement import StructuredRequirement
from src.parser.ai_extractor import AIExtractor
from src.utils.logger import logger


class CSVParser:
    """解析CSV格式的需求文件

    预期CSV格式:
    id,title,description
    REQ-001,功能名称,功能详细描述...
    """

    REQUIRED_COLUMNS = {"id", "description"}
    OPTIONAL_COLUMNS = {"title", "priority", "module"}

    def __init__(self):
        self.extractor = AIExtractor()

    def can_handle(self, source: str) -> bool:
        """判断是否为CSV格式"""
        source = source.strip()
        # 检查是否为文件路径
        if source.endswith(".csv"):
            return True
        # 检查内容是否以CSV头开头
        first_line = source.split("\n")[0].lower()
        return first_line.startswith("id,") or first_line.startswith("id\t")

    def parse(self, source: str) -> list[StructuredRequirement]:
        """
        解析CSV格式的需求

        Args:
            source: CSV文件路径或CSV内容字符串

        Returns:
            结构化需求列表
        """
        # 判断source是文件路径还是内容字符串
        if source.strip().endswith(".csv"):
            df = pd.read_csv(source, encoding="utf-8")
        else:
            df = pd.read_csv(io.StringIO(source))

        # 验证必要列
        missing = self.REQUIRED_COLUMNS - set(c.lower() for c in df.columns)
        if missing:
            raise ValueError(f"CSV缺少必要列: {missing}. 必要列: {self.REQUIRED_COLUMNS}")

        # 标准化列名
        df.columns = [c.lower().strip() for c in df.columns]

        logger.info(f"CSV解析: 共{len(df)}行需求数据")

        requirements = []
        for _, row in df.iterrows():
            req_id = str(row.get("id", ""))
            title = str(row.get("title", req_id))
            description = str(row["description"])

            if not description or description == "nan":
                logger.warning(f"跳过空描述行: {req_id}")
                continue

            # 使用AI提取器解析description
            req = self.extractor.extract(description, req_id)
            # 如果CSV有title，覆盖AI生成的
            if title and title != req_id and title != "nan":
                req.title = title
            requirements.append(req)

        logger.info(f"CSV解析完成: 成功解析{len(requirements)}条需求")
        return requirements
