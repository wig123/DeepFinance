"""引用相关数据模型"""

from typing import Any

from pydantic import BaseModel, Field


class BoundingRect(BaseModel):
    """边界矩形坐标 (TOPLEFT 坐标系)"""

    x1: float = Field(..., description="左边界")
    y1: float = Field(..., description="上边界")
    x2: float = Field(..., description="右边界")
    y2: float = Field(..., description="下边界")
    width: float = Field(..., description="宽度")
    height: float = Field(..., description="高度")


class PageDimensions(BaseModel):
    """页面尺寸"""

    width: float = Field(..., description="页面宽度")
    height: float = Field(..., description="页面高度")


class PDFHighlight(BaseModel):
    """PDF 高亮定位信息

    用于前端 react-pdf-highlighter-extended 组件定位和高亮显示
    """

    page_number: int = Field(..., description="页码 (1-indexed)")
    bounding_rect: BoundingRect = Field(..., description="边界矩形")
    rects: list[BoundingRect] | None = Field(None, description="多个矩形区域（多行文本）")
    page_dimensions: PageDimensions = Field(..., description="页面尺寸")


class CitationResponse(BaseModel):
    """引用响应"""

    type: str = Field(..., description="引用类型：document/chart/web")

    # 文档引用
    id: str | None = Field(None, description="引用ID")
    location: str | None = Field(None, description="位置")
    source: str | None = Field(None, description="来源")

    # 图表引用
    figure_id: str | None = Field(None, description="图表文件名")
    figure_path: str | None = Field(None, description="图表路径")
    figure_url: str | None = Field(None, description="图表URL")
    figure_analysis: dict[str, Any] | None = Field(None, description="图表分析")

    # 外部引用
    title: str | None = Field(None, description="标题")
    url: str | None = Field(None, description="URL")
    content: str | None = Field(None, description="内容摘要")
    published_date: str | None = Field(None, description="发布日期")
    relevance_score: float | None = Field(None, description="相关性评分")

    # PDF 定位信息（新增）
    pdf_highlight: PDFHighlight | None = Field(None, description="PDF 高亮定位信息")
    pdf_url: str | None = Field(None, description="原始 PDF 文件 URL")
