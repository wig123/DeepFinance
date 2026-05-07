"""流水线服务层

包装现有的 ReportPipeline，添加进度回调和 WebSocket 推送支持。
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.api.services.project_service import project_service
from src.api.websocket.progress import broadcaster
from src.analyzers import DataResearcher, DocumentAnalyzer, ReportGenerator
from src.models.report import PipelineStep
from src.tools.parser import DoclingParser, ImageAnalyzer

logger = logging.getLogger(__name__)


class PipelineService:
    """流水线服务

    包装 ReportPipeline，提供进度回调和 WebSocket 推送。
    """

    def __init__(
        self,
        enable_image_analysis: bool = True,
        enable_research: bool = True,
        analyzer_model: str = "gemini-3-flash-preview",
        generator_model: str = "gemini-3-flash-preview",
        search_engine: str = "tavily",
    ):
        self.enable_image_analysis = enable_image_analysis
        self.enable_research = enable_research
        self.analyzer_model = analyzer_model
        self.generator_model = generator_model
        self.search_engine = search_engine

        # 初始化分析器
        self.analyzer = DocumentAnalyzer(model=analyzer_model)
        self.researcher = DataResearcher(search_engine=search_engine) if enable_research else None
        self.generator = ReportGenerator(model=generator_model)

        # 图片分析器（chart_prompt 路径由环境变量 CHART_PROMPT_PATH 提供，缺省时跳过深度图表分析）
        self.image_analyzer = None
        if enable_image_analysis:
            env_path = os.environ.get("CHART_PROMPT_PATH")
            chart_prompt_path = Path(env_path) if env_path else None
            if chart_prompt_path and chart_prompt_path.exists():
                self.image_analyzer = ImageAnalyzer(chart_prompt_path=chart_prompt_path)
                logger.info("已启用图片智能分析")
            else:
                logger.info("未配置 CHART_PROMPT_PATH 或文件不存在，图片分析将走简单描述模式")

    async def run_with_progress(
        self,
        project_id: str,
        pdf_path: Path,
        output_dir: Path,
        user_query: str | None = None,
    ):
        """运行流水线并推送进度

        Args:
            project_id: 项目ID
            pdf_path: PDF文件路径
            output_dir: 输出目录
            user_query: 用户侧重点（可选）
        """
        pipeline_steps = []

        try:
            # ==================== 阶段1: 解析PDF ====================
            await self._run_parsing_stage(project_id, pdf_path, output_dir, pipeline_steps)

            # 获取解析结果目录
            source_dir = output_dir / "source"
            doc_dirs = list(source_dir.iterdir()) if source_dir.exists() else []
            doc_source_dir = doc_dirs[0] if doc_dirs else source_dir

            # ==================== 阶段2: 分析文档 ====================
            analysis = await self._run_analysis_stage(
                project_id, doc_source_dir, output_dir, pipeline_steps, user_query
            )

            # ==================== 阶段3: 补充研究 ====================
            research = None
            if self.enable_research:
                research = await self._run_research_stage(project_id, analysis, output_dir, pipeline_steps)

            # ==================== 阶段4: 生成报告 ====================
            await self._run_generation_stage(project_id, analysis, research, output_dir, pipeline_steps)

            # 更新项目状态为完成
            project_service.update_project_status(project_id, status="completed")

            # 发送完成消息
            await broadcaster.send_stage_complete(
                project_id,
                "generation",
                "报告生成完成",
                {"report_url": f"/api/projects/{project_id}/report"},
            )

        except Exception as e:
            logger.exception(f"流水线执行失败: {e}")
            # 更新项目状态为失败
            project_service.update_project_status(project_id, status="failed")
            # 发送错误消息
            await broadcaster.send_error(project_id, "pipeline", str(e), "PIPELINE_ERROR")
            raise

    async def _run_parsing_stage(
        self,
        project_id: str,
        pdf_path: Path,
        output_dir: Path,
        pipeline_steps: list[PipelineStep],
    ):
        """运行解析阶段"""
        stage_name = "parsing"
        start_time = time.time()

        # 更新状态
        project_service.update_pipeline_stage(project_id, stage_name, "in_progress", started_at=datetime.now())

        # 发送开始消息
        await broadcaster.send_stage_start(project_id, stage_name, "开始解析PDF文档...")

        try:
            # 创建解析器
            parser = DoclingParser(
                output_base=output_dir / "source",
                enable_image_analysis=self.enable_image_analysis,
                image_analyzer=self.image_analyzer,
            )

            # 运行解析（同步，在线程池中执行）
            loop = asyncio.get_event_loop()
            parse_result = await loop.run_in_executor(None, lambda: parser.execute(str(pdf_path)))

            if not parse_result.success:
                raise RuntimeError(f"PDF解析失败: {parse_result.error}")

            duration = time.time() - start_time

            # 更新状态
            details = {
                "pages_extracted": parse_result.data.page_count if hasattr(parse_result.data, "page_count") else 0,
                "figures_count": parse_result.data.figures_count,
            }
            project_service.update_pipeline_stage(
                project_id,
                stage_name,
                "completed",
                completed_at=datetime.now(),
                duration=duration,
                details=details,
            )

            # 发送完成消息
            await broadcaster.send_stage_complete(
                project_id,
                stage_name,
                f"文档解析完成，识别 {details['figures_count']} 个图表",
                details,
            )

            pipeline_steps.append(
                PipelineStep(
                    step="parse",
                    duration_seconds=duration,
                    artifact="source/",
                    status="completed",
                )
            )

            return parse_result

        except Exception as e:
            project_service.update_pipeline_stage(project_id, stage_name, "failed", error=str(e))
            await broadcaster.send_error(project_id, stage_name, str(e), "PARSING_ERROR")
            raise

    async def _run_analysis_stage(
        self,
        project_id: str,
        doc_source_dir: Path,
        output_dir: Path,
        pipeline_steps: list[PipelineStep],
        user_query: str | None = None,
    ):
        """运行分析阶段"""
        stage_name = "analysis"
        start_time = time.time()

        # 更新状态
        project_service.update_pipeline_stage(project_id, stage_name, "in_progress", started_at=datetime.now())

        # 发送开始消息
        await broadcaster.send_stage_start(project_id, stage_name, "开始分析文档内容...")

        try:
            # 运行分析（同步，在线程池中执行）
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(
                None, lambda: self.analyzer.analyze(doc_source_dir, user_query=user_query)
            )

            # 保存分析结果
            analysis_path = output_dir / "01_analysis.json"
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

            duration = time.time() - start_time

            # 统计补充研究需求
            total_research_needs = (
                len(analysis.supplementary_research_needs.temporal_updates)
                + len(analysis.supplementary_research_needs.comparative_data)
                + len(analysis.supplementary_research_needs.deep_dive_analysis)
                + len(analysis.supplementary_research_needs.market_perspectives)
            )

            # 更新状态
            details = {
                "sections_count": len(analysis.content_summary),
                "takeaways_count": len(analysis.key_takeaways),
                "research_needs_count": total_research_needs,
            }
            project_service.update_pipeline_stage(
                project_id,
                stage_name,
                "completed",
                completed_at=datetime.now(),
                duration=duration,
                details=details,
            )

            # 更新项目元数据
            if analysis.document_metadata:
                project_service.update_project_status(
                    project_id,
                    title=f"{analysis.document_metadata.company} {analysis.document_metadata.period}",
                    metadata={
                        "company": analysis.document_metadata.company,
                        "period": analysis.document_metadata.period,
                        "document_type": analysis.document_metadata.document_type,
                        "publish_date": analysis.document_metadata.publish_date,
                    },
                )

            # 发送完成消息
            await broadcaster.send_stage_complete(
                project_id,
                stage_name,
                f"分析完成，提取 {details['sections_count']} 个章节",
                details,
            )

            pipeline_steps.append(
                PipelineStep(
                    step="analysis",
                    duration_seconds=duration,
                    artifact="01_analysis.json",
                    status="completed",
                )
            )

            return analysis

        except Exception as e:
            project_service.update_pipeline_stage(project_id, stage_name, "failed", error=str(e))
            await broadcaster.send_error(project_id, stage_name, str(e), "ANALYSIS_ERROR")
            raise

    async def _run_research_stage(
        self,
        project_id: str,
        analysis,
        output_dir: Path,
        pipeline_steps: list[PipelineStep],
    ):
        """运行研究阶段"""
        stage_name = "research"
        start_time = time.time()

        # 统计研究需求
        total_research_needs = (
            len(analysis.supplementary_research_needs.temporal_updates)
            + len(analysis.supplementary_research_needs.comparative_data)
            + len(analysis.supplementary_research_needs.deep_dive_analysis)
            + len(analysis.supplementary_research_needs.market_perspectives)
        )

        if total_research_needs == 0 or self.researcher is None:
            # 跳过研究阶段
            project_service.update_pipeline_stage(project_id, stage_name, "completed", details={"skipped": True})
            await broadcaster.send_stage_complete(project_id, stage_name, "无需补充研究", {"skipped": True})
            return None

        # 更新状态
        project_service.update_pipeline_stage(project_id, stage_name, "in_progress", started_at=datetime.now())

        # 发送开始消息
        await broadcaster.send_stage_start(project_id, stage_name, f"开始补充研究，共 {total_research_needs} 个查询...")

        try:
            # 运行研究
            research = await self.researcher.research(
                research_needs=analysis.supplementary_research_needs,
                analysis_id=analysis.analysis_id,
            )

            # 保存研究结果
            research_path = output_dir / "02_research.json"
            with open(research_path, "w", encoding="utf-8") as f:
                json.dump(research.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

            duration = time.time() - start_time

            # 更新状态
            details = {
                "queries_count": len(research.queries),
                "results_count": sum(len(q.results) for q in research.queries),
            }
            project_service.update_pipeline_stage(
                project_id,
                stage_name,
                "completed",
                completed_at=datetime.now(),
                duration=duration,
                details=details,
            )

            # 发送完成消息
            await broadcaster.send_stage_complete(
                project_id,
                stage_name,
                f"研究完成，获取 {details['results_count']} 条结果",
                details,
            )

            pipeline_steps.append(
                PipelineStep(
                    step="research",
                    duration_seconds=duration,
                    artifact="02_research.json",
                    status="completed",
                )
            )

            return research

        except Exception as e:
            project_service.update_pipeline_stage(project_id, stage_name, "failed", error=str(e))
            await broadcaster.send_error(project_id, stage_name, str(e), "RESEARCH_ERROR")
            raise

    async def _run_generation_stage(
        self,
        project_id: str,
        analysis,
        research,
        output_dir: Path,
        pipeline_steps: list[PipelineStep],
    ):
        """运行报告生成阶段"""
        stage_name = "generation"
        start_time = time.time()

        # 更新状态
        project_service.update_pipeline_stage(project_id, stage_name, "in_progress", started_at=datetime.now())

        # 发送开始消息
        await broadcaster.send_stage_start(project_id, stage_name, "开始生成报告...")

        try:
            # 运行生成（同步，在线程池中执行）
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None,
                lambda: self.generator.generate(
                    analysis=analysis,
                    research=research,
                    output_dir=output_dir,
                    pipeline_steps=pipeline_steps,
                ),
            )

            # 保存报告
            report_path = output_dir / "report.md"
            report_path.write_text(report.content, encoding="utf-8")

            # 保存元数据
            metadata_path = output_dir / "report_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(report.metadata.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

            duration = time.time() - start_time

            # 更新状态
            details = {
                "report_path": str(report_path),
                "content_length": len(report.content),
            }
            project_service.update_pipeline_stage(
                project_id,
                stage_name,
                "completed",
                completed_at=datetime.now(),
                duration=duration,
                details=details,
            )

            pipeline_steps.append(
                PipelineStep(
                    step="report_generation",
                    duration_seconds=duration,
                    artifact="report.md",
                    status="completed",
                )
            )

            return report

        except Exception as e:
            project_service.update_pipeline_stage(project_id, stage_name, "failed", error=str(e))
            await broadcaster.send_error(project_id, stage_name, str(e), "GENERATION_ERROR")
            raise


def get_pipeline_service(mode: str = "full") -> PipelineService:
    """根据模式获取流水线服务"""
    if mode == "minimal":
        return PipelineService(enable_image_analysis=False, enable_research=False)
    elif mode == "no-research":
        return PipelineService(enable_image_analysis=True, enable_research=False)
    else:  # full
        return PipelineService(enable_image_analysis=True, enable_research=True)
