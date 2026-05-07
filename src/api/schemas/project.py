"""项目相关数据模型"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """创建项目请求"""

    user_query: str | None = Field(None, description="用户侧重点描述")
    mode: str = Field("full", description="运行模式：full/no-research/minimal")


class PipelineStage(BaseModel):
    """流水线阶段"""

    name: str = Field(..., description="阶段名称")
    status: str = Field(..., description="状态：pending/in_progress/completed/failed")
    started_at: datetime | None = Field(None, description="开始时间")
    completed_at: datetime | None = Field(None, description="完成时间")
    duration: float | None = Field(None, description="耗时（秒）")
    details: dict[str, Any] | None = Field(None, description="详细信息")
    error: str | None = Field(None, description="错误信息")


class ProjectMetadata(BaseModel):
    """项目元数据"""

    company: str | None = Field(None, description="公司名称")
    period: str | None = Field(None, description="报告期")
    document_type: str | None = Field(None, description="文档类型")
    publish_date: str | None = Field(None, description="发布日期")


class ProjectResponse(BaseModel):
    """项目响应"""

    project_id: str = Field(..., description="项目ID")
    status: str = Field(..., description="状态：processing/completed/failed")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime | None = Field(None, description="更新时间")
    title: str | None = Field(None, description="项目标题")
    metadata: ProjectMetadata | None = Field(None, description="元数据")
    websocket_url: str | None = Field(None, description="WebSocket连接URL")


class ProjectArtifacts(BaseModel):
    """项目产出物"""

    report_md: str | None = Field(None, description="Markdown报告路径")
    report_html: str | None = Field(None, description="HTML报告路径")
    analysis_json: str | None = Field(None, description="分析结果路径")
    research_json: str | None = Field(None, description="研究结果路径")


class PipelineInfo(BaseModel):
    """流水线信息"""

    current_stage: str = Field(..., description="当前阶段")
    stages: list[PipelineStage] = Field(default_factory=list, description="各阶段信息")


class ProjectDetail(ProjectResponse):
    """项目详情"""

    pipeline: PipelineInfo | None = Field(None, description="流水线信息")
    artifacts: ProjectArtifacts | None = Field(None, description="产出物路径")
    user_query: str | None = Field(None, description="用户输入的侧重点")
    mode: str | None = Field(None, description="运行模式")


class ProjectListResponse(BaseModel):
    """项目列表响应"""

    total: int = Field(..., description="总数")
    items: list[ProjectResponse] = Field(..., description="项目列表")
