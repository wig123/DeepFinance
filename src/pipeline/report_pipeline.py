"""报告生成流水线

简化的三步流程：
1. 解析PDF（DoclingParser + 图片分析）
2. 分析文档 + 补充研究（DocumentAnalyzer/ChunkedDocumentAnalyzer + DataResearcher）
3. 生成报告（ReportGenerator）
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from src.analyzers import DataResearcher, DocumentAnalyzer, ChunkedDocumentAnalyzer, ReportGenerator
from src.models.report import PipelineStep, ReportOutput
from src.tools.parser import DoclingParser, ImageAnalyzer

logger = logging.getLogger(__name__)


class ReportPipeline:
    """报告生成流水线

    串联所有步骤，从PDF到最终报告。

    Attributes:
        output_base: 输出根目录
        enable_image_analysis: 是否启用图片分析
        enable_research: 是否启用外部数据补充
    """

    def __init__(
        self,
        output_base: str | Path = "outputs",
        enable_image_analysis: bool = True,
        enable_research: bool = True,
        enable_chunked_analysis: bool = True,
        analyzer_model: str = "gemini-2.0-flash",
        generator_model: str = "claude-sonnet-4-5-20250929",
        search_engine: str = "tavily",
        # 分块分析参数
        target_chunk_size: int = 15000,
        min_chunks: int = 2,
        max_chunks: int = 6,
    ):
        """初始化流水线

        Args:
            output_base: 输出根目录
            enable_image_analysis: 是否启用图片智能分析
            enable_research: 是否启用外部数据补充
            enable_chunked_analysis: 是否启用分块分析（推荐用于大文档）
            analyzer_model: 文档分析模型（推荐Gemini，长上下文+低成本）
            generator_model: 报告生成模型（推荐Claude，质量最高）
            search_engine: 搜索引擎（tavily/serper）
            target_chunk_size: 分块目标大小（字符数）
            min_chunks: 最少分块数
            max_chunks: 最多分块数
        """
        self.output_base = Path(output_base)
        self.enable_image_analysis = enable_image_analysis
        self.enable_research = enable_research
        self.enable_chunked_analysis = enable_chunked_analysis

        # 初始化各个模块
        self.parser = None
        
        # 根据配置选择分析器
        if enable_chunked_analysis:
            self.analyzer = ChunkedDocumentAnalyzer(
                model=analyzer_model,
                target_chunk_size=target_chunk_size,
                min_chunks=min_chunks,
                max_chunks=max_chunks,
            )
            logger.info("使用分块文档分析器（适用于大文档）")
        else:
            self.analyzer = DocumentAnalyzer(model=analyzer_model)
            logger.info("使用标准文档分析器")
        
        self.researcher = DataResearcher(search_engine=search_engine) if enable_research else None
        self.generator = ReportGenerator(model=generator_model)

        # 如果启用图片分析，从环境变量 CHART_PROMPT_PATH 读取 prompt 路径；缺省则禁用深度分析
        self.image_analyzer = None
        if enable_image_analysis:
            env_path = os.environ.get("CHART_PROMPT_PATH")
            chart_prompt_path = Path(env_path) if env_path else None
            if chart_prompt_path and chart_prompt_path.exists():
                self.image_analyzer = ImageAnalyzer(chart_prompt_path=chart_prompt_path)
                logger.info("已启用图片智能分析")
            else:
                logger.info("未配置 CHART_PROMPT_PATH 或文件不存在，禁用深度图表分析")

        logger.info(
            f"流水线初始化完成: "
            f"图片分析={'开' if self.image_analyzer else '关'}, "
            f"分块分析={'开' if enable_chunked_analysis else '关'}, "
            f"外部研究={'开' if enable_research else '关'}"
        )

    def run(self, pdf_path: str | Path) -> Path:
        """运行完整流水线

        Args:
            pdf_path: PDF文件路径

        Returns:
            Path: 输出目录路径
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        logger.info(f"=" * 80)
        logger.info(f"开始处理: {pdf_path.name}")
        logger.info(f"=" * 80)

        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_name = pdf_path.stem
        output_dir = self.output_base / f"{doc_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"输出目录: {output_dir}")

        # 记录流水线步骤
        pipeline_steps = []

        # ==================== 步骤1: 解析PDF ====================
        logger.info("\n" + "=" * 80)
        logger.info("步骤 1/3: 解析PDF文档")
        logger.info("=" * 80)

        step1_start = time.time()

        # 初始化Parser（每次run时创建，避免状态污染）
        self.parser = DoclingParser(
            output_base=output_dir / "source",
            enable_image_analysis=self.enable_image_analysis,
            image_analyzer=self.image_analyzer,
        )

        parse_result = self.parser.execute(str(pdf_path))

        if not parse_result.success:
            raise RuntimeError(f"PDF解析失败: {parse_result.error}")

        step1_duration = time.time() - step1_start
        pipeline_steps.append(
            PipelineStep(
                step="parse",
                duration_seconds=step1_duration,
                artifact="source/",
                status="completed",
            )
        )

        # 获取实际的文档目录（DoclingParser会创建子目录）
        doc_source_dir = parse_result.data.output_dir

        logger.info(f"✓ 解析完成，耗时 {step1_duration:.1f}秒")
        logger.info(f"  - 内容: {doc_source_dir / 'content.md'}")
        logger.info(f"  - 图片: {parse_result.data.figures_count} 张")

        # ==================== 步骤2: 分析文档 ====================
        logger.info("\n" + "=" * 80)
        logger.info("步骤 2/3: 分析文档内容")
        logger.info("=" * 80)

        step2_start = time.time()

        analysis = self.analyzer.analyze(doc_source_dir)

        # 保存分析结果
        analysis_path = output_dir / "01_analysis.json"
        with open(analysis_path, "w", encoding="utf-8") as f:
            # 使用mode='python'转换datetime为字符串
            json.dump(analysis.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

        step2_duration = time.time() - step2_start
        pipeline_steps.append(
            PipelineStep(
                step="analysis",
                duration_seconds=step2_duration,
                artifact="01_analysis.json",
                status="completed",
            )
        )

        # 统计补充研究需求
        total_research_needs = (
            len(analysis.supplementary_research_needs.temporal_updates)
            + len(analysis.supplementary_research_needs.comparative_data)
            + len(analysis.supplementary_research_needs.deep_dive_analysis)
            + len(analysis.supplementary_research_needs.market_perspectives)
        )

        logger.info(f"✓ 分析完成，耗时 {step2_duration:.1f}秒")
        logger.info(f"  - 内容章节: {len(analysis.content_summary)} 个")
        logger.info(f"  - 关键要点: {len(analysis.key_takeaways)} 个")
        logger.info(f"  - 补充研究需求: {total_research_needs} 个")

        # ==================== 步骤3: 补充研究（可选）====================
        research = None
        if self.enable_research and total_research_needs > 0:
            logger.info("\n" + "=" * 80)
            logger.info("步骤 2.5/3: 补充外部数据")
            logger.info("=" * 80)

            step3_start = time.time()

            research = asyncio.run(
                self.researcher.research(
                    research_needs=analysis.supplementary_research_needs,
                    analysis_id=analysis.analysis_id,
                )
            )

            # 保存研究结果
            research_path = output_dir / "02_research.json"
            with open(research_path, "w", encoding="utf-8") as f:
                json.dump(research.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

            step3_duration = time.time() - step3_start
            pipeline_steps.append(
                PipelineStep(
                    step="research",
                    duration_seconds=step3_duration,
                    artifact="02_research.json",
                    status="completed",
                )
            )

            logger.info(f"✓ 研究完成，耗时 {step3_duration:.1f}秒")
            logger.info(f"  - 查询数: {len(research.queries)} 个")
            logger.info(f"  - 结果数: {sum(len(q.results) for q in research.queries)} 条")

        # ==================== 步骤4: 生成报告 ====================
        logger.info("\n" + "=" * 80)
        logger.info("步骤 3/3: 生成最终报告")
        logger.info("=" * 80)

        step4_start = time.time()

        report = self.generator.generate(
            analysis=analysis,
            research=research,
            output_dir=output_dir,
            pipeline_steps=pipeline_steps,
        )

        # 保存报告
        report_path = output_dir / "report.md"
        report_path.write_text(report.content, encoding="utf-8")

        # 保存元数据
        metadata_path = output_dir / "report_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(report.metadata.model_dump(mode='json'), f, indent=2, ensure_ascii=False)

        step4_duration = time.time() - step4_start
        pipeline_steps.append(
            PipelineStep(
                step="report_generation",
                duration_seconds=step4_duration,
                artifact="report.md",
                status="completed",
            )
        )

        logger.info(f"✓ 报告生成完成，耗时 {step4_duration:.1f}秒")
        logger.info(f"  - 报告: {report_path}")
        logger.info(f"  - 元数据: {metadata_path}")

        # ==================== 总结 ====================
        total_duration = sum(step.duration_seconds for step in pipeline_steps)

        logger.info("\n" + "=" * 80)
        logger.info("流水线执行完成")
        logger.info("=" * 80)
        logger.info(f"总耗时: {total_duration:.1f}秒")
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"\n生成文件:")
        for step in pipeline_steps:
            logger.info(f"  - {step.artifact} ({step.duration_seconds:.1f}秒)")

        return output_dir
