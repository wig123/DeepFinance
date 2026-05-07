"""文档解析模块。

提供 PDF 文档解析功能，将金融文档转换为结构化的 Markdown + 图片格式。

解析器选择:
- DoclingParser: 表格精度最高 (97.9%)，但较慢 (~4s/页)
- MinerUParser: 速度快 (~0.2s/页)，表格质量良好，推荐使用
"""

from .base import (
    BaseTool,
    DocumentMetadata,
    ParsedDocument,
    ToolResult,
    ToolStatus,
)
from .docling_parser import DoclingParser
from .mineru_parser import MinerUParser
from .image_analyzer import ImageAnalyzer

__all__ = [
    "BaseTool",
    "DoclingParser",
    "MinerUParser",
    "DocumentMetadata",
    "ImageAnalyzer",
    "ParsedDocument",
    "ToolResult",
    "ToolStatus",
]
