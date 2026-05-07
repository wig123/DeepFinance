"""引用查询路由"""

import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from rapidfuzz import fuzz, process

# 调试日志路径：默认 <项目根>/.cursor/debug.log，可用环境变量 DEBUG_LOG_PATH 覆盖。
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEBUG_LOG_PATH = Path(os.environ.get("DEBUG_LOG_PATH", _PROJECT_ROOT / ".cursor" / "debug.log"))

from src.api.schemas.citation import (
    CitationResponse,
    PDFHighlight,
    BoundingRect,
    PageDimensions,
)
from src.api.services.project_service import project_service

logger = logging.getLogger(__name__)
router = APIRouter()


# 模块级别的调试日志函数
def _debug_log(loc: str, msg: str, data: dict, hypothesis_id: str = ""):
    """写入调试日志到 NDJSON 文件"""
    import time
    log_path = DEBUG_LOG_PATH
    log_entry = {
        "location": loc,
        "message": msg,
        "data": data,
        "hypothesisId": hypothesis_id or data.get("hypothesisId", ""),
    }
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_json_file(file_path: Path) -> dict | None:
    """加载 JSON 文件"""
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def _find_citation_page_from_report(project_dir: Path, citation_id: str) -> int | None:
    """从报告中查找引用对应的页码（兼容接口）。

    Args:
        project_dir: 项目目录
        citation_id: 引用ID

    Returns:
        页码（1-indexed），未找到返回 None
    """
    page, _, _ = _find_citation_page_and_text_from_report(project_dir, citation_id)
    return page


def _find_citation_page_and_text_from_report(
    project_dir: Path, citation_id: str
) -> tuple[int | None, str | None, str | None]:
    """从报告中查找引用对应的页码、原文摘录和位置信息。

    通过以下步骤定位页码：
    1. 从 report.md 中读取引用定义，提取原文摘录和位置URL
    2. 在 content.md 中搜索包含该原文的段落
    3. 返回该段落所在的页码、原文和位置信息

    Args:
        project_dir: 项目目录
        citation_id: 引用ID（如 doc-q3-25-summary-1）

    Returns:
        (页码, 原文摘录, 位置信息) 元组，如 (2, "Revenue in Q3...", "page-2#table-1")
        未找到返回 (None, None, None)
    """
    import re

    # 读取报告文件
    report_path = project_dir / "report.md"
    if not report_path.exists():
        return None, None, None

    report_content = report_path.read_text(encoding="utf-8")

    # 查找引用定义，提取原文摘录和位置URL
    # 格式: [^citation_id]: [标题](source/content.md#page-2#table-1) | 原文："摘录内容"
    # 使用 IGNORECASE 因为前端可能将引用 ID 转换为小写
    pattern = rf'^\[\^{re.escape(citation_id)}\]:\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*\|\s*原文[：:]\s*["\"]([^"\"]+)["\"])?'
    match = re.search(pattern, report_content, re.MULTILINE | re.IGNORECASE)

    if not match:
        return None, None, None

    title = match.group(1)
    url = match.group(2)  # 如 source/content.md#page-2#table-1
    original_text = match.group(3) if match.group(3) else None

    # 从 URL 中提取位置信息
    # source/content.md#page-2#table-1 -> page-2#table-1
    location_match = re.search(r'#(page-\d+(?:#[^#]+)?)', url)
    location = location_match.group(1) if location_match else None

    # 从 location 中提取页码
    # page-2#table-1 -> 2
    page_match = re.search(r'page-(\d+)', location or url)
    page_number = int(page_match.group(1)) if page_match else None

    if not original_text:
        # 如果没有原文，直接返回从 URL 提取的页码和位置
        return page_number, None, location

    # 提取关键词进行搜索（取前50个字符作为搜索关键词）
    # 去除 Markdown 格式符号
    search_text = re.sub(r'\*+', '', original_text)[:50]

    if len(search_text) < 5:
        return page_number, original_text, location

    # 读取 content.md
    source_dir = project_dir / "source"
    content_files = list(source_dir.glob("*/content.md"))
    if not content_files:
        content_path = source_dir / "content.md"
        if content_path.exists():
            content_files = [content_path]

    if not content_files:
        return page_number, original_text, location

    content = content_files[0].read_text(encoding="utf-8")

    # 在 content.md 中查找原文位置（可能更准确）
    lines = content.split("\n")
    current_page = 1

    for line in lines:
        # 更新当前页码
        page_match_line = re.match(r"<!--\s*page:\s*(\d+)\s*-->", line)
        if page_match_line:
            current_page = int(page_match_line.group(1))
            continue

        # 检查是否包含搜索文本（忽略大小写和空格差异）
        line_normalized = line.lower().replace(" ", "")
        search_normalized = search_text.lower().replace(" ", "")

        if search_normalized[:20] in line_normalized:
            # 如果在 content 中找到更精确的页码，使用它；否则使用从 URL 提取的页码
            return current_page, original_text, location

    # 如果精确匹配失败，尝试模糊匹配（搜索关键数字或短语）
    # 提取原文中的数字
    numbers = re.findall(r'\d+\.?\d*%?', original_text)
    if numbers and len(numbers) >= 2:
        # 使用前两个数字作为特征
        current_page = 1
        for line in lines:
            page_match_line = re.match(r"<!--\s*page:\s*(\d+)\s*-->", line)
            if page_match_line:
                current_page = int(page_match_line.group(1))
                continue

            # 检查行中是否包含这些数字
            if numbers[0] in line and numbers[1] in line:
                return current_page, original_text, location

    # 使用从 URL 提取的页码作为兜底
    return page_number, original_text, location


