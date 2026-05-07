"""Publisher 数据模型"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """导出格式"""

    HTML = "html"
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"


class ExportRequest(BaseModel):
    """导出请求"""

    task_id: str = Field(..., description="任务ID，用于创建输出目录")
    title: str = Field(..., description="报告标题")
    content: str = Field(..., description="报告内容（Markdown 格式）")
    sources: list[str] = Field(default_factory=list, description="引用来源列表")
    formats: list[ExportFormat] = Field(
        default=[ExportFormat.HTML, ExportFormat.PDF],
        description="要导出的格式列表",
    )
    output_dir: Optional[str] = Field(
        default=None, description="输出目录，默认为 outputs/<task_id>"
    )
    images: Optional[dict[str, str]] = Field(
        default=None, description="图片映射 {图片名: 图片路径}"
    )


class ExportResult(BaseModel):
    """导出结果"""

    success: bool = Field(..., description="是否成功")
    task_id: str = Field(..., description="任务ID")
    output_dir: str = Field(..., description="输出目录路径")
    files: dict[str, str] = Field(
        default_factory=dict, description="生成的文件 {格式: 文件路径}"
    )
    errors: list[str] = Field(default_factory=list, description="错误列表")


class ReportMetadata(BaseModel):
    """报告元数据"""

    title: str
    author: str = "DeepFinance"
    created_at: str = ""
    version: str = "1.0"
    language: str = "zh-CN"
