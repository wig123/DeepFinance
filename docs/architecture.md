# DeepFinance Process Architecture

## Core Principles

- **Simplicity over Complexity**: Linear pipeline replaces 6-Agent orchestration
- **Leverage Long Context**: Gemini 2.5 supports 1M tokens, full document analysis without RAG
- **Complete Summary First**: 8-chapter detailed summary (25 metrics + 30 insights) replaces sparse bullet points
- **Structured Research Needs**: 4-dimension supplementary research (timeliness + comparison + depth + market views)
- **Cost Optimization**: Full pipeline uses Gemini Flash Lite (~$0.02/report)
- **Full Traceability**: Each step outputs independent JSON, citations precise to page/table level

## Process Architecture

```
PDF Document → [1.Parse] → [2.Analyze] → [2.5.Research]* → [3.Generate] → Markdown Report
                75.7s        54.3s          Optional          20.2s
                 ↓            ↓               ↓                 ↓
              source/    01_analysis.json  02_research.json  report.md
           (content.md   (8 chapters+25    (supplementary    (complete
            +17 images)  metrics+4 dims)   data)             report)
```

*Research stage is optional, disabled in minimal mode to accelerate validation

## Three-Step Pipeline

### 1. PDF Parsing (DoclingParser)

**Input**: PDF document
**Processing**:
- Docling extracts text + tables + images
- Claude Vision batch analyzes images (optional)
  - Stage 1: Classification (chart/illustration/icon)
  - Stage 2: Content description (chart analysis/illustration description)
- Generate Markdown + metadata.json

**Output**: `source/{doc_name}/`
- `content.md` - Complete document content
- `metadata.json` - Chart list + descriptions
- `images/` - Extracted image files

---

### 2. Document Analysis (DocumentAnalyzer)

**Input**: source directory (content.md + metadata.json)
**Processing**:
- Gemini 2.5 Flash Lite reads complete document (~60K characters)
- Outputs structured JSON (complete summary + supplementary research needs)

**Output**: `01_analysis.json`
```json
{
  "analysis_id": "source_20260109_113358",
  "document_metadata": {
    "document_type": "earnings_report",
    "company": "Tesla",
    "period": "Q3 2025",
    "publish_date": "2025-10-22",
    "key_topics": ["Financial Summary", "Operations Summary", "Product Launch", ...]
  },
  "content_summary": [  // 8 chapters, complete document summary
    {
      "section_id": "financial_summary",
      "section_title": "Financial Summary",
      "content": "Q3-2025 total revenue was $28,095M, up 12% YoY...",  // detailed narrative
      "key_metrics": [  // 6 metrics (this chapter)
        {
          "metric": "Total Revenue",
          "current_value": "$28,095M (Q3-2025)",
          "previous_value": "$25,182M (Q3-2024)",  // historical comparison
          "change": "+12% YoY",                     // change magnitude
          "context": "Total Revenue",               // context
          "source": "page-5#table-2"                // precise citation
        }
      ],
      "insights": [  // 4 insights (this chapter)
        "Despite record revenue, operating income and margins declined significantly..."
      ],
      "citations": [{"id": "doc-p5", "location": "page-5"}]
    }
    // ... 8 chapters total
  ],
  "key_takeaways": [  // 6 key takeaways
    {
      "id": "KT-001",
      "category": "positive",
      "statement": "Tesla achieved record revenue and free cash flow in Q3...",
      "evidence": "Total revenue $28.1B (+12% YoY)...",
      "significance": "Demonstrates company's ability to grow despite macro uncertainty",
      "sources": [{"id": "source", "location": "page-5"}]
    }
  ],
  "supplementary_research_needs": {  // 4-dimension supplementary research needs
    "temporal_updates": [  // timeliness supplement
      {
        "id": "temporal-001",
        "topic": "Q4 2025 production and delivery guidance",
        "reason": "Q3 production slightly below deliveries, need to understand Q4 progress",
        "search_queries": [
          "Tesla Q4 2025 production guidance update",
          "Tesla Q4 2025 delivery forecast"
        ],
        "priority": "high"
      }
    ],
    "comparative_data": [  // comparison information
      {
        "id": "compare-001",
        "comparison_type": "competitors",
        "metric": "Average cost per vehicle",
        "reason": "Need to compare cost structure changes with competitors like BYD",
        "search_queries": [
          "EV industry average cost per vehicle Q3 2025",
          "Tesla cost per vehicle vs competitors 2025"
        ]
      }
    ],
    "deep_dive_analysis": [  // deep analysis
      {
        "id": "deep-001",
        "topic": "AI/software profitability",
        "question": "What is Robotaxi's specific revenue contribution in Q3?",
        "reason": "Current financial report lacks clarity on this business's independent profitability",
        "search_queries": ["Tesla software revenue Q3 2025 breakdown"]
      }
    ],
    "market_perspectives": [  // market views
      {
        "id": "market-001",
        "topic": "Analyst views on margin compression",
        "perspective_type": "analyst_ratings",
        "search_queries": [
          "Analyst reaction to Tesla Q3 2025 margin compression"
        ]
      }
    ]
  },
  "charts_analysis": [...]  // 17 chart analyses
}
```

