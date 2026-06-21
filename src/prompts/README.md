# Prompt Management

All LLM prompts are stored in this directory for easy maintenance, version control, and optimization.

## File List

| File | Purpose | Used In |
|-----|------|---------|
| `document_analysis.txt` | Document analysis prompt | `DocumentAnalyzer` |
| `report_generation.txt` | Report generation prompt | `ReportGenerator` |

## Usage

### 1. Load Prompts

```python
from src.prompts import get_document_analysis_prompt

# Method 1: Use convenience function
prompt = get_document_analysis_prompt(
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)

# Method 2: Generic loader
from src.prompts import format_prompt

prompt = format_prompt(
    "document_analysis",
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)
```

### 2. Template Syntax

Uses Python's `str.format()` syntax:

```txt
You are a {role}.

Document information:
- Pages: {pages}
- Content: {content}
```

Variables are marked with `{variable_name}`, pass corresponding parameters when calling.

## Modifying Prompts

### Principles

1. **Maintain structured output** - Do not change JSON output format requirements
2. **Preserve key instructions** - Such as "return only JSON", "annotate citations", etc.
3. **Test and verify** - Run tests after modifications to ensure proper functionality

### Process

1. Edit the corresponding `.txt` file
2. Run tests to verify:
   ```bash
   uv run python test_pipeline.py --mode minimal
   ```
3. Check that the generated JSON structure is correct

## Adding New Prompts

1. Create new file: `src/prompts/your_prompt.txt`
2. Add convenience function in `__init__.py`:
   ```python
   def get_your_prompt(**kwargs) -> str:
       return format_prompt("your_prompt", **kwargs)
   ```
3. Import and use in code:
   ```python
   from src.prompts import get_your_prompt
   prompt = get_your_prompt(param1="...", param2="...")
   ```

## Prompt Design Guidelines

### Document Analysis Prompt

**Core Output**:
- `executive_summary` - Executive summary
- `key_findings` - Key findings (must include citations)
- `information_gaps` - Information gaps (generate search_queries)
- `charts_analysis` - Chart analysis summary

**Key Requirements**:
1. All findings must be annotated with citation locations
2. Information gaps should generate **3-5 specific search queries**
3. Return only JSON, no additional explanations

### Report Generation Prompt

**Core Output**: Complete Markdown research report

**Structure Requirements**:
- Executive summary
- Key findings (with citations)
- Industry comparison
- Risks and challenges
- Investment recommendations
- References

**Key Requirements**:
1. Use Markdown footnote citations: `[^ref-id]`
2. Citation coverage > 90%
3. Objective, neutral, data-driven

## Version History

| Date | File | Changes |
|-----|------|------|
| 2026-01-09 | All | Initial version, decoupled from code |
