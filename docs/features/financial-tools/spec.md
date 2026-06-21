# financial-tools

Financial data toolkit based on AKShare/efinance/yfinance.

## Goal

- Provide unified interface for financial data retrieval
- Cover stock quotes, financial reports, and company information
- Support A-shares/Hong Kong stocks/US stocks

## Inputs / Outputs

**Inputs**: Stock code, data type, time range

**Outputs**:
```python
ToolResult(
    success=True,
    data={"symbol": "600519", "name": "Kweichow Moutai", ...},
    source="akshare"
)
```

## Acceptance Criteria

- [x] AKShare adapter: cover as much data as possible
- [x] efinance adapter: backup
- [x] yfinance adapter: US stocks/global
- [x] Unified ToolResult format
- [x] Data caching mechanism

## Data Coverage

| Data Type | AKShare | efinance | yfinance |
|---------|---------|----------|----------|
| K-line data | ✓ | ✓ | ✓ |
| Financial statements | ✓ | ✓ | ✓ |
| Company information | ✓ | ✓ | ✓ |

## Constraints

- AKShare version locked (API changes frequently)
- yfinance may require proxy

## Non-goals

- Real-time trading interface

## Links

- `src/tools/financial/`
