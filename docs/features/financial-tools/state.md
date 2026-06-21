# State: financial-tools

**Updated**: 2025-12-26

## Why

Provide a unified interface for financial data retrieval tools, supporting K-line data, financial reports, and company information for A-shares, Hong Kong stocks, and US stocks.

## Status

- Features completed
- Three data source adapters implemented
- Caching mechanism implemented

## Tasks

### Done

- [x] Create cache.py data caching mechanism (diskcache)
- [x] Create akshare_adapter.py - AKShare adapter (primary)
- [x] Create efinance_adapter.py - efinance adapter (fallback)
- [x] Create yfinance_adapter.py - yfinance adapter (US stocks)
- [x] Create financial/__init__.py unified interface
- [x] Update src/tools/__init__.py exports

## Decisions

1. **Three-tier data source strategy**: AKShare primary + efinance fallback + yfinance global
   - Related ADR: ADR-002

2. **Automatic data source detection**: Automatically select the best data source based on stock code

3. **Cache TTL strategy**:
   - K-line data: 4 hours
   - Financial statements: 1 day
   - Company information: 7 days
   - Real-time data: 1 minute

## Risks

- AKShare API changes frequently, requires regular testing
- yfinance may require proxy for mainland China access

## Known Issues & Workarounds

- Issue: Some AKShare APIs may fail due to network issues
  - Workaround: Automatically fallback to efinance