def _find_text_block_by_fuzzy_match(
    project_dir: Path, search_text: str, target_page: int | None = None
) -> dict | None:
    """通过模糊匹配在 text_blocks 中查找最佳匹配的文本块。

    先在 content.md 中定位完整文本，再从 metadata 中获取对应的 bbox。

    Args:
        project_dir: 项目目录
        search_text: 要搜索的文本（引用原文）
        target_page: 目标页码（可选，用于缩小搜索范围）

    Returns:
        匹配的文本块信息，包含 bbox，或 None
    """
    import re
    import json as _json
    from pathlib import Path as _Path

    # #region agent log
    _log_path = DEBUG_LOG_PATH
    def _debug_log(loc, msg, data):
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps({"location": loc, "message": msg, "data": data}, ensure_ascii=False) + "\n")
    # #endregion

    # 清理搜索文本
    clean_search = re.sub(r'\*+', '', search_text)
    clean_search = re.sub(r'\s+', ' ', clean_search).strip()

    if len(clean_search) < 10:
        return None

    # Step 1: 在 content.md 中找到包含该文本的段落和页码
    source_dir = project_dir / "source"
    content_files = list(source_dir.glob("*/content.md"))
    if not content_files:
        content_path = source_dir / "content.md"
        if content_path.exists():
            content_files = [content_path]

    if not content_files:
        # #region agent log
        _debug_log("fuzzy:no_content", "No content.md files found", {"source_dir": str(source_dir), "hypothesisId": "H3"})
        # #endregion
        return None

    content = content_files[0].read_text(encoding="utf-8")

    # 按段落分割，记录每个段落的页码
    lines = content.split("\n")
    current_page = 1
    current_paragraph = []
    paragraphs = []  # [(page, text), ...]

    for line in lines:
        # 更新页码
        page_match = re.match(r"<!--\s*page:\s*(\d+)\s*-->", line)
        if page_match:
            if current_paragraph:
                paragraphs.append((current_page, ' '.join(current_paragraph)))
                current_paragraph = []
            current_page = int(page_match.group(1))
            continue

        # 跳过空行和标题
        if line.strip() and not line.startswith('#') and not line.startswith('!'):
            current_paragraph.append(line.strip())
        elif current_paragraph and line.strip() == '':
            # 段落结束
            paragraphs.append((current_page, ' '.join(current_paragraph)))
            current_paragraph = []

    if current_paragraph:
        paragraphs.append((current_page, ' '.join(current_paragraph)))

    # 过滤到目标页
    if target_page:
        paragraphs = [(p, t) for p, t in paragraphs if p == target_page]

    # Step 2: 使用模糊匹配找到最佳段落
    best_match_page = None
    best_match_text = None
    best_score = 0

    for page, para_text in paragraphs:
        # 清理段落前缀（如列表项 "- "）
        clean_para = re.sub(r'^[\-\*•]\s*', '', para_text.strip())
        # 使用更长的文本进行匹配
        score = fuzz.partial_ratio(clean_search[:200], clean_para[:400])
        if score > best_score:
            best_score = score
            best_match_page = page
            best_match_text = para_text

    # #region agent log
    _debug_log("fuzzy:content_match", "Content.md fuzzy match result", {"best_score": best_score, "best_match_page": best_match_page, "target_page": target_page, "paragraphs_count": len(paragraphs), "search_preview": clean_search[:50], "hypothesisId": "H3"})
    # #endregion

    # 如果 content.md 匹配分数低，使用目标页面或搜索所有文本块
    use_all_pages = False
    if best_score < 40:
        logger.debug(f"content.md 匹配分数太低: {best_score}, 将直接搜索 metadata 文本块")
        # 如果有目标页面，用目标页面；否则搜索所有页面
        if target_page:
            best_match_page = target_page
        else:
            use_all_pages = True
    else:
        logger.info(f"在 content.md 中找到匹配段落: page={best_match_page}, score={best_score}")

    # Step 3: 从 metadata 中找到该页最长的文本块（通常是主要内容段落）
    metadata_files = list(source_dir.glob("*/metadata.json"))
    if not metadata_files:
        metadata_path = source_dir / "metadata.json"
        if metadata_path.exists():
            metadata_files = [metadata_path]

    if not metadata_files:
        # #region agent log
        _debug_log("fuzzy:no_metadata", "No metadata.json files found", {"source_dir": str(source_dir), "hypothesisId": "H4"})
        # #endregion
        return None

    metadata = load_json_file(metadata_files[0])
    if not metadata:
        return None

    text_blocks = metadata.get("text_blocks", [])
    # #region agent log
    _debug_log("fuzzy:text_blocks", "Text blocks in metadata", {"text_blocks_count": len(text_blocks), "best_match_page": best_match_page, "metadata_file": str(metadata_files[0]), "hypothesisId": "H4"})
    # #endregion
    # 放宽 type 过滤，包含 text 和其他可能包含正文的类型（如 section_header、paragraph 等）
    # 排除明显不是正文的类型（如 figure、table、page_number）
    excluded_types = {"figure", "table", "page_number", "page_footer", "page_header"}
    
    if use_all_pages:
        # 搜索所有页面的文本块
        page_blocks = [b for b in text_blocks if b.get("type") not in excluded_types]
    else:
        page_blocks = [
            b for b in text_blocks 
            if b.get("page") == best_match_page and b.get("type") not in excluded_types
        ]

    # #region agent log
    _debug_log("fuzzy:page_blocks", "Filtered page blocks", {"page_blocks_count": len(page_blocks), "best_match_page": best_match_page, "use_all_pages": use_all_pages, "all_pages_in_blocks": list(set(b.get("page") for b in text_blocks)), "hypothesisId": "H4"})
    # #endregion

    if not page_blocks:
        return None

    # 在文本块中进行模糊匹配，选择与搜索文本最匹配的块
    # 而不是简单选择最长的块
    best_block = None
    best_block_score = 0
    
    # 定义最小有效 preview 长度（太短的 preview 无法进行有效匹配）
    MIN_PREVIEW_LENGTH = 30
    
    for block in page_blocks:
        # 兼容多种字段名：content_preview (DoclingParser), text, content
        block_text = block.get("content_preview", "") or block.get("text", "") or block.get("content", "")
        if not block_text:
            continue
        
        # 跳过太短的 preview（无法进行有效匹配）
        if len(block_text) < MIN_PREVIEW_LENGTH:
            continue
        
        # 计算与搜索文本的匹配度
        # 调整切片参数：原文取前 200 字符，preview 取全部（最长 300 字符）
        score = fuzz.partial_ratio(clean_search[:200], block_text)
        if score > best_block_score:
            best_block_score = score
            best_block = block
    
    # 如果匹配到了 section_header 且分数不高，可能是误匹配
    # 尝试选择同页面最大的 text 类型块作为备选
    if best_block and best_block.get("type") == "section_header" and best_block_score < 80:
        # 找同页面最大的 text 类型块
        text_blocks_on_page = [b for b in page_blocks if b.get("type") == "text"]
        if text_blocks_on_page:
            largest_text_block = max(text_blocks_on_page, key=lambda b: b.get("content_length", 0))
            # 如果最大的 text 块内容长度 > 500，可能包含引用内容
            if largest_text_block.get("content_length", 0) > 500:
                best_block = largest_text_block
                best_block_score = 60  # 给一个合理的分数
                logger.info(f"替换 section_header 为最大 text 块: {best_block.get('id')}")
    
    # #region agent log
    _debug_log("fuzzy:block_match", "Best matching text block", {
        "best_block_id": best_block.get("id") if best_block else None,
        "best_block_score": best_block_score,
        "search_text_preview": clean_search[:50],
        "hypothesisId": "H4"
    })
    # #endregion
    
    # content_preview 最长 300 字符，匹配分数通常在 40-80 之间
    # 阈值设为 35，跳过太短的 preview 后匹配质量会更好
    if best_block_score < 35:
        logger.debug(f"最佳匹配分数太低 ({best_block_score})，放弃文本块定位，将使用全页高亮")
        # #region agent log
        _debug_log("fuzzy:low_score", "Score too low, falling back to full page", {
            "best_block_score": best_block_score,
            "threshold": 35,
            "hypothesisId": "H4"
        })
        # #endregion
        return None
    
    logger.info(f"选择最佳匹配文本块: {best_block.get('id') if best_block else None}, score={best_block_score}")
    return best_block


