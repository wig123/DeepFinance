# ADR-002: 金融数据源选型

**Date**: 2025-12-26
**Status**: Accepted
**Related**: financial-tools, macro-tools

## Context

需要获取金融数据（股票行情、财报、宏观指标），要求：
- 免费/开源
- 覆盖 A股/港股/美股
- 稳定可靠

## Decision

采用三层数据源策略：

| 优先级 | 数据源 | 覆盖范围 |
|--------|--------|---------|
| 主力 | AKShare | A股/港股/宏观 |
| 备用 | efinance | A股（东方财富）|
| 全球 | yfinance | 美股/全球 |

## Rationale

**选择此方案**:
- AKShare 覆盖最全面，社区活跃
- efinance 数据源不同，可互补
- yfinance 是全球市场事实标准

**放弃的替代方案**:
- Tushare Pro：需要积分，有频次限制
- 付费数据源：成本考虑

## Consequences

### 正面
- 零成本启动
- 多数据源互备
- 覆盖全球主要市场

### 负面/代价
- AKShare API 变动频繁，需锁定版本
- yfinance 大陆访问可能需代理
- 数据质量不如付费源
