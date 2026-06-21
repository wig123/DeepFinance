# Chunked Analysis Architecture

## Problem

When analyzing large financial documents (50+ page financial reports) with a single LLM call:
- Output is prone to truncation
- Uneven information density leads to omissions
- Cannot be processed in parallel

## Solution

Split by sections → Analyze in parallel → Merge results

```
content.md (full text)
       │
       ▼
┌──────────────────┐
│  SectionParser   │  Split by ## headings
└────────┬─────────┘
         │
    ┌────┴────┬────────┐
    ▼         ▼        ▼
 [Chunk 1] [Chunk 2] [Chunk 3]  ← Adjacent sections aggregated to preserve semantic integrity
    │         │        │
    ▼         ▼        ▼
 [Analysis 1] [Analysis 2] [Analysis 3]  ← Parallel LLM calls
    │         │        │
    └────┬────┴────────┘
         ▼
┌──────────────────┐
│ Merge + Global Info │  document_metadata, key_takeaways
└──────────────────┘
```

## Chunking Parameters

```python
target_chunk_size = 15000    # Target chunk size (characters)
min_chunks = 2               # Minimum number of chunks
max_chunks = 6               # Maximum number of chunks
min_doc_size_for_chunking = 20000  # Threshold to trigger chunking
```

## Data Structures

### Input: Chunk

```python
@dataclass
class Chunk:
    chunk_index: int           # Chunk index
    content: str               # Chunk content
    section_titles: list[str]  # Section titles included
    start_page: int | None     # Start page
    end_page: int | None       # End page
    figures: list[str]         # Image filenames included
    char_count: int            # Character count
```

### Output: Per-chunk Analysis Results

```json
{
  "content_summary": [
    {
      "section_title": "Q3 Performance",
      "content": "Section summary...",
      "key_metrics": [
        {
          "metric": "Revenue",
          "current_value": "$11.5B",
          "change": "+17% YoY",
          "source": "page-3",
          "original_quote": "Revenue grew 17%..."
        }
      ],
      "insights": ["Insight 1", "Insight 2"]
    }
  ]
}
```

### Merged Global Information

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

## Key Code Paths

```
src/analyzers/
├── chunked_analyzer.py    # Main chunked analysis logic
├── section_parser.py      # Section splitting
└── document_analyzer.py   # Single chunk analysis (used directly for small documents)

src/prompts/
├── chunk_analysis.txt     # Single chunk analysis prompt
└── merge_analysis.txt     # Merge and generate global info prompt
```

## Usage

```python
from src.analyzers import ChunkedDocumentAnalyzer

analyzer = ChunkedDocumentAnalyzer(
    model="gemini-3-flash-preview",
    target_chunk_size=15000,
)

result = analyzer.analyze(source_dir=Path("outputs/xxx/source"))
```
