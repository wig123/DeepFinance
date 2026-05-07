# State: Orchestrator

**Updated**: 2025-12-26

## Why

实现 LangGraph 工作流编排器，作为报告生成系统的核心调度模块。

## Status

- 模块实现完成，所有功能验证通过
- 支持 invoke 和 stream 两种执行方式
- 支持 MemorySaver 断点续传

## Tasks

### Done

- [x] 创建 src/orchestrator/ 目录结构
- [x] 实现 nodes.py - 6 个节点函数（plan, research, write, review, publish, supplement）
- [x] 实现 edges.py - 2 个条件路由器（review_router, data_gap_router）
- [x] 实现 graph.py - 完整 StateGraph 定义
- [x] 实现 __init__.py - 模块导出
- [x] 验证 graph.invoke() 执行
- [x] 验证 graph.stream() 执行
- [x] 验证 checkpoint 断点续传

## Decisions

1. **节点设计**: 当前为占位实现，后续由具体 Agent 替换
2. **回调机制**: 通过 data_gap_router 实现 Writer 动态调用 Researcher
3. **审核循环**: review_router 根据 review_status 决定通过或返回修改

## Risks

无

## Known Issues & Workarounds

无
