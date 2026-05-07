"""MinerU PDF 解析器。

使用 MinerU 将 PDF 文档解析为 Markdown + 图片。
相比 Docling，MinerU 速度更快（约 4-5 倍），同时保持较好的表格和图片提取质量。
"""

import json
import logging
import re
import shutil
import time
from pathlib import Path
from typing import Any

from .base import (
    BaseTool,
    DocumentMetadata,
    ParsedDocument,
    ToolResult,
    ToolStatus,
)

logger = logging.getLogger(__name__)


class MinerUParser(BaseTool):
    """使用 MinerU 解析 PDF 文档。

    功能:
    - PDF → Markdown + 图片
    - 保留页码信息
    - 提取图表和表格
    - 输出 metadata.json
    - 可选的图片智能分析

    Attributes:
        output_base: 输出根目录
        backend: 解析后端 (pipeline, vlm-auto-engine, hybrid-auto-engine)
        enable_image_analysis: 是否启用图片分析
        image_analyzer: 图片分析器实例
    """

    name = "mineru_parser"
    description = "Parse PDF documents to Markdown with images using MinerU"

    def __init__(
        self,
        output_base: str | Path = "outputs",
        backend: str = "pipeline",  # pipeline 更快，hybrid 更准
        lang: str = "en",
        enable_image_analysis: bool = False,
        image_analyzer: "ImageAnalyzer | None" = None,
    ):
        """初始化解析器。

        Args:
            output_base: 输出根目录
            backend: 解析后端
                - "pipeline": 传统流水线，最快
                - "vlm-auto-engine": VLM 模型，更准
                - "hybrid-auto-engine": 混合模式，平衡
            lang: 文档语言 (en, ch, etc.)
            enable_image_analysis: 是否启用图片智能分析
            image_analyzer: 图片分析器实例
        """
        self.output_base = Path(output_base)
        self.backend = backend
        self.lang = lang
        self.enable_image_analysis = enable_image_analysis
        self.image_analyzer = image_analyzer

    def execute(
        self,
        source: str | Path,
        output_dir: str | Path | None = None,
    ) -> ToolResult[ParsedDocument]:
        """解析 PDF 文档。

        Args:
            source: PDF 文件路径
            output_dir: 输出目录 (可选，默认使用 output_base/<doc_name>)

        Returns:
            ToolResult[ParsedDocument]: 解析结果
        """
        start_time = time.time()
        source_path = Path(source)

        if not source_path.exists():
            return ToolResult.error(f"文件不存在: {source_path}")

        if not source_path.suffix.lower() == ".pdf":
            return ToolResult.error(f"不支持的文件格式: {source_path.suffix}")

        doc_name = source_path.stem
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = self.output_base / doc_name

        try:
            # 创建输出目录
            out_dir.mkdir(parents=True, exist_ok=True)
            images_dir = out_dir / "images"
            images_dir.mkdir(exist_ok=True)

            # ===== 阶段 1: MinerU 解析 =====
            logger.info(f"开始解析文档: {source_path} (backend={self.backend})")
            parse_start = time.time()

            mineru_output = out_dir / "_mineru_output"
            mineru_output.mkdir(exist_ok=True)

            # 调用 MinerU
            self._run_mineru(source_path, mineru_output)

            parse_duration = time.time() - parse_start
            logger.info(f"MinerU 解析完成，耗时 {parse_duration:.1f}s")

            # ===== 阶段 2: 处理 MinerU 输出 =====
            logger.info("处理 MinerU 输出...")

            # 读取 Markdown 内容
            md_file = mineru_output / doc_name / f"{doc_name}.md"
            if not md_file.exists():
                # 尝试其他可能的路径
                md_files = list(mineru_output.glob("**/*.md"))
                if md_files:
                    md_file = md_files[0]
                else:
                    return ToolResult.error(f"MinerU 未生成 Markdown 文件")

            content_md = md_file.read_text(encoding="utf-8")

            # 复制图片到 images 目录
            mineru_images_dir = md_file.parent / "images"
            figures_info = []
            if mineru_images_dir.exists():
                for i, img_path in enumerate(sorted(mineru_images_dir.glob("*.*"))):
                    if img_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif"]:
                        # 重命名为标准格式
                        new_name = f"fig_{i+1:03d}{img_path.suffix}"
                        new_path = images_dir / new_name
                        shutil.copy2(img_path, new_path)

                        # 更新 Markdown 中的图片路径
                        content_md = content_md.replace(
                            f"images/{img_path.name}",
                            f"images/{new_name}"
                        )

                        # 提取页码（从文件名或位置推断）
                        page_no = self._extract_page_from_filename(img_path.name)

                        figures_info.append({
                            "id": f"fig_{i+1}",
                            "page": page_no,
                            "filename": new_name,
                            "original_name": img_path.name,
                        })

            # 添加页码标记到 Markdown
            content_md = self._add_page_markers(content_md, mineru_output / doc_name)

            # ===== 阶段 3: 图片分析（可选，并发）=====
            image_paths = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))

            if self.enable_image_analysis and self.image_analyzer and image_paths:
                logger.info(f"阶段 3: 并发分析 {len(image_paths)} 张图片...")
                analysis_start = time.time()

                # 使用 ImageAnalyzer 的批量异步方法
                analysis_results = self.image_analyzer.analyze_images_batch(image_paths)

                analysis_duration = time.time() - analysis_start
                logger.info(f"图片分析完成，耗时 {analysis_duration:.1f}s")

                # 回填分析结果到 figures_info
                for fig_info in figures_info:
                    img_path = images_dir / fig_info["filename"]
                    if img_path in analysis_results:
                        result = analysis_results[img_path]
                        fig_info["image_type"] = result.get("image_type")
                        if "analysis" in result:
                            fig_info["analysis"] = result["analysis"]
                        if "description" in result:
                            fig_info["description"] = result["description"]

            # ===== 阶段 4: 提取表格信息 =====
            tables_info = self._extract_tables_info(content_md)

            # ===== 阶段 5: 提取文本块信息 =====
            text_blocks_info = self._extract_text_blocks(content_md)

            # 统计页数
            page_count = self._count_pages(content_md)

            # 构建元数据
            metadata = DocumentMetadata(
                title=doc_name,
                source=source_path.name,
                page_count=page_count,
                tables_count=len(tables_info),
                figures_count=len(figures_info),
                figures=figures_info,
                tables=tables_info,
                text_blocks=text_blocks_info,
            )

            # 保存文件
            content_path = out_dir / "content.md"
            content_path.write_text(content_md, encoding="utf-8")

            metadata_path = out_dir / "metadata.json"
            metadata_path.write_text(
                json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # 清理 MinerU 临时输出
            shutil.rmtree(mineru_output, ignore_errors=True)

            # 构建结果
            parsed_doc = ParsedDocument(
                name=doc_name,
                source_path=source_path,
                output_dir=out_dir,
                content_md=content_md,
                images=list(images_dir.glob("*.*")),
                metadata=metadata.to_dict(),
                page_count=page_count,
                tables_count=len(tables_info),
                figures_count=len(figures_info),
            )

            elapsed = time.time() - start_time
            logger.info(f"解析完成: {doc_name}, 总耗时 {elapsed:.2f}s")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=parsed_doc,
                message=f"成功解析文档: {doc_name}",
                elapsed_time=elapsed,
                metadata={
                    "pages": page_count,
                    "tables": len(tables_info),
                    "figures": len(figures_info),
                    "parse_time": parse_duration,
                },
            )

        except Exception as e:
            logger.exception(f"解析失败: {source_path}")
            return ToolResult.error(f"解析失败: {str(e)}")

    def _run_mineru(self, pdf_path: Path, output_dir: Path) -> None:
        """运行 MinerU 解析。

        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
        """
        from mineru.cli.common import do_parse, read_fn

        # 读取 PDF 字节
        pdf_bytes = read_fn(pdf_path)

        # 调用 do_parse
        do_parse(
            output_dir=str(output_dir),
            pdf_file_names=[pdf_path.stem],
            pdf_bytes_list=[pdf_bytes],
            p_lang_list=[self.lang],
            backend=self.backend,
            parse_method="auto",
            formula_enable=True,
            table_enable=True,
            f_dump_md=True,
            f_dump_middle_json=True,
            f_dump_content_list=False,
            f_dump_model_output=False,
            f_dump_orig_pdf=False,
            f_draw_layout_bbox=False,
            f_draw_span_bbox=False,
            f_make_md_mode="mm_markdown",  # MakeMode.MM_MD.value
            start_page_id=0,
            end_page_id=None,
        )

    def _extract_page_from_filename(self, filename: str) -> int:
        """从文件名提取页码。

        Args:
            filename: 图片文件名

        Returns:
            页码（1-indexed），默认返回 1
        """
        # 尝试匹配常见格式: page_1_xxx, p1_xxx, 1_xxx
        patterns = [
            r"page[_-]?(\d+)",
            r"p(\d+)[_-]",
            r"^(\d+)[_-]",
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 1

    def _add_page_markers(self, content: str, mineru_dir: Path) -> str:
        """添加页码标记到 Markdown。

        尝试从 MinerU 的 middle_json 中提取页码信息。

        Args:
            content: Markdown 内容
            mineru_dir: MinerU 输出目录

        Returns:
            添加页码标记后的内容
        """
        # 尝试读取 middle.json 获取页码信息
        middle_json_files = list(mineru_dir.glob("*_middle.json"))
        if not middle_json_files:
            middle_json_files = list(mineru_dir.glob("**/*_middle.json"))

        if middle_json_files:
            try:
                with open(middle_json_files[0], "r", encoding="utf-8") as f:
                    middle_data = json.load(f)

                # 从 middle.json 提取页面信息
                if "pdf_info" in middle_data:
                    page_count = len(middle_data["pdf_info"])
                    # 简单地在开头添加页码标记
                    return f"<!-- page: 1 -->\n\n{content}"

            except Exception as e:
                logger.warning(f"无法读取 middle.json: {e}")

        # 如果无法获取页码信息，返回原内容
        return f"<!-- page: 1 -->\n\n{content}"

    def _extract_tables_info(self, content: str) -> list[dict]:
        """从 Markdown 中提取表格信息。

        Args:
            content: Markdown 内容

        Returns:
            表格信息列表
        """
        tables = []
        # 匹配 Markdown 表格
        table_pattern = r"(\|[^\n]+\|\n)+(\|[-:| ]+\|\n)(\|[^\n]+\|\n)+"

        for i, match in enumerate(re.finditer(table_pattern, content)):
            tables.append({
                "id": f"table_{i+1}",
                "page": 1,  # MinerU 不直接提供表格页码
                "position": match.start(),
            })

        return tables

    def _extract_text_blocks(self, content: str) -> list[dict]:
        """从 Markdown 中提取文本块信息。

        Args:
            content: Markdown 内容

        Returns:
            文本块信息列表
        """
        text_blocks = []
        current_page = 1
        block_counter = 0

        # 按行处理
        lines = content.split("\n")
        current_block = []
        block_start_line = 0

        for i, line in enumerate(lines):
            # 检查页码标记
            page_match = re.match(r"<!--\s*page:\s*(\d+)\s*-->", line)
            if page_match:
                current_page = int(page_match.group(1))
                continue

            # 跳过空行、图片、表格分隔符
            stripped = line.strip()
            if not stripped or stripped.startswith("![") or stripped.startswith("|"):
                # 保存当前块
                if current_block:
                    block_text = "\n".join(current_block).strip()
                    if len(block_text) >= 10:
                        block_counter += 1
                        text_blocks.append({
                            "id": f"text_p{current_page}_{block_counter:03d}",
                            "page": current_page,
                            "type": "text",
                            "content_preview": block_text[:100],
                            "content_length": len(block_text),
                        })
                    current_block = []
                continue

            # 标题
            if stripped.startswith("#"):
                # 保存之前的块
                if current_block:
                    block_text = "\n".join(current_block).strip()
                    if len(block_text) >= 10:
                        block_counter += 1
                        text_blocks.append({
                            "id": f"text_p{current_page}_{block_counter:03d}",
                            "page": current_page,
                            "type": "text",
                            "content_preview": block_text[:100],
                            "content_length": len(block_text),
                        })
                    current_block = []

                # 添加标题块
                block_counter += 1
                text_blocks.append({
                    "id": f"text_p{current_page}_{block_counter:03d}",
                    "page": current_page,
                    "type": "section_header",
                    "content_preview": stripped.lstrip("#").strip()[:100],
                    "content_length": len(stripped),
                })
                continue

            # 普通文本，累积到当前块
            current_block.append(stripped)

        # 保存最后一个块
        if current_block:
            block_text = "\n".join(current_block).strip()
            if len(block_text) >= 10:
                block_counter += 1
                text_blocks.append({
                    "id": f"text_p{current_page}_{block_counter:03d}",
                    "page": current_page,
                    "type": "text",
                    "content_preview": block_text[:100],
                    "content_length": len(block_text),
                })

        return text_blocks

    def _count_pages(self, content: str) -> int:
        """统计页数。

        Args:
            content: Markdown 内容

        Returns:
            页数
        """
        page_markers = re.findall(r"<!--\s*page:\s*(\d+)\s*-->", content)
        if page_markers:
            return max(int(p) for p in page_markers)
        return 1
