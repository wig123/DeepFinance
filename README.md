# DeepFinance

A financial document analysis and in-depth research report generation system based on LangGraph multi-agent architecture.

## Demo Video

[![DeepFinance QA demo preview](docs/assets/deepfinance-showcase-qa-preview.gif)](docs/assets/deepfinance-showcase-qa-16x9.mp4)

Click the preview to watch the full DeepFinance QA demo with audio.

## Features

- ✅ **PDF Document Parsing**: Convert PDF to structured Markdown + images using Docling
- ✅ **Multi-source Data Collection**: Support for AKShare/efinance/yfinance (financial) + Tavily/Serper (search)
- ✅ **Multi-agent Collaboration**: Editor → Researcher → Writer → Reviewer → Publisher
- ✅ **Dynamic Backtracking Research**: Writer can callback Researcher during writing to supplement data
- ✅ **Citation Traceability**: All data carries source information, reports are traceable
- ✅ **Multi-format Export**: Support for HTML/PDF/Markdown/Word
- ✅ **Checkpoint Resume**: Using LangGraph memory checkpoints

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 2. Configure Environment Variables

```bash
# Copy configuration template
cp .env.example .env

# Edit .env and fill in your API keys
# At minimum, configure:
# - ANTHROPIC_API_KEY (or OPENAI_API_KEY)
# - TAVILY_API_KEY (optional, for web search)
```

### 3. Run Example

```bash
# View help
python -m src.main --help

# Parse PDF and generate report (prepare PDF file in inputs/ directory first)
python -m src.main --input inputs/report.pdf --output outputs/

# Enable streaming output to view execution process
python -m src.main --input inputs/report.pdf --stream

# Enable checkpoint resume
python -m src.main --input inputs/report.pdf --checkpoint --task-id my-task-001
```

### 4. Run Tests

```bash
# Run integration tests (no real PDF or API required)
python tests/test_integration.py
```

## Project Structure

```
DeepFinance/
├── src/
│   ├── agents/              # 6 agents
│   │   ├── editor/          # Plan outline
│   │   ├── researcher/      # Data collection
│   │   ├── writer/          # Report writing
│   │   └── reviewer/        # Quality review
│   ├── tools/               # Tool collection
│   │   ├── parser/          # PDF parsing
│   │   ├── financial/       # Financial data
│   │   ├── web/             # Web search
│   │   └── macro/           # Macro data
│   ├── orchestrator/        # LangGraph orchestrator
│   ├── publisher/           # Report export
│   ├── memory/              # State definition
│   └── main.py              # Command-line entry
├── inputs/                  # Input documents directory
├── outputs/                 # Generated reports directory
├── tests/                   # Tests
└── docs/                    # Documentation
```

## Workflow

```
📄 PDF Input
     ↓
🔍 Parser (Docling) → Markdown + Images
     ↓
📋 Editor → Plan research outline
     ↓
🔬 Researcher (parallel) → Multi-source data collection
     ↓
✍️  Writer ⟷ Researcher (dynamic backtracking)
     ↓
👀 Reviewer → Review and revise
     ↓
📦 Publisher → HTML/PDF/Word
```

## Main Commands

```bash
# Parse single PDF
python -m src.main -i inputs/report.pdf -o outputs/

# Batch process directory
python -m src.main -i inputs/ -o outputs/

# Specify task description
python -m src.main -i inputs/report.pdf -t "Analyze the company's 2023 financial report"

# Streaming output (view execution process of each node)
python -m src.main -i inputs/report.pdf --stream

# Enable checkpoint resume
python -m src.main -i inputs/report.pdf --checkpoint

# Debug mode
python -m src.main -i inputs/report.pdf --debug
```

## Configuration

### Required Configuration

- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`: LLM API key

### Optional Configuration

- `TAVILY_API_KEY`: Web search (recommended)
- `SERPER_API_KEY`: Alternative search engine
- Financial data sources: AKShare/efinance/yfinance are all free, no configuration needed

### Model Selection

Default uses Claude Sonnet 4 (`claude-sonnet-4-20250514`), customizable in `.env`:

```bash
EDITOR_MODEL=claude-sonnet-4-20250514
WRITER_MODEL=claude-opus-4-20241120
REVIEWER_MODEL=gpt-4-turbo
```

## Development Guide

### Adding New Features

```bash
# Use script to create new feature module
./docs/_scripts/new.sh feat my-feature
```

### Adding New Tools

1. Inherit from `BaseTool` class in `src/tools/base.py`
2. Implement in corresponding category directory
3. Auto-registration, no manual addition needed

### Adding New Agents

1. Create new directory under `src/agents/`
2. Implement Agent class and node functions
3. Integrate in `src/orchestrator/nodes.py`

## FAQ

### Q: How to test without PDF files?

A: Run `python tests/test_integration.py` to validate the workflow using mock data.

### Q: Can it run without API keys?

A: Yes, but Agents will degrade to placeholder mode. Recommend configuring at least `ANTHROPIC_API_KEY` for full functionality.

### Q: What PDF formats are supported?

A: Docling supports most PDFs (including scanned versions), with good table and image extraction.

### Q: How to add new data sources?

A: Create a new adapter under `src/tools/`, inheriting from `BaseTool` class.

## License

MIT

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent framework
- [Docling](https://github.com/DS4SD/docling) - PDF parsing
- [AKShare](https://github.com/akfamily/akshare) - Financial data