**Quality Metrics** (TSLA Q3 2025 test):
- **8 chapters**: Highlights, Financials, Operations, Automotive, Technology, Energy, Outlook, Statements
- **25 metrics**: Each with previous value + current value + change + context + source
- **30 insights**: Distributed across 8 chapters
- **5 research needs**: 4 dimensions, 13 executable queries total
- **Q&A Support**: Complete context preserved, information density increased by 60%~400%

---

### 2.5. External Research (DataResearcher) *Optional

**Input**: supplementary_research_needs (4 dimensions)
**Processing**:
- Collect all search_queries from 4 dimensions (e.g., 13 queries)
- Tavily parallel search (max concurrency 10, Semaphore controlled)
- Aggregate results by need_id

**Output**: `02_research.json`
```json
{
  "research_id": "research_20260109_113400",
  "related_analysis": "source_20260109_113358",
  "queries": [
    {
      "query_id": "temporal-001-query-0",
      "query_text": "Tesla Q4 2025 production guidance update",
      "source_gap": "temporal-001",
      "results": [
        {
          "source": "web_search",
          "title": "Tesla Q4 2025 Production Outlook...",
          "url": "https://...",
          "content": "...",
          "relevance_score": 0.95
        }
      ]
    }
  ],
  "summary_by_gap": {
    "temporal-001": {
      "answered": true,
      "confidence": "high",
      "key_findings": ["Finding 1", "Finding 2", ...],
      "sources_count": 8,
      "queries_count": 3
    }
  }
}
```

---

### 3. Report Generation (ReportGenerator)

**Input**:
- `01_analysis.json` - Document analysis
- `02_research.json` - External research (optional)

**Processing**:
- Gemini/Claude integrates all data
- Generates Markdown report

**Output**:
- `report.md` - Final report (with citations)
- `report_metadata.json` - Metadata

**Report Structure**:
```markdown
## Executive Summary
## Core Findings
### 1. Finding Title
Data Support: xxx[^doc-p5]
Comparative Analysis: xxx[^gap-001-2]
Chart Analysis: xxx[^p10_fig_004.png]

## Industry Comparison
## Risks and Challenges
## Investment Recommendations

## Citations
### Original Document
- [doc-p5]: page-5#table-2
### Chart Analysis
- [p10_fig_004.png]: Chart file
### External Data
- [gap-001-2]: Title (URL)
```

## Citation System

| Type | Format | Example | Source |
|------|--------|---------|--------|
| **Document Citation** | `[^doc-p{N}]` | `[^doc-p5]` | Original PDF page 5 |
| **Chart Citation** | `[^{filename}]` | `[^p10_fig_004.png]` | Extracted image |
| **Search Citation** | `[^gap-{N}-{M}]` | `[^gap-001-2]` | External search result |

## Prompt Management (`src/prompts/`)

All LLM prompts are decoupled into independent files for easy maintenance and optimization.

### Prompt List

| File | Purpose | Called From |
|------|---------|-------------|
| `document_analysis.txt` | Document analysis | `DocumentAnalyzer._build_analysis_prompt()` |
| `report_generation.txt` | Report generation | `ReportGenerator._build_report_prompt()` |

### Usage

```python
from src.prompts import get_document_analysis_prompt

prompt = get_document_analysis_prompt(
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)
```

### Modifying Prompts

1. Edit `src/prompts/analysis/*.txt` or `src/prompts/generation/*.txt`
2. Use `{variable_name}` to mark dynamic content
3. Test and validate: `uv run python scripts/run_pipeline.py --mode minimal`

## Key Components

### DoclingParser (`src/tools/parser/`)
- PDF parsing (Docling)
- Image analysis (Claude Vision, optional)
- Markdown generation

### DocumentAnalyzer (`src/analyzers/document_analyzer.py`)
- LLM: CloseAI Gemini 2.5 Flash Lite
- Output: Structured JSON (5 findings + 4 gaps)

### DataResearcher (`src/analyzers/data_researcher.py`)
- Search engine: Tavily
- Concurrency control: Semaphore(10)
- Async execution: asyncio.gather

