# State: web-tools

**Updated**: 2025-12-26

## Why

提供统一接口的多搜索引擎支持，为金融研究提供网络信息检索能力。

## Status

- 核心功能已完成实现
- Tavily 和 Serper 适配器就绪
- 主要阻塞：无

## Tasks

### Done

- [x] 创建目录结构 `src/tools/web/`
- [x] 实现 `base_search.py` - SearchTool 基类和 ToolResult 数据结构
- [x] 实现 `tavily_search.py` - Tavily 搜索适配器
- [x] 实现 `serper_search.py` - Serper 搜索适配器
- [x] 创建 `config.yaml` 配置文件存储 API keys
- [x] 统一接口设计，支持 SearchFactory 工厂模式

### Pending

- [ ] perplexity 适配器（预留接口）
- [ ] brave 适配器（预留接口）
- [ ] 网页正文爬取功能

## Decisions

1. **工厂模式**: 使用 SearchFactory 统一创建搜索引擎实例，便于扩展
2. **异步设计**: 所有搜索方法使用 async/await，支持并发调用
3. **配置管理**: API keys 存储在项目根目录 `config.yaml`，支持环境隔离

## Risks

- API key 安全性：生产环境应使用环境变量而非配置文件

## Known Issues & Workarounds

- 无当前已知问题