def _find_source_pdf(project_dir: Path) -> str | None:
    """查找源 PDF 文件路径"""
    source_dir = project_dir / "source"

    # 尝试在 source 目录下查找 PDF
    for pdf_path in source_dir.glob("**/*.pdf"):
        return str(pdf_path.relative_to(project_dir))

    # 尝试直接在项目目录下查找
    for pdf_path in project_dir.glob("*.pdf"):
        return pdf_path.name

    # 尝试从 project_state.json 获取源文件路径
    state_file = project_dir / "project_state.json"
    if state_file.exists():
        import json
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        source_file = state.get("source_file")
        if source_file and Path(source_file).exists():
            return source_file

    # 尝试在 uploads 目录下查找（根据项目ID）
    # project_dir 格式: outputs/proj_20260109_132956
    # 对应 uploads 文件: uploads/proj_20260109_132956.pdf
    project_id = project_dir.name
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        for pdf_path in uploads_dir.glob(f"{project_id}.*"):
            if pdf_path.suffix.lower() == ".pdf":
                # 返回相对于项目根目录的路径
                return str(pdf_path)
        
        # 尝试匹配项目ID的前缀（处理带时间戳的项目ID）
        # proj_20260123_011313_20260123_180814 → 尝试匹配 proj_20260123_011313
        if "_20" in project_id:
            # 找到第二个时间戳的位置
            parts = project_id.split("_")
            if len(parts) >= 4:
                # 尝试前3部分作为原始项目ID
                base_id = "_".join(parts[:3])
                for pdf_path in uploads_dir.glob(f"{base_id}.*"):
                    if pdf_path.suffix.lower() == ".pdf":
                        return str(pdf_path)

    return None


