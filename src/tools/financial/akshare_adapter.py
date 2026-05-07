"""AKShare 适配器

主力数据源，覆盖 A股/港股/宏观数据。
API 文档: https://akshare.akfamily.xyz/

注意：AKShare API 变动频繁，版本锁定在 pyproject.toml
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Literal

import pandas as pd

from ..base import Tool, ToolResult, register_tool
from .cache import get_cache

logger = logging.getLogger(__name__)

# 数据源标识
SOURCE = "akshare"

# 周期映射
PERIOD_MAP = {
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "monthly",
    "d": "daily",
    "w": "weekly",
    "m": "monthly",
}

# 复权类型映射
ADJUST_MAP = {
    "none": "",      # 不复权
    "forward": "qfq",  # 前复权
    "backward": "hfq",  # 后复权
    "qfq": "qfq",
    "hfq": "hfq",
    "": "",
}


def _safe_import_akshare():
    """安全导入 akshare，处理导入错误"""
    try:
        import akshare as ak
        return ak
    except ImportError as e:
        logger.error(f"AKShare 未安装: {e}")
        return None


def _normalize_symbol(symbol: str) -> str:
    """标准化股票代码

    - 去除前缀（如 SH, SZ, sh, sz）
    - 保留纯数字代码
    """
    symbol = symbol.upper().strip()
    for prefix in ["SH", "SZ", "BJ", "HK"]:
        if symbol.startswith(prefix):
            return symbol[2:]
    return symbol


def _df_to_dict_list(df: pd.DataFrame) -> list[dict]:
    """将 DataFrame 转换为字典列表，处理时间类型"""
    if df is None or df.empty:
        return []

    # 转换日期列
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")

    return df.to_dict(orient="records")


@register_tool
class AKShareKlineTool(Tool):
    """AKShare K线数据工具"""

    @property
    def name(self) -> str:
        return "akshare_kline"

    @property
    def description(self) -> str:
        return "获取A股股票K线数据（日/周/月），支持复权"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519, 000001"
                },
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "K线周期"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式 YYYYMMDD"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期，格式 YYYYMMDD"
                },
                "adjust": {
                    "type": "string",
                    "enum": ["none", "forward", "backward"],
                    "description": "复权类型：none-不复权, forward-前复权, backward-后复权"
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
        adjust: str = "none",
    ) -> ToolResult:
        """获取K线数据"""
        ak = _safe_import_akshare()
        if ak is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="AKShare 库未安装"
            )

        symbol = _normalize_symbol(symbol)
        period = PERIOD_MAP.get(period, "daily")
        adjust_val = ADJUST_MAP.get(adjust, "")

        # 默认日期范围
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        cache = get_cache()
        cache_key = f"{SOURCE}:kline:{symbol}:{period}:{start_date}:{end_date}:{adjust_val}"

        # 尝试从缓存获取
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True, "symbol": symbol}
            )

        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust_val,
            )

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的K线数据"
                )

            # 标准化列名
            column_map = {
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
                "adjust": adjust,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            # 缓存数据（日K线缓存4小时）
            ttl = 14400 if period == "daily" else 86400
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
class AKShareCompanyInfoTool(Tool):
    """AKShare 公司信息工具"""

    @property
    def name(self) -> str:
        return "akshare_company_info"

    @property
    def description(self) -> str:
        return "获取A股上市公司基本信息（名称、行业、上市日期等）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519, 000001"
                }
            },
            "required": ["symbol"]
        }

    async def execute(self, symbol: str) -> ToolResult:
        """获取公司基本信息"""
        ak = _safe_import_akshare()
        if ak is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="AKShare 库未安装"
            )

        symbol = _normalize_symbol(symbol)

        cache = get_cache()
        cache_key = f"{SOURCE}:company_info:{symbol}"

        # 尝试从缓存获取（公司信息缓存7天）
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=symbol)

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的公司信息"
                )

            # 转换为字典
            # 数据格式：item | value
            info_dict = dict(zip(df["item"], df["value"]))

            data = {
                "symbol": symbol,
                "name": info_dict.get("股票简称", ""),
                "full_name": info_dict.get("公司名称", ""),
                "industry": info_dict.get("行业", ""),
                "list_date": info_dict.get("上市时间", ""),
                "total_shares": info_dict.get("总股本", ""),
                "float_shares": info_dict.get("流通股", ""),
                "total_market_cap": info_dict.get("总市值", ""),
                "float_market_cap": info_dict.get("流通市值", ""),
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
class AKShareFinancialTool(Tool):
    """AKShare 财务报表工具"""

    @property
    def name(self) -> str:
        return "akshare_financial"

    @property
    def description(self) -> str:
        return "获取A股上市公司财务报表（资产负债表、利润表、现金流量表）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519, 000001"
                },
                "report_type": {
                    "type": "string",
                    "enum": ["balance", "income", "cashflow"],
                    "description": "报表类型：balance-资产负债表, income-利润表, cashflow-现金流量表"
                },
                "date": {
                    "type": "string",
                    "description": "报告期，格式 YYYYMMDD，如 20231231"
                }
            },
            "required": ["symbol"]
        }

    async def execute(
        self,
        symbol: str,
        report_type: str = "income",
        date: Optional[str] = None,
    ) -> ToolResult:
        """获取财务报表数据"""
        ak = _safe_import_akshare()
        if ak is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="AKShare 库未安装"
            )

        symbol = _normalize_symbol(symbol)

        # 默认报告期：上一个季度末
        if not date:
            now = datetime.now()
            # 计算上一个季度末
            quarter = (now.month - 1) // 3
            if quarter == 0:
                date = f"{now.year - 1}1231"
            else:
                month = quarter * 3
                date = f"{now.year}{month:02d}{'30' if month in [6, 9] else '31'}"

        cache = get_cache()
        cache_key = f"{SOURCE}:financial:{symbol}:{report_type}:{date}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            # 根据报表类型调用不同接口
            if report_type == "balance":
                # 资产负债表
                df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
            elif report_type == "income":
                # 利润表
                df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
            elif report_type == "cashflow":
                # 现金流量表
                df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
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

            data = {
                "symbol": symbol,
                "report_type": report_type,
                "date": date,
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
class AKShareFinancialIndicatorTool(Tool):
    """AKShare 财务指标工具"""

    @property
    def name(self) -> str:
        return "akshare_financial_indicator"

    @property
    def description(self) -> str:
        return "获取A股上市公司财务分析指标（盈利能力、成长能力、偿债能力等）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 600519, 000001"
                }
            },
            "required": ["symbol"]
        }

    async def execute(self, symbol: str) -> ToolResult:
        """获取财务分析指标"""
        ak = _safe_import_akshare()
        if ak is None:
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error="AKShare 库未安装"
            )

        symbol = _normalize_symbol(symbol)

        cache = get_cache()
        cache_key = f"{SOURCE}:financial_indicator:{symbol}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return ToolResult(
                success=True,
                data=cached_data,
                source=SOURCE,
                metadata={"cached": True}
            )

        try:
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df is None or df.empty:
                return ToolResult(
                    success=False,
                    data=None,
                    source=SOURCE,
                    error=f"未找到股票 {symbol} 的财务指标"
                )

            data = {
                "symbol": symbol,
                "records": _df_to_dict_list(df),
                "count": len(df),
            }

            cache.set(cache_key, data, ttl=86400)

            return ToolResult(
                success=True,
                data=data,
                source=SOURCE,
                metadata={"cached": False}
            )

        except Exception as e:
            logger.exception(f"获取财务指标失败: {symbol}")
            return ToolResult(
                success=False,
                data=None,
                source=SOURCE,
                error=f"获取财务指标失败: {str(e)}"
            )


# 便捷函数
async def get_stock_kline(
    symbol: str,
    period: str = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "none",
) -> ToolResult:
    """获取股票K线数据的便捷函数"""
    tool = AKShareKlineTool()
    return await tool.execute(
        symbol=symbol,
        period=period,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )


async def get_company_info(symbol: str) -> ToolResult:
    """获取公司信息的便捷函数"""
    tool = AKShareCompanyInfoTool()
    return await tool.execute(symbol=symbol)


async def get_financial_report(
    symbol: str,
    report_type: str = "income",
    date: Optional[str] = None,
) -> ToolResult:
    """获取财务报表的便捷函数"""
    tool = AKShareFinancialTool()
    return await tool.execute(symbol=symbol, report_type=report_type, date=date)


async def get_financial_indicator(symbol: str) -> ToolResult:
    """获取财务指标的便捷函数"""
    tool = AKShareFinancialIndicatorTool()
    return await tool.execute(symbol=symbol)
