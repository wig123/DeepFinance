"""Tool 基类和 ToolResult 定义。

提供所有工具的通用基类和结果封装。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ToolStatus(Enum):
    """工具执行状态。"""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"  # 部分成功


@dataclass
class ToolResult(Generic[T]):
    """工具执行结果的通用封装。

    Attributes:
        status: 执行状态
        data: 返回数据
        message: 状态描述信息
        errors: 错误列表
        metadata: 额外元数据
        elapsed_time: 执行耗时(秒)
    """

    status: ToolStatus
    data: T | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    elapsed_time: float = 0.0

    @property
    def success(self) -> bool:
        """是否成功执行。"""
        return self.status == ToolStatus.SUCCESS

    @classmethod
    def ok(cls, data: T, message: str = "", **metadata: Any) -> "ToolResult[T]":
        """创建成功结果。"""
        return cls(
            status=ToolStatus.SUCCESS,
            data=data,
            message=message,
            metadata=metadata,
        )

    @classmethod
    def error(cls, message: str, errors: list[str] | None = None) -> "ToolResult[T]":
        """创建错误结果。"""
        return cls(
            status=ToolStatus.ERROR,
            message=message,
            errors=errors or [message],
        )

    @classmethod
    def partial(
        cls, data: T, message: str, errors: list[str] | None = None
    ) -> "ToolResult[T]":
        """创建部分成功结果。"""
        return cls(
            status=ToolStatus.PARTIAL,
            data=data,
            message=message,
            errors=errors or [],
        )


class BaseTool(ABC):
    """工具基类。

    所有工具需要实现 execute 方法。
    """

    name: str = "base_tool"
    description: str = "Base tool class"

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> ToolResult[Any]:
        """执行工具任务。

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"


@dataclass
class ParsedDocument:
    """解析后的文档结构。

    Attributes:
        name: 文档名称(无扩展名)
        source_path: 原始文件路径
        output_dir: 输出目录
        content_md: Markdown 内容
        images: 图片路径列表
        metadata: 文档元信息
        page_count: 页数
        tables_count: 表格数量
        figures_count: 图表数量
    """

    name: str
    source_path: Path
    output_dir: Path
    content_md: str
    images: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    page_count: int = 0
    tables_count: int = 0
    figures_count: int = 0

    @property
    def content_path(self) -> Path:
        """Markdown 内容文件路径。"""
        return self.output_dir / "content.md"

    @property
    def images_dir(self) -> Path:
        """图片目录路径。"""
        return self.output_dir / "images"

    @property
    def metadata_path(self) -> Path:
        """元数据文件路径。"""
        return self.output_dir / "metadata.json"


@dataclass
class DocumentMetadata:
    """文档元数据。

    Attributes:
        title: 文档标题
        source: 源文件名
        page_count: 页数
        tables_count: 表格数量
        figures_count: 图表数量
        parsed_at: 解析时间
        parser_version: 解析器版本
        figures: 图表信息列表
        tables: 表格信息列表
        text_blocks: 文本块信息列表（含 bbox 坐标，用于精确定位）
    """

    title: str
    source: str
    page_count: int
    tables_count: int
    figures_count: int
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    parser_version: str = "1.0.0"
    figures: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    text_blocks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "title": self.title,
            "source": self.source,
            "page_count": self.page_count,
            "tables_count": self.tables_count,
            "figures_count": self.figures_count,
            "parsed_at": self.parsed_at,
            "parser_version": self.parser_version,
            "figures": self.figures,
            "tables": self.tables,
            "text_blocks": self.text_blocks,
        }
