# 分块分析架构

## 问题

大型金融文档（50+ 页财报）单次 LLM 分析时：
- 输出容易截断
- 信息密度不均匀导致遗漏
- 无法并行处理

## 解决方案

按章节切分 → 并行分析 → 合并结果

```
content.md (全文)
       │
       ▼
┌──────────────────┐
│  SectionParser   │  按 ## 标题切分
└────────┬─────────┘
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
 [块1]     [块2]    [块3]     ← 相邻章节聚合，保持语义完整
    │         │        │
    ▼         ▼        ▼
 [分析1]   [分析2]  [分析3]   ← 并行 LLM 调用
    │         │        │
    └────┬────┴────────┘
         ▼
┌──────────────────┐
│   合并 + 全局信息  │  document_metadata, key_takeaways
└──────────────────┘
```

## 分块参数

```python
target_chunk_size = 15000    # 目标块大小（字符）
min_chunks = 2               # 最少分块数
max_chunks = 6               # 最多分块数
min_doc_size_for_chunking = 20000  # 触发分块的阈值
```

## 数据结构

### 输入：Chunk

```python
@dataclass
class Chunk:
    chunk_index: int           # 块索引
    content: str               # 块内容
    section_titles: list[str]  # 包含的章节标题
    start_page: int | None     # 起始页
    end_page: int | None       # 结束页
    figures: list[str]         # 包含的图片文件名
    char_count: int            # 字符数
```

### 输出：每块分析结果

```json
{
  "content_summary": [
    {
      "section_title": "Q3 Performance",
      "content": "章节摘要...",
      "key_metrics": [
        {
          "metric": "Revenue",
          "current_value": "$11.5B",
          "change": "+17% YoY",
          "source": "page-3",
          "original_quote": "Revenue grew 17%..."
        }
      ],
      "insights": ["洞察1", "洞察2"]
    }
  ]
}
```

### 合并后全局信息

```json
{
  "document_metadata": {
    "company": "Netflix",
    "period": "Q3 2025",
    "document_type": "earnings_report"
  },
  "key_takeaways": [...],
  "supplementary_research_needs": {
    "temporal_updates": [...],
    "comparative_data": [...],
    "deep_dive_analysis": [...],
    "market_perspectives": [...]
  }
}
```

## 关键代码路径

```
src/analyzers/
├── chunked_analyzer.py    # 分块分析主逻辑
├── section_parser.py      # 章节切分
└── document_analyzer.py   # 单块分析（小文档直接用）

src/prompts/
├── chunk_analysis.txt     # 单块分析 prompt
└── merge_analysis.txt     # 合并生成全局信息 prompt
```

## 调用方式

```python
from src.analyzers import ChunkedDocumentAnalyzer

analyzer = ChunkedDocumentAnalyzer(
    model="gemini-3-flash-preview",
    target_chunk_size=15000,
)

result = analyzer.analyze(source_dir=Path("outputs/xxx/source"))
```
