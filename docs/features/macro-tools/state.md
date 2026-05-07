# State: macro-tools

**Updated**: 2025-12-26

## Why

提供统一接口获取宏观经济数据（GDP、CPI/PPI、利率/汇率），支持金融研究报告生成。

## Status

- 基于 AKShare 的宏观数据工具已完成
- 支持中国及部分全球数据
- 主要阻塞：无

## Tasks

### Done

- [x] MacroTool 基类设计（统一接口）
- [x] MacroIndicator 枚举定义
- [x] AKShareMacroTool 实现
  - [x] GDP/GDP 同比
  - [x] CPI/CPI 同比/CPI 环比
  - [x] PPI/PPI 同比
  - [x] LPR 利率（1Y/5Y）
  - [x] 央行基准利率
  - [x] 汇率（即期/历史中间价）
  - [x] 进出口同比
- [x] 数据缓存机制（TTL: 1 小时）

## Decisions

1. **数据源**: 使用 AKShare 作为主力数据源
   - 相关 ADR: ADR-002

2. **缓存策略**: 宏观数据更新慢，默认缓存 1 小时，汇率缓存 5 分钟

3. **异步执行**: 使用 `run_in_executor` 包装同步 IO

## Risks

- AKShare API 可能变动，需锁定版本

## Known Issues & Workarounds

- 无