### ReportGenerator (`src/analyzers/report_generator.py`)
- LLM: CloseAI Gemini / Claude Sonnet
- Output: Markdown report

### ReportPipeline (`src/pipeline/report_pipeline.py`)
- Orchestrator, sequentially calls 4 components
- Saves intermediate results (JSON)
- Records pipeline metadata

## Configuration Options

```python
pipeline = ReportPipeline(
    output_base="outputs/",
    enable_image_analysis=True,      # Image analysis (requires Claude)
    enable_research=True,            # External search (requires Tavily)
    analyzer_model="gemini-2.5-flash-lite-preview-09-2025",
    generator_model="gemini-2.5-flash-lite-preview-09-2025",
    search_engine="tavily",
)
```

### Three Modes

| Mode | Image Analysis | External Research | Purpose | Duration |
|------|---------------|-------------------|---------|----------|
| **minimal** | ❌ | ❌ | Quick validation | ~115s |
| **no-research** | ✅ | ❌ | Document analysis only | ~150s |
| **full** | ✅ | ✅ | Complete report | ~200s |

## Data Models (`src/models/report.py`)

All data structures use Pydantic, supporting:
- Type validation
- JSON serialization (`model_dump(mode='json')`)
- Automatic documentation generation

### Core Models (New Version)

#### 1. Document Analysis Related
```python
# Document metadata
DocumentMetadata(
    document_type: str,           # document type
    company: str,                  # company name
    period: str,                   # reporting period
    publish_date: str | None,      # publish date
    key_topics: list[str]          # key topics
)

# Key metric (5-field complete structure)
KeyMetric(
    metric: str,                   # metric name
    current_value: str,            # current value
    previous_value: str | None,    # historical value (new)
    change: str | None,            # change magnitude (new)
    context: str | None,           # context explanation (new)
    source: str                    # citation source
)

# Content section (complete summary, not sparse bullet points)
ContentSection(
    section_id: str,               # section ID
    section_title: str,            # section title
    content: str,                  # detailed narrative summary
    key_metrics: list[KeyMetric],  # metrics for this section
    insights: list[str],           # key insights
    citations: list[dict]          # citation sources
)

# Key takeaway (high-level summary)
KeyTakeaway(
    id: str,
    category: str,                 # positive/negative/neutral
    statement: str,                # takeaway statement
    evidence: str,                 # supporting evidence
    significance: str,             # significance explanation
    sources: list[dict]            # citation sources
)
```

#### 2. Supplementary Research Needs (4 Dimensions)
```python
# Temporal update
TemporalUpdate(
    id: str,
    topic: str,                    # topic
    reason: str,                   # why update is needed
    search_queries: list[str],     # search query list
    priority: str                  # high/medium/low
)

# Comparative data
ComparativeData(
    id: str,
    comparison_type: str,          # industry_average/competitors/historical
    metric: str,                   # metric to compare
    reason: str,                   # reason for comparison
    search_queries: list[str]
)

# Deep dive analysis
DeepDiveAnalysis(
    id: str,
    topic: str,                    # deep dive topic
    question: str,                 # specific question
    reason: str,                   # why deep dive is needed
    search_queries: list[str]
)

# Market perspective
MarketPerspective(
    id: str,
    topic: str,                    # topic of interest
    perspective_type: str,         # analyst_ratings/institutional_views
    search_queries: list[str]
)

# Supplementary research needs (4-dimension aggregation)
SupplementaryResearchNeeds(
    temporal_updates: list[TemporalUpdate],
    comparative_data: list[ComparativeData],
    deep_dive_analysis: list[DeepDiveAnalysis],
    market_perspectives: list[MarketPerspective]
)
```

#### 3. Analysis Results
```python
AnalysisResult(
    analysis_id: str,
    source_document: dict,         # source document info
    document_metadata: DocumentMetadata,
    content_summary: list[ContentSection],      # 8-chapter complete summary
    key_takeaways: list[KeyTakeaway],           # 6 key takeaways
    supplementary_research_needs: SupplementaryResearchNeeds,  # 4-dimension needs
    charts_analysis: list[ChartAnalysis]
)
```

#### 4. Other Models
- `Citation` - Citation information
- `ChartAnalysis` - Chart analysis
- `SearchResult` - Search results
- `QueryResult` - Query results
- `ResearchResult` - Research results
- `ReportMetadata` - Report metadata

## API Provider

Currently supported:
- **CloseAI** (recommended): Gemini series, stable and available
- **APIYi**: Claude series, some models available
- **Yunwu AI**: Alternative

Configuration via environment variables:
```bash
CLOSEAI_API_KEY=sk-...
CLOSEAI_GOOGLE_BASE_URL=https://api.openai-proxy.org/google
```

