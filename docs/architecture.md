# DeepFinance 流程架构

## 核心原则

- **简单优于复杂**：线性流水线替代6-Agent编排
- **利用长上下文**：Gemini 2.5 支持1M tokens，全文档分析无需RAG
- **完整总结优先**：8章节详细总结（25指标+30洞察）替代稀疏要点
- **结构化研究需求**：4维度补充研究（时效性+对比+深度+市场观点）
- **成本优化**：全流程使用Gemini Flash Lite（~$0.02/报告）
- **完全追溯**：每步输出独立JSON，引用链精确到页面/表格

## 流程架构

```
PDF文档 → [1.解析] → [2.分析] → [2.5.研究]* → [3.生成] → Markdown报告
          75.7秒       54.3秒        可选         20.2秒
           ↓            ↓             ↓             ↓
        source/    01_analysis.json  02_research.json  report.md
     (content.md   (8章节+25指标    (补充数据)      (完整报告)
      +17图片)     +4维度需求)
```

*研究阶段可选，minimal模式下关闭以加速验证

## 三步流水线

### 1. PDF解析 (DoclingParser)

**输入**: PDF文档
**处理**:
- Docling提取文本+表格+图片
- Claude Vision批量分析图片（可选）
  - 阶段1: 分类（chart/illustration/icon）
  - 阶段2: 内容描述（图表分析/插图描述）
- 生成Markdown + metadata.json

**输出**: `source/{doc_name}/`
- `content.md` - 完整文档内容
- `metadata.json` - 图表列表+描述
- `images/` - 提取的图片文件

---

### 2. 文档分析 (DocumentAnalyzer)

**输入**: source目录（content.md + metadata.json）
**处理**:
- Gemini 2.5 Flash Lite 读取完整文档（~60K字符）
- 输出结构化JSON（完整总结+补充研究需求）

**输出**: `01_analysis.json`
```json
{
  "analysis_id": "source_20260109_113358",
  "document_metadata": {
    "document_type": "earnings_report",
    "company": "Tesla",
    "period": "Q3 2025",
    "publish_date": "2025-10-22",
    "key_topics": ["财务摘要", "运营摘要", "产品发布", ...]
  },
  "content_summary": [  // 8个章节，完整文档总结
    {
      "section_id": "financial_summary",
      "section_title": "Financial Summary (财务摘要)",
      "content": "Q3-2025 总收入为 $28,095M，同比增长 12%...",  // 详细叙述
      "key_metrics": [  // 6个指标（本章节）
        {
          "metric": "总收入",
          "current_value": "$28,095M (Q3-2025)",
          "previous_value": "$25,182M (Q3-2024)",  // 历史对比
          "change": "+12% YoY",                     // 变化幅度
          "context": "总收入",                       // 上下文
          "source": "page-5#table-2"                 // 精确引用
        }
      ],
      "insights": [  // 4条洞察（本章节）
        "尽管总收入创下新高，但营业收入和利润率大幅下降..."
      ],
      "citations": [{"id": "doc-p5", "location": "page-5"}]
    }
    // ... 共8个章节
  ],
  "key_takeaways": [  // 6个关键要点
    {
      "id": "KT-001",
      "category": "positive",
      "statement": "特斯拉Q3实现了创纪录的收入和自由现金流...",
      "evidence": "总收入 $28.1B (+12% YoY)...",
      "significance": "证明了公司在宏观不确定性下仍能实现增长",
      "sources": [{"id": "source", "location": "page-5"}]
    }
  ],
  "supplementary_research_needs": {  // 4个维度的补充研究需求
    "temporal_updates": [  // 时效性补充
      {
        "id": "temporal-001",
        "topic": "Q4 2025 生产和交付指引",
        "reason": "Q3 产量略低于交付量，需要了解Q4进展",
        "search_queries": [
          "Tesla Q4 2025 production guidance update",
          "Tesla Q4 2025 delivery forecast"
        ],
        "priority": "high"
      }
    ],
    "comparative_data": [  // 对比信息
      {
        "id": "compare-001",
        "comparison_type": "competitors",
        "metric": "平均每车成本",
        "reason": "需要与比亚迪等竞争对手对比成本结构变化",
        "search_queries": [
          "EV industry average cost per vehicle Q3 2025",
          "Tesla cost per vehicle vs competitors 2025"
        ]
      }
    ],
    "deep_dive_analysis": [  // 深度分析
      {
        "id": "deep-001",
        "topic": "AI/软件盈利能力",
        "question": "Robotaxi在Q3的具体收入贡献是多少？",
        "reason": "当前财报中该业务的独立盈利数据不清晰",
        "search_queries": ["Tesla software revenue Q3 2025 breakdown"]
      }
    ],
    "market_perspectives": [  // 市场观点
      {
        "id": "market-001",
        "topic": "分析师对利润率下降的看法",
        "perspective_type": "analyst_ratings",
        "search_queries": [
          "Analyst reaction to Tesla Q3 2025 margin compression"
        ]
      }
    ]
  },
  "charts_analysis": [...]  // 17个图表分析
}
```

