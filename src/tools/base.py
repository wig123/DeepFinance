"""
Tool 基类和 ToolResult 定义
所有工具必须继承此基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, List
from datetime import datetime


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    source: str  # 数据来源标识
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "source": self.source,
            "error": self.error,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class Tool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称（唯一）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（供 LLM 选择）"""
        pass

    @property
    def parameters(self) -> dict:
        """JSON Schema 参数定义"""
        return {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具，返回结构化结果"""
        pass

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"


# 工具注册表
_TOOL_REGISTRY: dict[str, type[Tool]] = {}


def register_tool(tool_class: type[Tool]) -> type[Tool]:
    """装饰器：注册工具到全局注册表"""
    instance = tool_class()
    _TOOL_REGISTRY[instance.name] = tool_class
    return tool_class


def get_tool(name: str) -> Optional[type[Tool]]:
    """根据名称获取工具类"""
    return _TOOL_REGISTRY.get(name)


def list_tools() -> List[str]:
    """列出所有已注册的工具"""
    return list(_TOOL_REGISTRY.keys())


def get_all_tools() -> dict[str, type[Tool]]:
    """获取所有工具"""
    return _TOOL_REGISTRY.copy()
