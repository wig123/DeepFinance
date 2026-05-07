"""
网页搜索工具模块。

提供统一接口的多搜索引擎适配器。

使用示例:
    from src.tools.web import SearchFactory

    # 创建搜索工具
    searcher = SearchFactory.create("tavily")

    # 执行搜索
    result = await searcher.execute(query="Python async programming")

    if result.success:
        for item in result.data:
            print(f"- {item['title']}: {item['url']}")
"""

from .base_search import (
    SearchTool,
    SearchResult,
    SearchFactory,
)
from .tavily_search import TavilySearchTool
from .serper_search import SerperSearchTool


__all__ = [
    # 基类
    "SearchTool",
    "SearchResult",
    "SearchFactory",
    # 实现
    "TavilySearchTool",
    "SerperSearchTool",
]
