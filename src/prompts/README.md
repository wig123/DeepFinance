# 提示词管理

所有LLM提示词统一存放在此目录，便于维护、版本控制和优化。

## 文件列表

| 文件 | 用途 | 使用位置 |
|-----|------|---------|
| `document_analysis.txt` | 文档分析提示词 | `DocumentAnalyzer` |
| `report_generation.txt` | 报告生成提示词 | `ReportGenerator` |

## 使用方式

### 1. 加载提示词

```python
from src.prompts import get_document_analysis_prompt

# 方式1: 使用便捷函数
prompt = get_document_analysis_prompt(
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)

# 方式2: 通用加载器
from src.prompts import format_prompt

prompt = format_prompt(
    "document_analysis",
    pages=42,
    figures_count=17,
    figures_summary="...",
    content="...",
)
```

### 2. 模板语法

使用Python的`str.format()`语法：

```txt
你是一位{role}。

文档信息:
- 页数: {pages}
- 内容: {content}
```

变量使用`{变量名}`标记，调用时传入对应参数。

## 修改提示词

### 原则

1. **保持结构化输出** - 不要改变JSON输出格式要求
2. **保留关键指令** - 如"只返回JSON"、"标注引用"等
3. **测试验证** - 修改后运行测试确保正常工作

### 流程

1. 编辑对应的`.txt`文件
2. 运行测试验证:
   ```bash
   uv run python test_pipeline.py --mode minimal
   ```
3. 检查生成的JSON结构是否正确

## 添加新提示词

1. 创建新文件: `src/prompts/your_prompt.txt`
2. 在`__init__.py`中添加便捷函数:
   ```python
   def get_your_prompt(**kwargs) -> str:
       return format_prompt("your_prompt", **kwargs)
   ```
3. 在代码中导入使用:
   ```python
   from src.prompts import get_your_prompt
   prompt = get_your_prompt(param1="...", param2="...")
   ```

## 提示词设计要点

### 文档分析提示词

**核心输出**:
- `executive_summary` - 执行摘要
- `key_findings` - 核心发现（必须带引用）
- `information_gaps` - 信息缺口（生成search_queries）
- `charts_analysis` - 图表分析汇总

**关键要求**:
1. 所有发现必须标注引用位置
2. 信息缺口要生成**3-5个具体的搜索query**
3. 只返回JSON，无其他说明

### 报告生成提示词

**核心输出**: 完整的Markdown研究报告

**结构要求**:
- 执行摘要
- 核心发现（带引用）
- 行业对比
- 风险与挑战
- 投资建议
- 引用来源

**关键要求**:
1. 使用Markdown脚注引用: `[^ref-id]`
2. 引用覆盖率 > 90%
3. 客观中立，数据驱动

## 版本历史

| 日期 | 文件 | 变更 |
|-----|------|------|
| 2026-01-09 | 所有 | 初始版本，从代码中解耦 |