## Performance Metrics (Actual Test Data)

### TSLA Q3 2025 Test (minimal mode, no image analysis, no external research)
- **Total Duration**: 150.3s
  - Parsing stage: 75.7s (Docling parses PDF, extracts 17 images)
  - Analysis stage: 54.3s (Gemini 2.5 Flash Lite, 59K characters)
  - Generation stage: 20.2s (Gemini 2.5 Flash Lite)
- **Cost**: ~$0.015 (all Gemini Flash Lite, no image analysis)

### TSLA Q3 2025 Test (full mode, with images + research)
- **Estimated Total Duration**: ~200s
  - Parsing stage: ~150s (includes Claude Vision analysis of 17 images)
  - Analysis stage: ~54s
  - Research stage: ~10s (13 queries, Tavily parallel)
  - Generation stage: ~20s
- **Estimated Cost**: ~$0.10 (includes Claude Vision image analysis + Tavily search)

## Quality Metrics (New Architecture)

### Information Density
- **Chapter Count**: 8 (vs old version 3-5 core findings) → **+60%~167%**
- **Total Metrics**: 25, each with 5 fields (vs old version 5-10, 1-2 fields) → **+150%~400%**
- **Total Insights**: 30 (vs old version 10-15) → **+100%~200%**
- **Content Character Count**: 3,492 characters of detailed narrative (vs old version sparse bullet points) → **Complete context**

### Structured Research Needs
- **Old Version**: Vague "information gaps", no clear definition
- **New Version**: 4 dimensions (timeliness + comparison + depth + market views), each with explicit `reason` + `search_queries`
- **Executability**: 100% (13 executable queries, vs old version vague questions)

### Q&A Support Capability
- **Complete Context Preservation**: ✅ (8 chapters + 25 metrics + 30 insights)
- **Precise Citations**: ✅ (all data has page-X#table-Y level citations)
- **Historical Comparison**: ✅ (metrics all have previous value + current value + change + context)

### Report Quality
- **Citation Coverage**: 100% (all observations have footnote citations)
- **Report Structure**: Executive summary + 4 core findings + industry comparison + risk analysis + investment recommendations
- **Citation Types**: 3 types (document + chart + external)
- **Traceability**: Complete (every data point can be traced to source document page)

## Architecture Improvement Comparison (Old vs New)

| Dimension | Old Architecture | New Architecture | Improvement |
|-----------|-----------------|------------------|-------------|
| **Output Structure** | 3-5 "core findings" | 8 complete chapters (detailed narrative) | +60%~167% information density |
| **Metric Detail** | Current value only | Previous + current + change + context + source (5 fields) | +250% contextual information |
| **Total Metrics** | 5-10 | **25** | +150%~400% |
| **Insights** | 10-15 | **30** | +100%~200% |
| **Research Need Definition** | Vague "information gaps" | 4-dimension structured (timeliness + comparison + depth + market views) | 100% executable |
| **Q&A Support** | ❌ Information too sparse | ✅ Complete context preserved | Can directly answer detailed questions |
| **Citation Precision** | Page level | Page + table level (e.g., page-5#table-2) | More precise location |

### Core Design Improvements

1. **Complete Summary First**
   - **Old Version**: Extract 3-5 "core findings" (bullet points)
   - **New Version**: Generate complete narrative summary of 8 chapters
   - **Benefit**: No information loss, supports subsequent Q&A

2. **Enhanced Metric Structuring**
   - **Old Version**: `KeyMetric(metric, current_value, source)`
   - **New Version**: `KeyMetric(metric, current_value, previous_value, change, context, source)`
   - **Benefit**: Historical comparison at a glance, clear context

3. **Precise Research Needs**
   - **Old Version**: `InformationGap(question, search_queries)` - vague definition
   - **New Version**: 4 dimensions, each with explicit `reason` field explaining why needed
     - `TemporalUpdate` - Timeliness supplement (e.g., "Document published 3 months ago, need latest developments")
     - `ComparativeData` - Comparison information (e.g., "Need to compare cost structure with BYD")
     - `DeepDiveAnalysis` - Deep analysis (e.g., "Robotaxi revenue contribution unclear")
     - `MarketPerspective` - Market views (e.g., "Analyst views on margin decline")
   - **Benefit**: Clear research objectives, executable searches

4. **Data Normalization**
   - **Problem**: Unstable LLM output (string vs list vs dict)
   - **Solution**: Added `_normalize_key_takeaway()` and `_normalize_chart_analysis()` standardization functions
   - **Benefit**: 100% Pydantic validation pass rate