def _build_pdf_highlight(bbox_data: dict, page: int) -> PDFHighlight | None:
    """从 bbox 数据构建 PDFHighlight 对象"""
    if not bbox_data:
        return None

    bbox = bbox_data.get("bbox")
    page_dims = bbox_data.get("page_dimensions")

    if not bbox or not page_dims:
        return None

    return PDFHighlight(
        page_number=page,
        bounding_rect=BoundingRect(
            x1=bbox["x1"],
            y1=bbox["y1"],
            x2=bbox["x2"],
            y2=bbox["y2"],
            width=bbox["width"],
            height=bbox["height"],
        ),
        page_dimensions=PageDimensions(
            width=page_dims["width"],
            height=page_dims["height"],
        ),
    )


@router.get("/{project_id}/citations/{citation_id}", response_model=CitationResponse)
async def get_citation(project_id: str, citation_id: str):
    """获取引用详情

    根据引用ID返回详细信息。

    引用ID格式：
    - doc-p5 → 文档引用（第5页）
    - fig_004 或 p10_fig_004.png → 图表引用
    - gap-001-2 或 temporal-001-2 → 外部研究引用

    Args:
        project_id: 项目ID
        citation_id: 引用ID

    Returns:
        引用详情
    """
    # 检查项目是否存在
    if not project_service.project_exists(project_id):
        raise HTTPException(404, f"项目不存在: {project_id}")

    project_dir = project_service.get_project_dir(project_id)

    # 获取 PDF URL
    pdf_path = _find_source_pdf(project_dir)
    pdf_url = f"/api/projects/{project_id}/files/{pdf_path}" if pdf_path else None
    
    # #region agent log
    _debug_log("get_citation:pdf_url", "PDF URL resolution", {
        "project_id": project_id,
        "citation_id": citation_id,
        "pdf_path": pdf_path,
        "pdf_url": pdf_url,
        "hypothesisId": "H3"
    })
    # #endregion

    # 文档引用
    if citation_id.startswith("doc-"):
        return _get_document_citation(project_id, project_dir, citation_id, pdf_url)

    # 图表引用
    if _is_figure_citation(citation_id):
        return _get_figure_citation(project_id, project_dir, citation_id, pdf_url)

    # 外部研究引用
    if _is_research_citation(citation_id):
        return _get_research_citation(project_dir, citation_id)

    raise HTTPException(400, f"无效的引用ID格式: {citation_id}")


