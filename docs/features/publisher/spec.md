# publisher

Publisher for multi-format report export.

## Goal

- Export final reports to HTML/PDF/Word
- Prioritize basic functionality, optimize styling later

## Inputs / Outputs

**Inputs**: Final report Markdown, image assets

**Outputs**:
```
outputs/<task_id>/
├── report.html
├── report.pdf
└── report.docx
```

## Acceptance Criteria

- [ ] Output HTML
- [ ] Output PDF
- [ ] Output Word
- [ ] Images correctly embedded
- [ ] Reference links clickable (HTML)

## Tech Stack

| Format | Tool |
|------|------|
| HTML | Jinja2 templates |
| PDF | WeasyPrint |
| Word | python-docx |

## Constraints

- Prioritize basic functionality
- Iterate on styling later

## Non-goals

- Complex interactive charts
- Custom templates (first version)

## Links

- `src/publisher/`
