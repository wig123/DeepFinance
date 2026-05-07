"""efinance 适配器

备用数据源，基于东方财富数据。
GitHub: https://github.com/micro-sheep/efinance

用于 AKShare 失效时的备选方案。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Union, List

import pandas as pd

from ..base import Tool, ToolResult, register_tool
from .cache import get_cache

logger = logging.getLogger(__name__)

# 数据源标识
SOURCE = "efinance"

# K线周期映射
# efinance 的 klt 参数：1-1分钟, 5-5分钟, 15-15分钟, 30-30分钟, 60-60分钟, 101-日, 102-周, 103-月
KLT_MAP = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
    "daily": 101,
    "weekly": 102,
    "monthly": 103,
    "d": 101,
    "w": 102,
    "m": 103,
}


def _safe_import_efinance():
    """安全导入 efinance"""
    try:
        import efinance as ef
        return ef
    except ImportError as e:
        logger.error(f"efinance 未安装: {e}")
        return None


def _normalize_symbol(symbol: str) -> str:
    """标准化股票代码"""
    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "BJ"]:
        if symbol.startswith(prefix):
            return symbol[2:]
    return symbol


def _df_to_dict_list(df: pd.DataFrame) -> list[dict]:
    """将 DataFrame 转换为字典列表"""
    if df is None or df.empty:
        return []

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")

    return df.to_dict(orient="records")


@register_tool
class EfinanceKlineTool(Tool):
    """efinance K线数据工具"""

    @property
    def name(self) -> str:
        return "efinance_kline"

    @property
    def description(self) -> str:
        return "获取股票K线数据（日/周/月/分钟级），支持A股和美股"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码（A股如600519，美股如AAPL）或股票名称"
                },
                "period": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "30m", "60m", "daily", "weekly", "monthly"],
                    "description": "K线周期"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式 YYYYMMDD"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期，格式 YYYYMMDD"
                }
            },
            "required": ["symbol"]
        }

    async def execute(
        self,
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ToolResult:
        """获取K线数据"""
        ef = _safe_import_efinance()
        if ef is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="efinance 库未安装"
            )

        klt = KLT_MAP.get(period, 101)

        cache = get_cache()
        cache_key = f"{SOURCE}:kline:{symbol}:{period}:{start_date}:{end_date}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True, "symbol": symbol}
            )

        try:
            # efinance 的参数名是 beg 和 end
            kwargs = {"klt": klt}
            if start_date:
                kwargs["beg"] = start_date
            if end_date:
                kwargs["end"] = end_date

            df = ef.stock.get_quote_history(symbol, **kwargs)

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的K线数据"
                )

            # 标准化列名
            column_map = {
                "股票代码": "symbol",
                "股票名称": "name",
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "pct_change",
                "涨跌额": "change",
                "换手率": "turnover",
            }
            df = df.rename(columns=column_map)

            data = {
                "symbol": symbol,
                "period": period,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            # 日K线缓存4小时，分钟线缓存1小时
            ttl = 14400 if klt >= 101 else 3600
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
class EfinanceCompanyInfoTool(Tool):
    """efinance 公司信息工具"""

    @property
    def name(self) -> str:
        return "efinance_company_info"

    @property
    def description(self) -> str:
        return "获取股票基本信息"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519"
                }
            },
            "required": ["symbol"]
        }

    async def execute(self, symbol: str) -> ToolResult:
        """获取公司基本信息"""
        ef = _safe_import_efinance()
        if ef is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="efinance 库未安装"
            )

        symbol = _normalize_symbol(symbol)

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
            df = ef.stock.get_base_info(symbol)

            if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的信息"
                )

            # get_base_info 可能返回 Series 或 DataFrame
            if isinstance(df, pd.Series):
                info_dict = df.to_dict()
            else:
                info_dict = df.iloc[0].to_dict() if len(df) > 0 else {}

            data = {
                "symbol": symbol,
                "raw": info_dict,
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
class EfinanceCompanyPerformanceTool(Tool):
    """efinance 公司业绩工具"""

    @property
    def name(self) -> str:
        return "efinance_company_performance"

    @property
    def description(self) -> str:
        return "获取A股上市公司季度业绩数据（营收、净利润、EPS、ROE等）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "quarter": {
                    "type": "string",
                    "description": "季度，格式如 2024Q3，不填则获取最新季度"
                }
            },
            "required": []
        }

    async def execute(self, quarter: Optional[str] = None) -> ToolResult:
        """获取全市场公司业绩"""
        ef = _safe_import_efinance()
        if ef is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="efinance 库未安装"
            )

        cache = get_cache()
        cache_key = f"{SOURCE}:company_performance:{quarter or 'latest'}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            if quarter:
                df = ef.stock.get_all_company_performance(quarter)
            else:
                df = ef.stock.get_all_company_performance()

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error="未获取到公司业绩数据"
                )

            data = {
                "quarter": quarter or "latest",
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
            logger.exception("获取公司业绩失败")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取公司业绩失败: {str(e)}"
            )


@register_tool
class EfinanceRealtimeTool(Tool):
    """efinance 实时行情工具"""

    @property
    def name(self) -> str:
        return "efinance_realtime"

    @property
    def description(self) -> str:
        return "获取股票实时行情数据"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "股票代码列表，如 ['600519', '000001']"
                }
            },
            "required": ["symbols"]
        }

    async def execute(self, symbols: Union[str, List[str]]) -> ToolResult:
        """获取实时行情"""
        ef = _safe_import_efinance()
        if ef is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="efinance 库未安装"
            )

        # 确保是列表
        if isinstance(symbols, str):
            symbols = [symbols]

        symbols = [_normalize_symbol(s) for s in symbols]

        # 实时数据不缓存太久
        cache = get_cache()
        cache_key = f"{SOURCE}:realtime:{','.join(sorted(symbols))}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            df = ef.stock.get_realtime_quotes(symbols)

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error="未获取到实时行情数据"
                )

            data = {
                "symbols": symbols,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            cache.set(cache_key, data, ttl=60)  # 1分钟

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False}
            )

        except Exception as e:
            logger.exception("获取实时行情失败")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取实时行情失败: {str(e)}"
            )


# 便捷函数
async def get_stock_kline(
    symbol: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> ToolResult:
    """获取股票K线数据的便捷函数"""
    tool = EfinanceKlineTool()
    return await tool.execute(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


async def get_company_info(symbol: str) -> ToolResult:
    """获取公司信息的便捷函数"""
    tool = EfinanceCompanyInfoTool()
    return await tool.execute(symbol=symbol)


async def get_realtime_quotes(symbols: Union[str, List[str]]) -> ToolResult:
    """获取实时行情的便捷函数"""
    tool = EfinanceRealtimeTool()
    return await tool.execute(symbols=symbols)
