# web-tools

Web search and crawler toolkit.

## Goal

- Provide unified interface for multiple search engines
- Return structured results with source attribution
- Support web page content extraction

## Inputs / Outputs

**Inputs**: Search keywords, engine selection (optional)

**Outputs**:
```python
ToolResult(
    success=True,
    data=[{"title": "...", "url": "...", "snippet": "..."}],
    source="tavily"
)
```

## Acceptance Criteria

- [ ] Implement tavily adapter
- [ ] Implement serper adapter
- [ ] Unified SearchTool interface
- [ ] Reserve interfaces for perplexity/brave

## Supported Engines

| Engine | Status | API Key |
|------|------|---------|
| Tavily | Required | `tvly-dev-...` |
| Serper | Required | `1550e507...` |
| Perplexity | Reserved | `pplx-MGXv...` |
| Brave | Reserved | `BSA0ZO3Y...` |

## Constraints

- Results must include source URL
- Single search timeout: 30s

## Non-goals

- Complex anti-scraping bypass

## Links

- `src/tools/web/`
