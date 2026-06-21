# DeepFinance

A financial document analysis and in-depth research report generation system based on long-context LLMs.

## Goals & Non-goals

**Goals**:
- Parse financial PDF documents (including charts) into structured Markdown + images
- Multi-source financial data collection (API, web, database)
- Dynamic retrospective in-depth research (supplemental data during analysis)
- Generate traceable, well-formatted reports (supporting HTML/PDF/Word)

**Non-goals**:
- RAG retrieval system (document scale <100 pages, full content reading)
- Real-time trading system
- Data storage/database management

## Tech Stack

- **Doc Parsing**: Docling (PDF/image extraction) + Claude Vision (chart analysis)
- **LLM**:
  - Gemini 2.0 Flash (document analysis, long context + low cost)
  - Claude Sonnet 4.5 (report generation, highest quality)
- **Data Sources**: Tavily Search + financial APIs (AKShare/yfinance)
- **Export**: WeasyPrint (PDF) / python-docx (Word)

## Directory Map

```
DeepFinance/
├── docs/                     # Documentation
│   ├── _ai-rules.md          # AI writing rules (must read)
│   ├── decisions/            # Architecture Decision Records (ADR)
│   └── features/             # Feature specifications
├── src/
│   ├── models/               # Data models
│   │   └── report.py         # Report-related models
│   ├── analyzers/            # Analyzers
│   │   ├── document_analyzer.py   # Document analysis
│   │   ├── data_researcher.py     # Data supplementation
│   │   └── report_generator.py    # Report generation
│   ├── pipeline/             # Pipeline
│   │   └── report_pipeline.py     # Main pipeline
│   ├── tools/                # Tool modules
│   │   ├── parser/           # Document parsing (Docling + image analysis)
│   │   ├── financial/        # Financial data tools
│   │   ├── web/              # Web search
│   │   └── macro/            # Macro data
│   └── publisher/            # Report export (HTML/PDF/Word)
├── scripts/                  # Entry scripts (API startup / end-to-end tests)
├── outputs/                  # Generated reports directory
└── tests/                    # Integration tests
```

## Architecture

**Simplified three-step pipeline**:

```
PDF → DoclingParser → DocumentAnalyzer → DataResearcher → ReportGenerator
         (image analysis)  (Gemini analysis)  (parallel search)  (Claude generation)
```

**Process description**:

1. **Parsing Stage** (DoclingParser)
   - Extract document structure (headings, paragraphs, tables)
   - Save images and intelligently analyze (in-depth chart analysis vs. simple illustration description)
   - Output: Markdown + metadata.json

2. **Analysis Stage** (DocumentAnalyzer)
   - Use Gemini 2.0 Flash to read all content at once
   - Generate executive summary, key findings
   - Identify information gaps, generate search queries
   - Output: 01_analysis.json

3. **Research Stage** (DataResearcher, optional)
   - Execute web searches in parallel (Tavily)
   - Intelligently call financial APIs (TODO)
   - Output: 02_research.json

4. **Generation Stage** (ReportGenerator)
   - Use Claude Sonnet 4.5 to generate final report
   - Markdown format + footnote citations
   - Output: report.md + report_metadata.json

**Output structure**:

```
outputs/TSLA-Q3-2025_20260109/
├── source/
│   ├── content.md            # Parsed document
│   ├── metadata.json         # Metadata
│   └── images/               # Images
├── 01_analysis.json          # Document analysis
├── 02_research.json          # Supplemental research
├── report.md                 # Final report
└── report_metadata.json      # Report metadata
```

## Commands

```bash
# Install dependencies
uv sync

# Run full pipeline
uv run python scripts/run_pipeline.py --mode full

# Without external research (faster)
uv run python scripts/run_pipeline.py --mode no-research

# Minimal configuration (all Gemini, cheapest)
uv run python scripts/run_pipeline.py --mode minimal

# Python API usage
from src.pipeline import ReportPipeline

pipeline = ReportPipeline(
    enable_image_analysis=True,
    enable_research=True,
    analyzer_model="gemini-2.0-flash",
    generator_model="claude-sonnet-4-5-20250929",
)
output_dir = pipeline.run("path/to/document.pdf")
```

## Rules for Claude

1. **Before writing documentation**: Must read `docs/_ai-rules.md` first
2. **New features**: **Must** use `./docs/_scripts/new.sh feat <name>`
3. **Tool development**:
   - Inherit from the Tool base class in `src/tools/base.py`
   - Implement in the corresponding category directory
   - Automatic registration mechanism, no manual addition needed
4. **Data models**:
   - Use Pydantic models from `src/models/report.py`
   - All intermediate results and final reports use standardized models
5. **Citation tracking**: All external data must carry source information
   - Use Markdown footnote format: `[^ref-id]`
   - Citation definition: `[^ref-id]: [description](location)`

## Key Design Principles

1. **Simple over complex**: Linear pipeline replaces complex Agent orchestration
2. **Leverage long context**: Gemini 2.0 Flash supports 1M tokens, no RAG needed
3. **Cost optimization**: Use Gemini for analysis (cheap), Claude for generation (high quality)
4. **Traceability**: Each step outputs independent JSON for easy debugging and retrospection
5. **Parallel optimization**: Research stage uses asyncio for parallel queries

## Task State

Long-term tasks use a feature-centric documentation system:
- `docs/features/<name>/spec.md` - Feature specifications (stable)
- `docs/features/<name>/state.md` - Progress tracking (temporary)

Major decisions are synced to `docs/decisions/*.adr.md`
