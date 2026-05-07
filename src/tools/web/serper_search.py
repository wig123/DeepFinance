"""
Serper 搜索 API 适配器。

Serper 提供 Google 搜索结果 API。
API 文档: https://serper.dev/
"""

import aiohttp
import asyncio
from typing import Optional, Literal

from ..base import ToolResult, register_tool
from .base_search import SearchTool, SearchResult, SearchFactory


@register_tool
class SerperSearchTool(SearchTool):
    """Serper (Google 搜索) API 适配器。"""

    ENGINE_NAME = "serper"
    API_ENDPOINT = "https://google.serper.dev/search"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化 Serper 搜索工具。

        Args:
            api_key: Serper API 密钥。若为 None，从配置加载。
            timeout: 请求超时时间（秒）。
        """
        super().__init__(api_key=api_key, timeout=timeout)

    @property
    def name(self) -> str:
        return "serper_search"

    @property
    def description(self) -> str:
        return "使用 Serper (Google) 搜索引擎进行网页搜索，返回结构化结果"

    async def execute(
        self,
        query: str = "",
        max_results: int = 10,
        search_type: Literal["search", "news", "images"] = "search",
        country: str = "cn",
        language: str = "zh-cn",
        **kwargs
    ) -> ToolResult:
        """
        执行 Serper 搜索。

        Args:
            query: 搜索关键词。
            max_results: 最大结果数 (1-100)。
            search_type: 搜索类型 - "search", "news" 或 "images"。
            country: 国家代码 (如 "cn", "us")。
            language: 语言代码 (如 "zh-cn", "en")。
            **kwargs: 传递给 Serper API 的其他参数。

        Returns:
            ToolResult: 搜索结果或错误。
        """
        if not query.strip():
            return self._create_error_result("查询关键词不能为空")

        # 限制 max_results 范围
        max_results = max(1, min(100, max_results))

        # 根据搜索类型选择 endpoint
        endpoint = self.API_ENDPOINT
        if search_type == "news":
            endpoint = "https://google.serper.dev/news"
        elif search_type == "images":
            endpoint = "https://google.serper.dev/images"

        payload = {
            "q": query,
            "num": max_results,
            "gl": country,
            "hl": language,
        }

        # 添加额外参数
        payload.update(kwargs)

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return self._create_error_result(
                            f"Serper API 错误 ({response.status}): {error_text}"
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

        # 根据搜索类型解析结果
        results = []

        if search_type == "search":
            # 常规搜索结果
            for item in data.get("organic", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")
                ))
        elif search_type == "news":
            # 新闻结果
            for item in data.get("news", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")
                ))
        elif search_type == "images":
            # 图片结果
            for item in data.get("images", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("imageUrl", "")  # 用图片 URL 作为 snippet
                ))

        return self._create_success_result(results)


# 注册到工厂
SearchFactory.register("serper", SerperSearchTool)
