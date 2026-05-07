# State: doc-parser

**Updated**: 2025-12-26

## Why

将金融 PDF 文档解析为结构化的 Markdown + 图片格式，保留页码信息用于溯源，为后续的研究和报告生成提供高质量的文本输入。

## Status

- 核心功能已实现，包括 PDF → Markdown + 图片转换
- 支持页码标记、表格提取、图片保存
- 输出 metadata.json 元信息

## Tasks

### Done

- [x] 创建 base.py - Tool 基类和 ToolResult
- [x] 实现 docling_parser.py - 使用 Docling 解析 PDF
- [x] 创建模块导出 __init__.py

### Pending

- [ ] 添加单元测试
- [ ] 支持批量解析进度回调
- [ ] 添加 OCR 可选支持

## Decisions

1. **使用 Docling 作为 PDF 解析器**: Docling 提供了高质量的 PDF 解析能力，支持表格结构识别和图片提取
   - 相关 ADR: 无

2. **页码标记格式**: 使用 HTML 注释 `<!-- page: N -->` 格式，不影响 Markdown 渲染且易于解析

3. **图片命名规范**: 使用 `p{page}_fig_{num}.png` 格式，便于追溯图片来源页

## Risks

- Docling 对复杂表格的解析可能不完美
- 部分扫描版 PDF 需要 OCR 支持（当前未启用）

## Known Issues & Workarounds

- Issue: Docling 图片提取可能返回 data URI 而非 PIL Image
  - Workaround: 支持 base64 解码保存
