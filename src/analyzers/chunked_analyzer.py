"""分块文档分析器

将大型文档按章节切分成多块，并行分析后合并结果。
解决长文档分析时 LLM 输出截断的问题。
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.models.report import (
    AnalysisResult,
    ChartAnalysis,
    ContentSection,
    DocumentMetadata,
    KeyTakeaway,
    SupplementaryResearchNeeds,
    TemporalUpdate,
    ComparativeData,
    DeepDiveAnalysis,
    MarketPerspective,
)
from src.prompts import get_chunk_analysis_prompt, get_merge_analysis_prompt
from .section_parser import SectionParser, Chunk

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class ChunkedDocumentAnalyzer:
    """分块文档分析器
    
    将文档按章节切分成多块，并行分析后合并结果。
    
    工作流程：
    1. 使用 SectionParser 将文档按 ## 标题切分成章节
    2. 将相邻章节聚合成块（保持语义完整）
    3. 并行调用 LLM 分析每个块
    4. 合并各块的 content_summary 和 charts_analysis
    5. 调用 LLM 生成全局的 document_metadata、key_takeaways、supplementary_research_needs
    
    Attributes:
        model: 使用的模型名称
        llm: LLM 实例
        section_parser: 章节解析器
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        target_chunk_size: int = 15000,
        min_chunks: int = 2,
        max_chunks: int = 6,
        min_doc_size_for_chunking: int = 20000,
    ):
        """初始化分块分析器
        
        Args:
            model: 模型名称
            temperature: 温度参数
            target_chunk_size: 目标块大小（字符数）
            min_chunks: 最少分块数
            max_chunks: 最多分块数
            min_doc_size_for_chunking: 触发分块的最小文档大小
        """
        self.model = model
        self.temperature = temperature
        
        # 初始化章节解析器
        self.section_parser = SectionParser(
            target_chunk_size=target_chunk_size,
            min_chunks=min_chunks,
            max_chunks=max_chunks,
            min_doc_size_for_chunking=min_doc_size_for_chunking,
        )
        
        # 初始化 LLM
        if "gemini" in model.lower():
            self._init_gemini(model)
        elif "claude" in model.lower():
            self._init_claude(model)
        else:
            raise ValueError(f"不支持的模型: {model}")
    
    def _init_gemini(self, model: str):
        """初始化 Gemini 模型"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=self.temperature,
                max_output_tokens=16384,  # 分块后输出更小，16K 足够
                google_api_key=os.getenv("CLOSEAI_API_KEY"),
                client_options={"api_endpoint": "https://api.openai-proxy.org/google"},
                convert_system_message_to_human=True,
            )
            logger.info(f"已初始化 Gemini 模型（分块分析）: {model}")
        except ImportError:
            raise ImportError(
                "需要安装 langchain-google-genai: pip install langchain-google-genai"
            )
    
    def _init_claude(self, model: str):
        """初始化 Claude 模型"""
        try:
            from langchain_anthropic import ChatAnthropic
            
            self.llm = ChatAnthropic(
                model=model,
                temperature=self.temperature,
                timeout=120.0,
                max_retries=2,
            )
            logger.info(f"已初始化 Claude 模型（分块分析）: {model}")
        except ImportError:
            raise ImportError(
                "需要安装 langchain-anthropic: pip install langchain-anthropic"
            )
    
    def analyze(self, source_dir: Path, user_query: str | None = None) -> AnalysisResult:
        """分析文档（同步入口）
        
        Args:
            source_dir: 解析后的文档目录
            user_query: 用户侧重点描述
            
        Returns:
            AnalysisResult: 分析结果
        """
        # 检查是否已在事件循环中运行
        try:
            loop = asyncio.get_running_loop()
            # 如果在事件循环中，使用 nest_asyncio 或创建新线程
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self.analyze_async(source_dir, user_query))
        except RuntimeError:
            # 没有运行中的事件循环，直接创建
            return asyncio.run(self.analyze_async(source_dir, user_query))
    
    async def analyze_async(self, source_dir: Path, user_query: str | None = None) -> AnalysisResult:
        """分析文档（异步）
        
        Args:
            source_dir: 解析后的文档目录
            user_query: 用户侧重点描述
            
        Returns:
            AnalysisResult: 分析结果
        """
        logger.info(f"开始分块分析文档: {source_dir}")
        if user_query:
            logger.info(f"用户侧重点: {user_query}")
        
        # 1. 读取文档内容和元数据
        content_path = source_dir / "content.md"
        metadata_path = source_dir / "metadata.json"
        
        if not content_path.exists():
            raise FileNotFoundError(f"找不到文档内容: {content_path}")
        
        content = content_path.read_text(encoding="utf-8")
        logger.info(f"已读取文档内容: {len(content)} 字符")
        
        metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            logger.info(f"已读取元数据: {len(metadata.get('figures', []))} 个图表")
        
        # 2. 按章节切分文档
        chunks = self.section_parser.parse_and_chunk(content)
        
        if len(chunks) == 1:
            logger.info("文档较小，无需分块，使用单次分析")
            # 对于小文档，仍然使用分块逻辑但只有一块
        
        logger.info(f"文档切分为 {len(chunks)} 个块")
        
        # 3. 并行分析各块
        chunk_results = await self._analyze_chunks_parallel(
            chunks, metadata, user_query
        )
        
        # 4. 合并结果
        merged_result = await self._merge_chunk_results(
            chunk_results, metadata, source_dir, content
        )
        
        return merged_result
    
    async def _analyze_chunks_parallel(
        self,
        chunks: list[Chunk],
        metadata: dict,
        user_query: str | None,
    ) -> list[dict]:
        """并行分析各块
        
        Args:
            chunks: 块列表
            metadata: 文档元数据
            user_query: 用户侧重点
            
        Returns:
            各块的分析结果列表
        """
        total_chunks = len(chunks)
        
        async def analyze_single_chunk(chunk: Chunk) -> dict:
            """分析单个块"""
            chunk_index = chunk.chunk_index + 1  # 从 1 开始展示
            
            logger.info(
                f"分析块 {chunk_index}/{total_chunks}: "
                f"{chunk.char_count} 字符, {len(chunk.sections)} 章节"
            )
            
            # 构建 prompt
            prompt = self._build_chunk_prompt(
                chunk, total_chunks, metadata, user_query
            )
            
            # 调用 LLM（使用 asyncio.to_thread 包装同步调用）
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            response_text = self._extract_response_text(response)
            
            logger.info(f"块 {chunk_index} 分析完成，响应 {len(response_text)} 字符")
            
            # 解析 JSON
            result = self._parse_llm_response(response_text)
            result["_chunk_index"] = chunk.chunk_index
            result["_page_range"] = (chunk.start_page, chunk.end_page)
            
            return result
        
        # 并行执行
        tasks = [analyze_single_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"块 {i+1} 分析失败: {result}")
                # 返回空结果
                valid_results.append({
                    "_chunk_index": i,
                    "content_summary": [],
                    "charts_analysis": [],
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    def _build_chunk_prompt(
        self,
        chunk: Chunk,
        total_chunks: int,
        metadata: dict,
        user_query: str | None,
    ) -> str:
        """构建分块分析 prompt"""
        # 章节标题列表
        section_titles = "\n".join(
            f"- {title}" for title in chunk.section_titles
        )
        
        # 页码范围
        page_range = f"第 {chunk.start_page or '?'} - {chunk.end_page or '?'} 页"
        
        # 图表信息（只包含本块的图表）
        figures_summary = ""
        if metadata.get("figures") and chunk.figures:
            figures_summary = "\n本部分包含的图表:\n"
            for fig in metadata["figures"]:
                if fig.get("filename") in chunk.figures:
                    fig_type = fig.get("image_type", "unknown")
                    figures_summary += f"- {fig.get('filename')}: {fig_type}"
                    if fig.get("analysis"):
                        figures_summary += " (已有AI分析)"
                    figures_summary += "\n"
        
        # 用户侧重点
        user_focus = ""
        if user_query:
            user_focus = f"""
