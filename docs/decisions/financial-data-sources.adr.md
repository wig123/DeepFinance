# ADR-002: Financial Data Source Selection

**Date**: 2025-12-26
**Status**: Accepted
**Related**: financial-tools, macro-tools

## Context

Need to acquire financial data (stock quotes, financial reports, macroeconomic indicators) with the following requirements:
- Free/open-source
- Coverage of A-shares/Hong Kong stocks/US stocks
- Stable and reliable

## Decision

Adopt a three-tier data source strategy:

| Priority | Data Source | Coverage |
|----------|-------------|----------|
| Primary | AKShare | A-shares/Hong Kong stocks/Macro |
| Backup | efinance | A-shares (East Money) |
| Global | yfinance | US stocks/Global |

## Rationale

**Why this approach**:
- AKShare has the most comprehensive coverage with an active community
- efinance uses different data sources, providing complementary coverage
- yfinance is the de facto standard for global markets

**Rejected alternatives**:
- Tushare Pro: Requires credits with rate limits
- Paid data sources: Cost considerations

## Consequences

### Positive
- Zero-cost startup
- Multi-source redundancy
- Coverage of major global markets

### Negative/Trade-offs
- AKShare API changes frequently, version pinning required
- yfinance may require proxy for mainland China access
- Data quality inferior to paid sources
