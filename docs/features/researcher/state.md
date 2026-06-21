# State: Researcher Agent

**Updated**: 2025-12-26

## Why

Core module for implementing multi-source data collection, supporting research tasks assigned by Editor and dynamic callbacks from Writer.

## Status

- Core module implementation completed
- Supports four types of tools: financial/web/macro/parser
- Supports concurrent execution and dynamic callbacks

## Tasks

### Done

- [x] Create directory structure `src/agents/researcher/`
- [x] Implement prompts.py - system prompts
- [x] Implement planner.py - research plan generation (rule engine + LLM hybrid)
- [x] Implement executor.py - concurrent tool invocation execution
- [x] Implement agent.py - ResearcherAgent main class
- [x] Implement __init__.py - module exports
- [x] Update agents/__init__.py exports

## Decisions

1. **Rule Engine + LLM Hybrid Planning**: Prioritize keyword-based rules for fast tool matching, with optional LLM planning for complex queries
2. **Reliability Scoring**: Structured data sources (financial/macro) 0.95, web search 0.70
3. **Data Caching**: Support caching of retrieved data to avoid redundant requests

## Risks

- Tool API availability depends on external services
- Requires API Key configuration for each data source
