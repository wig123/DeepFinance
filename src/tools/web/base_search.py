"""
搜索工具基类。

提供统一接口的多搜索引擎适配器基类。
"""

import os
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import yaml

from ..base import Tool, ToolResult, register_tool


@dataclass
class SearchResult:
    """单条搜索结果。"""
    title: str
    url: str
    snippet: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet
        }


class SearchTool(Tool):
    """
    搜索工具抽象基类。

    所有搜索引擎适配器必须继承此类并实现 execute 方法。
    """

    # 引擎标识符
    ENGINE_NAME: str = "base"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化搜索工具。

        Args:
            api_key: API 密钥。若为 None，从配置文件加载。
            timeout: 请求超时时间（秒）。
        """
        self._api_key = api_key
        self._timeout = timeout

        # 如未提供 api_key，从配置加载
        if self._api_key is None:
            self._load_config()

    def _load_config(self) -> None:
        """加载 API 密钥：优先环境变量，回退 config.yaml。"""
        # 优先环境变量（推荐方式，避免明文入仓）
        env_var = f"{self.ENGINE_NAME.upper()}_API_KEY"
        env_key = os.environ.get(env_var)

        config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
        engine_config: dict = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            engine_config = config.get("web_search", {}).get(self.ENGINE_NAME, {})

        self._api_key = env_key or engine_config.get("api_key")

        if engine_config.get("timeout"):
            self._timeout = engine_config["timeout"]

        if not self._api_key:
            # 不抛异常：允许在未配置 key 的环境下 import / 注册工具，
            # 实际调用 search() 时再由各子类自然抛出鉴权错误。
            import logging
            logging.getLogger(__name__).warning(
                "未找到 %s 的 API key（环境变量 %s 或 config.yaml）。"
                "调用搜索时将失败。",
                self.ENGINE_NAME, env_var,
            )

    @property
    def api_key(self) -> str:
        """获取 API 密钥。"""
        return self._api_key

    @property
    def timeout(self) -> int:
        """获取超时时间。"""
        return self._timeout

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称（唯一）。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（供 LLM 选择）。"""
        pass

    @property
    def parameters(self) -> dict:
        """JSON Schema 参数定义。"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 10
                }
            },
            "required": ["query"]
        }

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行搜索查询。

        Args:
            query: 搜索关键词。
            max_results: 最大结果数。
            **kwargs: 其他引擎特定参数。

        Returns:
            ToolResult: 搜索结果或错误。
        """
        pass

    def _create_success_result(
        self,
        results: list[SearchResult]
    ) -> ToolResult:
        """创建成功的 ToolResult。"""
        return ToolResult(
            success=True,
            data=[r.to_dict() for r in results],
            source=self.ENGINE_NAME
        )

    def _create_error_result(self, error: str) -> ToolResult:
        """创建错误的 ToolResult。"""
        return ToolResult(
            success=False,
            data=[],
            source=self.ENGINE_NAME,
            error=error
        )


class SearchFactory:
    """搜索引擎工厂类。"""

    _registry: dict[str, type[SearchTool]] = {}

    @classmethod
    def register(cls, engine_name: str, tool_class: type[SearchTool]) -> None:
        """注册搜索工具类。"""
        cls._registry[engine_name] = tool_class

    @classmethod
    def create(
        cls,
        engine: str = "tavily",
        api_key: Optional[str] = None,
        timeout: int = 30
    ) -> SearchTool:
        """
        创建搜索工具实例。

        Args:
            engine: 搜索引擎名称 ('tavily', 'serper' 等)
            api_key: 可选的 API key 覆盖。
            timeout: 请求超时时间（秒）。

        Returns:
            SearchTool 实例。

        Raises:
            ValueError: 如果引擎未注册。
        """
        if engine not in cls._registry:
            available = ", ".join(cls._registry.keys()) or "无"
            raise ValueError(
                f"未知搜索引擎: {engine}。可用: {available}"
            )

        return cls._registry[engine](api_key=api_key, timeout=timeout)

    @classmethod
    def available_engines(cls) -> list[str]:
        """获取可用搜索引擎列表。"""
        return list(cls._registry.keys())
