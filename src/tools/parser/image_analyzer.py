"""图片智能分析器。

对解析出的图片进行分类和分析：
- 图表类（chart）：使用金融图表分析提示词进行深度分析
- 非图表类（illustration）：简单的视觉描述
- 装饰图标（icon）：标记为无意义，不需要处理
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

ImageType = Literal["chart", "illustration", "icon"]


class ImageAnalyzer:
    """图片智能分析器。

    功能:
    1. 分类图片类型（chart/illustration/icon）
    2. 对图表进行深度分析（使用金融图表分析提示词）
    3. 对非图表图片进行简单描述

    Attributes:
        llm: ChatAnthropic 实例
        chart_prompt: 图表分析提示词
    """

    def __init__(
        self,
        model_name: str = "claude-sonnet-4-5-20250929",
        chart_prompt_path: str | Path | None = None,
        max_concurrent: int = 10,
    ):
        """初始化分析器。

        Args:
            model_name: LLM 模型名称
            chart_prompt_path: 图表分析提示词文件路径
            max_concurrent: 最大并发请求数（默认10）
        """
        import os
        from dotenv import load_dotenv

        # 加载环境变量
        load_dotenv()

        # 初始化 LLM（会自动从环境变量读取 ANTHROPIC_API_KEY 和 ANTHROPIC_BASE_URL）
        self.llm = ChatAnthropic(
            model=model_name,
            timeout=60.0,  # 超时时间（秒）
            max_retries=2,  # 最大重试次数
        )
        self.max_concurrent = max_concurrent

        # 加载图表分析提示词
        if chart_prompt_path:
            prompt_file = Path(chart_prompt_path)
            if prompt_file.exists():
                self.chart_prompt = prompt_file.read_text(encoding="utf-8")
                logger.info(f"已加载图表分析提示词: {prompt_file}")
            else:
                logger.warning(f"提示词文件不存在: {prompt_file}，使用默认提示词")
                self.chart_prompt = self._default_chart_prompt()
        else:
            self.chart_prompt = self._default_chart_prompt()

    def classify_image(self, image_path: Path) -> ImageType:
        """分类图片类型。

        Args:
            image_path: 图片路径

        Returns:
            图片类型: "chart" | "illustration" | "icon"
        """
        prompt = """你是一个图片分类专家。请判断这张图片属于以下哪一类：

1. **chart**: 数据图表（折线图、柱状图、饼图、散点图、热力图、K线图等包含数据可视化的图表）
2. **illustration**: 非图表的实物图片（产品照片、建筑外观、人物照片、场景图、流程图等）
3. **icon**: 装饰性图标或 logo（公司标志、简单图标、装饰元素、页眉页脚图案等）

只需要回答一个单词: chart、illustration 或 icon。不要有任何其他解释。"""

        try:
            # 读取图片并编码为 base64
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            response = self.llm.invoke([message])
            result = response.content.strip().lower()

            if result in ["chart", "illustration", "icon"]:
                logger.debug(f"图片分类: {image_path.name} -> {result}")
                return result
            else:
                logger.warning(
                    f"无法识别图片类型: {result}，默认为 illustration ({image_path.name})"
                )
                return "illustration"

        except Exception as e:
            logger.error(f"图片分类失败 ({image_path.name}): {e}")
            return "illustration"

    def analyze_chart(self, image_path: Path) -> dict[str, str]:
        """对图表进行深度分析。

        Args:
            image_path: 图表图片路径

        Returns:
            分析结果字典，包含四个部分:
            - 图表构成
            - 数据关系
            - 模式特征
            - 核心洞察
        """
        try:
            # 读取图片并编码为 base64
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": self.chart_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            response = self.llm.invoke([message])
            content = response.content.strip()

            # 解析四个部分
            sections = self._parse_chart_analysis(content)

            logger.debug(f"图表分析完成: {image_path.name}")
            return sections

        except Exception as e:
            logger.error(f"图表分析失败 ({image_path.name}): {e}")
            return {
                "图表构成": "分析失败",
                "数据关系": "分析失败",
                "模式特征": "分析失败",
                "核心洞察": "分析失败",
            }

    def describe_illustration(self, image_path: Path) -> str:
        """对非图表图片进行简单描述。

        Args:
            image_path: 图片路径

        Returns:
            图片描述文本
        """
        prompt = """请用 1-2 句话简洁描述这张图片的内容。
