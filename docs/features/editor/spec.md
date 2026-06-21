# editor

Agent for planning research outlines and coordinating parallel research.

## Goal

- Analyze tasks and source documents, plan research outlines
- Assign subtasks to Researchers
- Coordinate parallel research

## Inputs / Outputs

**Inputs**: Task description, parsed source documents

**Outputs**:
```python
{
    "outline": [
        {"section": "Company Overview", "research_queries": [...]},
        {"section": "Financial Analysis", "research_queries": [...]}
    ],
    "parallel_tasks": [...]
}
```

## Acceptance Criteria

- [ ] Input task → Output research outline
- [ ] Can assign subtasks to multiple Researchers
- [ ] Output logs are viewable
- [ ] Integration tests pass

## Workflow

```
Source documents + Task → Analyze key points → Generate outline → Assign Researcher
```

## Constraints

- Structured outline output
- Each section has a clear research direction

## Non-goals

- Directly execute research tasks

## Links

- `src/agents/editor.py`
