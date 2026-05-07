# orchestrator

主编排器，LangGraph 状态图管理完整流程。

## Goal

- 协调所有 Agent 执行顺序
- 管理状态流转
- 支持中断和恢复

## Workflow

```
Parser → Editor → Researcher(并行) → Writer ⟷ Researcher
                                        ↓
                                    Reviewer → Publisher
```

## Inputs / Outputs

**Inputs**: 任务描述、输入文档目录

**Outputs**: 最终报告（多格式）、执行日志

## Acceptance Criteria

- [ ] LangGraph StateGraph 定义
- [ ] 完整流程跑通示例
- [ ] 状态转换日志可查看
- [ ] 支持中断恢复

## State Definition

```python
class ReportState(TypedDict):
    task: dict
    source_docs: List[str]
    research_outline: dict
    research_data: List[dict]
    draft: str
    review_feedback: str
    final_report: str
    sources: List[str]
```

## Constraints

- 每个节点输出日志
- 状态可序列化

## Non-goals

- 分布式执行

## Links

- `src/agents/orchestrator.py`
- `src/memory/state.py`
