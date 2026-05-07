# macro-tools

宏观经济数据工具，按需扩展。

## Goal

- 提供宏观指标获取接口
- 按需扩展具体指标
- 统一数据格式

## Inputs / Outputs

**Inputs**: 指标类型、时间范围、国家/地区

**Outputs**:
```python
ToolResult(
    success=True,
    data={"indicator": "GDP", "values": [...]},
    source="akshare"
)
```

## Acceptance Criteria

- [ ] 预留统一 MacroTool 接口
- [ ] 按需实现具体指标
- [ ] 带来源的结构化数据

## Potential Indicators

| 指标 | 优先级 | 数据源 |
|------|--------|--------|
| GDP | 按需 | AKShare |
| CPI/PPI | 按需 | AKShare |
| 利率/汇率 | 按需 | AKShare |

## Constraints

- 宏观数据更新慢，可缓存

## Non-goals

- 实时宏观数据

## Links

- `src/tools/macro/`
