"""
宏观经济数据工具基类

定义统一的宏观数据获取接口，便于扩展不同数据源。
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

from ..base import Tool, ToolResult


class MacroIndicator(Enum):
    """宏观经济指标类型"""

    # GDP 相关
    GDP = "gdp"  # GDP 绝对值
    GDP_YOY = "gdp_yoy"  # GDP 同比增速

    # 物价指数
    CPI = "cpi"  # 消费者物价指数
    CPI_YOY = "cpi_yoy"  # CPI 同比
    CPI_MOM = "cpi_mom"  # CPI 环比
    PPI = "ppi"  # 生产者物价指数
    PPI_YOY = "ppi_yoy"  # PPI 同比

    # 利率
    LPR = "lpr"  # 贷款市场报价利率
    LPR_1Y = "lpr_1y"  # 1年期 LPR
    LPR_5Y = "lpr_5y"  # 5年期 LPR
    INTEREST_RATE = "interest_rate"  # 央行基准利率

    # 汇率
    EXCHANGE_RATE = "exchange_rate"  # 汇率
    USD_CNY = "usd_cny"  # 美元兑人民币

    # 贸易
    EXPORTS_YOY = "exports_yoy"  # 出口同比
    IMPORTS_YOY = "imports_yoy"  # 进口同比


class Country(Enum):
    """国家/地区"""

    CHINA = "china"
    USA = "usa"
    GERMANY = "germany"
    JAPAN = "japan"
    UK = "uk"


@dataclass
class MacroDataRequest:
    """宏观数据请求参数"""

    indicator: MacroIndicator
    country: Country = Country.CHINA
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None  # YYYY-MM-DD
    limit: Optional[int] = None  # 限制返回条数


@dataclass
class MacroDataPoint:
    """单个宏观数据点"""

    date: str  # 日期
    value: float  # 当前值
    previous_value: Optional[float] = None  # 前值
    predicted_value: Optional[float] = None  # 预测值
    unit: Optional[str] = None  # 单位（如 %）


@dataclass
class MacroDataResponse:
    """宏观数据响应"""

    indicator: str
    country: str
    values: List[MacroDataPoint]
    unit: Optional[str] = None
    description: Optional[str] = None


class MacroTool(Tool):
    """宏观数据工具基类

    所有宏观数据源适配器需继承此类并实现具体方法。
    """

    @property
    def name(self) -> str:
        return "macro_tool"

    @property
    def description(self) -> str:
        return "获取宏观经济数据的基类工具"

    @property
    def parameters(self) -> dict:
        """参数定义"""
        return {
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "description": "指标类型",
                    "enum": [e.value for e in MacroIndicator],
                },
                "country": {
                    "type": "string",
                    "description": "国家/地区",
                    "enum": [c.value for c in Country],
                    "default": "china",
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期 (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期 (YYYY-MM-DD)",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回条数限制",
                },
            },
            "required": ["indicator"],
        }

    @abstractmethod
    async def get_indicator(
        self, request: MacroDataRequest
    ) -> MacroDataResponse:
        """获取指标数据

        Args:
            request: 数据请求参数

        Returns:
            MacroDataResponse: 指标数据响应
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具

        Args:
            indicator: 指标类型
            country: 国家/地区（默认中国）
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回条数限制

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 解析参数
            indicator_str = kwargs.get("indicator")
            if not indicator_str:
                return ToolResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error="缺少必填参数: indicator",
                )

            try:
                indicator = MacroIndicator(indicator_str)
            except ValueError:
                return ToolResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error=f"不支持的指标类型: {indicator_str}",
                )

            country_str = kwargs.get("country", "china")
            try:
                country = Country(country_str)
            except ValueError:
                return ToolResult(
                    success=False,
                    data=None,
                    source=self.name,
                    error=f"不支持的国家/地区: {country_str}",
                )

            # 构建请求
            request = MacroDataRequest(
                indicator=indicator,
                country=country,
                start_date=kwargs.get("start_date"),
                end_date=kwargs.get("end_date"),
                limit=kwargs.get("limit"),
            )

            # 获取数据
            response = await self.get_indicator(request)

            # 返回结果
            return ToolResult(
                success=True,
                data={
                    "indicator": response.indicator,
                    "country": response.country,
                    "values": [
                        {
                            "date": v.date,
                            "value": v.value,
                            "previous_value": v.previous_value,
                            "predicted_value": v.predicted_value,
                            "unit": v.unit,
                        }
                        for v in response.values
                    ],
                    "unit": response.unit,
                    "description": response.description,
                },
                source=self.name,
                metadata={"request": kwargs},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                source=self.name,
                error=f"获取宏观数据失败: {str(e)}",
            )
