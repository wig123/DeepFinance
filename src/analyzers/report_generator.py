"""报告生成器

基于文档分析和补充研究数据，生成带引用的最终报告。
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.models.report import (
    AnalysisResult,
    PipelineStep,
    ReportMetadata,
    ReportOutput,
    ResearchResult,
)
from src.prompts import get_report_generation_prompt

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class ReportGenerator:
    """报告生成器

    使用高质量LLM（推荐Claude）生成最终报告。

    Attributes:
        model: 使用的模型名称
        llm: LLM实例
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.2,
    ):
        """初始化生成器

        Args:
            model: 模型名称（推荐Claude Sonnet 4.5，质量最高）
            temperature: 温度参数
        """
        self.model = model
        self.temperature = temperature

        # 初始化LLM
        if "claude" in model.lower():
            self._init_claude(model)
        elif "gemini" in model.lower():
            self._init_gemini(model)
        else:
            raise ValueError(f"不支持的模型: {model}")

    def _init_claude(self, model: str):
        """初始化Claude模型"""
        try:
            from langchain_anthropic import ChatAnthropic

            self.llm = ChatAnthropic(
                model=model,
                temperature=self.temperature,
                timeout=600.0,  # 报告生成需要较长时间（10分钟）
                max_retries=3,
            )
            logger.info(f"已初始化Claude模型: {model}")
        except ImportError:
            raise ImportError(
                "需要安装 langchain-anthropic: pip install langchain-anthropic"
            )

    def _init_gemini(self, model: str):
        """初始化Gemini模型（通过CloseAI的Google Genai接口）"""
        import os
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            # 使用CloseAI的Google Genai接口
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=self.temperature,
                max_output_tokens=32768,  # 报告生成需要更长输出
                google_api_key=os.getenv("CLOSEAI_API_KEY"),
                client_options={"api_endpoint": "https://api.openai-proxy.org/google"},
                convert_system_message_to_human=True,
            )
            logger.info(f"已初始化Gemini模型（通过CloseAI）: {model}")
        except ImportError:
            raise ImportError(
                "需要安装 langchain-google-genai: pip install langchain-google-genai"
            )

    def generate(
        self,
        analysis: AnalysisResult,
        research: ResearchResult | None,
        output_dir: Path,
        pipeline_steps: list[PipelineStep] | None = None,
    ) -> ReportOutput:
        """生成报告

        Args:
            analysis: 文档分析结果
            research: 补充研究结果（可选）
            output_dir: 输出目录
            pipeline_steps: 流水线步骤记录（用于元数据）

        Returns:
            ReportOutput: 报告输出
        """
        logger.info("开始生成最终报告...")

        # 1. 构造prompt
        prompt = self._build_report_prompt(analysis, research)

        # 2. 调用LLM生成报告
        logger.info(f"调用LLM生成报告 (模型: {self.model})...")
        start_time = datetime.now()

        response = self.llm.invoke(prompt)
        # 处理 Gemini 等模型返回列表的情况
        raw_content = response.content
        if isinstance(raw_content, list):
            # 将列表中的文本部分拼接成字符串
            report_content = "".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in raw_content
            )
        else:
            report_content = raw_content

        generation_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"报告生成完成，耗时 {generation_time:.1f}秒")

        # 3. 构造元数据
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 统计引用
        citations_stats = self._count_citations(report_content)

        metadata = ReportMetadata(
            report_id=report_id,
            title=self._extract_title(report_content),
            model=self.model,
            generation_time_seconds=generation_time,
            pipeline=pipeline_steps or [],
            citations=citations_stats,
            quality_metrics={
                "content_sections_count": len(analysis.content_summary),
                "key_takeaways_count": len(analysis.key_takeaways),
                "research_needs_resolved": sum(
                    1
                    for gap_id, summary in (research.summary_by_gap.items() if research else [])
                    if summary.get("answered", False)
                ),
                "research_needs_total": (
                    len(analysis.supplementary_research_needs.temporal_updates)
                    + len(analysis.supplementary_research_needs.comparative_data)
                    + len(analysis.supplementary_research_needs.deep_dive_analysis)
                    + len(analysis.supplementary_research_needs.market_perspectives)
                ),
            },
        )

        # 4. 返回结果
        return ReportOutput(
            content=report_content,
            metadata=metadata,
            output_dir=output_dir,
        )

    def _build_report_prompt(
        self, analysis: AnalysisResult, research: ResearchResult | None
    ) -> str:
        """构造报告生成prompt"""

        # 准备分析结果（新版结构）
        analysis_json = {
            "document_metadata": {
                "company": analysis.document_metadata.company,
                "period": analysis.document_metadata.period,
                "document_type": analysis.document_metadata.document_type,
                "key_topics": analysis.document_metadata.key_topics,
            },
            "content_summary": [
                {
                    "section_title": s.section_title,
                    "content": s.content,
                    "key_metrics": [
                        {
                            "metric": m.metric,
                            "current_value": m.current_value,
                            "change": m.change,
                            "context": m.context,
                            "source": m.source,
                            "original_quote": getattr(m, 'original_quote', None),
                        }
                        for m in s.key_metrics
                    ],
                    "insights": s.insights,
                }
                for s in analysis.content_summary
            ],
            "key_takeaways": [
                {
                    "category": t.category,
                    "statement": t.statement,
                    "evidence": t.evidence,
                    "significance": t.significance,
                }
                for t in analysis.key_takeaways
            ],
            "charts_analysis": [
                {"figure_id": c.figure_id, "type": c.type, "analysis": c.analysis}
                for c in analysis.charts_analysis
            ],
        }

        # 准备研究结果
        research_json = {}
        if research:
            research_json = {
                "queries": [
                    {
                        "query": q.query_text,
                        "source_gap": q.source_gap,
                        "results": [
                            {
                                "title": r.title,
                                "url": r.url,
                                "content": r.content[:500],  # 截断过长内容
                            }
                            for r in q.results[:3]  # 每个query取前3条结果
                        ],
                    }
                    for q in research.queries
                ],
                "summary_by_gap": research.summary_by_gap,
            }

        # 使用外部提示词模板
        return get_report_generation_prompt(
            analysis_json=json.dumps(analysis_json, ensure_ascii=False, indent=2),
            research_json=json.dumps(research_json, ensure_ascii=False, indent=2) if research_json else "无补充数据",
            generated_at=datetime.now().isoformat(),
            report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            model=self.model,
        )

    def _extract_title(self, content: str) -> str:
        """从报告中提取标题"""
        import re

        # 尝试从YAML front matter提取
        yaml_match = re.search(r"^---\s*\ntitle:\s*(.+?)\n", content, re.MULTILINE)
        if yaml_match:
            return yaml_match.group(1).strip()

        # 尝试从第一个一级标题提取
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        return "未知标题"

    def _count_citations(self, content: str) -> dict:
        """统计报告中的引用"""
        import re

        # 统计脚注引用
        footnote_refs = re.findall(r"\[\^([\w-]+)\]", content)
        footnote_defs = re.findall(r"^\[\^([\w-]+)\]:", content, re.MULTILINE)

        # 按类型分类
        doc_refs = [ref for ref in footnote_defs if ref.startswith("doc-")]
        web_refs = [ref for ref in footnote_defs if ref.startswith("web-")]
        api_refs = [ref for ref in footnote_defs if ref.startswith("api-")]
        chart_refs = [ref for ref in footnote_defs if ref.startswith("fig-") or ref.startswith("chart-")]

        return {
            "total_count": len(set(footnote_refs)),
            "defined_count": len(set(footnote_defs)),
            "by_type": {
                "document": len(doc_refs),
                "web": len(web_refs),
                "api": len(api_refs),
                "chart_analysis": len(chart_refs),
            },
            "references": [{"id": ref_id} for ref_id in set(footnote_defs)],
        }