重点说明：图片主体是什么、展示的场景或对象、有哪些关键视觉元素。
不要进行主观评价，只做客观描述。"""

        try:
            # 读取图片并编码为 base64
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            response = self.llm.invoke([message])
            description = response.content.strip()

            logger.debug(f"图片描述完成: {image_path.name}")
            return description

        except Exception as e:
            logger.error(f"图片描述失败 ({image_path.name}): {e}")
            return "图片描述生成失败"

    def _parse_chart_analysis(self, content: str) -> dict[str, str]:
        """解析图表分析结果为四个部分。

        Args:
            content: LLM 返回的分析文本

        Returns:
            包含四个部分的字典
        """
        sections = {
            "图表构成": "",
            "数据关系": "",
            "模式特征": "",
            "核心洞察": "",
        }

        current_section = None
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测章节标题（支持多种格式）
            if "【图表构成】" in line or line.startswith("**【图表构成】**"):
                current_section = "图表构成"
                continue
            elif "【数据关系】" in line or line.startswith("**【数据关系】**"):
                current_section = "数据关系"
                continue
            elif "【模式特征】" in line or line.startswith("**【模式特征】**"):
                current_section = "模式特征"
                continue
            elif "【核心洞察】" in line or line.startswith("**【核心洞察】**"):
                current_section = "核心洞察"
                continue

            # 累积内容到当前章节
            if current_section:
                if sections[current_section]:
                    sections[current_section] += "\n" + line
                else:
                    sections[current_section] = line

        # 清理空白
        for key in sections:
            sections[key] = sections[key].strip()

        return sections

    def _default_chart_prompt(self) -> str:
        """默认的图表分析提示词。

        Returns:
            默认提示词文本
        """
        return """你是一位严谨的、专注于金融领域的图表分析专家。请严格按照以下四层结构分析这张金融图表：

**【图表构成】**
- 简洁描述图表的基础构成元素
- 内容：图表类型、标题、坐标轴/维度的范围和标签、图例（颜色/样式编码）
- 只描述关键元素，无需穷尽所有细节

**【数据关系】**
- 提取图表中最关键的、可量化的数据事实
- 内容：关键数值及其位置、主要的数量关系、数据点之间的简单对比
- 确保数值准确，忠实于图表

**【模式特征】**
- 用几句话纯粹描述数据的形态特征，不做任何业务解读
- 内容：整体形态（趋势方向、波动幅度、周期性等）、结构特点、明显的异常或拐点
- 用中性的形态词汇描述"看到的模式是什么"，而非"这意味着什么"

**【核心洞察】**
- 基于前面的形态特征，提炼业务层面的结论和影响
- 结构：
  核心结论：（最重要的业务判断，≤30字）

  业务含义：
  - 含义1（这个模式说明什么业务状况/问题/优势？≤20字）
  - 含义2（对哪个环节/指标/能力有什么影响？≤20字）

  风险关注：
  - 风险点1（具体阈值+可能后果，≤25字）
  - 风险点2（如有，具体阈值+可能后果，≤25字）
"""

    # ===== 批量异步分析方法 =====

    async def _classify_image_async(self, image_path: Path) -> ImageType:
        """异步分类图片类型。

        Args:
            image_path: 图片路径

        Returns:
            图片类型
        """
        prompt = """你是一个图片分类专家。请判断这张图片属于以下哪一类：

1. **chart**: 数据图表（折线图、柱状图、饼图、散点图、热力图、K线图等包含数据可视化的图表）
2. **illustration**: 非图表的实物图片（产品照片、建筑外观、人物照片、场景图、流程图等）
3. **icon**: 装饰性图标或 logo（公司标志、简单图标、装饰元素、页眉页脚图案等）

只需要回答一个单词: chart、illustration 或 icon。不要有任何其他解释。"""

        try:
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            # 使用 ainvoke 异步调用
            response = await self.llm.ainvoke([message])
            result = response.content.strip().lower()

            if result in ["chart", "illustration", "icon"]:
                return result
            else:
                logger.warning(
                    f"无法识别图片类型: {result}，默认为 illustration ({image_path.name})"
                )
                return "illustration"

        except Exception as e:
            logger.error(f"图片分类失败 ({image_path.name}): {e}")
            return "illustration"

    async def _analyze_chart_async(self, image_path: Path) -> dict[str, str]:
        """异步对图表进行深度分析。

        Args:
            image_path: 图表图片路径

        Returns:
            分析结果字典
        """
        try:
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": self.chart_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            # 使用 ainvoke 异步调用
            response = await self.llm.ainvoke([message])
            content = response.content.strip()

            sections = self._parse_chart_analysis(content)
            return sections

        except Exception as e:
            logger.error(f"图表分析失败 ({image_path.name}): {e}")
            return {
                "图表构成": "分析失败",
                "数据关系": "分析失败",
                "模式特征": "分析失败",
                "核心洞察": "分析失败",
            }

    async def _describe_illustration_async(self, image_path: Path) -> str:
        """异步对非图表图片进行简单描述。

        Args:
            image_path: 图片路径

        Returns:
            图片描述文本
        """
        prompt = """请用 1-2 句话简洁描述这张图片的内容。
