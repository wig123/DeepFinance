# doc-parser

PDF document parsing module that uses Docling to extract structured content.

## Goal

- Parse financial PDFs (including charts and tables) into Markdown + images
- Preserve page number information for traceability
- Extract chart titles/captions

## Inputs / Outputs

**Inputs**: PDF file path or directory

**Outputs**:
```
output/<doc_name>/
├── content.md          # Main document (with page markers)
├── images/
│   └── p3_fig_001.png  # Image from page 3
└── metadata.json       # Metadata
```

## Acceptance Criteria

- [ ] PDF → md + images
- [ ] Preserve page numbers: `<!-- page: 3 -->`
- [ ] Extract chart titles
- [ ] Output metadata.json
- [ ] Convert tables to Markdown format

## Constraints

- Single document ≤100 pages
- Preserve original image resolution

## Non-goals

- OCR handwritten content
- Mixed multilingual layout

## Links

- `src/tools/parser/docling_parser.py`
