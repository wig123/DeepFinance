# ADR-001: 多智能体架构设计

**Date**: 2025-12-26
**Status**: Accepted
**Related**: orchestrator, editor, researcher, writer, reviewer, publisher

## Context

需要构建一个金融报告生成系统，要求：
- 支持多源数据采集
- 动态回溯补充数据
- 可观测的执行过程
- 可扩展的 Agent 角色

## Decision

采用 LangGraph 多智能体架构，包含 6 个专职 Agent：

```
Parser → Editor → Researcher(并行) → Writer ⟷ Researcher → Reviewer → Publisher
```

- **Editor**: 规划研究大纲，分配任务
- **Researcher**: 执行数据采集（可被 Writer 回调）
- **Writer**: 生成带引用的报告
- **Reviewer**: 审核质量
- **Publisher**: 多格式输出

## Rationale

**选择此方案**:
- LangGraph 原生支持状态图和条件边，适合复杂工作流
- 职责分离便于独立测试和维护
- Writer 可直接调用 Researcher 实现动态回溯

**放弃的替代方案**:
- 单一 Agent + 工具调用：难以管理复杂状态
- CrewAI：封装过重，定制性不足

## Consequences

### 正面
- 每个 Agent 职责清晰，可独立测试
- 流程可观测，便于调试
- 支持中断恢复

### 负面/代价
- Agent 间通信需要定义清晰的接口
- 状态管理复杂度增加
