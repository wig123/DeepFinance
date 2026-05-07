# State: financial-tools

**Updated**: 2025-12-26

## Why

提供统一接口的金融数据获取工具，支持 A股/港股/美股的 K线、财报、公司信息。

## Status

- 功能已完成
- 三个数据源适配器已实现
- 缓存机制已实现

## Tasks

### Done

- [x] 创建 cache.py 数据缓存机制（diskcache）
- [x] 创建 akshare_adapter.py - AKShare 适配器（主力）
- [x] 创建 efinance_adapter.py - efinance 适配器（备用）
- [x] 创建 yfinance_adapter.py - yfinance 适配器（美股）
- [x] 创建 financial/__init__.py 统一接口
- [x] 更新 src/tools/__init__.py 导出

## Decisions

1. **三层数据源策略**: AKShare 主力 + efinance 备用 + yfinance 全球
   - 相关 ADR: ADR-002

2. **自动数据源检测**: 根据股票代码自动选择最佳数据源

3. **缓存 TTL 策略**:
   - K线数据: 4小时
   - 财务报表: 1天
   - 公司信息: 7天
   - 实时数据: 1分钟

## Risks

- AKShare API 变动频繁，需定期测试
- yfinance 大陆访问可能需代理

## Known Issues & Workarounds

- Issue: AKShare 部分接口可能因网络问题失败
  - Workaround: 自动降级到 efinance
