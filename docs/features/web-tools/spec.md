# web-tools

网页搜索与爬虫工具集。

## Goal

- 提供统一接口的多搜索引擎支持
- 返回结构化结果 + 来源标识
- 支持网页正文爬取

## Inputs / Outputs

**Inputs**: 搜索关键词、引擎选择（可选）

**Outputs**:
```python
ToolResult(
    success=True,
    data=[{"title": "...", "url": "...", "snippet": "..."}],
    source="tavily"
)
```

## Acceptance Criteria

- [ ] 实现 tavily 适配器
- [ ] 实现 serper 适配器
- [ ] 统一 SearchTool 接口
- [ ] perplexity/brave 预留接口

## Supported Engines

| 引擎 | 状态 | API Key |
|------|------|---------|
| Tavily | 必须 | `tvly-dev-...` |
| Serper | 必须 | `1550e507...` |
| Perplexity | 预留 | `pplx-MGXv...` |
| Brave | 预留 | `BSA0ZO3Y...` |

## Constraints

- 结果必须携带来源 URL
- 单次搜索超时 30s

## Non-goals

- 复杂反爬绕过

## Links

- `src/tools/web/`