**用户特别关注**：
{user_query}

请在分析时侧重以上方面。
"""
        
        return get_chunk_analysis_prompt(
            chunk_index=chunk.chunk_index + 1,
            total_chunks=total_chunks,
            section_titles=section_titles,
            page_range=page_range,
            figures_summary=figures_summary,
            user_focus=user_focus,
            content=chunk.content,
        )
    
    async def _merge_chunk_results(
        self,
        chunk_results: list[dict],
        metadata: dict,
        source_dir: Path,
        content: str,
    ) -> AnalysisResult:
        """合并各块结果并生成全局信息
        
        Args:
            chunk_results: 各块的分析结果
            metadata: 文档元数据
            source_dir: 源文档目录
            content: 原始文档内容
            
        Returns:
            AnalysisResult: 最终分析结果
        """
        logger.info("开始合并各块分析结果...")
        
        # 1. 拼接 content_summary
        merged_content_summary = []
        
        # 按 chunk_index 排序
        sorted_results = sorted(chunk_results, key=lambda x: x.get("_chunk_index", 0))
        
        for result in sorted_results:
            # 合并内容摘要
            for section in result.get("content_summary", []):
                try:
                    merged_content_summary.append(ContentSection(**section))
                except Exception as e:
                    logger.warning(f"解析 content_section 失败: {e}")
        
        # 2. 从 metadata 中提取图表分析（图表分析在解析阶段已完成）
        merged_charts_analysis = self._extract_charts_from_metadata(metadata)
        
        logger.info(
            f"合并完成: {len(merged_content_summary)} 个章节摘要, "
            f"{len(merged_charts_analysis)} 个图表分析"
        )
        
        # 2. 调用 LLM 生成全局信息
        global_info = await self._generate_global_info(
            merged_content_summary, metadata
        )
        
        # 3. 构造最终结果
        analysis_id = f"chunked_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 解析全局信息
        doc_metadata_data = global_info.get("document_metadata", {})
        document_metadata = DocumentMetadata(**doc_metadata_data)
        
        key_takeaways = [
            self._normalize_key_takeaway(t)
            for t in global_info.get("key_takeaways", [])
        ]
        
        research_needs_data = global_info.get("supplementary_research_needs", {})
        supplementary_research_needs = SupplementaryResearchNeeds(
            temporal_updates=[
                TemporalUpdate(**item)
                for item in research_needs_data.get("temporal_updates", [])
            ],
            comparative_data=[
                ComparativeData(**item)
                for item in research_needs_data.get("comparative_data", [])
            ],
            deep_dive_analysis=[
                DeepDiveAnalysis(**item)
                for item in research_needs_data.get("deep_dive_analysis", [])
            ],
            market_perspectives=[
                MarketPerspective(**item)
                for item in research_needs_data.get("market_perspectives", [])
            ],
        )
        
        result = AnalysisResult(
            analysis_id=analysis_id,
            source_document={
                "path": str(source_dir),
                "content_length": len(content),
                "figures_count": len(metadata.get("figures", [])),
                "pages": metadata.get("page_count", 0),
                "chunks_analyzed": len(chunk_results),
            },
            document_metadata=document_metadata,
            content_summary=merged_content_summary,
            key_takeaways=key_takeaways,
            supplementary_research_needs=supplementary_research_needs,
            charts_analysis=merged_charts_analysis,
        )
        
        # 统计
        total_research_needs = (
            len(supplementary_research_needs.temporal_updates)
            + len(supplementary_research_needs.comparative_data)
            + len(supplementary_research_needs.deep_dive_analysis)
            + len(supplementary_research_needs.market_perspectives)
        )
        
        logger.info(
            f"分块分析完成: {len(merged_content_summary)} 个章节, "
            f"{len(key_takeaways)} 个要点, "
            f"{total_research_needs} 个补充研究需求"
        )
        
        return result
    
    async def _generate_global_info(
        self,
        content_summary: list[ContentSection],
        metadata: dict,
    ) -> dict:
        """生成全局信息（document_metadata, key_takeaways, supplementary_research_needs）
        
        Args:
            content_summary: 合并后的内容摘要
            metadata: 文档元数据
            
        Returns:
            全局信息字典
        """
        logger.info("生成全局信息（元数据、要点、研究需求）...")
        
        # 构建合并后的内容摘要文本
        summaries_text = ""
        for section in content_summary:
            summaries_text += f"\n### {section.section_title}\n"
            summaries_text += f"{section.content}\n"
            if section.key_metrics:
                summaries_text += "\n**关键指标**:\n"
                for metric in section.key_metrics:
                    summaries_text += (
                        f"- {metric.metric}: {metric.current_value} "
                        f"({metric.change or 'N/A'})\n"
                    )
            if section.insights:
                summaries_text += "\n**洞察**:\n"
                for insight in section.insights:
                    summaries_text += f"- {insight}\n"
        
        # 构建 prompt
        prompt = get_merge_analysis_prompt(
            pages=metadata.get("page_count", "未知"),
            figures_count=len(metadata.get("figures", [])),
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            merged_content_summaries=summaries_text,
        )
        
        # 调用 LLM
        response = await asyncio.to_thread(self.llm.invoke, prompt)
        response_text = self._extract_response_text(response)
        
        logger.info(f"全局信息生成完成，响应 {len(response_text)} 字符")
        
        return self._parse_llm_response(response_text)
    
    def _extract_response_text(self, response: Any) -> str:
        """从 LLM 响应中提取文本"""
        response_text = response.content
        
        # 处理 Gemini 返回的 list 格式
        if isinstance(response_text, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response_text
            )
        
        return response_text
    
    def _parse_llm_response(self, response_text: str) -> dict:
        """解析 LLM 返回的 JSON"""
        response_text = response_text.strip()
        
        # 去除 markdown 代码块标记
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"原始响应: {response_text[:500]}...")
            
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # 返回空结构
            return {
                "content_summary": [],
                "charts_analysis": [],
                "document_metadata": {
                    "document_type": "unknown",
                    "company": "Unknown",
                    "period": "Unknown",
                    "publish_date": None,
                    "key_topics": [],
                },
                "key_takeaways": [],
                "supplementary_research_needs": {
                    "temporal_updates": [],
                    "comparative_data": [],
                    "deep_dive_analysis": [],
                    "market_perspectives": [],
                },
            }
    
    def _normalize_key_takeaway(self, takeaway_data: dict) -> KeyTakeaway:
        """标准化关键要点数据"""
        if "sources" in takeaway_data:
            sources = takeaway_data["sources"]
            normalized_sources = []
            
            if isinstance(sources, str):
                normalized_sources = [{"id": "source", "location": sources}]
            elif isinstance(sources, list):
                for source in sources:
                    if isinstance(source, str):
                        normalized_sources.append({"id": "source", "location": source})
                    elif isinstance(source, dict):
                        normalized_sources.append(source)
            
            takeaway_data["sources"] = normalized_sources
        
        return KeyTakeaway(**takeaway_data)
    
    def _normalize_chart_analysis(self, chart_data: dict) -> ChartAnalysis:
        """标准化图表分析数据"""
        if "analysis" in chart_data and isinstance(chart_data["analysis"], dict):
            normalized_analysis = {}
            for key, value in chart_data["analysis"].items():
                if isinstance(value, list):
                    normalized_analysis[key] = "\n".join(str(item) for item in value)
                else:
                    normalized_analysis[key] = str(value)
            chart_data["analysis"] = normalized_analysis
        
        return ChartAnalysis(**chart_data)
    
    def _extract_charts_from_metadata(self, metadata: dict) -> list[ChartAnalysis]:
        """从 metadata 中提取图表分析
        
        图表分析在解析阶段由 ImageAnalyzer 完成，存储在 metadata.json 的 figures 字段中。
        此方法将其转换为 ChartAnalysis 格式。
        
        Args:
            metadata: 文档元数据
            
        Returns:
            ChartAnalysis 列表
        """
        charts_analysis = []
        figures = metadata.get("figures", [])
        
        for fig in figures:
            # 跳过装饰性图标
            image_type = fig.get("image_type", "unknown")
            if image_type == "icon":
                continue
            
            chart_data = {
                "figure_id": fig.get("id", f"fig_{fig.get('filename', 'unknown')}"),
                "type": image_type,
                "title": fig.get("caption", ""),
            }
            
            # 如果有 AI 分析结果
            if fig.get("analysis"):
                chart_data["analysis"] = fig["analysis"]
            
            # 如果是插图，有描述
            if fig.get("description"):
                chart_data["description"] = fig["description"]
            
            try:
                charts_analysis.append(self._normalize_chart_analysis(chart_data))
            except Exception as e:
                logger.warning(f"解析图表分析失败 ({fig.get('id')}): {e}")
        
        logger.info(f"从 metadata 提取 {len(charts_analysis)} 个图表分析（排除 {len(figures) - len(charts_analysis)} 个图标）")
        return charts_analysis
