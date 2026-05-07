"""Publisher 主类"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .exporters import get_exporter, EXPORTERS
from .schemas import ExportFormat, ExportRequest, ExportResult, ReportMetadata

logger = logging.getLogger(__name__)


class Publisher:
    """报告发布器 - 支持多格式导出"""

    def __init__(self, base_output_dir: str = "outputs"):
        """
        初始化发布器

        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = Path(base_output_dir)

    def publish(self, request: ExportRequest) -> ExportResult:
        """
        发布报告（导出为多种格式）

        Args:
            request: 导出请求

        Returns:
            ExportResult: 导出结果
        """
        # 确定输出目录
        if request.output_dir:
            output_dir = Path(request.output_dir)
        else:
            output_dir = self.base_output_dir / request.task_id

        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Publisher] 开始发布报告: {request.title}")
        logger.info(f"[Publisher] 输出目录: {output_dir}")
        logger.info(f"[Publisher] 导出格式: {[f.value for f in request.formats]}")

        # 准备元数据
        metadata = ReportMetadata(
            title=request.title,
            created_at=datetime.now().isoformat(),
        )

        # 执行导出
        files = {}
        errors = []

        for fmt in request.formats:
            try:
                exporter = get_exporter(fmt)
                output_path = output_dir / f"report.{fmt.value}"

                success = exporter.export(
                    content=request.content,
                    output_path=output_path,
                    metadata=metadata,
                    sources=request.sources,
                )

                if success:
                    files[fmt.value] = str(output_path)
                else:
                    errors.append(f"{fmt.value}: 导出失败")

            except Exception as e:
                error_msg = f"{fmt.value}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"[Publisher] {error_msg}")

        # 返回结果
        result = ExportResult(
            success=len(errors) == 0,
            task_id=request.task_id,
            output_dir=str(output_dir),
            files=files,
            errors=errors,
        )

        if result.success:
            logger.info(f"[Publisher] 报告发布成功，生成 {len(files)} 个文件")
        else:
            logger.warning(f"[Publisher] 报告发布部分失败: {errors}")

        return result

    def publish_simple(
        self,
        task_id: str,
        title: str,
        content: str,
        sources: Optional[list[str]] = None,
        formats: Optional[list[str]] = None,
    ) -> ExportResult:
        """
        简化的发布接口

        Args:
            task_id: 任务 ID
            title: 报告标题
            content: 报告内容（Markdown）
            sources: 引用来源列表
            formats: 导出格式列表，默认 ["html", "pdf"]

        Returns:
            ExportResult: 导出结果
        """
        # 解析格式
        if formats is None:
            export_formats = [ExportFormat.HTML, ExportFormat.PDF]
        else:
            export_formats = [ExportFormat(f) for f in formats]

        request = ExportRequest(
            task_id=task_id,
            title=title,
            content=content,
            sources=sources or [],
            formats=export_formats,
        )

        return self.publish(request)

    @staticmethod
    def list_supported_formats() -> list[str]:
        """列出支持的导出格式"""
        return [fmt.value for fmt in EXPORTERS.keys()]


def publisher_node(state: dict) -> dict:
    """LangGraph 节点函数"""
    draft = state.get("draft")
    task_id = state.get("task_id", "default")

    if not draft:
        return {
            **state,
            "publish_result": ExportResult(
                success=False,
                task_id=task_id,
                output_dir="",
                files={},
                errors=["缺少报告草稿"],
            ),
        }

    publisher = Publisher()

    # 合并报告内容
    full_content = f"# {draft.title}\n\n{draft.abstract}\n\n"
    for section in draft.sections:
        full_content += f"## {section.title}\n\n{section.content}\n\n"

    # 发布
    result = publisher.publish_simple(
        task_id=task_id,
        title=draft.title,
        content=full_content,
        sources=draft.sources,
        formats=["html", "md"],  # 默认导出 HTML 和 Markdown
    )

    return {
        **state,
        "publish_result": result,
        "output_files": result.files,
    }


async def async_publisher_node(state: dict) -> dict:
    """LangGraph 异步节点函数"""
    # Publisher 操作是 IO 密集型但不需要异步
    # 直接调用同步版本
    return publisher_node(state)
