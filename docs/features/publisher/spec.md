# publisher

发布者，多格式报告导出。

## Goal

- 将最终报告导出为 HTML/PDF/Word
- 基本功能优先，样式后续优化

## Inputs / Outputs

**Inputs**: 最终报告 Markdown、图片资源

**Outputs**:
```
outputs/<task_id>/
├── report.html
├── report.pdf
└── report.docx
```

## Acceptance Criteria

- [ ] 输出 HTML
- [ ] 输出 PDF
- [ ] 输出 Word
- [ ] 图片正确嵌入
- [ ] 引用链接可点击（HTML）

## Tech Stack

| 格式 | 工具 |
|------|------|
| HTML | Jinja2 模板 |
| PDF | WeasyPrint |
| Word | python-docx |

## Constraints

- 基本功能优先
- 样式后续迭代

## Non-goals

- 复杂交互式图表
- 自定义模板（第一版）

## Links

- `src/publisher/`
