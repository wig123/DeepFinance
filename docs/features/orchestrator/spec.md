# orchestrator

Main orchestrator, LangGraph state graph managing the complete workflow.

## Goal

- Coordinate execution order of all Agents
- Manage state transitions
- Support interruption and resumption

## Workflow

```
Parser → Editor → Researcher(parallel) → Writer ⟷ Researcher
                                           ↓
                                       Reviewer → Publisher
```

## Inputs / Outputs

**Inputs**: Task description, input document directory

**Outputs**: Final report (multiple formats), execution logs

## Acceptance Criteria

- [ ] LangGraph StateGraph definition
- [ ] Complete workflow end-to-end example
- [ ] State transition logs viewable
- [ ] Support interruption and resumption

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

- Each node outputs logs
- State must be serializable

## Non-goals

- Distributed execution

## Links

- `src/agents/orchestrator.py`
- `src/memory/state.py`
