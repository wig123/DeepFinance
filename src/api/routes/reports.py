"""报告查看路由"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas.report import AnalysisResponse, ReportResponse
from src.api.services.project_service import project_service

router = APIRouter()


def load_json_file(file_path: Path) -> dict | None:
    """加载 JSON 文件"""
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


@router.get("/{project_id}/report", response_model=ReportResponse)
async def get_report(
    project_id: str,
    format: str = Query("markdown", description="格式：markdown/html/json"),
):
    """获取报告内容

    Args:
        project_id: 项目ID
        format: 输出格式（markdown/html/json）

    Returns:
        报告内容
    """
    # 检查项目是否存在
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(404, f"项目不存在: {project_id}")

    if project.status != "completed":
        raise HTTPException(400, f"项目尚未完成: {project.status}")

    project_dir = project_service.get_project_dir(project_id)

    # 根据格式返回内容
    if format == "markdown":
        report_path = project_dir / "report.md"
        if not report_path.exists():
            raise HTTPException(404, "报告文件不存在")
        content = report_path.read_text(encoding="utf-8")

    elif format == "html":
        report_path = project_dir / "report.html"
        if not report_path.exists():
            # 如果没有 HTML，返回 Markdown
            report_path = project_dir / "report.md"
            if not report_path.exists():
                raise HTTPException(404, "报告文件不存在")
        content = report_path.read_text(encoding="utf-8")

    elif format == "json":
        # 返回结构化的分析结果
        analysis_path = project_dir / "01_analysis.json"
        if not analysis_path.exists():
            raise HTTPException(404, "分析结果不存在")
        analysis = load_json_file(analysis_path)
        content = json.dumps(analysis, ensure_ascii=False, indent=2)

    else:
        raise HTTPException(400, f"不支持的格式: {format}")

    # 加载元数据
    metadata_path = project_dir / "report_metadata.json"
    metadata = load_json_file(metadata_path)

    return ReportResponse(
        content=content,
        format=format,
        metadata={
            "title": metadata.get("title") if metadata else None,
            "generated_at": metadata.get("generated_at") if metadata else None,
            "model": metadata.get("model") if metadata else None,
            "generation_time_seconds": metadata.get("generation_time_seconds") if metadata else None,
        },
    )


@router.get("/{project_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(project_id: str):
    """获取分析结果

    返回结构化的文档分析结果。

    Args:
        project_id: 项目ID

    Returns:
        分析结果
    """
    # 检查项目是否存在
    if not project_service.project_exists(project_id):
        raise HTTPException(404, f"项目不存在: {project_id}")

    project_dir = project_service.get_project_dir(project_id)
    analysis_path = project_dir / "01_analysis.json"

    if not analysis_path.exists():
        raise HTTPException(404, "分析结果不存在，项目可能仍在处理中")

    analysis = load_json_file(analysis_path)

    return AnalysisResponse(
        analysis_id=analysis.get("analysis_id", ""),
        document_metadata=analysis.get("document_metadata", {}),
        content_summary=analysis.get("content_summary", []),
        key_takeaways=analysis.get("key_takeaways", []),
        supplementary_research_needs=analysis.get("supplementary_research_needs", {}),
        charts_analysis=analysis.get("charts_analysis", []),
    )


@router.get("/{project_id}/research")
async def get_research(project_id: str):
    """获取研究结果

    返回补充研究的结果。

    Args:
        project_id: 项目ID

    Returns:
        研究结果
    """
    # 检查项目是否存在
    if not project_service.project_exists(project_id):
        raise HTTPException(404, f"项目不存在: {project_id}")

    project_dir = project_service.get_project_dir(project_id)
    research_path = project_dir / "02_research.json"

    if not research_path.exists():
        raise HTTPException(404, "研究结果不存在")

    research = load_json_file(research_path)
    return research