**质量指标**（TSLA Q3 2025 测试）:
- **8个章节**：Highlights、财务、运营、汽车、技术、能源、展望、报表
- **25个指标**：每个都有 前值+后值+变化+上下文+来源
- **30条洞察**：分布在8个章节中
- **5个研究需求**：分4个维度，共13个可执行查询
- **支持问答**：完整上下文保留，信息密度提升 60%~400%

---

### 2.5. 外部研究 (DataResearcher) *可选

**输入**: supplementary_research_needs（4个维度）
**处理**:
- 从4个维度收集所有search_queries（如13个）
- Tavily并行搜索（最大并发10，Semaphore控制）
- 按need_id聚合结果

**输出**: `02_research.json`
```json
{
  "research_id": "research_20260109_113400",
  "related_analysis": "source_20260109_113358",
  "queries": [
    {
      "query_id": "temporal-001-query-0",
      "query_text": "Tesla Q4 2025 production guidance update",
      "source_gap": "temporal-001",
      "results": [
        {
          "source": "web_search",
          "title": "Tesla Q4 2025 Production Outlook...",
          "url": "https://...",
          "content": "...",
          "relevance_score": 0.95
        }
      ]
    }
  ],
  "summary_by_gap": {
    "temporal-001": {
      "answered": true,
      "confidence": "high",
      "key_findings": ["标题1", "标题2", ...],
      "sources_count": 8,
      "queries_count": 3
    }
  }
}
```

---

### 3. 报告生成 (ReportGenerator)

**输入**:
- `01_analysis.json` - 文档分析
- `02_research.json` - 外部研究（可选）

**处理**:
- Gemini/Claude整合所有数据
- 生成Markdown报告

**输出**:
- `report.md` - 最终报告（带引用）
- `report_metadata.json` - 元数据

**报告结构**:
```markdown
## 执行摘要
## 核心发现
### 1. 发现标题
数据支撑: xxx[^doc-p5]
对比分析: xxx[^gap-001-2]
图表分析: xxx[^p10_fig_004.png]

## 行业对比
## 风险与挑战
## 投资建议

## 引用来源
### 原始文档
- [doc-p5]: page-5#表-2
### 图表分析
- [p10_fig_004.png]: 图表文件
### 外部数据
- [gap-001-2]: 标题 (URL)
```

## 引用体系

| 类型 | 格式 | 示例 | 来源 |
|-----|------|------|------|
| **文档引用** | `[^doc-p{N}]` | `[^doc-p5]` | 原PDF第5页 |
| **图表引用** | `[^{filename}]` | `[^p10_fig_004.png]` | 提取的图片 |
| **搜索引用** | `[^gap-{N}-{M}]` | `[^gap-001-2]` | 外部搜索结果 |

## 提示词管理 (`src/prompts/`)

所有LLM提示词解耦到独立文件，便于维护和优化。

### 提示词列表

| 文件 | 用途 | 调用位置 |
|-----|------|---------|
| `document_analysis.txt` | 文档分析 | `DocumentAnalyzer._build_analysis_prompt()` |
| `report_generation.txt` | 报告生成 | `ReportGenerator._build_report_prompt()` |

### 使用方式

```python
from src.prompts import get_document_analysis_prompt

prompt = get_document_analysis_prompt(
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)
```

### 修改提示词

1. 编辑 `src/prompts/analysis/*.txt` 或 `src/prompts/generation/*.txt`
2. 使用 `{变量名}` 标记动态内容
3. 测试验证: `uv run python scripts/run_pipeline.py --mode minimal`

## 关键组件

### DoclingParser (`src/tools/parser/`)
- PDF解析（Docling）
- 图片分析（Claude Vision，可选）
- Markdown生成

### DocumentAnalyzer (`src/analyzers/document_analyzer.py`)
- LLM: CloseAI Gemini 2.5 Flash Lite
- 输出: 结构化JSON（5发现+4缺口）

### DataResearcher (`src/analyzers/data_researcher.py`)
- 搜索引擎: Tavily
- 并发控制: Semaphore(10)
- 异步执行: asyncio.gather

### ReportGenerator (`src/analyzers/report_generator.py`)
- LLM: CloseAI Gemini / Claude Sonnet
- 输出: Markdown报告

