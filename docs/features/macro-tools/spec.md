# macro-tools

Macroeconomic data tools, extensible on demand.

## Goal

- Provide macroeconomic indicator retrieval interface
- Extend specific indicators on demand
- Unify data format

## Inputs / Outputs

**Inputs**: Indicator type, time range, country/region

**Outputs**:
```python
ToolResult(
    success=True,
    data={"indicator": "GDP", "values": [...]},
    source="akshare"
)
```

## Acceptance Criteria

- [ ] Reserve unified MacroTool interface
- [ ] Implement specific indicators on demand
- [ ] Structured data with sources

## Potential Indicators

| Indicator | Priority | Data Source |
|------|--------|--------|
| GDP | On demand | AKShare |
| CPI/PPI | On demand | AKShare |
| Interest Rate/Exchange Rate | On demand | AKShare |

## Constraints

- Macroeconomic data updates slowly, can be cached

## Non-goals

- Real-time macroeconomic data

## Links

- `src/tools/macro/`
