# State: macro-tools

**Updated**: 2025-12-26

## Why

Provide a unified interface for retrieving macroeconomic data (GDP, CPI/PPI, interest rates/exchange rates) to support financial research report generation.

## Status

- Macro data tools based on AKShare are completed
- Support for China and partial global data
- Main blockers: None

## Tasks

### Done

- [x] MacroTool base class design (unified interface)
- [x] MacroIndicator enum definition
- [x] AKShareMacroTool implementation
  - [x] GDP/GDP YoY
  - [x] CPI/CPI YoY/CPI MoM
  - [x] PPI/PPI YoY
  - [x] LPR interest rate (1Y/5Y)
  - [x] Central bank benchmark interest rate
  - [x] Exchange rate (spot/historical middle rate)
  - [x] Import/export YoY
- [x] Data caching mechanism (TTL: 1 hour)

## Decisions

1. **Data Source**: Use AKShare as the primary data source
   - Related ADR: ADR-002

2. **Caching Strategy**: Macro data updates slowly, default cache 1 hour, exchange rate cache 5 minutes

3. **Async Execution**: Use `run_in_executor` to wrap synchronous IO

## Risks

- AKShare API may change, version pinning required

## Known Issues & Workarounds

- None