### ReportPipeline (`src/pipeline/report_pipeline.py`)
- 编排器，顺序调用4个组件
- 保存中间结果（JSON）
- 记录pipeline metadata

## 配置选项

```python
pipeline = ReportPipeline(
    output_base="outputs/",
    enable_image_analysis=True,      # 图片分析（需Claude）
    enable_research=True,            # 外部搜索（需Tavily）
    analyzer_model="gemini-2.5-flash-lite-preview-09-2025",
    generator_model="gemini-2.5-flash-lite-preview-09-2025",
    search_engine="tavily",
)
```

### 三种模式

| 模式 | 图片分析 | 外部研究 | 用途 | 耗时 |
|-----|---------|---------|------|------|
| **minimal** | ❌ | ❌ | 快速验证 | ~115秒 |
| **no-research** | ✅ | ❌ | 仅文档分析 | ~150秒 |
| **full** | ✅ | ✅ | 完整报告 | ~200秒 |

## 数据模型 (`src/models/report.py`)

所有数据结构使用Pydantic，支持：
- 类型验证
- JSON序列化（`model_dump(mode='json')`）
- 自动文档生成

### 核心模型（新版）

#### 1. 文档分析相关
```python
# 文档元信息
DocumentMetadata(
    document_type: str,           # 文档类型
    company: str,                  # 公司名称
    period: str,                   # 报告期间
    publish_date: str | None,      # 发布日期
    key_topics: list[str]          # 关键主题
)

# 关键指标（5字段完整结构）
KeyMetric(
    metric: str,                   # 指标名称
    current_value: str,            # 当前值
    previous_value: str | None,    # 历史值（新增）
    change: str | None,            # 变化幅度（新增）
    context: str | None,           # 上下文说明（新增）
    source: str                    # 引用来源
)

# 内容章节（完整总结，非稀疏要点）
ContentSection(
    section_id: str,               # 章节ID
    section_title: str,            # 章节标题
    content: str,                  # 详细叙述性总结
    key_metrics: list[KeyMetric],  # 本章节指标
    insights: list[str],           # 关键洞察
    citations: list[dict]          # 引用来源
)

# 关键要点（高层总结）
KeyTakeaway(
    id: str,
    category: str,                 # positive/negative/neutral
    statement: str,                # 要点陈述
    evidence: str,                 # 证据支撑
    significance: str,             # 重要性说明
    sources: list[dict]            # 引用来源
)
```

#### 2. 补充研究需求（4个维度）
```python
# 时效性补充
TemporalUpdate(
    id: str,
    topic: str,                    # 主题
    reason: str,                   # 为什么需要更新
    search_queries: list[str],     # 搜索查询列表
    priority: str                  # high/medium/low
)

# 对比信息
ComparativeData(
    id: str,
    comparison_type: str,          # industry_average/competitors/historical
    metric: str,                   # 需要对比的指标
    reason: str,                   # 对比原因
    search_queries: list[str]
)

# 深度分析
DeepDiveAnalysis(
    id: str,
    topic: str,                    # 深入主题
    question: str,                 # 具体问题
    reason: str,                   # 为什么需要深入
    search_queries: list[str]
)

# 市场观点
MarketPerspective(
    id: str,
    topic: str,                    # 关注主题
    perspective_type: str,         # analyst_ratings/institutional_views
    search_queries: list[str]
)

# 补充研究需求（4维度聚合）
SupplementaryResearchNeeds(
    temporal_updates: list[TemporalUpdate],
    comparative_data: list[ComparativeData],
    deep_dive_analysis: list[DeepDiveAnalysis],
    market_perspectives: list[MarketPerspective]
)
```

#### 3. 分析结果
```python
AnalysisResult(
    analysis_id: str,
    source_document: dict,         # 源文档信息
    document_metadata: DocumentMetadata,
    content_summary: list[ContentSection],      # 8章节完整总结
    key_takeaways: list[KeyTakeaway],           # 6个关键要点
    supplementary_research_needs: SupplementaryResearchNeeds,  # 4维度需求
    charts_analysis: list[ChartAnalysis]
)
```

#### 4. 其他模型
- `Citation` - 引用信息
- `ChartAnalysis` - 图表分析
- `SearchResult` - 搜索结果
- `QueryResult` - 查询结果
- `ResearchResult` - 研究结果
- `ReportMetadata` - 报告元数据

## API Provider

当前支持:
- **CloseAI** (推荐): Gemini系列，稳定可用
- **API易**: Claude系列，部分模型可用
- **云雾AI**: 备选

配置通过环境变量:
```bash
CLOSEAI_API_KEY=sk-...
CLOSEAI_GOOGLE_BASE_URL=https://api.openai-proxy.org/google
```

