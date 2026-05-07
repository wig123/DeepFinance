# researcher

研究员 Agent，执行多轮检索并收集带来源的数据。

## Goal

- 根据 Editor 分配的任务执行检索
- 调用 web-tools / financial-tools 获取数据
- 返回带来源的结构化数据

## Inputs / Outputs

**Inputs**: 研究任务（来自 Editor/Writer）

**Outputs**:
```python
{
    "query": "Tesla Q3 2025 财报",
    "results": [...],
    "sources": ["https://ir.tesla.com/..."]
}
```

## Acceptance Criteria

- [x] 根据大纲并行检索 (BatchExecutor)
- [x] 调用工具获取数据 (ToolExecutor)
- [x] 返回带来源的结果 (DataItem.source)
- [x] 中间结果可观测 (ExecutionResult)
- [ ] 集成测试通过

## Tool Usage

```
研究任务 → 选择工具 → 执行检索 → 验证结果 → 返回
              ↓
    web-tools / financial-tools / macro-tools
```

## Constraints

- 所有数据必须携带来源
- 可被 Writer 动态调用补充数据

## Non-goals

- 数据分析和报告撰写

## Links

- `src/agents/researcher/` - 模块目录
  - `agent.py` - ResearcherAgent 主类
  - `planner.py` - 研究计划生成
  - `executor.py` - 工具调用执行
  - `prompts.py` - 系统提示词
