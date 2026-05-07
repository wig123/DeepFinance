# writer

撰稿人 Agent，生成带引用的报告，可动态调用 Researcher 补充数据。

## Goal

- 基于研究数据生成报告草稿
- 确保所有数据点有引用
- 发现数据不足时调用 Researcher 补充

## Inputs / Outputs

**Inputs**: 研究大纲、研究数据、源文档

**Outputs**:
```python
{
    "draft": "# 报告标题\n...",
    "sources": ["[^1]: ...", "[^2]: ..."],
    "data_gaps": []  # 或需要补充的数据
}
```

## Acceptance Criteria

- [ ] 生成带引用的报告
- [ ] 可调用 Researcher 补充数据（动态回溯）
- [ ] 输出日志可查看
- [ ] 集成测试通过

## Callback Mechanism

```
写作中发现数据不足 → 调用 Researcher → 获取补充数据 → 继续写作
```

## Citation Format

```markdown
根据 Tesla Q3 2025 财报[^1]，营收达到...

[^1]: Tesla Q3 2025 Update, https://ir.tesla.com/...
```

## Constraints

- 禁止生成无来源的数据点
- 引用格式统一

## Non-goals

- 格式排版（由 Publisher 处理）

## Links

- `src/agents/writer.py`
