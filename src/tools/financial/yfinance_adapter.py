"""yfinance 适配器

全球数据源，覆盖美股及全球市场。
GitHub: https://github.com/ranaroussi/yfinance

注意：大陆访问可能需要代理
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, List

import pandas as pd

from ..base import Tool, ToolResult, register_tool
from .cache import get_cache

logger = logging.getLogger(__name__)

# 数据源标识
SOURCE = "yfinance"

# 周期映射
PERIOD_MAP = {
    "1d": "1d",
    "5d": "5d",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "10y": "10y",
    "ytd": "ytd",
    "max": "max",
}

# 间隔映射
INTERVAL_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "90m": "90m",
    "1h": "1h",
    "1d": "1d",
    "5d": "5d",
    "1wk": "1wk",
    "1mo": "1mo",
    "3mo": "3mo",
    "daily": "1d",
    "weekly": "1wk",
    "monthly": "1mo",
}


def _safe_import_yfinance():
    """安全导入 yfinance"""
    try:
        import yfinance as yf
        return yf
    except ImportError as e:
        logger.error(f"yfinance 未安装: {e}")
        return None


def _df_to_dict_list(df: pd.DataFrame) -> list[dict]:
    """将 DataFrame 转换为字典列表"""
    if df is None or df.empty:
        return []

    # 重置索引，将日期变为列
    df = df.reset_index()

    # 转换日期列
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        elif hasattr(df[col], 'dt'):
            try:
                df[col] = df[col].dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    return df.to_dict(orient="records")


@register_tool
class YFinanceKlineTool(Tool):
    """yfinance K线数据工具"""

    @property
    def name(self) -> str:
        return "yfinance_kline"

    @property
    def description(self) -> str:
        return "获取全球股票K线数据（美股、港股、全球市场），支持多种周期"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码（如 AAPL, MSFT, 0700.HK）"
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
                    "description": "数据周期"
                },
                "interval": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"],
                    "description": "K线间隔"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式 YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期，格式 YYYY-MM-DD"
                }
            },
            "required": ["symbol"]
        }

    async def execute(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ToolResult:
        """获取K线数据"""
        yf = _safe_import_yfinance()
        if yf is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="yfinance 库未安装"
            )

        symbol = symbol.upper().strip()
        interval = INTERVAL_MAP.get(interval, "1d")

        cache = get_cache()
        cache_key = f"{SOURCE}:kline:{symbol}:{period}:{interval}:{start_date}:{end_date}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True, "symbol": symbol}
            )

        try:
            ticker = yf.Ticker(symbol)

            # 如果指定了日期范围，使用 start/end
            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的K线数据"
                )

            # 标准化列名
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Dividends": "dividends",
                "Stock Splits": "splits",
            })

            data = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            # 日K线缓存4小时，分钟线缓存1小时
            ttl = 14400 if interval in ["1d", "1wk", "1mo"] else 3600
            cache.set(cache_key, data, ttl=ttl)

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False, "symbol": symbol}
            )

        except Exception as e:
            logger.exception(f"获取K线数据失败: {symbol}")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取K线数据失败: {str(e)}"
            )


@register_tool
class YFinanceCompanyInfoTool(Tool):
    """yfinance 公司信息工具"""

    @property
    def name(self) -> str:
        return "yfinance_company_info"

    @property
    def description(self) -> str:
        return "获取全球上市公司基本信息（名称、行业、市值、PE等）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码（如 AAPL, MSFT, 0700.HK）"
                }
            },
            "required": ["symbol"]
        }

    async def execute(self, symbol: str) -> ToolResult:
        """获取公司基本信息"""
        yf = _safe_import_yfinance()
        if yf is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="yfinance 库未安装"
            )

        symbol = symbol.upper().strip()

        cache = get_cache()
        cache_key = f"{SOURCE}:company_info:{symbol}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("regularMarketPrice") is None:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的信息"
                )

            # 提取关键信息
            data = {
                "symbol": symbol,
                "name": info.get("shortName", ""),
                "long_name": info.get("longName", ""),
                "industry": info.get("industry", ""),
                "sector": info.get("sector", ""),
                "country": info.get("country", ""),
                "currency": info.get("currency", ""),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "50_day_average": info.get("fiftyDayAverage"),
                "200_day_average": info.get("twoHundredDayAverage"),
                "employees": info.get("fullTimeEmployees"),
                "website": info.get("website", ""),
                "summary": info.get("longBusinessSummary", ""),
                "raw": info,
            }

            cache.set(cache_key, data, ttl=604800)  # 7天

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False}
            )

        except Exception as e:
            logger.exception(f"获取公司信息失败: {symbol}")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取公司信息失败: {str(e)}"
            )


@register_tool
class YFinanceFinancialTool(Tool):
    """yfinance 财务报表工具"""

    @property
    def name(self) -> str:
        return "yfinance_financial"

    @property
    def description(self) -> str:
        return "获取全球上市公司财务报表（利润表、资产负债表、现金流量表）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码（如 AAPL, MSFT）"
                },
                "report_type": {
                    "type": "string",
                    "enum": ["income", "balance", "cashflow"],
                    "description": "报表类型"
                },
                "quarterly": {
                    "type": "boolean",
                    "description": "是否获取季度报表，默认年度报表"
                }
            },
            "required": ["symbol"]
        }

    async def execute(
        self,
        symbol: str,
        report_type: str = "income",
        quarterly: bool = False,
    ) -> ToolResult:
        """获取财务报表"""
        yf = _safe_import_yfinance()
        if yf is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="yfinance 库未安装"
            )

        symbol = symbol.upper().strip()

        cache = get_cache()
        cache_key = f"{SOURCE}:financial:{symbol}:{report_type}:{'q' if quarterly else 'a'}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            ticker = yf.Ticker(symbol)

            # 根据报表类型和周期获取数据
            if report_type == "income":
                df = ticker.quarterly_income_stmt if quarterly else ticker.income_stmt
            elif report_type == "balance":
                df = ticker.quarterly_balance_sheet if quarterly else ticker.balance_sheet
            elif report_type == "cashflow":
                df = ticker.quarterly_cashflow if quarterly else ticker.cashflow
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"不支持的报表类型: {report_type}"
                )

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的财务数据"
                )

            # 转置使日期成为行
            df = df.T

            data = {
                "symbol": symbol,
                "report_type": report_type,
                "quarterly": quarterly,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            cache.set(cache_key, data, ttl=86400)  # 1天

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False}
            )

        except Exception as e:
            logger.exception(f"获取财务报表失败: {symbol}")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取财务报表失败: {str(e)}"
            )


@register_tool
class YFinanceMultiDownloadTool(Tool):
    """yfinance 批量下载工具"""

    @property
    def name(self) -> str:
        return "yfinance_multi_download"

    @property
    def description(self) -> str:
        return "批量下载多只股票的历史数据"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "股票代码列表"
                },
                "period": {
                    "type": "string",
                    "description": "数据周期（如 1mo, 3mo, 1y）"
                },
                "interval": {
                    "type": "string",
                    "description": "K线间隔（如 1d, 1wk）"
                }
            },
            "required": ["symbols"]
        }

    async def execute(
        self,
        symbols: Union[str, List[str]],
        period: str = "1mo",
        interval: str = "1d",
    ) -> ToolResult:
        """批量下载数据"""
        yf = _safe_import_yfinance()
        if yf is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="yfinance 库未安装"
            )

        if isinstance(symbols, str):
            symbols = [s.strip() for s in symbols.split(",")]

        symbols = [s.upper() for s in symbols]

        cache = get_cache()
        cache_key = f"{SOURCE}:multi:{','.join(sorted(symbols))}:{period}:{interval}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            df = yf.download(symbols, period=period, interval=interval, group_by="ticker")

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error="未获取到数据"
                )

            # 处理多股票返回的多级列索引
            result = {}
            if len(symbols) == 1:
                result[symbols[0]] = _df_to_dict_list(df)
            else:
                for symbol in symbols:
                    if symbol in df.columns.get_level_values(0):
                        symbol_df = df[symbol].dropna()
                        result[symbol] = _df_to_dict_list(symbol_df)

            data = {
                "symbols": symbols,
                "period": period,
                "interval": interval,
                "data": result,
            }

            cache.set(cache_key, data, ttl=14400)  # 4小时

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False}
            )

        except Exception as e:
            logger.exception("批量下载数据失败")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"批量下载数据失败: {str(e)}"
            )


# 便捷函数
async def get_stock_kline(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> ToolResult:
    """获取股票K线数据的便捷函数"""
    tool = YFinanceKlineTool()
    return await tool.execute(
        symbol=symbol,
        period=period,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )


async def get_company_info(symbol: str) -> ToolResult:
    """获取公司信息的便捷函数"""
    tool = YFinanceCompanyInfoTool()
    return await tool.execute(symbol=symbol)


async def get_financial_report(
    symbol: str,
    report_type: str = "income",
    quarterly: bool = False,
) -> ToolResult:
    """获取财务报表的便捷函数"""
    tool = YFinanceFinancialTool()
    return await tool.execute(
        symbol=symbol,
        report_type=report_type,
        quarterly=quarterly,
    )


async def download_multiple(
    symbols: Union[str, List[str]],
    period: str = "1mo",
    interval: str = "1d",
) -> ToolResult:
    """批量下载数据的便捷函数"""
    tool = YFinanceMultiDownloadTool()
    return await tool.execute(
        symbols=symbols,
        period=period,
        interval=interval,
    )