def _get_document_citation(
    project_id: str, project_dir: Path, citation_id: str, pdf_url: str | None
) -> CitationResponse:
    """获取文档引用

    支持两种引用格式：
    1. 页码格式: doc-p5 → 直接使用第5页
    2. 语义格式: doc-q3-25-summary-1 → 从报告中查找章节对应页码 + 文本块精确定位

    定位优先级：
    1. 文本块 bbox（通过模糊匹配原文找到精确位置）
    2. 表格 bbox（如果引用包含 table）
    3. 页面级别（全页高亮）

    Args:
        project_id: 项目ID
        project_dir: 项目目录
        citation_id: 引用ID
        pdf_url: PDF 文件 URL

    Returns:
        CitationResponse
    """
    import re
    import json as _json
    from pathlib import Path as _Path

    # #region agent log
    _log_path = DEBUG_LOG_PATH
    def _debug_log(loc, msg, data):
        with open(_log_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps({"location": loc, "message": msg, "data": data, "hypothesisId": "H1-H5"}, ensure_ascii=False) + "\n")
    _debug_log("citations.py:entry", "get_document_citation called", {"citation_id": citation_id, "project_id": project_id})
    # #endregion

    page_number = None
    source = citation_id.replace("doc-", "")
    original_text = None  # 保存原文用于后续模糊匹配

    # 策略1: 尝试解析 doc-pN 格式的页码
    page_part = citation_id.replace("doc-p", "").replace("doc-", "")
    parts = page_part.split("-")
    page_str = parts[0]

    # 初始化 docling_page_for_search（用于 metadata 查询）
    docling_page_for_search = None
    
    try:
        page_number = int(page_str)
        # Docling 页码 = PDF 页码（经验证，无需转换）
        docling_page_for_search = page_number
        source = f"page-{page_str}"
        if len(parts) > 1:
            source = f"page-{page_str}#{'-'.join(parts[1:])}"
        # #region agent log
        _debug_log("citations.py:page_format", "Parsed as page format (doc-pN)", {"page_number": page_number, "docling_page": docling_page_for_search, "source": source, "hypothesisId": "H5"})
        # #endregion
    except ValueError:
        # 策略2: 语义化引用，从报告中查找页码、原文和位置信息
        found_page, original_text, location = _find_citation_page_and_text_from_report(
            project_dir, citation_id
        )
        # 保存 Docling 页码用于后续的 metadata 查询
        # 经验证：Docling 页码 = PDF 页码，无需转换
        docling_page_for_search = found_page
        pdf_page = found_page
        # #region agent log
        _debug_log("citations.py:semantic_format", "Parsed as semantic format", {"found_page": found_page, "pdf_page": pdf_page, "original_text": original_text[:100] if original_text else None, "original_text_len": len(original_text) if original_text else 0, "location": location, "hypothesisId": "H1,H2"})
        # #endregion
        if pdf_page:
            page_number = pdf_page
            # 使用从报告中提取的完整位置信息（包含 #table-1 等）
            source = location if location else f"page-{page_number}#{page_part}"
            logger.info(f"从报告提取位置信息: {citation_id} -> {source}")
        else:
            # 兜底: 默认第一页
            page_number = 1
            docling_page_for_search = 2  # Docling 从 page 2 开始

    # 尝试从 metadata 获取 bbox（用于更精确定位）
    pdf_highlight = None

    # #region agent log
    _debug_log("citations.py:before_fuzzy", "Before fuzzy match check", {"original_text_exists": original_text is not None, "original_text_len": len(original_text) if original_text else 0, "will_try_fuzzy": original_text is not None and len(original_text) >= 10, "hypothesisId": "H2"})
    # #endregion

    # 优先级1: 使用原文进行文本块模糊匹配
    # 注意：使用 Docling 页码进行搜索，因为 metadata 中的页码是 Docling 页码
    if original_text and len(original_text) >= 10:
        text_block = _find_text_block_by_fuzzy_match(
            project_dir, original_text, target_page=docling_page_for_search
        )
        # #region agent log
        _debug_log("citations.py:fuzzy_result", "Fuzzy match result", {"text_block_found": text_block is not None, "has_bbox": text_block.get("bbox") if text_block else None, "block_id": text_block.get("id") if text_block else None, "hypothesisId": "H3"})
        # #endregion
        if text_block and text_block.get("bbox"):
            # 使用找到的文本块页码（可能比页面级定位更准确）
            # 经验证：Docling 页码 = PDF 页码，无需转换
            docling_page = text_block.get("page", page_number)
            block_page = docling_page
            bbox = text_block["bbox"].copy()  # 复制 bbox，避免修改原始数据
            page_dims = text_block.get("page_dimensions", {"width": 612, "height": 792})
            
            # 尝试根据引用原文在块内的位置细分 bbox
            # 放宽条件：只要块高度 > 40px 且能找到引用原文的位置就尝试细分
            block_content = text_block.get("content_preview", "") or text_block.get("text", "")
            content_length = text_block.get("content_length", len(block_content))
            bbox_height = bbox.get("height", 0) or (bbox.get("y2", 0) - bbox.get("y1", 0))
            
            if bbox_height > 40 and original_text and len(original_text) >= 20:
                # 在块内容中查找引用原文的位置
                search_text = original_text[:100]  # 使用前100个字符搜索
                pos = block_content.lower().find(search_text[:50].lower())
                
                if pos >= 0:
                    # 计算引用在块内的相对位置 (0-1)
                    relative_pos = pos / max(1, len(block_content))
                    # 估算引用覆盖的相对范围（至少覆盖 30% 的高度以确保可见）
                    relative_len = max(0.3, min(0.5, len(original_text) / max(1, content_length)))
                    
                    # 根据相对位置调整 bbox 的 y 坐标
                    block_height = bbox.get("height", 0) or (bbox["y2"] - bbox["y1"])
                    
                    # 降低细分阈值，让更多块可以被细分
                    if block_height > 40:
                        # 计算细分后的 y 坐标范围
                        new_y1 = bbox["y1"] + block_height * max(0, relative_pos - 0.05)
                        new_y2 = bbox["y1"] + block_height * min(1, relative_pos + relative_len + 0.1)
                        
                        # 确保最小高度（降低到 40px，约 2-3 行文字）
                        min_sub_height = 40
                        if new_y2 - new_y1 < min_sub_height:
                            center = (new_y1 + new_y2) / 2
                            new_y1 = center - min_sub_height / 2
                            new_y2 = center + min_sub_height / 2
                        
                        # #region agent log
                        _debug_log("citations.py:subdivide_bbox", "Subdividing text block", {
                            "block_id": text_block.get("id"),
                            "content_length": content_length,
                            "block_height": block_height,
                            "search_pos": pos,
                            "relative_pos": relative_pos,
                            "relative_len": relative_len,
                            "original_y1": bbox["y1"],
                            "original_y2": bbox["y2"],
                            "new_y1": new_y1,
                            "new_y2": new_y2,
                        })
                        # #endregion
                        
                        bbox["y1"] = max(bbox["y1"], new_y1)
                        bbox["y2"] = min(bbox["y2"], new_y2)
                        bbox["height"] = bbox["y2"] - bbox["y1"]
                        logger.info(f"细分文本块: {text_block.get('id')}, pos={relative_pos:.2f}, height={bbox['height']:.1f}")
            
            # 如果 bbox 太小（高度小于 150 像素，约 10 行文字），扩展为更合理的区域
            # 大多数引用文本跨越多行，需要更大的高亮区域
            MIN_HIGHLIGHT_HEIGHT = 150
            bbox_height = bbox.get("height", 0) or (bbox.get("y2", 0) - bbox.get("y1", 0))
            
            if bbox_height < MIN_HIGHLIGHT_HEIGHT:
                # 扩展 bbox：保持 x 坐标，主要向下扩展（因为文本通常向下延伸）
                expand_up = 20  # 向上扩展少一点
                expand_down = MIN_HIGHLIGHT_HEIGHT - bbox_height + 30  # 主要向下扩展
                expand_amount = (expand_up + expand_down) / 2  # 用于日志
                new_y1 = max(0, bbox["y1"] - expand_up)
                new_y2 = min(page_dims["height"], bbox["y2"] + expand_down)
                
                # #region agent log
                _debug_log("citations.py:expand_bbox", "Expanding small bbox", {
                    "original_height": bbox_height,
                    "expanded_y1": new_y1,
                    "expanded_y2": new_y2,
                    "new_height": new_y2 - new_y1,
                })
                # #endregion
                
                bbox = {
                    "x1": bbox["x1"],
                    "y1": new_y1,
                    "x2": bbox["x2"],
                    "y2": new_y2,
                    "width": bbox.get("width", bbox["x2"] - bbox["x1"]),
                    "height": new_y2 - new_y1,
                }
                logger.info(f"扩展小 bbox: {bbox_height:.1f} -> {new_y2 - new_y1:.1f}")
            
            pdf_highlight = _build_pdf_highlight(
                {"bbox": bbox, "page_dimensions": page_dims},
                block_page,
            )
            page_number = block_page  # 更新为更精确的页码
            logger.info(f"文本块定位成功: {citation_id} -> page {page_number}, block {text_block.get('id')}")

    # 优先级2: 如果引用位置包含 table 标识符（如 #table-1），尝试查找对应 bbox
    if not pdf_highlight and ("table" in citation_id.lower() or "table" in source.lower()):
        logger.info(f"引用包含表格标识，尝试查找表格 bbox: {source}")
        source_dir = project_dir / "source"
        metadata_files = list(source_dir.glob("*/metadata.json"))
        if not metadata_files:
            metadata_path = source_dir / "metadata.json"
            if metadata_path.exists():
                metadata_files = [metadata_path]

        for metadata_path in metadata_files:
            metadata = load_json_file(metadata_path)
            if not metadata:
                continue

            # 查找匹配的表格
            tables = metadata.get("tables", [])
            logger.debug(f"在第 {page_number} 页找到 {len([t for t in tables if t.get('page') == page_number])} 个表格")

            for table in tables:
                if table.get("page") == page_number and table.get("bbox"):
                    logger.info(f"找到表格 bbox: {table['id']} on page {page_number}")
                    pdf_highlight = _build_pdf_highlight(
                        {"bbox": table["bbox"], "page_dimensions": table.get("page_dimensions", {"width": 612, "height": 792})},
                        page_number
                    )
                    break

            if pdf_highlight:
                break

    # 优先级3: 如果没有精确 bbox，创建页面级别的默认高亮（全页）
    if not pdf_highlight:
        # #region agent log
        _debug_log("citations.py:fallback", "Using fallback full-page highlight", {"page_number": page_number, "reason": "no_precise_bbox"})
        # #endregion
        pdf_highlight = PDFHighlight(
            page_number=page_number,
            bounding_rect=BoundingRect(x1=0, y1=0, x2=612, y2=792, width=612, height=792),
            page_dimensions=PageDimensions(width=612, height=792),
        )
    else:
        # #region agent log
        _debug_log("citations.py:success", "Using precise bbox highlight", {"page_number": page_number, "bbox": {"x1": pdf_highlight.bounding_rect.x1, "y1": pdf_highlight.bounding_rect.y1, "x2": pdf_highlight.bounding_rect.x2, "y2": pdf_highlight.bounding_rect.y2}})
        # #endregion

    return CitationResponse(
        type="document",
        id=citation_id,
        location=f"page-{page_number}",
        source=source,
        pdf_highlight=pdf_highlight,
        pdf_url=pdf_url,
    )


