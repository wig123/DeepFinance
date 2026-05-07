"""数据模型定义"""

from .report import (
    # 基础类型
    SourceType,
    Citation,
    # 新版：完整文档总结模型
    DocumentMetadata,
    KeyMetric,
    ContentSection,
    KeyTakeaway,
    # 补充研究需求（4个维度）
    TemporalUpdate,
    ComparativeData,
    DeepDiveAnalysis,
    MarketPerspective,
    SupplementaryResearchNeeds,
    # 图表和分析
    ChartAnalysis,
    AnalysisResult,
    # 搜索和研究
    SearchResult,
    QueryResult,
    ResearchResult,
    # 报告输出
    ReportMetadata,
    PipelineStep,
    ReportOutput,
)

__all__ = [
    # 基础类型
    "SourceType",
    "Citation",
    # 新版：完整文档总结模型
    "DocumentMetadata",
    "KeyMetric",
    "ContentSection",
    "KeyTakeaway",
    # 补充研究需求（4个维度）
    "TemporalUpdate",
    "ComparativeData",
    "DeepDiveAnalysis",
    "MarketPerspective",
    "SupplementaryResearchNeeds",
    # 图表和分析
    "ChartAnalysis",
    "AnalysisResult",
    # 搜索和研究
    "SearchResult",
    "QueryResult",
    "ResearchResult",
    # 报告输出
    "ReportMetadata",
    "PipelineStep",
    "ReportOutput",
]
