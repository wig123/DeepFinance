# State: Researcher Agent

**Updated**: 2025-12-26

## Why

实现多源数据收集的核心模块，支持 Editor 分配的研究任务和 Writer 的动态回调。

## Status

- 核心模块已实现完成
- 支持 financial/web/macro/parser 四类工具
- 支持并发执行和动态回调

## Tasks

### Done

- [x] 创建目录结构 `src/agents/researcher/`
- [x] 实现 prompts.py - 系统提示词
- [x] 实现 planner.py - 研究计划生成（规则引擎 + LLM 混合）
- [x] 实现 executor.py - 并发工具调用执行
- [x] 实现 agent.py - ResearcherAgent 主类
- [x] 实现 __init__.py - 模块导出
- [x] 更新 agents/__init__.py 导出

## Decisions

1. **规则引擎 + LLM 混合规划**: 优先使用关键词规则快速匹配工具，复杂问题可选 LLM 规划
2. **可靠性评分**: 结构化数据源（financial/macro）0.95，网页搜索 0.70
3. **数据缓存**: 支持缓存已获取数据，避免重复请求

## Risks

- 工具 API 可用性依赖外部服务
- 需要配置各数据源的 API Key
