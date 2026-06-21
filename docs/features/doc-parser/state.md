# State: doc-parser

**Updated**: 2025-12-26

## Why

Parse financial PDF documents into structured Markdown + images format, preserving page number information for traceability, to provide high-quality text input for subsequent research and report generation.

## Status

- Core functionality implemented, including PDF → Markdown + images conversion
- Supports page number markers, table extraction, and image saving
- Outputs metadata.json with meta information

## Tasks

### Done

- [x] Create base.py - Tool base class and ToolResult
- [x] Implement docling_parser.py - Parse PDF using Docling
- [x] Create module export __init__.py

### Pending

- [ ] Add unit tests
- [ ] Support batch parsing progress callbacks
- [ ] Add optional OCR support

## Decisions

1. **Use Docling as PDF parser**: Docling provides high-quality PDF parsing capabilities, supporting table structure recognition and image extraction
   - Related ADR: None

2. **Page number marker format**: Use HTML comment `<!-- page: N -->` format, which does not affect Markdown rendering and is easy to parse

3. **Image naming convention**: Use `p{page}_fig_{num}.png` format for easy traceability of image source pages

## Risks

- Docling may not parse complex tables perfectly
- Some scanned PDFs require OCR support (currently not enabled)

## Known Issues & Workarounds

- Issue: Docling image extraction may return data URI instead of PIL Image
  - Workaround: Support base64 decoding for saving
