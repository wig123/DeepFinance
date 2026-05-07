"""Docling PDF 解析器。

使用 Docling 将 PDF 文档解析为 Markdown + 图片。
"""

import json
import logging
import time
from io import StringIO
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DocItemLabel, ImageRefMode, TableItem, PictureItem

from .base import (
    BaseTool,
    DocumentMetadata,
    ParsedDocument,
    ToolResult,
    ToolStatus,
)

logger = logging.getLogger(__name__)


class DoclingParser(BaseTool):
    """使用 Docling 解析 PDF 文档。

    功能:
    - PDF → Markdown + 图片
    - 保留页码信息: <!-- page: N -->
    - 提取图表标题
    - 输出 metadata.json
    - 表格转 Markdown 格式

    Attributes:
        output_base: 输出根目录
        max_pages: 最大页数限制 (默认 100)
        images_scale: 图片缩放比例 (默认 2.0)
        do_table_structure: 是否提取表格结构 (默认 True)
    """

    name = "docling_parser"
    description = "Parse PDF documents to Markdown with images using Docling"

    def __init__(
        self,
        output_base: str | Path = "outputs",
        max_pages: int = 100,
        images_scale: float = 2.0,
        do_table_structure: bool = True,
        enable_image_analysis: bool = False,
        image_analyzer: "ImageAnalyzer | None" = None,
    ):
        """初始化解析器。

        Args:
            output_base: 输出根目录
            max_pages: 最大页数限制
            images_scale: 图片缩放比例
            do_table_structure: 是否提取表格结构
            enable_image_analysis: 是否启用图片智能分析
            image_analyzer: 图片分析器实例
        """
        self.output_base = Path(output_base)
        self.max_pages = max_pages
        self.images_scale = images_scale
        self.do_table_structure = do_table_structure
        self.enable_image_analysis = enable_image_analysis
        self.image_analyzer = image_analyzer
        self._converter: DocumentConverter | None = None

    @property
    def converter(self) -> DocumentConverter:
        """获取或创建 DocumentConverter 实例。"""
        if self._converter is None:
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = self.do_table_structure
            pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            pipeline_options.generate_picture_images = True
            pipeline_options.images_scale = self.images_scale

            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        return self._converter

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

            # 解析文档
            logger.info(f"开始解析文档: {source_path}")
            result = self.converter.convert(str(source_path))
            doc = result.document

            # 构建带页码标记的 Markdown
            content_md, figures_info, tables_info, text_blocks_info = self._build_markdown_with_pages(
                doc, images_dir
            )

            # 收集图片列表
            images = list(images_dir.glob("*.png"))

            # 构建元数据
            page_count = result.input.page_count if result.input.page_count else 0
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

            # 构建结果
            parsed_doc = ParsedDocument(
                name=doc_name,
                source_path=source_path,
                output_dir=out_dir,
                content_md=content_md,
                images=images,
                metadata=metadata.to_dict(),
                page_count=page_count,
                tables_count=len(tables_info),
                figures_count=len(figures_info),
            )

            elapsed = time.time() - start_time
            logger.info(f"解析完成: {doc_name}, 耗时 {elapsed:.2f}s")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=parsed_doc,
                message=f"成功解析文档: {doc_name}",
                elapsed_time=elapsed,
                metadata={
                    "pages": page_count,
                    "tables": len(tables_info),
                    "figures": len(figures_info),
                },
            )

        except Exception as e:
            logger.exception(f"解析失败: {source_path}")
            return ToolResult.error(f"解析失败: {str(e)}")

    def _build_markdown_with_pages(
        self, doc: Any, images_dir: Path
    ) -> tuple[str, list[dict], list[dict], list[dict]]:
        """构建带页码标记的 Markdown 内容（支持批量异步图片分析）。

        Args:
            doc: Docling 文档对象
            images_dir: 图片保存目录

        Returns:
            tuple: (markdown内容, 图表信息列表, 表格信息列表, 文本块信息列表)
        """
        # ===== 阶段 1: 收集所有元素并保存图片 =====
        elements = []  # 保存所有文档元素信息
        figures_info: list[dict] = []
        tables_info: list[dict] = []
        text_blocks_info: list[dict] = []  # 文本块 bbox 信息
        image_paths: list[Path] = []  # 收集所有图片路径
        current_page = -1
        figure_counter = 0
        table_counter = 0
        text_block_counter = 0

        logger.info("阶段 1: 收集文档元素并保存图片...")

        for item, level in doc.iterate_items():
            # 获取页码信息
            page_no = self._get_page_number(item)
            if page_no is not None and page_no != current_page:
                current_page = page_no
                elements.append({"type": "page_marker", "page": current_page + 1})

            # 处理不同类型的元素
            if hasattr(item, "label"):
                label = item.label

                if label == DocItemLabel.SECTION_HEADER:
                    heading_level = min(level + 1, 6)
                    elements.append(
                        {
                            "type": "heading",
                            "level": heading_level,
                            "text": item.text,
                        }
                    )
                    # 提取标题的 bbox
                    text_block_counter += 1
                    text_block = self._extract_text_block(
                        item, doc, current_page + 1, text_block_counter
                    )
                    if text_block:
                        text_blocks_info.append(text_block)

                elif label in (DocItemLabel.TEXT, DocItemLabel.PARAGRAPH):
                    elements.append({"type": "text", "text": item.text})
                    # 提取文本段落的 bbox
                    text_block_counter += 1
                    text_block = self._extract_text_block(
                        item, doc, current_page + 1, text_block_counter
                    )
                    if text_block:
                        text_blocks_info.append(text_block)

                elif label == DocItemLabel.LIST_ITEM:
                    elements.append({"type": "list_item", "text": item.text})
                    # 提取列表项的 bbox（之前遗漏了！）
                    text_block_counter += 1
                    text_block = self._extract_text_block(
                        item, doc, current_page + 1, text_block_counter
                    )
                    if text_block:
                        text_blocks_info.append(text_block)

                elif label == DocItemLabel.TABLE:
                    table_counter += 1
                    table_md, table_info = self._process_table(
                        item, doc, table_counter, current_page + 1
                    )
                    elements.append({"type": "table", "markdown": table_md})
                    tables_info.append(table_info)

                elif label == DocItemLabel.PICTURE:
                    figure_counter += 1
                    # 只保存图片，不生成 Markdown
                    figure_info = self._save_figure(
                        item, doc, images_dir, figure_counter, current_page + 1
                    )
                    if figure_info["filename"]:
                        image_paths.append(images_dir / figure_info["filename"])
                    elements.append(
                        {
                            "type": "figure",
                            "figure_num": figure_counter,
                            "figure_info": figure_info,
                        }
                    )
                    figures_info.append(figure_info)

                elif label == DocItemLabel.CAPTION:
                    elements.append({"type": "caption", "text": item.text})

                elif label == DocItemLabel.FORMULA:
                    elements.append({"type": "formula", "text": item.text})

                elif label == DocItemLabel.CODE:
                    elements.append({"type": "code", "text": item.text})

                elif label == DocItemLabel.FOOTNOTE:
                    elements.append({"type": "footnote", "text": item.text})

        # ===== 阶段 2: 批量异步分析图片 =====
        analysis_results = {}
        if self.enable_image_analysis and self.image_analyzer and image_paths:
            logger.info(
                f"阶段 2: 批量异步分析 {len(image_paths)} 张图片..."
            )
            analysis_results = self.image_analyzer.analyze_images_batch(image_paths)

            # 回填分析结果到 figures_info
            for fig_info in figures_info:
                if fig_info["filename"]:
                    img_path = images_dir / fig_info["filename"]
                    if img_path in analysis_results:
                        result = analysis_results[img_path]
                        fig_info["image_type"] = result.get("image_type")
                        if "analysis" in result:
                            fig_info["analysis"] = result["analysis"]
                        if "description" in result:
                            fig_info["description"] = result["description"]

        # ===== 阶段 3: 生成 Markdown =====
        logger.info("阶段 3: 生成 Markdown 内容...")
        buffer = StringIO()

        for elem in elements:
            elem_type = elem["type"]

            if elem_type == "page_marker":
                buffer.write(f"\n<!-- page: {elem['page']} -->\n\n")

            elif elem_type == "heading":
                buffer.write(f"{'#' * elem['level']} {elem['text']}\n\n")

            elif elem_type == "text":
                buffer.write(f"{elem['text']}\n\n")

            elif elem_type == "list_item":
                buffer.write(f"- {elem['text']}\n")

            elif elem_type == "table":
                buffer.write(elem["markdown"])

            elif elem_type == "figure":
                # 生成图片 Markdown（包含分析结果）
                figure_md = self._generate_figure_markdown(
                    elem["figure_num"], elem["figure_info"]
                )
                buffer.write(figure_md)

            elif elem_type == "caption":
                buffer.write(f"*{elem['text']}*\n\n")

            elif elem_type == "formula":
                buffer.write(f"$$\n{elem['text']}\n$$\n\n")

            elif elem_type == "code":
                buffer.write(f"```\n{elem['text']}\n```\n\n")

            elif elem_type == "footnote":
                buffer.write(f"[^{elem['text']}]\n")

        logger.info(f"提取到 {len(text_blocks_info)} 个文本块 bbox")
        return buffer.getvalue(), figures_info, tables_info, text_blocks_info

    def _get_page_number(self, item: Any) -> int | None:
        """获取元素的页码。

        Args:
            item: 文档元素

        Returns:
            页码 (0-indexed) 或 None
        """
        if hasattr(item, "prov") and item.prov:
            for prov in item.prov:
                if hasattr(prov, "page_no"):
                    return prov.page_no
        return None

    def _get_bbox_info(
        self, item: Any, doc: Any, page_no: int
    ) -> dict | None:
        """提取元素的 bbox 坐标信息。

        Docling 使用 BOTTOMLEFT 坐标系（原点在左下角，Y 轴向上），
        PDF.js 使用 TOPLEFT 坐标系（原点在左上角，Y 轴向下）。
        此方法将坐标统一转换为 TOPLEFT 格式。

        Args:
            item: 文档元素
            doc: 文档对象
            page_no: 页码 (1-indexed)

        Returns:
            bbox 信息字典，包含坐标和页面尺寸，或 None
        """
        if not hasattr(item, "prov") or not item.prov:
            return None

        prov = item.prov[0]
        if not hasattr(prov, "bbox") or prov.bbox is None:
            return None

        bbox = prov.bbox

        # 获取页面尺寸
        page_dims = self._get_page_dimensions(doc, page_no - 1)  # 转为 0-indexed
        if not page_dims:
            return None

        page_width, page_height = page_dims

        # Docling bbox 属性: l(left), t(top), r(right), b(bottom)
        # 但注意 Docling 的 t/b 是基于 BOTTOMLEFT 的，需要转换
        l = float(bbox.l) if hasattr(bbox, "l") else 0
        t = float(bbox.t) if hasattr(bbox, "t") else 0
        r = float(bbox.r) if hasattr(bbox, "r") else 0
        b = float(bbox.b) if hasattr(bbox, "b") else 0

        # 检查坐标原点
        coord_origin = "BOTTOMLEFT"
        if hasattr(bbox, "coord_origin"):
            coord_origin = str(bbox.coord_origin.value) if hasattr(bbox.coord_origin, "value") else str(bbox.coord_origin)

        # 转换为 TOPLEFT 坐标系 (PDF.js 标准)
        if coord_origin == "BOTTOMLEFT":
            # BOTTOMLEFT: y=0 在底部，y 向上增加
            # TOPLEFT: y=0 在顶部，y 向下增加
            # 转换公式: new_y = page_height - old_y
            y1 = page_height - t  # top -> y1 (TOPLEFT)
            y2 = page_height - b  # bottom -> y2 (TOPLEFT)
            x1 = l
            x2 = r
        else:
            # 已经是 TOPLEFT
            x1, y1, x2, y2 = l, t, r, b

        return {
            "bbox": {
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2),
                "width": round(x2 - x1, 2),
                "height": round(y2 - y1, 2),
            },
            "page_dimensions": {
                "width": round(page_width, 2),
                "height": round(page_height, 2),
            },
        }

    def _get_page_dimensions(self, doc: Any, page_index: int) -> tuple[float, float] | None:
        """获取指定页面的尺寸。

        Args:
            doc: 文档对象
            page_index: 页码索引 (0-indexed)

        Returns:
            (width, height) 元组，或 None
        """
        try:
            # 尝试从 doc.pages 获取页面尺寸
            if hasattr(doc, "pages") and doc.pages:
                if page_index < len(doc.pages):
                    page = doc.pages[page_index]
                    if hasattr(page, "size"):
                        size = page.size
                        if hasattr(size, "width") and hasattr(size, "height"):
                            return (float(size.width), float(size.height))

            # 默认 Letter 尺寸 (8.5 x 11 inches at 72 dpi)
            return (612.0, 792.0)
        except Exception as e:
            logger.warning(f"获取页面尺寸失败: {e}")
            return (612.0, 792.0)

    def _process_table(
        self, item: Any, doc: Any, table_num: int, page_no: int
    ) -> tuple[str, dict]:
        """处理表格元素。

        Args:
            item: 表格元素
            doc: 文档对象
            table_num: 表格序号
            page_no: 页码

        Returns:
            tuple: (Markdown表格, 表格信息字典)
        """
        buffer = StringIO()

        # 获取表格标题
        caption = ""
        if hasattr(item, "caption_text"):
            caption = item.caption_text(doc=doc) or ""

        if caption:
            buffer.write(f"**表 {table_num}**: {caption}\n\n")
        else:
            buffer.write(f"**表 {table_num}**\n\n")

        # 导出表格为 DataFrame 再转 Markdown
        try:
            if hasattr(item, "export_to_dataframe"):
                df = item.export_to_dataframe()
                buffer.write(df.to_markdown(index=False))
                buffer.write("\n\n")
            elif hasattr(item, "text"):
                buffer.write(f"{item.text}\n\n")
        except Exception as e:
            logger.warning(f"表格导出失败: {e}")
            if hasattr(item, "text"):
                buffer.write(f"{item.text}\n\n")

        # 构建表格信息（包含 bbox）
        table_info = {
            "id": f"table_{table_num}",
            "page": page_no,
            "caption": caption,
        }

        # 提取 bbox 坐标
        bbox_info = self._get_bbox_info(item, doc, page_no)
        if bbox_info:
            table_info["bbox"] = bbox_info["bbox"]
            table_info["page_dimensions"] = bbox_info["page_dimensions"]

        return buffer.getvalue(), table_info

    def _save_figure(
        self,
        item: Any,
        doc: Any,
        images_dir: Path,
        figure_num: int,
        page_no: int,
    ) -> dict:
        """保存图片（不生成 Markdown）。

        Args:
            item: 图片元素
            doc: 文档对象
            images_dir: 图片保存目录
            figure_num: 图片序号
            page_no: 页码

        Returns:
            图片信息字典
        """
        # 生成图片文件名: p{page}_fig_{num}.png
        image_filename = f"p{page_no}_fig_{figure_num:03d}.png"
        image_path = images_dir / image_filename

        # 获取图片标题
        caption = ""
        if hasattr(item, "caption_text"):
            caption = item.caption_text(doc=doc) or ""

        # 保存图片
        saved = False
        if hasattr(item, "image") and item.image:
            try:
                if hasattr(item.image, "pil_image") and item.image.pil_image:
                    item.image.pil_image.save(str(image_path))
                    saved = True
                elif hasattr(item.image, "uri") and item.image.uri:
                    # 如果是 data URI，尝试解码保存
                    uri = str(item.image.uri)
                    if uri.startswith("data:image"):
                        import base64

                        # 提取 base64 数据
                        data_start = uri.find(",") + 1
                        if data_start > 0:
                            img_data = base64.b64decode(uri[data_start:])
                            image_path.write_bytes(img_data)
                            saved = True
            except Exception as e:
                logger.warning(f"图片保存失败: {e}")

        # 构建图片信息（包含 bbox）
        figure_info = {
            "id": f"fig_{figure_num}",
            "page": page_no,
            "caption": caption,
            "filename": image_filename if saved else None,
        }

        # 提取 bbox 坐标
        bbox_info = self._get_bbox_info(item, doc, page_no)
        if bbox_info:
            figure_info["bbox"] = bbox_info["bbox"]
            figure_info["page_dimensions"] = bbox_info["page_dimensions"]

        return figure_info

    def _generate_figure_markdown(self, figure_num: int, figure_info: dict) -> str:
        """根据图片信息和分析结果生成 Markdown。

        Args:
            figure_num: 图片序号
            figure_info: 图片信息字典（包含可能的分析结果）

        Returns:
            Markdown 文本
        """
        buffer = StringIO()

        # 图片引用
        if figure_info["filename"]:
            buffer.write(f"![图 {figure_num}](images/{figure_info['filename']})\n\n")
        else:
            buffer.write(f"<!-- 图 {figure_num}: 图片提取失败 -->\n\n")

        # 图片标题
        if figure_info.get("caption"):
            buffer.write(f"*图 {figure_num}: {figure_info['caption']}*\n\n")

        # 回填分析结果
        if "analysis" in figure_info:
            buffer.write("**【图表分析】**\n\n")
            analysis = figure_info["analysis"]
            for section_name in ["图表构成", "数据关系", "模式特征", "核心洞察"]:
                if section_name in analysis and analysis[section_name]:
                    buffer.write(f"**{section_name}**\n\n")
                    buffer.write(f"{analysis[section_name]}\n\n")

        elif "description" in figure_info:
            buffer.write("**【图片描述】**\n\n")
            buffer.write(f"{figure_info['description']}\n\n")

        elif figure_info.get("image_type") == "icon":
            buffer.write("*（装饰性图标，已忽略）*\n\n")

        return buffer.getvalue()

    def _extract_text_block(
        self,
        item: Any,
        doc: Any,
        page_no: int,
        block_counter: int,
    ) -> dict | None:
        """提取文本块信息（含 bbox 坐标）。

        提取文本段落、标题等文本元素的坐标信息，用于后续的精确定位。
        只保存前 100 个字符作为预览，用于模糊匹配。

        Args:
            item: 文档元素
            doc: 文档对象
            page_no: 页码 (1-indexed)
            block_counter: 文本块序号

        Returns:
            文本块信息字典，或 None（如果无有效 bbox）
        """
        if not hasattr(item, "text") or not item.text:
            return None

        text = item.text.strip()
        if len(text) < 10:  # 跳过过短的文本
            return None

        # 提取 bbox 坐标
        bbox_info = self._get_bbox_info(item, doc, page_no)
        if not bbox_info:
            return None

        # 获取元素类型
        label_name = "text"
        if hasattr(item, "label"):
            label_name = str(item.label.value) if hasattr(item.label, "value") else str(item.label)

        return {
            "id": f"text_p{page_no}_{block_counter:03d}",
            "page": page_no,
            "type": label_name,
            "content_preview": text[:300],  # 保存前 300 字符用于匹配（之前 100 太少）
            "content_length": len(text),
            "bbox": bbox_info["bbox"],
            "page_dimensions": bbox_info["page_dimensions"],
        }

    def parse_directory(
        self, directory: str | Path
    ) -> ToolResult[list[ParsedDocument]]:
        """批量解析目录下的所有 PDF 文件。

        Args:
            directory: PDF 文件目录

        Returns:
            ToolResult[list[ParsedDocument]]: 解析结果列表
        """
        start_time = time.time()
        dir_path = Path(directory)

        if not dir_path.is_dir():
            return ToolResult.error(f"目录不存在: {dir_path}")

        pdf_files = list(dir_path.glob("*.pdf"))
        if not pdf_files:
            return ToolResult.error(f"目录中没有 PDF 文件: {dir_path}")

        results: list[ParsedDocument] = []
        errors: list[str] = []

        for pdf_path in pdf_files:
            result = self.execute(pdf_path)
            if result.success and result.data:
                results.append(result.data)
            else:
                errors.append(f"{pdf_path.name}: {result.message}")

        elapsed = time.time() - start_time

        if not results:
            return ToolResult.error(
                f"所有文件解析失败 ({len(errors)}/{len(pdf_files)})", errors
            )

        if errors:
            return ToolResult(
                status=ToolStatus.PARTIAL,
                data=results,
                message=f"部分解析成功: {len(results)}/{len(pdf_files)}",
                errors=errors,
                elapsed_time=elapsed,
            )

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=results,
            message=f"全部解析成功: {len(results)} 个文件",
            elapsed_time=elapsed,
        )
