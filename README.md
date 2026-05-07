# DeepFinance

基于 LangGraph 多智能体的金融文档分析与深度研究报告生成系统。

## 特性

- ✅ **PDF 文档解析**: 使用 Docling 将 PDF 转为结构化 Markdown + 图片
- ✅ **多源数据采集**: 支持 AKShare/efinance/yfinance（金融）+ Tavily/Serper（搜索）
- ✅ **多智能体协作**: Editor → Researcher → Writer → Reviewer → Publisher
- ✅ **动态回溯研究**: Writer 可在写作过程中回调 Researcher 补充数据
- ✅ **引用溯源**: 所有数据携带来源信息，报告可溯源
- ✅ **多格式导出**: 支持 HTML/PDF/Markdown/Word
- ✅ **断点续传**: 使用 LangGraph 内存检查点

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入你的 API keys
# 至少需要配置:
# - ANTHROPIC_API_KEY (或 OPENAI_API_KEY)
# - TAVILY_API_KEY (可选，用于网络搜索)
```

### 3. 运行示例

```bash
# 查看帮助
python -m src.main --help

# 解析 PDF 并生成报告（需要先准备 PDF 文件到 inputs/ 目录）
python -m src.main --input inputs/report.pdf --output outputs/

# 启用流式输出，查看执行过程
python -m src.main --input inputs/report.pdf --stream

# 启用断点续传
python -m src.main --input inputs/report.pdf --checkpoint --task-id my-task-001
```

### 4. 运行测试

```bash
# 运行集成测试（不需要真实 PDF 和 API）
python tests/test_integration.py
```

## 项目结构

```
DeepFinance/
├── src/
│   ├── agents/              # 6 个智能体
│   │   ├── editor/          # 规划大纲
│   │   ├── researcher/      # 数据采集
│   │   ├── writer/          # 报告撰写
│   │   └── reviewer/        # 质量审核
│   ├── tools/               # 工具集
│   │   ├── parser/          # PDF 解析
│   │   ├── financial/       # 金融数据
│   │   ├── web/             # 网页搜索
│   │   └── macro/           # 宏观数据
│   ├── orchestrator/        # LangGraph 编排器
│   ├── publisher/           # 报告导出
│   ├── memory/              # 状态定义
│   └── main.py              # 命令行入口
├── inputs/                  # 输入文档目录
├── outputs/                 # 生成报告目录
├── tests/                   # 测试
└── docs/                    # 文档
```

## 工作流程

```
📄 PDF Input
     ↓
🔍 Parser (Docling) → Markdown + Images
     ↓
📋 Editor → 规划研究大纲
     ↓
🔬 Researcher (并行) → 多源数据采集
     ↓
✍️  Writer ⟷ Researcher (动态回溯)
     ↓
👀 Reviewer → 审核修订
     ↓
📦 Publisher → HTML/PDF/Word
```

## 主要命令

```bash
# 解析单个 PDF
python -m src.main -i inputs/report.pdf -o outputs/

# 批量处理目录
python -m src.main -i inputs/ -o outputs/

# 指定任务描述
python -m src.main -i inputs/report.pdf -t "分析该公司2023年财报"

# 流式输出（查看每个节点的执行过程）
python -m src.main -i inputs/report.pdf --stream

# 启用断点续传
python -m src.main -i inputs/report.pdf --checkpoint

# 调试模式
python -m src.main -i inputs/report.pdf --debug
```

## 配置说明

### 必需配置

- `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`: LLM API 密钥

### 可选配置

- `TAVILY_API_KEY`: 网络搜索（推荐）
- `SERPER_API_KEY`: 备用搜索引擎
- 金融数据源：AKShare/efinance/yfinance 均为免费，无需配置

### 模型选择

默认使用 Claude Sonnet 4 (`claude-sonnet-4-20250514`)，可在 `.env` 中自定义：

```bash
EDITOR_MODEL=claude-sonnet-4-20250514
WRITER_MODEL=claude-opus-4-20241120
REVIEWER_MODEL=gpt-4-turbo
```

## 开发指南

### 添加新功能

```bash
# 使用脚本创建新功能模块
./docs/_scripts/new.sh feat my-feature
```

### 添加新工具

1. 继承 `src/tools/base.py` 的 `BaseTool` 类
2. 在对应 category 目录下实现
3. 自动注册，无需手动添加

### 添加新 Agent

1. 在 `src/agents/` 下创建新目录
2. 实现 Agent 类和节点函数
3. 在 `src/orchestrator/nodes.py` 中集成

## 常见问题

### Q: 没有 PDF 文件怎么测试？

A: 运行 `python tests/test_integration.py`，使用 mock 数据验证流程。

### Q: 没有 API key 能运行吗？

A: 可以，但 Agents 会降级到占位模式。建议配置至少 `ANTHROPIC_API_KEY` 体验完整功能。

### Q: 支持哪些 PDF 格式？

A: Docling 支持大部分 PDF（包括扫描版），表格和图片提取效果良好。

### Q: 如何添加新的数据源？

A: 在 `src/tools/` 下创建新的适配器，继承 `BaseTool` 类即可。

## 许可证

MIT

## 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体框架
- [Docling](https://github.com/DS4SD/docling) - PDF 解析
- [AKShare](https://github.com/akfamily/akshare) - 金融数据
