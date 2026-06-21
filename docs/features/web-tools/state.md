# State: web-tools

**Updated**: 2025-12-26

## Why

Provide unified interface for multiple search engines to enable web information retrieval capabilities for financial research.

## Status

- Core functionality implemented
- Tavily and Serper adapters ready
- Main blockers: None

## Tasks

### Done

- [x] Create directory structure `src/tools/web/`
- [x] Implement `base_search.py` - SearchTool base class and ToolResult data structure
- [x] Implement `tavily_search.py` - Tavily search adapter
- [x] Implement `serper_search.py` - Serper search adapter
- [x] Create `config.yaml` configuration file to store API keys
- [x] Unified interface design with SearchFactory factory pattern support

### Pending

- [ ] perplexity adapter (interface reserved)
- [ ] brave adapter (interface reserved)
- [ ] Web page content scraping functionality

## Decisions

1. **Factory Pattern**: Use SearchFactory to uniformly create search engine instances for easy extension
2. **Async Design**: All search methods use async/await to support concurrent calls
3. **Configuration Management**: API keys stored in project root `config.yaml`, supports environment isolation

## Risks

- API key security: Production environments should use environment variables instead of configuration files

## Known Issues & Workarounds

- No known issues at this time