重点说明：图片主体是什么、展示的场景或对象、有哪些关键视觉元素。
不要进行主观评价，只做客观描述。"""

        try:
            image_data = base64.b64encode(image_path.read_bytes()).decode()

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            )

            # 使用 ainvoke 异步调用
            response = await self.llm.ainvoke([message])
            description = response.content.strip()
            return description

        except Exception as e:
            logger.error(f"图片描述失败 ({image_path.name}): {e}")
            return "图片描述生成失败"

    async def _analyze_single_image_async(
        self, image_path: Path
    ) -> dict[str, any]:
        """异步分析单张图片（分类 + 内容分析）。

        Args:
            image_path: 图片路径

        Returns:
            包含 image_type 和分析结果的字典
        """
        result = {"image_path": image_path}

        # 1. 分类
        image_type = await self._classify_image_async(image_path)
        result["image_type"] = image_type

        # 2. 根据类型进行内容分析
        if image_type == "chart":
            analysis = await self._analyze_chart_async(image_path)
            result["analysis"] = analysis
        elif image_type == "illustration":
            description = await self._describe_illustration_async(image_path)
            result["description"] = description
        # icon 类型不需要额外分析

        return result

    def analyze_images_batch(
        self, image_paths: list[Path]
    ) -> dict[Path, dict[str, any]]:
        """批量异步分析多张图片（两阶段并行优化）。

        阶段1: 所有图片并行分类
        阶段2: 所有图片并行内容分析

        Args:
            image_paths: 图片路径列表

        Returns:
            字典，键为图片路径，值为分析结果
        """
        if not image_paths:
            return {}

        logger.info(f"开始批量分析 {len(image_paths)} 张图片（两阶段并行）...")

        # 两阶段批量并行处理（带并发控制）
        async def run_batch_optimized():
            # 创建并发控制信号量
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def classify_with_limit(img_path):
                async with semaphore:
                    return await self._classify_image_async(img_path)

            async def analyze_with_limit(img_path):
                async with semaphore:
                    return await self._analyze_chart_async(img_path)

            async def describe_with_limit(img_path):
                async with semaphore:
                    return await self._describe_illustration_async(img_path)

            # ===== 阶段 1: 所有图片并行分类（带并发限制）=====
            logger.info(
                f"  阶段1: 并行分类 {len(image_paths)} 张图片（最大并发{self.max_concurrent}）..."
            )
            classify_tasks = [classify_with_limit(img_path) for img_path in image_paths]
            image_types = await asyncio.gather(*classify_tasks)

            # 构建结果字典
            results = {}
            for img_path, img_type in zip(image_paths, image_types):
                results[img_path] = {
                    "image_path": img_path,
                    "image_type": img_type,
                }

            # ===== 阶段 2: 所有图片并行内容分析（带并发限制）=====
            logger.info(
                f"  阶段2: 并行内容分析 {len(image_paths)} 张图片（最大并发{self.max_concurrent}）..."
            )

            # 分组任务：图表分析 vs 非图表描述
            chart_tasks = []
            chart_paths = []
            illustration_tasks = []
            illustration_paths = []

            for img_path, img_type in zip(image_paths, image_types):
                if img_type == "chart":
                    chart_tasks.append(analyze_with_limit(img_path))
                    chart_paths.append(img_path)
                elif img_type == "illustration":
                    illustration_tasks.append(describe_with_limit(img_path))
                    illustration_paths.append(img_path)

            # 并行执行所有内容分析任务
            all_tasks = chart_tasks + illustration_tasks
            if all_tasks:
                all_results = await asyncio.gather(*all_tasks)

                # 回填图表分析结果
                for i, img_path in enumerate(chart_paths):
                    results[img_path]["analysis"] = all_results[i]

                # 回填非图表描述结果
                offset = len(chart_paths)
                for i, img_path in enumerate(illustration_paths):
                    results[img_path]["description"] = all_results[offset + i]

            return list(results.values())

        # 运行异步任务
        try:
            results = asyncio.run(run_batch_optimized())
        except RuntimeError as e:
            # 如果当前已有事件循环在运行，使用现有循环
            if "already running" in str(e):
                loop = asyncio.get_event_loop()
                results = loop.run_until_complete(run_batch_optimized())
            else:
                raise

        # 转换为字典格式
        results_dict = {r["image_path"]: r for r in results}

        logger.info(f"✓ 批量分析完成，共 {len(results_dict)} 张图片")

        # 统计
        chart_count = sum(
            1 for r in results_dict.values() if r.get("image_type") == "chart"
        )
        illustration_count = sum(
            1
            for r in results_dict.values()
            if r.get("image_type") == "illustration"
        )
        icon_count = sum(
            1 for r in results_dict.values() if r.get("image_type") == "icon"
        )

        logger.info(
            f"  - 图表类: {chart_count}, 非图表类: {illustration_count}, 装饰图标: {icon_count}"
        )

        return results_dict
