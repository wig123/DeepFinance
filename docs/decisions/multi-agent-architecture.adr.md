# ADR-001: Multi-Agent Architecture Design

**Date**: 2025-12-26
**Status**: Accepted
**Related**: orchestrator, editor, researcher, writer, reviewer, publisher

## Context

Need to build a financial report generation system with the following requirements:
- Support multi-source data collection
- Dynamic backtracking for supplementary data
- Observable execution process
- Extensible Agent roles

## Decision

Adopt a LangGraph multi-agent architecture with 6 specialized Agents:

```
Parser → Editor → Researcher(parallel) → Writer ⟷ Researcher → Reviewer → Publisher
```

- **Editor**: Plan research outline and assign tasks
- **Researcher**: Execute data collection (can be called back by Writer)
- **Writer**: Generate reports with citations
- **Reviewer**: Review quality
- **Publisher**: Multi-format output

## Rationale

**Why this approach**:
- LangGraph natively supports state graphs and conditional edges, suitable for complex workflows
- Separation of concerns facilitates independent testing and maintenance
- Writer can directly invoke Researcher to enable dynamic backtracking

**Rejected alternatives**:
- Single Agent + tool calling: difficult to manage complex state
- CrewAI: over-encapsulated, insufficient customizability

## Consequences

### Positive
- Each Agent has clear responsibilities and can be tested independently
- Observable workflow, easy to debug
- Supports interruption and resumption

### Negative/Trade-offs
- Inter-Agent communication requires well-defined interfaces
- Increased state management complexity
