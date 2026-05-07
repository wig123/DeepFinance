# DeepFinance

基于长上下文LLM的金融文档分析与深度研究报告生成系统。

## Goals & Non-goals

**Goals**:
- 解析金融 PDF 文档（含图表）为结构化 Markdown + 图片
- 多源金融数据采集（API、网页、数据库）
- 动态回溯式深度研究（分析过程中可补充数据）
- 生成可溯源的精美报告（支持 HTML/PDF/Word）

**Non-goals**:
- RAG 检索系统（文档规模 <100 页，全量读取）
- 实时交易系统
- 数据存储/数据库管理

## Tech Stack

- **Doc Parsing**: Docling（PDF/图片提取）+ Claude Vision（图表分析）
- **LLM**:
  - Gemini 2.0 Flash（文档分析，长上下文+低成本）
  - Claude Sonnet 4.5（报告生成，质量最高）
- **Data Sources**: Tavily Search + 金融API（AKShare/yfinance）
- **Export**: WeasyPrint (PDF) / python-docx (Word)

## Directory Map

```
DeepFinance/
├── docs/                     # 文档
│   ├── _ai-rules.md          # AI写作规则（必读）
│   ├── decisions/            # 架构决策 ADR
│   └── features/             # 功能规格
├── src/
│   ├── models/               # 数据模型
│   │   └── report.py         # 报告相关模型
│   ├── analyzers/            # 分析器
│   │   ├── document_analyzer.py   # 文档分析
│   │   ├── data_researcher.py     # 数据补充
│   │   └── report_generator.py    # 报告生成
│   ├── pipeline/             # 流水线
│   │   └── report_pipeline.py     # 主流水线
│   ├── tools/                # 工具模块
│   │   ├── parser/           # 文档解析（Docling + 图片分析）
│   │   ├── financial/        # 金融数据工具
│   │   ├── web/              # 网页搜索
│   │   └── macro/            # 宏观数据
│   └── publisher/            # 报告导出（HTML/PDF/Word）
├── scripts/                  # 入口脚本（API 启动 / 端到端测试）
├── outputs/                  # 生成报告目录
└── tests/                    # 集成测试
```

## Architecture

**简化的三步流水线**：

```
PDF → DoclingParser → DocumentAnalyzer → DataResearcher → ReportGenerator
         (图片分析)       (Gemini分析)      (并行搜索)        (Claude生成)
```

**流程说明**：

1. **解析阶段**（DoclingParser）
   - 提取文档结构（标题、段落、表格）
   - 保存图片并智能分析（图表深度分析 vs 插图简单描述）
   - 输出：Markdown + metadata.json

2. **分析阶段**（DocumentAnalyzer）
   - 使用Gemini 2.0 Flash一次性读取全部内容
   - 生成执行摘要、核心发现
   - 识别信息缺口，生成搜索查询
   - 输出：01_analysis.json

3. **研究阶段**（DataResearcher，可选）
   - 并行执行Web搜索（Tavily）
   - 智能调用金融API（TODO）
   - 输出：02_research.json

4. **生成阶段**（ReportGenerator）
   - 使用Claude Sonnet 4.5生成最终报告
   - Markdown格式 + 脚注引用
   - 输出：report.md + report_metadata.json

**输出结构**：

```
outputs/TSLA-Q3-2025_20260109/
├── source/
│   ├── content.md            # 解析的文档
│   ├── metadata.json         # 元数据
│   └── images/               # 图片
├── 01_analysis.json          # 文档分析
├── 02_research.json          # 补充研究
├── report.md                 # 最终报告
└── report_metadata.json      # 报告元数据
```

## Commands

```bash
# 安装依赖
uv sync

# 运行完整流水线
uv run python scripts/run_pipeline.py --mode full

# 无外部研究（更快）
uv run python scripts/run_pipeline.py --mode no-research

# 最小配置（全用Gemini，最便宜）
uv run python scripts/run_pipeline.py --mode minimal

# Python API使用
from src.pipeline import ReportPipeline

pipeline = ReportPipeline(
    enable_image_analysis=True,
    enable_research=True,
    analyzer_model="gemini-2.0-flash",
    generator_model="claude-sonnet-4-5-20250929",
)
output_dir = pipeline.run("path/to/document.pdf")
```

## Rules for Claude

1. **写文档前**：必须先读 `docs/_ai-rules.md`
2. **新建功能**：**必须**使用 `./docs/_scripts/new.sh feat <name>`
3. **工具开发**：
   - 继承 `src/tools/base.py` 的 Tool 基类
   - 在对应 category 目录下实现
   - 自动注册机制，无需手动添加
4. **数据模型**：
   - 使用 `src/models/report.py` 中的 Pydantic 模型
   - 所有中间结果和最终报告都使用标准化模型
5. **引用追踪**：所有外部数据必须携带来源信息
   - 使用 Markdown 脚注格式：`[^ref-id]`
   - 引用定义：`[^ref-id]: [说明](位置)`

## Key Design Principles

1. **简单优于复杂**：线性流水线替代复杂的Agent编排
2. **利用长上下文**：Gemini 2.0 Flash支持100万tokens，无需RAG
3. **成本优化**：分析用Gemini（便宜），生成用Claude（质量高）
4. **可追溯性**：每步输出独立JSON，便于调试和回溯
5. **并行优化**：Research阶段使用asyncio并行查询

## Task State

长期任务使用 Feature-centric 文档体系：
- `docs/features/<name>/spec.md` - 功能规格（稳定）
- `docs/features/<name>/state.md` - 进度跟踪（临时）

重大决策同步到 `docs/decisions/*.adr.md`
