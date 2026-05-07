"""
Tavily 搜索 API 适配器。

Tavily 提供 AI 优化的搜索结果，支持高质量内容提取。
API 文档: https://docs.tavily.com/
"""

import aiohttp
import asyncio
from typing import Optional

from ..base import ToolResult, register_tool
from .base_search import SearchTool, SearchResult, SearchFactory


@register_tool
class TavilySearchTool(SearchTool):
    """Tavily 搜索 API 适配器。"""

    ENGINE_NAME = "tavily"
    API_ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化 Tavily 搜索工具。

        Args:
            api_key: Tavily API 密钥。若为 None，从配置加载。
            timeout: 请求超时时间（秒）。
        """
        super().__init__(api_key=api_key, timeout=timeout)

    @property
    def name(self) -> str:
        return "tavily_search"

    @property
    def description(self) -> str:
        return "使用 Tavily AI 搜索引擎进行网页搜索，返回结构化结果"

    async def execute(
        self,
        query: str = "",
        max_results: int = 10,
        search_depth: str = "basic",
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
        **kwargs
    ) -> ToolResult:
        """
        执行 Tavily 搜索。

        Args:
            query: 搜索关键词。
            max_results: 最大结果数 (1-20)。
            search_depth: "basic" 或 "advanced"。advanced 提供更详细结果。
            include_domains: 限定搜索的域名列表。
            exclude_domains: 排除的域名列表。
            **kwargs: 传递给 Tavily API 的其他参数。

        Returns:
            ToolResult: 搜索结果或错误。
        """
        if not query.strip():
            return self._create_error_result("查询关键词不能为空")

        # 限制 max_results 范围
        max_results = max(1, min(20, max_results))

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": False,
            "include_raw_content": False,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        # 添加额外参数
        payload.update(kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_ENDPOINT,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return self._create_error_result(
                            f"Tavily API 错误 ({response.status}): {error_text}"
                        )

                    data = await response.json()

        except asyncio.TimeoutError:
            return self._create_error_result(
                f"请求超时 ({self.timeout}s)"
            )
        except aiohttp.ClientError as e:
            return self._create_error_result(f"网络错误: {str(e)}")
        except Exception as e:
            return self._create_error_result(f"未知错误: {str(e)}")

        # 解析结果
        results = []
        for item in data.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", "")[:500]  # 截断过长内容
            ))

        return self._create_success_result(results)


# 注册到工厂
SearchFactory.register("tavily", TavilySearchTool)
