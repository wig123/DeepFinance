"""
宏观经济数据工具模块

提供统一接口获取宏观经济指标数据，包括：
- GDP
- CPI/PPI
- 利率/汇率
"""

from .base_macro import MacroTool, MacroIndicator
from .akshare_macro import AKShareMacroTool

__all__ = ["MacroTool", "MacroIndicator", "AKShareMacroTool"]
