"""数据研究器

并行查询外部数据源（Web搜索 + 金融API）以补充文档分析中的信息缺口。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

from src.models.report import (
    QueryResult,
    ResearchResult,
    SearchResult,
    SupplementaryResearchNeeds,
)
from src.tools.web import SearchFactory

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class DataResearcher:
    """数据研究器

    功能:
    1. 并行执行web搜索
    2. 智能识别是否需要调用金融API
    3. 汇总研究结果

    Attributes:
        search_engine: 搜索引擎类型（tavily/serper）
        max_concurrent: 最大并发数
    """

    def __init__(
        self,
        search_engine: str = "tavily",
        max_concurrent: int = 10,
    ):
        """初始化研究器

        Args:
            search_engine: 搜索引擎类型（tavily/serper）
            max_concurrent: 最大并发查询数
        """
        self.search_engine = search_engine
        self.max_concurrent = max_concurrent

        # 创建搜索工具
        try:
            self.searcher = SearchFactory.create(search_engine)
            logger.info(f"已初始化搜索工具: {search_engine}")
        except Exception as e:
            logger.error(f"初始化搜索工具失败: {e}")
            raise

    async def research(
        self,
        research_needs: SupplementaryResearchNeeds,
        analysis_id: str,
    ) -> ResearchResult:
        """执行研究（新版：处理4个维度的补充研究需求）

        Args:
            research_needs: 补充研究需求（包含4个维度）
            analysis_id: 关联的分析ID

        Returns:
            ResearchResult: 研究结果
        """
        # 统计需求总数
        total_needs = (
            len(research_needs.temporal_updates)
            + len(research_needs.comparative_data)
            + len(research_needs.deep_dive_analysis)
            + len(research_needs.market_perspectives)
        )
        logger.info(f"开始研究 {total_needs} 个补充研究需求...")

        # 1. 从4个维度收集所有查询
        all_queries = []

        # 1.1 时效性补充
        for item in research_needs.temporal_updates:
            for query_text in item.search_queries:
                logger.info(f"[{item.id}] 查询: {query_text}")
                all_queries.append(
                    {
                        "gap_id": item.id,
                        "query_text": query_text,
                        "priority": item.priority,
                        "dimension": "temporal_updates",
                    }
                )

        # 1.2 对比信息
        for item in research_needs.comparative_data:
            for query_text in item.search_queries:
                logger.info(f"[{item.id}] 查询: {query_text}")
                all_queries.append(
                    {
                        "gap_id": item.id,
                        "query_text": query_text,
                        "priority": "medium",
                        "dimension": "comparative_data",
                    }
                )

        # 1.3 深度分析
        for item in research_needs.deep_dive_analysis:
            for query_text in item.search_queries:
                logger.info(f"[{item.id}] 查询: {query_text}")
                all_queries.append(
                    {
                        "gap_id": item.id,
                        "query_text": query_text,
                        "priority": "medium",
                        "dimension": "deep_dive_analysis",
                    }
                )

        # 1.4 市场观点
        for item in research_needs.market_perspectives:
            for query_text in item.search_queries:
                logger.info(f"[{item.id}] 查询: {query_text}")
                all_queries.append(
                    {
                        "gap_id": item.id,
                        "query_text": query_text,
                        "priority": "low",
                        "dimension": "market_perspectives",
                    }
                )

        logger.info(f"共 {len(all_queries)} 个查询待执行")

        # 2. 并行执行查询
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = [self._execute_query(q, semaphore) for q in all_queries]
        query_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. 处理结果
        successful_results = []
        failed_count = 0

        for i, result in enumerate(query_results):
            if isinstance(result, Exception):
                logger.error(f"查询失败 [{all_queries[i]['query_text']}]: {result}")
                failed_count += 1
            elif result:
                successful_results.append(result)

        logger.info(f"查询完成: {len(successful_results)} 成功, {failed_count} 失败")

        # 4. 按研究需求汇总
        summary_by_gap = self._summarize_by_gap(research_needs, successful_results)

        # 5. 构造研究结果
        research_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = ResearchResult(
            research_id=research_id,
            related_analysis=analysis_id,
            queries=successful_results,
            summary_by_gap=summary_by_gap,
        )

        return result

    async def _execute_query(self, query_info: dict, semaphore: asyncio.Semaphore) -> QueryResult | None:
        """执行单个查询（带并发控制）"""
        async with semaphore:
            gap_id = query_info["gap_id"]
            query_text = query_info["query_text"]

            logger.info(f"[{gap_id}] 查询: {query_text}")

            try:
                # 执行web搜索
                search_result = await self.searcher.execute(query=query_text)

                if not search_result.success:
                    logger.warning(f"搜索失败: {search_result.error}")
                    return None

                # 转换为SearchResult列表
                results = []
                for item in search_result.data:
                    results.append(
                        SearchResult(
                            source="web_search",
                            title=item.get("title"),
                            url=item.get("url"),
                            content=item.get("content", ""),
                            relevance_score=item.get("score"),
                        )
                    )

                # TODO: 智能判断是否需要调用金融API
                # 如果query包含股票代码、财报关键词等，可以补充调用金融API
                financial_results = await self._try_financial_api(query_text)
                results.extend(financial_results)

                query_id = f"{gap_id}-query-{len(results)}"

                return QueryResult(
                    query_id=query_id,
                    query_text=query_text,
                    source_gap=gap_id,
                    results=results,
                )

            except Exception as e:
                logger.error(f"查询异常 [{query_text}]: {e}")
                return None

    async def _try_financial_api(self, query_text: str) -> list[SearchResult]:
        """尝试调用金融API获取补充数据

        根据query内容智能判断是否需要调用金融API。
        例如：如果query包含股票代码、"财报"、"股价"等关键词，则调用相应API。
        """
        results = []

        # TODO: 实现智能识别逻辑
        # 1. 正则提取股票代码
        # 2. 识别关键词（财报、股价、估值等）
        # 3. 调用对应的金融API
        # 4. 转换为SearchResult格式

        # 示例实现（简化版）
        import re

        # 提取可能的股票代码
        # A股: 6位数字
        # 美股: 大写字母
        stock_codes = re.findall(r"\b[A-Z]{1,5}\b|\b\d{6}\b", query_text)

        if stock_codes and any(
            keyword in query_text
            for keyword in ["股价", "财报", "业绩", "营收", "利润", "市值"]
        ):
            logger.info(f"检测到股票相关查询，尝试调用金融API: {stock_codes}")

            # 这里可以调用 get_company_info, get_financial_report 等
            # 暂时返回空，后续补充
            pass

        return results

    def _summarize_by_gap(
        self, research_needs: SupplementaryResearchNeeds, query_results: list[QueryResult]
    ) -> dict[str, Any]:
        """按研究需求汇总结果（新版：处理4个维度）"""
        summary = {}

        # 收集所有需求的ID
        all_need_ids = []
        all_need_ids.extend([item.id for item in research_needs.temporal_updates])
        all_need_ids.extend([item.id for item in research_needs.comparative_data])
        all_need_ids.extend([item.id for item in research_needs.deep_dive_analysis])
        all_need_ids.extend([item.id for item in research_needs.market_perspectives])

        for need_id in all_need_ids:
            # 找到该需求的所有查询结果
            need_queries = [qr for qr in query_results if qr.source_gap == need_id]

            # 统计
            total_results = sum(len(qr.results) for qr in need_queries)
            answered = total_results > 0

            # 提取关键发现（简化版：取前3条结果的标题）
            key_findings = []
            for qr in need_queries[:3]:  # 只取前3个查询
                for result in qr.results[:2]:  # 每个查询取前2条结果
                    if result.title:
                        key_findings.append(result.title)

            summary[need_id] = {
                "answered": answered,
                "confidence": "high" if total_results >= 3 else "medium" if total_results > 0 else "low",
                "key_findings": key_findings[:5],  # 最多5条
                "sources_count": total_results,
                "queries_count": len(need_queries),
            }

        return summary