## 性能指标（实测数据）

### TSLA Q3 2025 测试（minimal模式，无图片分析，无外部研究）
- **总耗时**: 150.3秒
  - 解析阶段: 75.7秒（Docling解析PDF，17张图片提取）
  - 分析阶段: 54.3秒（Gemini 2.5 Flash Lite，59K字符）
  - 生成阶段: 20.2秒（Gemini 2.5 Flash Lite）
- **成本**: ~$0.015（全Gemini Flash Lite，无图片分析）

### TSLA Q3 2025 测试（full模式，含图片+研究）
- **预估总耗时**: ~200秒
  - 解析阶段: ~150秒（含17张图片的Claude Vision分析）
  - 分析阶段: ~54秒
  - 研究阶段: ~10秒（13个查询，Tavily并行）
  - 生成阶段: ~20秒
- **预估成本**: ~$0.10（含Claude Vision图片分析 + Tavily搜索）

## 质量指标（新架构）

### 信息密度
- **章节数**: 8个（vs 旧版 3-5 核心发现）→ **+60%~167%**
- **指标总数**: 25个，每个5字段（vs 旧版 5-10个，1-2字段）→ **+150%~400%**
- **洞察总数**: 30条（vs 旧版 10-15条）→ **+100%~200%**
- **内容字符数**: 3,492字详细叙述（vs 旧版稀疏要点）→ **完整上下文**

### 研究需求结构化
- **旧版**: 模糊的"信息缺口"，无明确定义
- **新版**: 4个维度（时效性+对比+深度+市场观点），每个都有明确的 `reason` + `search_queries`
- **可执行性**: 100%（13个可执行查询，vs 旧版模糊问题）

### 支持问答能力
- **完整上下文保留**: ✅（8章节+25指标+30洞察）
- **精确引用**: ✅（所有数据都有 page-X#table-Y 级别引用）
- **历史对比**: ✅（指标都有 前值+后值+变化+上下文）

### 报告质量
- **引用覆盖率**: 100%（所有观点都有脚注引用）
- **报告结构**: 执行摘要+4核心发现+行业对比+风险分析+投资建议
- **引用类型**: 3类（文档+图表+外部）
- **可溯源性**: 完整（每个数据点都能追溯到源文档页面）

## 架构改进对比（旧版 vs 新版）

| 维度 | 旧版架构 | 新版架构 | 改进效果 |
|------|---------|---------|----------|
| **输出结构** | 3-5 个"核心发现" | 8 个完整章节（详细叙述） | +60%~167% 信息密度 |
| **指标详细度** | 仅当前值 | 前值+后值+变化+上下文+来源（5字段） | +250% 上下文信息 |
| **总指标数** | 5-10 个 | **25 个** | +150%~400% |
| **洞察数** | 10-15 条 | **30 条** | +100%~200% |
| **研究需求定义** | 模糊的"信息缺口" | 4 维度结构化（时效性+对比+深度+市场观点） | 100% 可执行 |
| **支持问答** | ❌ 信息过于稀疏 | ✅ 完整上下文保留 | 可直接回答细节问题 |
| **引用精确度** | 页面级别 | 页面+表格级别（如 page-5#table-2） | 更精确定位 |

### 核心设计改进

1. **完整总结优先**
   - **旧版**: 提取 3-5 个"核心发现"（要点式）
   - **新版**: 生成 8 个章节的完整叙述性总结
   - **收益**: 信息不丢失，支持后续问答

2. **指标结构化增强**
   - **旧版**: `KeyMetric(metric, current_value, source)`
   - **新版**: `KeyMetric(metric, current_value, previous_value, change, context, source)`
   - **收益**: 历史对比一目了然，上下文清晰

3. **研究需求精确化**
   - **旧版**: `InformationGap(question, search_queries)` - 定义模糊
   - **新版**: 4 个维度，每个都有明确的 `reason` 字段说明为什么需要
     - `TemporalUpdate` - 时效性补充（如"文档发布3个月前，需要最新进展"）
     - `ComparativeData` - 对比信息（如"需要与比亚迪对比成本结构"）
     - `DeepDiveAnalysis` - 深度分析（如"Robotaxi收入贡献不清晰"）
     - `MarketPerspective` - 市场观点（如"分析师对利润率下降的看法"）
   - **收益**: 研究目标明确，搜索可执行

4. **数据规范化**
   - **问题**: LLM 输出不稳定（字符串 vs 列表 vs 字典）
   - **解决**: 增加 `_normalize_key_takeaway()` 和 `_normalize_chart_analysis()` 标准化函数
   - **收益**: Pydantic 验证通过率 100%