def _is_figure_citation(citation_id: str) -> bool:
    """判断是否为图表引用"""
    result = (
        citation_id.startswith("fig_")
        or citation_id.startswith("fig-")  # 支持 fig-p4-003 格式
        or (citation_id.startswith("p") and "_fig_" in citation_id)
        or citation_id.endswith(".png")
        or citation_id.endswith(".jpg")
    )
    # #region agent log
    _debug_log("is_figure_citation", "Checking citation type", {
        "citation_id": citation_id,
        "is_figure": result,
        "hypothesisId": "H1"
    })
    # #endregion
    return result


def _get_figure_citation(
    project_id: str, project_dir: Path, citation_id: str, pdf_url: str | None
) -> CitationResponse:
    """获取图表引用

    Args:
        project_id: 项目ID
        project_dir: 项目目录
        citation_id: 引用ID
        pdf_url: PDF 文件 URL

    Returns:
        CitationResponse
    """
    # 查找 source 目录下的 metadata.json
    source_dir = project_dir / "source"
    metadata_files = list(source_dir.glob("*/metadata.json"))

    if not metadata_files:
        # 尝试直接在 source 下查找
        metadata_path = source_dir / "metadata.json"
        if metadata_path.exists():
            metadata_files = [metadata_path]

    # 将 fig-p4-003 格式转换为多种匹配模式
    # fig-p4-003 -> p4_fig_003, p4_fig_003.png, fig_3
    normalized_id = citation_id
    if citation_id.startswith("fig-"):
        # fig-p4-003 -> p4-003 -> p4_003
        parts = citation_id[4:].split("-")  # ['p4', '003']
        if len(parts) == 2 and parts[0].startswith("p"):
            page_part = parts[0]  # p4
            num_part = parts[1]   # 003
            normalized_id = f"{page_part}_fig_{num_part}"  # p4_fig_003
    
    # #region agent log
    _debug_log("figure_citation", "Matching figure citation", {
        "citation_id": citation_id,
        "normalized_id": normalized_id,
        "hypothesisId": "H2"
    })
    # #endregion

    for metadata_path in metadata_files:
        metadata = load_json_file(metadata_path)
        if metadata is None:
            continue

        figures = metadata.get("figures", [])
        for fig in figures:
            fig_filename = fig.get("filename", "")
            fig_id = fig.get("id", "")
            
            # 从 filename 提取不带扩展名的 ID: p4_fig_003.png -> p4_fig_003
            fig_filename_base = fig_filename.replace(".png", "").replace(".jpg", "")

            # 匹配引用ID（支持多种格式）
            is_match = (
                citation_id == fig_filename
                or citation_id in fig_filename
                or citation_id == fig_id
                or fig_id in citation_id
                or normalized_id == fig_filename_base  # 新增：fig-p4-003 -> p4_fig_003
                or normalized_id in fig_filename  # 新增：p4_fig_003 in p4_fig_003.png
            )
            
            # #region agent log
            if is_match:
                _debug_log("figure_citation", "Figure match found", {
                    "citation_id": citation_id,
                    "fig_filename": fig_filename,
                    "fig_id": fig_id,
                    "normalized_id": normalized_id,
                    "bbox": fig.get("bbox"),
                    "hypothesisId": "H2"
                })
            # #endregion

            if is_match:
                # 构建 PDF 高亮信息
                # 经验证：Docling 页码 = PDF 页码，无需转换
                docling_page = fig.get("page", 1)
                pdf_page = docling_page
                
                # #region agent log
                _debug_log("figure_citation", "Page conversion", {
                    "docling_page": docling_page,
                    "pdf_page": pdf_page,
                    "hypothesisId": "H4"
                })
                # #endregion
                
                pdf_highlight = None
                if fig.get("bbox") and fig.get("page_dimensions"):
                    pdf_highlight = _build_pdf_highlight(
                        {"bbox": fig["bbox"], "page_dimensions": fig["page_dimensions"]},
                        pdf_page  # 使用转换后的 PDF 物理页码
                    )
                elif fig.get("page"):
                    # 没有精确 bbox，使用页面级别
                    pdf_highlight = PDFHighlight(
                        page_number=pdf_page,  # 使用转换后的 PDF 物理页码
                        bounding_rect=BoundingRect(x1=0, y1=0, x2=612, y2=792, width=612, height=792),
                        page_dimensions=PageDimensions(width=612, height=792),
                    )

                # 构建图片相对路径
                images_subdir = metadata_path.parent.name
                fig_path = f"{images_subdir}/images/{fig_filename}" if fig_filename else ""

                return CitationResponse(
                    type="chart",
                    figure_id=fig_filename,
                    figure_path=fig_path,
                    figure_url=f"/api/projects/{project_id}/files/source/{fig_path}" if fig_path else None,
                    figure_analysis={
                        "type": fig.get("image_type", "chart"),
                        "title": fig.get("caption"),
                        "analysis": fig.get("analysis"),
                        "description": fig.get("description"),
                    },
                    pdf_highlight=pdf_highlight,
                    pdf_url=pdf_url,
                )

    # 如果在 metadata 中找不到，尝试直接查找图片文件
    for img_path in source_dir.glob("**/*.png"):
        if citation_id in img_path.name or citation_id == img_path.name:
            rel_path = img_path.relative_to(source_dir)

            # 尝试从文件名解析页码: p8_fig_001.png -> page 8
            page_number = 1
            if img_path.name.startswith("p") and "_fig_" in img_path.name:
                try:
                    page_number = int(img_path.name.split("_")[0][1:])
                except ValueError:
                    pass

            pdf_highlight = PDFHighlight(
                page_number=page_number,
                bounding_rect=BoundingRect(x1=0, y1=0, x2=612, y2=792, width=612, height=792),
                page_dimensions=PageDimensions(width=612, height=792),
            )

            return CitationResponse(
                type="chart",
                figure_id=img_path.name,
                figure_path=str(rel_path),
                figure_url=f"/api/projects/{project_id}/files/source/{rel_path}",
                pdf_highlight=pdf_highlight,
                pdf_url=pdf_url,
            )

    raise HTTPException(404, f"图表未找到: {citation_id}")


