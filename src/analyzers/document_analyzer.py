"""文档分析器

使用长上下文LLM（Gemini/Claude）对解析后的文档进行初步分析。
"""

import json
import logging
from datetime import datetime
from pathlib import Path

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
from src.prompts import get_document_analysis_prompt

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class DocumentAnalyzer:
    """文档分析器

    读取解析后的文档，使用长上下文LLM进行分析：
    1. 生成执行摘要
    2. 提取核心发现（带引用）
    3. 识别信息缺口
    4. 汇总图表分析

    Attributes:
        model: 使用的模型名称（gemini/claude）
        llm: LLM实例
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
    ):
        """初始化分析器

        Args:
            model: 模型名称，支持：
                - gemini-2.0-flash: Google Gemini（推荐，长上下文+低成本）
                - claude-sonnet-4-5-20250929: Anthropic Claude
            temperature: 温度参数（0-1），越低越确定性
        """
        self.model = model
        self.temperature = temperature

        # 根据模型类型初始化LLM
        if "gemini" in model.lower():
            self._init_gemini(model)
        elif "claude" in model.lower():
            self._init_claude(model)
        else:
            raise ValueError(f"不支持的模型: {model}")

    def _init_gemini(self, model: str):
        """初始化Gemini模型（通过CloseAI的Google Genai接口）"""
        import os
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as e:
            raise ImportError(
                "需要安装 langchain-google-genai: pip install langchain-google-genai"
            ) from e

        # 使用CloseAI的Google Genai接口
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=self.temperature,
            max_output_tokens=32768,  # 增加到 32K 避免截断
            google_api_key=os.getenv("CLOSEAI_API_KEY"),
            client_options={"api_endpoint": "https://api.openai-proxy.org/google"},
            convert_system_message_to_human=True,
        )
        logger.info(f"已初始化Gemini模型（通过CloseAI）: {model}")

    def _init_claude(self, model: str):
        """初始化Claude模型"""
        try:
            from langchain_anthropic import ChatAnthropic

            self.llm = ChatAnthropic(
                model=model,
                temperature=self.temperature,
                timeout=120.0,
                max_retries=2,
            )
            logger.info(f"已初始化Claude模型: {model}")
        except ImportError:
            raise ImportError(
                "需要安装 langchain-anthropic: pip install langchain-anthropic"
            )

    def analyze(self, source_dir: Path, user_query: str | None = None) -> AnalysisResult:
        """分析文档

        Args:
            source_dir: 解析后的文档目录（包含 content.md 和 metadata.json）
            user_query: 用户侧重点描述（可选），如有则在分析时给予侧重

        Returns:
            AnalysisResult: 分析结果
        """
        logger.info(f"开始分析文档: {source_dir}")
        if user_query:
            logger.info(f"用户侧重点: {user_query}")

        # 1. 读取文档内容
        content_path = source_dir / "content.md"
        metadata_path = source_dir / "metadata.json"

        if not content_path.exists():
            raise FileNotFoundError(f"找不到文档内容: {content_path}")

        content = content_path.read_text(encoding="utf-8")
        logger.info(f"已读取文档内容: {len(content)} 字符")

        # 读取元数据
        metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            logger.info(f"已读取元数据: {len(metadata.get('figures', []))} 个图表")

        # 2. 构造分析prompt
        prompt = self._build_analysis_prompt(content, metadata, user_query)

        # 3. 调用LLM
        logger.info(f"调用LLM进行分析 (模型: {self.model})...")
        response = self.llm.invoke(prompt)
        response_text = response.content

        # 处理不同模型返回格式（Gemini 3 返回 list）
        if isinstance(response_text, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in response_text
            )

        # 记录响应信息用于调试
        logger.info(f"LLM响应长度: {len(response_text)} 字符")
        if hasattr(response, 'response_metadata'):
            finish_reason = response.response_metadata.get('finish_reason', 'unknown')
            logger.info(f"LLM完成原因: {finish_reason}")
            if finish_reason == 'MAX_TOKENS':
                logger.warning("响应被截断！考虑增加 max_output_tokens")

        # 4. 解析JSON结果
        logger.info("解析LLM返回结果...")
        analysis_data = self._parse_llm_response(response_text)

        # 5. 构造AnalysisResult（新版结构）
        analysis_id = f"source_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 5.1 文档元信息
        doc_metadata_data = analysis_data.get("document_metadata", {})
        document_metadata = DocumentMetadata(**doc_metadata_data)

        # 5.2 完整内容总结
        content_summary = [
            ContentSection(**section)
            for section in analysis_data.get("content_summary", [])
        ]

        # 5.3 关键要点
        key_takeaways = [
            self._normalize_key_takeaway(takeaway)
            for takeaway in analysis_data.get("key_takeaways", [])
        ]

        # 5.4 补充研究需求（4个维度）
        research_needs_data = analysis_data.get("supplementary_research_needs", {})
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

        # 5.5 图表分析
        charts_analysis = [
            self._normalize_chart_analysis(chart)
            for chart in analysis_data.get("charts_analysis", [])
        ]

        result = AnalysisResult(
            analysis_id=analysis_id,
            source_document={
                "path": str(source_dir),
                "content_length": len(content),
                "figures_count": len(metadata.get("figures", [])),
                "pages": metadata.get("pages", 0),
            },
            document_metadata=document_metadata,
            content_summary=content_summary,
            key_takeaways=key_takeaways,
            supplementary_research_needs=supplementary_research_needs,
            charts_analysis=charts_analysis,
        )

        # 统计补充研究需求总数
        total_research_needs = (
            len(supplementary_research_needs.temporal_updates)
            + len(supplementary_research_needs.comparative_data)
            + len(supplementary_research_needs.deep_dive_analysis)
            + len(supplementary_research_needs.market_perspectives)
        )

        logger.info(
            f"分析完成: {len(content_summary)} 个章节, "
            f"{len(key_takeaways)} 个要点, "
            f"{total_research_needs} 个补充研究需求"
        )

        return result

    def _normalize_key_takeaway(self, takeaway_data: dict) -> KeyTakeaway:
        """标准化关键要点数据"""
        # 处理 sources 字段：可能是字符串或字符串列表，需要转为字典列表
        if "sources" in takeaway_data:
            sources = takeaway_data["sources"]
            normalized_sources = []

            if isinstance(sources, str):
                # 单个字符串，转为字典
                normalized_sources = [{"id": "source", "location": sources}]
            elif isinstance(sources, list):
                for source in sources:
                    if isinstance(source, str):
                        # 字符串，转为字典
                        normalized_sources.append({"id": "source", "location": source})
                    elif isinstance(source, dict):
                        # 已经是字典，直接使用
                        normalized_sources.append(source)

            takeaway_data["sources"] = normalized_sources

        return KeyTakeaway(**takeaway_data)

    def _normalize_chart_analysis(self, chart_data: dict) -> ChartAnalysis:
        """标准化图表分析数据（处理LLM返回的列表类型）"""
        # 如果analysis字段存在且是字典，检查其中的值
        if "analysis" in chart_data and isinstance(chart_data["analysis"], dict):
            normalized_analysis = {}
            for key, value in chart_data["analysis"].items():
                if isinstance(value, list):
                    # 将列表转换为字符串（用换行连接）
                    normalized_analysis[key] = "\n".join(str(item) for item in value)
                else:
                    normalized_analysis[key] = str(value)
            chart_data["analysis"] = normalized_analysis

        return ChartAnalysis(**chart_data)

    def _build_analysis_prompt(self, content: str, metadata: dict, user_query: str | None = None) -> str:
        """构造分析提示词"""

        # 提取图表信息
        figures_summary = ""
        if metadata.get("figures"):
            figures_summary = "\n\n图表列表:\n"
            for fig in metadata["figures"]:
                fig_type = fig.get("image_type", "unknown")
                figures_summary += f"- {fig.get('filename', 'unknown')}: {fig_type}"
                if fig.get("analysis"):
                    figures_summary += " (已有AI分析)"
                figures_summary += "\n"

        # 构建用户侧重点提示
        user_focus = ""
        if user_query:
            user_focus = f"""
**用户特别关注**：
{user_query}

请在分析时侧重以上方面，在相关章节中提供更详细的数据、洞察和解读。
"""

        # 使用外部提示词模板
        return get_document_analysis_prompt(
            pages=metadata.get('pages', '未知'),
            figures_count=len(metadata.get('figures', [])),
            figures_summary=figures_summary,
            user_focus=user_focus,
            content=content,
        )

    def _parse_llm_response(self, response_text: str) -> dict:
        """解析LLM返回的JSON"""
        # 去除可能的markdown代码块标记
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        try:
            data = json.loads(response_text)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始响应: {response_text[:500]}...")

            # 尝试提取JSON部分
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    logger.warning("从响应中提取JSON成功")
                    return data
                except json.JSONDecodeError:
                    pass

            # 返回完整的空结构（包含所有必需字段）
            logger.error("无法解析LLM响应，返回空结构")
            return {
                "document_metadata": {
                    "document_type": "unknown",
                    "company": "Unknown",
                    "period": "Unknown",
                    "publish_date": None,
                    "key_topics": []
                },
                "content_summary": [],
                "key_findings": [],
                "information_gaps": [],
                "charts_analysis": [],
            }
