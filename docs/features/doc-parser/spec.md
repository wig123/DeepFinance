# doc-parser

PDF 文档解析模块，使用 Docling 提取结构化内容。

## Goal

- 将金融 PDF（含图表、表格）解析为 Markdown + 图片
- 保留页码信息用于溯源
- 提取图表标题/说明文字

## Inputs / Outputs

**Inputs**: PDF 文件路径或目录

**Outputs**:
```
output/<doc_name>/
├── content.md          # 主文档（含页码标记）
├── images/
│   └── p3_fig_001.png  # 第3页图片
└── metadata.json       # 元信息
```

## Acceptance Criteria

- [ ] PDF → md + 图片
- [ ] 保留页码：`<!-- page: 3 -->`
- [ ] 提取图表标题
- [ ] 输出 metadata.json
- [ ] 表格转 Markdown 格式

## Constraints

- 单文档 ≤100 页
- 图片保留原始分辨率

## Non-goals

- OCR 手写内容
- 多语言混排

## Links

- `src/tools/parser/docling_parser.py`
