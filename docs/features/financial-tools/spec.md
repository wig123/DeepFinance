# financial-tools

金融数据工具集，基于 AKShare/efinance/yfinance。

## Goal

- 提供统一接口的金融数据获取
- 覆盖股票行情、财报、公司信息
- 支持 A股/港股/美股

## Inputs / Outputs

**Inputs**: 股票代码、数据类型、时间范围

**Outputs**:
```python
ToolResult(
    success=True,
    data={"symbol": "600519", "name": "贵州茅台", ...},
    source="akshare"
)
```

## Acceptance Criteria

- [x] AKShare 适配器：尽量覆盖多的数据
- [x] efinance 适配器：备用
- [x] yfinance 适配器：美股/全球
- [x] 统一 ToolResult 格式
- [x] 数据缓存机制

## Data Coverage

| 数据类型 | AKShare | efinance | yfinance |
|---------|---------|----------|----------|
| K线数据 | ✓ | ✓ | ✓ |
| 财务报表 | ✓ | ✓ | ✓ |
| 公司信息 | ✓ | ✓ | ✓ |

## Constraints

- AKShare 锁定版本（API 变动频繁）
- yfinance 可能需代理

## Non-goals

- 实时交易接口

## Links

- `src/tools/financial/`
