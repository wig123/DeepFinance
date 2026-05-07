"""章节解析器

解析 Docling 输出的 content.md，按 ## 标题提取章节并聚合成块。
"""

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """文档章节"""
    
    title: str  # 章节标题
    content: str  # 章节完整内容（包含标题行）
    char_count: int  # 字符数
    start_page: int | None = None  # 起始页码
    end_page: int | None = None  # 结束页码
    figures: list[str] = field(default_factory=list)  # 图表 ID 列表


@dataclass
class Chunk:
    """文档块（包含一个或多个章节）"""
    
    sections: list[Section]
    chunk_index: int = 0  # 块索引（从 0 开始）
    
    @property
    def content(self) -> str:
        """拼接所有章节内容"""
        return "\n".join(s.content for s in self.sections)
    
    @property
    def char_count(self) -> int:
        """总字符数"""
        return sum(s.char_count for s in self.sections)
    
    @property
    def section_titles(self) -> list[str]:
        """所有章节标题"""
        return [s.title for s in self.sections]
    
    @property
    def start_page(self) -> int | None:
        """起始页码"""
        for s in self.sections:
            if s.start_page is not None:
                return s.start_page
        return None
    
    @property
    def end_page(self) -> int | None:
        """结束页码"""
        for s in reversed(self.sections):
            if s.end_page is not None:
                return s.end_page
        return None
    
    @property
    def figures(self) -> list[str]:
        """所有图表 ID"""
        result = []
        for s in self.sections:
            result.extend(s.figures)
        return result


class SectionParser:
    """章节解析器
    
    从 Docling 解析的 content.md 中提取章节结构，
    并按目标大小聚合成块。
    """
    
    # 页码标记正则
    PAGE_MARKER_PATTERN = re.compile(r'<!-- page: (\d+) -->')
    # 图表引用正则
    FIGURE_PATTERN = re.compile(r'!\[图 \d+\]\(images/(p\d+_fig_\d+\.png)\)')
    
    def __init__(
        self,
        target_chunk_size: int = 15000,
        min_chunks: int = 2,
        max_chunks: int = 6,
        min_doc_size_for_chunking: int = 20000,
    ):
        """初始化章节解析器
        
        Args:
            target_chunk_size: 目标块大小（字符数）
            min_chunks: 最少分块数
            max_chunks: 最多分块数
            min_doc_size_for_chunking: 触发分块的最小文档大小
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunks = min_chunks
        self.max_chunks = max_chunks
        self.min_doc_size_for_chunking = min_doc_size_for_chunking
    
    def parse_sections(self, content: str) -> list[Section]:
        """按 ## 标题解析章节
        
        Args:
            content: content.md 的内容
            
        Returns:
            章节列表
        """
        sections: list[Section] = []
        lines = content.split('\n')
        
        current_title = "_preamble"
        current_lines: list[str] = []
        current_start_page: int | None = None
        current_end_page: int | None = None
        current_figures: list[str] = []
        
        for line in lines:
            # 检查页码标记
            page_match = self.PAGE_MARKER_PATTERN.search(line)
            if page_match:
                page_no = int(page_match.group(1))
                if current_start_page is None:
                    current_start_page = page_no
                current_end_page = page_no
            
            # 检查图表引用
            figure_match = self.FIGURE_PATTERN.search(line)
            if figure_match:
                current_figures.append(figure_match.group(1))
            
            # 检查章节标题
            if line.startswith('## '):
                # 保存当前章节
                if current_lines:
                    section_content = '\n'.join(current_lines)
                    sections.append(Section(
                        title=current_title,
                        content=section_content,
                        char_count=len(section_content),
                        start_page=current_start_page,
                        end_page=current_end_page,
                        figures=current_figures,
                    ))
                
                # 开始新章节
                current_title = line[3:].strip()
                current_lines = [line]
                current_start_page = current_end_page  # 继承上一个章节的结束页码
                current_figures = []
            else:
                current_lines.append(line)
        
        # 保存最后一个章节
        if current_lines:
            section_content = '\n'.join(current_lines)
            sections.append(Section(
                title=current_title,
                content=section_content,
                char_count=len(section_content),
                start_page=current_start_page,
                end_page=current_end_page,
                figures=current_figures,
            ))
        
        logger.info(f"解析出 {len(sections)} 个章节")
        for i, s in enumerate(sections):
            logger.debug(f"  [{i}] {s.title}: {s.char_count} 字符, 页码 {s.start_page}-{s.end_page}")
        
        return sections
    
    def aggregate_sections(self, sections: list[Section]) -> list[Chunk]:
        """聚合章节成块，确保语义完整
        
        Args:
            sections: 章节列表
            
        Returns:
            块列表
        """
        if not sections:
            return []
        
        total_chars = sum(s.char_count for s in sections)
        
        # 如果文档较小，不分块
        if total_chars < self.min_doc_size_for_chunking:
            logger.info(f"文档较小 ({total_chars} 字符)，不进行分块")
            return [Chunk(sections=sections, chunk_index=0)]
        
        # 计算合理的块数
        estimated_chunks = total_chars // self.target_chunk_size
        num_chunks = max(self.min_chunks, min(self.max_chunks, estimated_chunks))
        adjusted_target = total_chars // num_chunks
        
        logger.info(
            f"文档总计 {total_chars} 字符，预计分 {num_chunks} 块，"
            f"目标每块 {adjusted_target} 字符"
        )
        
        chunks: list[Chunk] = []
        current_sections: list[Section] = []
        current_size = 0
        
        for section in sections:
            # 判断是否应该开始新块
            should_start_new_chunk = (
                current_size >= adjusted_target * 0.7 and
                current_size + section.char_count > adjusted_target * 1.3 and
                current_sections  # 确保当前块不为空
            )
            
            if should_start_new_chunk:
                chunks.append(Chunk(
                    sections=current_sections,
                    chunk_index=len(chunks),
                ))
                current_sections = [section]
                current_size = section.char_count
            else:
                current_sections.append(section)
                current_size += section.char_count
        
        # 保存最后一个块
        if current_sections:
            chunks.append(Chunk(
                sections=current_sections,
                chunk_index=len(chunks),
            ))
        
        # 日志输出
        logger.info(f"聚合为 {len(chunks)} 个块:")
        for chunk in chunks:
            logger.info(
                f"  Chunk {chunk.chunk_index}: {chunk.char_count} 字符, "
                f"{len(chunk.sections)} 章节, "
                f"页码 {chunk.start_page}-{chunk.end_page}"
            )
            for s in chunk.sections:
                logger.debug(f"    - {s.title}")
        
        return chunks
    
    def parse_and_chunk(self, content: str) -> list[Chunk]:
        """解析并分块（一步到位）
        
        Args:
            content: content.md 的内容
            
        Returns:
            块列表
        """
        sections = self.parse_sections(content)
        return self.aggregate_sections(sections)
    
    def parse_from_file(self, content_path: Path) -> list[Chunk]:
        """从文件解析并分块
        
        Args:
            content_path: content.md 文件路径
            
        Returns:
            块列表
        """
        content = content_path.read_text(encoding="utf-8")
        return self.parse_and_chunk(content)
