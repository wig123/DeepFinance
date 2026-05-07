"""报告相关数据模型"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportMetadataResponse(BaseModel):
    """报告元数据"""

    title: str | None = Field(None, description="报告标题")
    generated_at: datetime | None = Field(None, description="生成时间")
    model: str | None = Field(None, description="使用的模型")
    generation_time_seconds: float | None = Field(None, description="生成耗时")


class ReportResponse(BaseModel):
    """报告响应"""

    content: str = Field(..., description="报告内容")
    format: str = Field(..., description="格式：markdown/html/json")
    metadata: ReportMetadataResponse | None = Field(None, description="元数据")


class AnalysisResponse(BaseModel):
    """分析结果响应"""

    analysis_id: str = Field(..., description="分析ID")
    document_metadata: dict[str, Any] = Field(..., description="文档元信息")
    content_summary: list[dict[str, Any]] = Field(..., description="内容总结")
    key_takeaways: list[dict[str, Any]] = Field(..., description="关键要点")
    supplementary_research_needs: dict[str, Any] = Field(..., description="补充研究需求")
    charts_analysis: list[dict[str, Any]] = Field(default_factory=list, description="图表分析")
