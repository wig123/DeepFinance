"""金融数据工具集

提供统一接口的金融数据获取，覆盖 A股/港股/美股。

数据源优先级：
1. AKShare (主力) - A股/港股/宏观数据
2. efinance (备用) - A股（东方财富）
3. yfinance (全球) - 美股/全球市场

使用示例：
    from src.tools.financial import get_stock_kline, get_company_info

    # 获取A股K线
    result = await get_stock_kline("600519", source="akshare")

    # 获取美股K线
    result = await get_stock_kline("AAPL", source="yfinance")

    # 自动选择数据源
    result = await get_stock_kline("600519")
"""

from typing import Optional, Literal, Union, List

from ..base import ToolResult

# 导入适配器
from .akshare_adapter import (
    AKShareKlineTool,
    AKShareCompanyInfoTool,
    AKShareFinancialTool,
    AKShareFinancialIndicatorTool,
)
from .efinance_adapter import (
    EfinanceKlineTool,
    EfinanceCompanyInfoTool,
    EfinanceCompanyPerformanceTool,
    EfinanceRealtimeTool,
)
from .yfinance_adapter import (
    YFinanceKlineTool,
    YFinanceCompanyInfoTool,
    YFinanceFinancialTool,
    YFinanceMultiDownloadTool,
)

# 导入缓存
from .cache import get_cache, FinancialCache

# 数据源类型
SourceType = Literal["akshare", "efinance", "yfinance", "auto"]


def _detect_market(symbol: str) -> str:
    """检测股票所属市场

    Returns:
        "cn" - A股
        "hk" - 港股
        "us" - 美股
        "unknown" - 未知
    """
    symbol = symbol.upper().strip()

    # 港股：以 .HK 结尾或纯数字4-5位
    if symbol.endswith(".HK"):
        return "hk"

    # A股：6位数字开头
    if symbol.isdigit() and len(symbol) == 6:
        return "cn"

    # 带交易所前缀的 A股
    for prefix in ["SH", "SZ", "BJ"]:
        if symbol.startswith(prefix) and symbol[2:].isdigit():
            return "cn"

    # 美股：字母组合
    if symbol.replace(".", "").replace("-", "").isalpha():
        return "us"

    return "unknown"


async def get_stock_kline(
    symbol: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "none",
    source: SourceType = "auto",
) -> ToolResult:
    """获取股票K线数据的统一接口

    Args:
        symbol: 股票代码
        period: K线周期 (daily/weekly/monthly)
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        adjust: 复权类型 (none/forward/backward)
        source: 数据源 (akshare/efinance/yfinance/auto)

    Returns:
        ToolResult: 统一格式的结果
    """
    # 自动检测数据源
    if source == "auto":
        market = _detect_market(symbol)
        if market == "cn":
            source = "akshare"
        elif market == "hk":
            source = "akshare"  # AKShare 也支持港股
        elif market == "us":
            source = "yfinance"
        else:
            source = "akshare"  # 默认尝试 AKShare

    # 调用对应适配器
    if source == "akshare":
        from .akshare_adapter import get_stock_kline as akshare_kline
        result = await akshare_kline(symbol, period, start_date, end_date, adjust)
        # 如果失败，尝试 efinance
        if not result.success:
            from .efinance_adapter import get_stock_kline as efinance_kline
            result = await efinance_kline(symbol, period, start_date, end_date)
        return result

    elif source == "efinance":
        from .efinance_adapter import get_stock_kline as efinance_kline
        return await efinance_kline(symbol, period, start_date, end_date)

    elif source == "yfinance":
        from .yfinance_adapter import get_stock_kline as yfinance_kline
        # yfinance 使用不同的参数格式
        yf_period = {
            "daily": "1y",
            "weekly": "2y",
            "monthly": "5y",
        }.get(period, "1y")
        yf_interval = {
            "daily": "1d",
            "weekly": "1wk",
            "monthly": "1mo",
        }.get(period, "1d")
        return await yfinance_kline(symbol, yf_period, yf_interval, start_date, end_date)

    else:
        return ToolResult(
            success=False,
            data=None,
            source="",
            error=f"不支持的数据源: {source}"
        )


async def get_company_info(
    symbol: str,
    source: SourceType = "auto",
) -> ToolResult:
    """获取公司基本信息的统一接口

    Args:
        symbol: 股票代码
        source: 数据源

    Returns:
        ToolResult: 统一格式的结果
    """
    if source == "auto":
        market = _detect_market(symbol)
        source = "yfinance" if market == "us" else "akshare"

    if source == "akshare":
        from .akshare_adapter import get_company_info as akshare_info
        result = await akshare_info(symbol)
        if not result.success:
            from .efinance_adapter import get_company_info as efinance_info
            result = await efinance_info(symbol)
        return result

    elif source == "efinance":
        from .efinance_adapter import get_company_info as efinance_info
        return await efinance_info(symbol)

    elif source == "yfinance":
        from .yfinance_adapter import get_company_info as yfinance_info
        return await yfinance_info(symbol)

    else:
        return ToolResult(
            success=False,
            data=None,
            source="",
            error=f"不支持的数据源: {source}"
        )


async def get_financial_report(
    symbol: str,
    report_type: str = "income",
    date: Optional[str] = None,
    quarterly: bool = False,
    source: SourceType = "auto",
) -> ToolResult:
    """获取财务报表的统一接口

    Args:
        symbol: 股票代码
        report_type: 报表类型 (income/balance/cashflow)
        date: 报告期 YYYYMMDD（仅 A股）
        quarterly: 是否季度报表（仅 yfinance）
        source: 数据源

    Returns:
        ToolResult: 统一格式的结果
    """
    if source == "auto":
        market = _detect_market(symbol)
        source = "yfinance" if market == "us" else "akshare"

    if source == "akshare":
        from .akshare_adapter import get_financial_report as akshare_report
        return await akshare_report(symbol, report_type, date)

    elif source == "yfinance":
        from .yfinance_adapter import get_financial_report as yfinance_report
        return await yfinance_report(symbol, report_type, quarterly)

    else:
        return ToolResult(
            success=False,
            data=None,
            source="",
            error=f"不支持的数据源: {source}"
        )


# 导出所有工具类和函数
__all__ = [
    # 统一接口
    "get_stock_kline",
    "get_company_info",
    "get_financial_report",
    # AKShare 工具
    "AKShareKlineTool",
    "AKShareCompanyInfoTool",
    "AKShareFinancialTool",
    "AKShareFinancialIndicatorTool",
    # efinance 工具
    "EfinanceKlineTool",
    "EfinanceCompanyInfoTool",
    "EfinanceCompanyPerformanceTool",
    "EfinanceRealtimeTool",
    # yfinance 工具
    "YFinanceKlineTool",
    "YFinanceCompanyInfoTool",
    "YFinanceFinancialTool",
    "YFinanceMultiDownloadTool",
    # 缓存
    "get_cache",
    "FinancialCache",
]
