# editor

规划研究大纲 + 协调并行研究的 Agent。

## Goal

- 分析任务和源文档，规划研究大纲
- 分配子任务给 Researcher
- 协调并行研究

## Inputs / Outputs

**Inputs**: 任务描述、解析后的源文档

**Outputs**:
```python
{
    "outline": [
        {"section": "公司概况", "research_queries": [...]},
        {"section": "财务分析", "research_queries": [...]}
    ],
    "parallel_tasks": [...]
}
```

## Acceptance Criteria

- [ ] 输入任务 → 输出研究大纲
- [ ] 可分配子任务给多个 Researcher
- [ ] 输出日志可查看
- [ ] 集成测试通过

## Workflow

```
源文档 + 任务 → 分析关键点 → 生成大纲 → 分配 Researcher
```

## Constraints

- 大纲结构化输出
- 每个 section 有明确的研究方向

## Non-goals

- 直接执行研究任务

## Links

- `src/agents/editor.py`
