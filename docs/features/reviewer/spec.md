# reviewer

审核员 Agent，审核报告质量并提供修订建议。

## Goal

- 审核报告的准确性和完整性
- 检查引用是否有效
- 输出修订建议或通过

## Inputs / Outputs

**Inputs**: Writer 生成的草稿、研究数据

**Outputs**:
```python
{
    "status": "pass" | "revise",
    "feedback": [
        {"section": "财务分析", "issue": "缺少同比数据", "suggestion": "..."}
    ]
}
```

## Acceptance Criteria

- [ ] 审核报告内容
- [ ] 输出修订建议或通过
- [ ] 中间结果可观测
- [ ] 集成测试通过

## Review Checklist

- [ ] 数据点都有引用
- [ ] 引用链接有效
- [ ] 逻辑连贯
- [ ] 无明显遗漏

## Constraints

- 必须在 Publisher 之前执行
- 审核结果结构化输出

## Non-goals

- 自动修复问题（只提建议）

## Links

- `src/agents/reviewer.py`
