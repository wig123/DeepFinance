"""
基于 AKShare 的宏观经济数据工具

使用 AKShare 库获取中国及全球宏观经济数据。
数据源：东方财富、新浪财经等
"""

import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, List, Dict, Any, Callable
import pandas as pd

from ..base import ToolResult, register_tool
from .base_macro import (
    MacroTool,
    MacroIndicator,
    Country,
    MacroDataRequest,
    MacroDataResponse,
    MacroDataPoint,
)


# 缓存装饰器：宏观数据更新慢，缓存 1 小时
def cached_macro_data(ttl_seconds: int = 3600):
    """带 TTL 的缓存装饰器"""
    cache: Dict[str, tuple] = {}

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            now = datetime.now()

            # 检查缓存
            if key in cache:
                result, timestamp = cache[key]
                if (now - timestamp).total_seconds() < ttl_seconds:
                    return result

            # 调用原函数
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper

    return decorator


@register_tool
class AKShareMacroTool(MacroTool):
    """基于 AKShare 的宏观数据工具

    支持的指标：
    - GDP/GDP同比增速
    - CPI/PPI
    - LPR利率
    - 汇率
    - 进出口数据
    """

    def __init__(self):
        self._ak = None  # 延迟导入

    @property
    def name(self) -> str:
        return "akshare_macro"

    @property
    def description(self) -> str:
        return "使用AKShare获取宏观经济数据（GDP、CPI、PPI、利率、汇率等）"

    def _get_akshare(self):
        """延迟导入 akshare"""
        if self._ak is None:
            try:
                import akshare as ak

                self._ak = ak
            except ImportError:
                raise ImportError(
                    "akshare 未安装，请运行: pip install akshare"
                )
        return self._ak

    async def get_indicator(
        self, request: MacroDataRequest
    ) -> MacroDataResponse:
        """获取指标数据"""
        # 根据指标类型分发到具体方法
        indicator_handlers = {
            # GDP
            MacroIndicator.GDP: self._get_gdp,
            MacroIndicator.GDP_YOY: self._get_gdp_yoy,
            # CPI/PPI
            MacroIndicator.CPI: self._get_cpi,
            MacroIndicator.CPI_YOY: self._get_cpi_yoy,
            MacroIndicator.CPI_MOM: self._get_cpi_mom,
            MacroIndicator.PPI: self._get_ppi,
            MacroIndicator.PPI_YOY: self._get_ppi_yoy,
            # 利率
            MacroIndicator.LPR: self._get_lpr,
            MacroIndicator.LPR_1Y: self._get_lpr_1y,
            MacroIndicator.LPR_5Y: self._get_lpr_5y,
            MacroIndicator.INTEREST_RATE: self._get_interest_rate,
            # 汇率
            MacroIndicator.EXCHANGE_RATE: self._get_exchange_rate,
            MacroIndicator.USD_CNY: self._get_usd_cny,
            # 贸易
            MacroIndicator.EXPORTS_YOY: self._get_exports_yoy,
            MacroIndicator.IMPORTS_YOY: self._get_imports_yoy,
        }

        handler = indicator_handlers.get(request.indicator)
        if not handler:
            raise ValueError(f"不支持的指标类型: {request.indicator}")

        # 在线程池中执行同步 IO 操作
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler, request)

    # ==================== GDP 相关 ====================

    @cached_macro_data(ttl_seconds=3600)
    def _get_gdp(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取中国 GDP 数据"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("GDP 绝对值目前仅支持中国数据")

        df = ak.macro_china_gdp()
        values = self._parse_quarterly_data(df, request)

        return MacroDataResponse(
            indicator="GDP",
            country=request.country.value,
            values=values,
            unit="亿元",
            description="中国季度 GDP 数据",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_gdp_yoy(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 GDP 同比增速"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("GDP 同比目前仅支持中国数据")

        df = ak.macro_china_gdp_yearly()
        values = self._parse_jinshi_data(df, request)

        return MacroDataResponse(
            indicator="GDP_YOY",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国 GDP 同比增速",
        )

    # ==================== CPI 相关 ====================

    @cached_macro_data(ttl_seconds=3600)
    def _get_cpi(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 CPI 数据"""
        ak = self._get_akshare()

        if request.country == Country.CHINA:
            df = ak.macro_china_cpi()
            values = self._parse_monthly_cpi(df, request)
            desc = "中国月度 CPI 数据"
        else:
            raise ValueError(f"CPI 数据暂不支持: {request.country}")

        return MacroDataResponse(
            indicator="CPI",
            country=request.country.value,
            values=values,
            unit=None,
            description=desc,
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_cpi_yoy(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 CPI 同比"""
        ak = self._get_akshare()

        if request.country == Country.CHINA:
            df = ak.macro_china_cpi_yearly()
            values = self._parse_jinshi_data(df, request)
            desc = "中国 CPI 同比增速"
        elif request.country == Country.GERMANY:
            df = ak.macro_germany_cpi_yearly()
            values = self._parse_eastmoney_data(df, request)
            desc = "德国 CPI 同比增速"
        else:
            raise ValueError(f"CPI 同比暂不支持: {request.country}")

        return MacroDataResponse(
            indicator="CPI_YOY",
            country=request.country.value,
            values=values,
            unit="%",
            description=desc,
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_cpi_mom(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 CPI 环比"""
        ak = self._get_akshare()

        if request.country == Country.CHINA:
            df = ak.macro_china_cpi_monthly()
            values = self._parse_jinshi_data(df, request)
            desc = "中国 CPI 环比"
        elif request.country == Country.GERMANY:
            df = ak.macro_germany_cpi_monthly()
            values = self._parse_eastmoney_data(df, request)
            desc = "德国 CPI 环比"
        else:
            raise ValueError(f"CPI 环比暂不支持: {request.country}")

        return MacroDataResponse(
            indicator="CPI_MOM",
            country=request.country.value,
            values=values,
            unit="%",
            description=desc,
        )

    # ==================== PPI 相关 ====================

    @cached_macro_data(ttl_seconds=3600)
    def _get_ppi(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 PPI 数据"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("PPI 数据目前仅支持中国")

        df = ak.macro_china_ppi()
        values = self._parse_monthly_ppi(df, request)

        return MacroDataResponse(
            indicator="PPI",
            country=request.country.value,
            values=values,
            unit=None,
            description="中国月度 PPI 数据",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_ppi_yoy(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 PPI 同比"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("PPI 同比目前仅支持中国")

        df = ak.macro_china_ppi_yearly()
        values = self._parse_jinshi_data(df, request)

        return MacroDataResponse(
            indicator="PPI_YOY",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国 PPI 同比增速",
        )

    # ==================== 利率相关 ====================

    @cached_macro_data(ttl_seconds=3600)
    def _get_lpr(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 LPR 利率"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("LPR 仅适用于中国")

        df = ak.macro_china_lpr()
        values = self._parse_lpr_data(df, request)

        return MacroDataResponse(
            indicator="LPR",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国贷款市场报价利率 (LPR)",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_lpr_1y(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 1 年期 LPR"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("LPR 仅适用于中国")

        df = ak.macro_china_lpr()
        values = self._parse_lpr_data(df, request, tenor="1Y")

        return MacroDataResponse(
            indicator="LPR_1Y",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国 1 年期 LPR",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_lpr_5y(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取 5 年期 LPR"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("LPR 仅适用于中国")

        df = ak.macro_china_lpr()
        values = self._parse_lpr_data(df, request, tenor="5Y")

        return MacroDataResponse(
            indicator="LPR_5Y",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国 5 年期 LPR",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_interest_rate(
        self, request: MacroDataRequest
    ) -> MacroDataResponse:
        """获取央行基准利率"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("央行利率目前仅支持中国")

        df = ak.macro_bank_china_interest_rate()
        values = self._parse_jinshi_data(df, request)

        return MacroDataResponse(
            indicator="INTEREST_RATE",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国央行基准利率决议",
        )

    # ==================== 汇率相关 ====================

    @cached_macro_data(ttl_seconds=300)  # 汇率缓存 5 分钟
    def _get_exchange_rate(
        self, request: MacroDataRequest
    ) -> MacroDataResponse:
        """获取汇率数据"""
        ak = self._get_akshare()

        # 获取实时汇率
        df = ak.fx_spot_quote()
        values = self._parse_fx_spot(df, request)

        return MacroDataResponse(
            indicator="EXCHANGE_RATE",
            country=request.country.value,
            values=values,
            unit=None,
            description="人民币汇率即期报价",
        )

    @cached_macro_data(ttl_seconds=300)
    def _get_usd_cny(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取美元兑人民币汇率"""
        ak = self._get_akshare()

        # 获取历史中间价
        df = ak.currency_boc_safe()
        values = self._parse_usd_cny(df, request)

        return MacroDataResponse(
            indicator="USD_CNY",
            country=request.country.value,
            values=values,
            unit=None,
            description="美元兑人民币汇率中间价",
        )

    # ==================== 贸易相关 ====================

    @cached_macro_data(ttl_seconds=3600)
    def _get_exports_yoy(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取出口同比"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("出口数据目前仅支持中国")

        df = ak.macro_china_exports_yoy()
        values = self._parse_jinshi_data(df, request)

        return MacroDataResponse(
            indicator="EXPORTS_YOY",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国出口同比增速（美元计）",
        )

    @cached_macro_data(ttl_seconds=3600)
    def _get_imports_yoy(self, request: MacroDataRequest) -> MacroDataResponse:
        """获取进口同比"""
        ak = self._get_akshare()

        if request.country != Country.CHINA:
            raise ValueError("进口数据目前仅支持中国")

        df = ak.macro_china_imports_yoy()
        values = self._parse_jinshi_data(df, request)

        return MacroDataResponse(
            indicator="IMPORTS_YOY",
            country=request.country.value,
            values=values,
            unit="%",
            description="中国进口同比增速（美元计）",
        )

    # ==================== 数据解析辅助方法 ====================

    def _parse_jinshi_data(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析金十数据格式

        列名：商品、日期、今值、预测值、前值
        """
        values = []

        # 日期筛选
        df = self._filter_by_date(df, request, date_col="日期")

        for _, row in df.iterrows():
            try:
                date_str = str(row.get("日期", ""))
                if pd.isna(date_str) or not date_str:
                    continue

                # 尝试解析日期
                if isinstance(date_str, str):
                    date = date_str[:10]  # 取前10个字符
                else:
                    date = pd.to_datetime(date_str).strftime("%Y-%m-%d")

                value = row.get("今值")
                if pd.isna(value):
                    continue

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(value),
                        previous_value=(
                            float(row.get("前值"))
                            if pd.notna(row.get("前值"))
                            else None
                        ),
                        predicted_value=(
                            float(row.get("预测值"))
                            if pd.notna(row.get("预测值"))
                            else None
                        ),
                        unit="%",
                    )
                )
            except Exception:
                continue

        # 限制返回条数
        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_eastmoney_data(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析东方财富数据格式

        列名：时间、前值、现值、发布日期
        """
        values = []

        for _, row in df.iterrows():
            try:
                time_str = str(row.get("时间", ""))
                if not time_str:
                    continue

                # 解析 "2023年10月" 格式
                date = self._parse_chinese_date(time_str)
                if not date:
                    continue

                value = row.get("现值")
                if pd.isna(value):
                    continue

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(value),
                        previous_value=(
                            float(row.get("前值"))
                            if pd.notna(row.get("前值"))
                            else None
                        ),
                        unit="%",
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_quarterly_data(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析季度 GDP 数据"""
        values = []

        for _, row in df.iterrows():
            try:
                quarter = str(row.get("季度", ""))
                if not quarter:
                    continue

                # 解析 "2023年第4季度" 格式
                date = self._parse_quarter_date(quarter)
                if not date:
                    continue

                gdp_value = row.get("国内生产总值-绝对值")
                if pd.isna(gdp_value):
                    gdp_value = row.get("国内生产总值-累计值")

                if pd.isna(gdp_value):
                    continue

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(gdp_value),
                        unit="亿元",
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_monthly_cpi(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析月度 CPI 数据"""
        values = []

        for _, row in df.iterrows():
            try:
                month = str(row.get("月份", ""))
                if not month:
                    continue

                # 解析 "2023年10月份" 格式
                date = self._parse_chinese_month(month)
                if not date:
                    continue

                value = row.get("全国-当月")
                if pd.isna(value):
                    continue

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(value),
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_monthly_ppi(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析月度 PPI 数据"""
        values = []

        for _, row in df.iterrows():
            try:
                month = str(row.get("月份", ""))
                if not month:
                    continue

                date = self._parse_chinese_month(month)
                if not date:
                    continue

                value = row.get("当月")
                if pd.isna(value):
                    continue

                yoy = row.get("当月同比增长")

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(value),
                        previous_value=(
                            float(yoy) if pd.notna(yoy) else None
                        ),  # 用 previous_value 存同比
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_lpr_data(
        self,
        df: pd.DataFrame,
        request: MacroDataRequest,
        tenor: Optional[str] = None,
    ) -> List[MacroDataPoint]:
        """解析 LPR 数据"""
        values = []

        # 日期筛选
        df = self._filter_by_date(df, request, date_col="TRADE_DATE")

        for _, row in df.iterrows():
            try:
                date_str = str(row.get("TRADE_DATE", ""))
                if not date_str:
                    continue

                date = date_str[:10]

                if tenor == "1Y":
                    value = row.get("LPR1Y")
                elif tenor == "5Y":
                    value = row.get("LPR5Y")
                else:
                    # 返回两个利率中的 1 年期
                    value = row.get("LPR1Y")

                if pd.isna(value):
                    continue

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=float(value),
                        unit="%",
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    def _parse_fx_spot(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析外汇即期报价"""
        values = []
        today = datetime.now().strftime("%Y-%m-%d")

        for _, row in df.iterrows():
            try:
                pair = str(row.get("货币对", ""))
                if not pair:
                    continue

                bid = row.get("买报价")
                ask = row.get("卖报价")

                if pd.isna(bid) or pd.isna(ask):
                    continue

                # 用中间价
                mid = (float(bid) + float(ask)) / 2

                values.append(
                    MacroDataPoint(
                        date=today,
                        value=mid,
                        unit=pair,  # 用 unit 存货币对
                    )
                )
            except Exception:
                continue

        return values

    def _parse_usd_cny(
        self, df: pd.DataFrame, request: MacroDataRequest
    ) -> List[MacroDataPoint]:
        """解析美元兑人民币历史数据"""
        values = []

        # 日期筛选
        df = self._filter_by_date(df, request, date_col="日期")

        for _, row in df.iterrows():
            try:
                date_str = str(row.get("日期", ""))
                if not date_str:
                    continue

                date = date_str[:10]
                value = row.get("美元")

                if pd.isna(value):
                    continue

                # 转换为 1 美元 = X 人民币
                rate = float(value) / 100

                values.append(
                    MacroDataPoint(
                        date=date,
                        value=rate,
                        unit="USD/CNY",
                    )
                )
            except Exception:
                continue

        if request.limit:
            values = values[: request.limit]

        return values

    # ==================== 日期解析辅助 ====================

    def _filter_by_date(
        self, df: pd.DataFrame, request: MacroDataRequest, date_col: str
    ) -> pd.DataFrame:
        """按日期筛选数据"""
        if request.start_date or request.end_date:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                if request.start_date:
                    df = df[df[date_col] >= request.start_date]
                if request.end_date:
                    df = df[df[date_col] <= request.end_date]
            except Exception:
                pass
        return df

    def _parse_chinese_date(self, date_str: str) -> Optional[str]:
        """解析中文日期格式 (2023年10月)"""
        try:
            import re

            match = re.match(r"(\d{4})年(\d{1,2})月", date_str)
            if match:
                year, month = match.groups()
                return f"{year}-{int(month):02d}-01"
        except Exception:
            pass
        return None

    def _parse_chinese_month(self, date_str: str) -> Optional[str]:
        """解析中文月份格式 (2023年10月份)"""
        try:
            import re

            match = re.match(r"(\d{4})年(\d{1,2})月", date_str)
            if match:
                year, month = match.groups()
                return f"{year}-{int(month):02d}-01"
        except Exception:
            pass
        return None

    def _parse_quarter_date(self, quarter_str: str) -> Optional[str]:
        """解析季度格式 (2023年第4季度)"""
        try:
            import re

            match = re.match(r"(\d{4})年第(\d)季度", quarter_str)
            if match:
                year, q = match.groups()
                # 季度转月份：Q1->03, Q2->06, Q3->09, Q4->12
                month = int(q) * 3
                return f"{year}-{month:02d}-01"
        except Exception:
            pass
        return None
