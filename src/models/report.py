"""报告生成数据模型

定义从文档分析到最终报告生成的所有数据结构。
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """引用来源类型"""

    DOCUMENT = "document"  # 原始文档
    WEB = "web"  # 网络搜索
    API = "api"  # 金融API
    CHART_ANALYSIS = "chart_analysis"  # AI图表分析


class Citation(BaseModel):
    """引用源"""

    id: str = Field(..., description="引用ID，如 doc-p3, web-1")
    type: SourceType = Field(..., description="引用类型")
    location: str = Field(..., description="位置：URL、文件路径、锚点等")
    title: str | None = Field(None, description="标题")
    quote: str | None = Field(None, description="原文引用片段")
    accessed_at: datetime | None = Field(None, description="访问时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# 新版：完整文档总结模型
# ============================================================================


class DocumentMetadata(BaseModel):
    """文档元信息"""

    document_type: str = Field(..., description="文档类型：earnings_report/annual_report等")
    company: str = Field(..., description="公司名称")
    period: str = Field(..., description="报告期，如 Q3 2025")
    publish_date: str | None = Field(None, description="发布日期")
    key_topics: list[str] = Field(default_factory=list, description="主要议题")


class KeyMetric(BaseModel):
    """关键指标"""

    metric: str = Field(..., description="指标名称")
    current_value: str = Field(..., description="当前值")
    previous_value: str | None = Field(None, description="对比值（去年同期）")
    change: str | None = Field(None, description="变化，如 +12% YoY")
    context: str | None = Field(None, description="上下文说明")
    source: str = Field(..., description="引用位置，如 page-5#table-2")
    original_quote: str | None = Field(None, description="英文原文引用（2-3句话）")


class ContentSection(BaseModel):
    """内容章节（完整总结的一个部分）"""

    section_id: str = Field(..., description="章节ID，如 financial_performance")
    section_title: str = Field(..., description="章节标题")
    content: str = Field(..., description="详细总结内容")
    key_metrics: list[KeyMetric] = Field(default_factory=list, description="关键指标")
    insights: list[str] = Field(default_factory=list, description="关键洞察（3-5句话）")
    citations: list[dict[str, str]] = Field(default_factory=list, description="引用列表")


class KeyTakeaway(BaseModel):
    """关键要点"""

    id: str = Field(..., description="要点ID")
    category: str = Field(..., description="分类：positive/negative/neutral")
    statement: str = Field(..., description="要点陈述（1句话）")
    evidence: str = Field(..., description="数据支撑")
    significance: str = Field(..., description="重要性说明")
    sources: list[dict[str, str]] = Field(default_factory=list, description="引用")


# ============================================================================
# 补充研究需求（4个维度）
# ============================================================================


class TemporalUpdate(BaseModel):
    """时效性补充"""

    id: str = Field(..., description="需求ID")
    topic: str = Field(..., description="主题")
    reason: str = Field(..., description="为什么需要")
    search_queries: list[str] = Field(default_factory=list, description="搜索查询列表")
    priority: str = Field(..., description="优先级：high/medium/low")


class ComparativeData(BaseModel):
    """对比信息"""

    id: str = Field(..., description="需求ID")
    comparison_type: str = Field(
        ..., description="对比类型：industry_average/competitors/historical_trend"
    )
    metric: str = Field(..., description="需要对比的指标")
    reason: str = Field(..., description="为什么需要对比")
    search_queries: list[str] = Field(default_factory=list, description="搜索查询列表")


class DeepDiveAnalysis(BaseModel):
    """深度分析"""

    id: str = Field(..., description="需求ID")
    topic: str = Field(..., description="需要深挖的主题")
    question: str | None = Field(None, description="具体问题")
    reason: str | None = Field(None, description="为什么需要")
    search_queries: list[str] = Field(default_factory=list, description="搜索查询列表")


class MarketPerspective(BaseModel):
    """市场观点"""

    id: str = Field(..., description="需求ID")
    topic: str = Field(..., description="主题")
    perspective_type: str = Field(
        default="analyst_ratings", description="观点类型：analyst_ratings/institutional_views/price_reaction"
    )
    search_queries: list[str] = Field(default_factory=list, description="搜索查询列表")


class SupplementaryResearchNeeds(BaseModel):
    """补充研究需求（4个维度）"""

    temporal_updates: list[TemporalUpdate] = Field(default_factory=list, description="时效性补充")
    comparative_data: list[ComparativeData] = Field(default_factory=list, description="对比信息")
    deep_dive_analysis: list[DeepDiveAnalysis] = Field(default_factory=list, description="深度分析")
    market_perspectives: list[MarketPerspective] = Field(default_factory=list, description="市场观点")


class ChartAnalysis(BaseModel):
    """图表分析结果"""

    figure_id: str = Field(..., description="图表ID")
    type: str = Field(..., description="图表类型：chart/illustration/icon")
    title: str | None = Field(None, description="图表标题")
    analysis: dict[str, str] | None = Field(
        None, description="四层分析：图表构成、数据关系、模式特征、核心洞察"
    )
    description: str | None = Field(None, description="插图描述")


class AnalysisResult(BaseModel):
    """初步分析结果（DocumentAnalyzer输出）"""

    analysis_id: str = Field(..., description="分析ID")
    source_document: dict[str, Any] = Field(..., description="源文档信息")

    # 新版结构
    document_metadata: DocumentMetadata = Field(..., description="文档元信息")
    content_summary: list[ContentSection] = Field(
        default_factory=list, description="完整内容总结（按章节）"
    )
    key_takeaways: list[KeyTakeaway] = Field(default_factory=list, description="关键要点汇总")
    supplementary_research_needs: SupplementaryResearchNeeds = Field(
        ..., description="补充研究需求（4个维度）"
    )
    charts_analysis: list[ChartAnalysis] = Field(default_factory=list, description="图表分析")

    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# 搜索与研究结果
# ============================================================================


class SearchResult(BaseModel):
    """单条搜索结果"""

    source: str = Field(..., description="来源：web_search/financial_api/...")
    title: str | None = Field(None, description="标题")
    url: str | None = Field(None, description="URL")
    content: str = Field(..., description="内容")
    published_date: str | None = Field(None, description="发布日期")
    relevance_score: float | None = Field(None, description="相关性评分")
    data: dict[str, Any] | None = Field(None, description="结构化数据")


class QueryResult(BaseModel):
    """单个查询的结果"""

    query_id: str = Field(..., description="查询ID")
    query_text: str = Field(..., description="查询文本")
    source_gap: str = Field(..., description="对应的研究需求ID")
    results: list[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ResearchResult(BaseModel):
    """研究结果（DataResearcher输出）"""

    research_id: str = Field(..., description="研究ID")
    related_analysis: str = Field(..., description="关联的analysis_id")
    queries: list[QueryResult] = Field(default_factory=list, description="所有查询结果")
    summary_by_gap: dict[str, Any] = Field(..., description="按需求ID汇总的结果")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# 报告输出
# ============================================================================


class PipelineStep(BaseModel):
    """流水线步骤"""

    step: str = Field(..., description="步骤名称")
    duration_seconds: float = Field(..., description="耗时（秒）")
    artifact: str = Field(..., description="产出物路径")
    status: str = Field(default="completed", description="状态：completed/failed")
    error: str | None = Field(None, description="错误信息")


class ReportMetadata(BaseModel):
    """报告元数据"""

    report_id: str = Field(..., description="报告ID")
    title: str = Field(..., description="报告标题")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    model: str = Field(..., description="使用的模型")
    generation_cost: float | None = Field(None, description="生成成本（美元）")
    generation_time_seconds: float | None = Field(None, description="总耗时（秒）")

    # Pipeline信息
    pipeline: list[PipelineStep] = Field(default_factory=list, description="流水线步骤")

    # 引用统计
    citations: dict[str, Any] = Field(default_factory=dict, description="引用信息统计")

    # 质量指标
    quality_metrics: dict[str, Any] = Field(default_factory=dict, description="质量指标")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReportOutput(BaseModel):
    """完整报告输出"""

    content: str = Field(..., description="报告Markdown内容")
    metadata: ReportMetadata = Field(..., description="报告元数据")
    output_dir: Path = Field(..., description="输出目录")

    class Config:
        arbitrary_types_allowed = True
