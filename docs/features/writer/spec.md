# writer

Writer Agent that generates reports with citations and can dynamically invoke Researcher to supplement data.

## Goal

- Generate report drafts based on research data
- Ensure all data points have citations
- Invoke Researcher to supplement data when insufficient

## Inputs / Outputs

**Inputs**: Research outline, research data, source documents

**Outputs**:
```python
{
    "draft": "# Report Title\n...",
    "sources": ["[^1]: ...", "[^2]: ..."],
    "data_gaps": []  # or data that needs to be supplemented
}
```

## Acceptance Criteria

- [ ] Generate reports with citations
- [ ] Can invoke Researcher to supplement data (dynamic backtracking)
- [ ] Output logs are viewable
- [ ] Integration tests pass

## Callback Mechanism

```
Insufficient data found during writing → Call Researcher → Obtain supplemental data → Continue writing
```

## Citation Format

```markdown
According to Tesla Q3 2025 financial report[^1], revenue reached...

[^1]: Tesla Q3 2025 Update, https://ir.tesla.com/...
```

## Constraints

- Prohibited from generating data points without sources
- Unified citation format

## Non-goals

- Format layout (handled by Publisher)

## Links

- `src/agents/writer.py`