def _is_research_citation(citation_id: str) -> bool:
    """判断是否为研究引用"""
    prefixes = ("gap-", "temporal-", "compare-", "deep-", "market-")
    return any(citation_id.startswith(prefix) for prefix in prefixes)


def _get_research_citation(project_dir: Path, citation_id: str) -> CitationResponse:
    """获取研究引用"""
    research_path = project_dir / "02_research.json"
    research = load_json_file(research_path)

    if research is None:
        raise HTTPException(404, "研究结果不存在")

    # 解析引用ID: gap-001-2 → source_gap=gap-001, result_index=2
    # 或者 temporal-001-2 → source_gap=temporal-001, result_index=2
    parts = citation_id.rsplit("-", 1)

    if len(parts) == 2 and parts[1].isdigit():
        source_gap = parts[0]
        result_index = int(parts[1])
    else:
        source_gap = citation_id
        result_index = 0

    # 查找对应的查询结果
    for query in research.get("queries", []):
        query_source_gap = query.get("source_gap", "")

        # 匹配 source_gap
        if query_source_gap == source_gap or source_gap in query_source_gap:
            results = query.get("results", [])
            if result_index < len(results):
                result = results[result_index]
                return CitationResponse(
                    type="web",
                    title=result.get("title"),
                    url=result.get("url"),
                    content=result.get("content", "")[:500],  # 限制长度
                    published_date=result.get("published_date"),
                    relevance_score=result.get("relevance_score"),
                )

    raise HTTPException(404, f"外部引用未找到: {citation_id}")
