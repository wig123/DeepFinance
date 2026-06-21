# researcher

Researcher Agent that performs multi-round retrieval and collects data with sources.

## Goal

- Execute retrieval based on tasks assigned by Editor
- Call web-tools / financial-tools to obtain data
- Return structured data with sources

## Inputs / Outputs

**Inputs**: Research tasks (from Editor/Writer)

**Outputs**:
```python
{
    "query": "Tesla Q3 2025 financial report",
    "results": [...],
    "sources": ["https://ir.tesla.com/..."]
}
```

## Acceptance Criteria

- [x] Parallel retrieval based on outline (BatchExecutor)
- [x] Call tools to obtain data (ToolExecutor)
- [x] Return results with sources (DataItem.source)
- [x] Intermediate results are observable (ExecutionResult)
- [ ] Integration tests pass

## Tool Usage

```
Research task → Select tool → Execute retrieval → Validate results → Return
                     ↓
         web-tools / financial-tools / macro-tools
```

## Constraints

- All data must carry sources
- Can be dynamically called by Writer to supplement data

## Non-goals

- Data analysis and report writing

## Links

- `src/agents/researcher/` - Module directory
  - `agent.py` - ResearcherAgent main class
  - `planner.py` - Research plan generation
  - `executor.py` - Tool call execution
  - `prompts.py` - System prompt
