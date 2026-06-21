# PDF Parsing Optimization In-Depth Research Report

## Current Status

| Sub-stage | Time | Percentage | Tech Stack |
|--------|------|------|--------|
| Docling Parsing | 21s | 32% | TableFormer ACCURATE + MPS |
| Image Analysis | 42.5s | 65% | Claude Vision (Serial) |
| Other Processing | 2s | 3% | bbox extraction, Markdown generation |
| **Total** | **65.5s** | 100% | |

---

## Optimization Direction 1: Docling Configuration Optimization

### 1.1 TableFormer Mode Switching

```python
# Current: ACCURATE mode
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# Optimized: FAST mode
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

| Mode | L4 GPU | M3 Max (MPS) | x86 CPU |
|------|--------|--------------|---------|
| FAST | 400ms/table | 704ms/table | 1.74s/table |
| ACCURATE | ~2x FAST | ~2x FAST | ~2x FAST |

**Expected Gain**: 40-50% reduction in table processing time

### 1.2 Batch Size Tuning

```python
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

pipeline_options = ThreadedPdfPipelineOptions(
    ocr_batch_size=64,      # Default 4 → 64
    layout_batch_size=64,   # Default 4 → 64
    table_batch_size=4,     # Currently does not support GPU batching
)
```

**Expected Gain**: Improved GPU utilization, 20-30% overall speedup

### 1.3 Explicit Accelerator Configuration

```python
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

accelerator_options = AcceleratorOptions(
    num_threads=8,                    # Increase CPU threads
    device=AcceleratorDevice.MPS,     # Explicitly specify MPS
)
```

---

## Optimization Direction 2: Parser Replacement

### 2.1 Parser Performance Comparison (2025 Benchmark)

| Parser | Speed | Table Accuracy | GPU Support | Features |
|--------|------|----------|----------|------|
| **pypdfium2** | 0.003s ⚡ | None | ❌ | Pure text extraction, extremely fast |
| **PyMuPDF4LLM** | 0.12s ⚡ | Poor | ❌ | Fast, poor table handling |
| **MinerU** | 0.21s/page | Excellent | ✅ CUDA | 4x faster than Marker |
| **Marker** | 0.86s/page | Excellent | ✅ CUDA/MPS | High structural fidelity |
| **Docling** | 4s/page | 97.9% | ✅ CUDA/MPS | Best table accuracy |

### 2.2 Recommended Replacement Solutions

#### Solution A: Hybrid Strategy (Speed + Quality)

```python
# Simple documents → PyMuPDF4LLM (0.12s)
# Complex tables → Docling (4s)

def smart_parse(pdf_path):
    # Quick pre-detection
    if has_complex_tables(pdf_path):
        return docling_parse(pdf_path)
    else:
        return pymupdf4llm_parse(pdf_path)
```

#### Solution B: MinerU Replacement

```bash
pip install magic-pdf
```

```python
from magic_pdf.data.data_reader_writer import FileBasedDataReader
from magic_pdf.pipe.UNIPipe import UNIPipe

# MinerU configuration
reader = FileBasedDataReader("")
pipe = UNIPipe(pdf_bytes, model_list=[])
pipe.pipe_parse()
md_content = pipe.pipe_mk_markdown()
```

**Advantages**:
- Speed: 0.21s/page (vs Docling 4s/page) = **19x speedup**
- Tables: Complex tables rendered as HTML
- Multilingual: Supports OCR for 109 languages

---

## Optimization Direction 3: Image Analysis Optimization

### 3.1 Batch Asynchronous Processing (Implemented but Not Enabled)

Current code has `analyze_images_batch` but may not be fully utilized:

```python
# Current: Possibly serial
for img_path in image_paths:
    result = analyze_image(img_path)

# Optimized: Parallel batch processing
import asyncio

async def batch_analyze(image_paths, batch_size=5):
    batches = [image_paths[i:i+batch_size] for i in range(0, len(image_paths), batch_size)]
    results = []
    for batch in batches:
        tasks = [analyze_image_async(img) for img in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
    return results
```

**Expected Gain**: 17 images from 42.5s → 10-12s (3-4 parallel batches)

### 3.2 Image Classification Pre-filtering

```python
def should_analyze(image_path: Path) -> bool:
    """Quickly determine if deep analysis is needed"""
    from PIL import Image
    img = Image.open(image_path)

    # Skip images that are too small (possibly icons)
    if img.width < 100 or img.height < 100:
        return False

    # Skip solid color/simple images
    colors = img.getcolors(maxcolors=100)
    if colors and len(colors) < 10:
        return False

    return True
```

**Expected Gain**: 30-50% reduction in unnecessary API calls

### 3.3 Local Vision Model Alternative

```python
# Local alternative to Claude Vision
# 1. LLaVA-1.6 (7B)
# 2. Qwen2-VL (7B)
# 3. InternVL2 (8B)

# Example: Using Ollama + LLaVA
import ollama

response = ollama.generate(
    model='llava:7b',
    prompt='Analyze this financial chart...',
    images=[image_path]
)
```

**Advantages**:
- No API call latency
- No cost
- Batch processing capable

**Disadvantages**:
- Requires GPU memory (7B model ~14GB VRAM)
- Quality may be slightly lower than Claude Vision

---

## Optimization Direction 4: Architecture-Level Optimization

### 4.1 Incremental Parsing + Caching

```python
import hashlib
from diskcache import Cache

cache = Cache('.cache/pdf_parse')

def cached_parse(pdf_path: Path):
    # Calculate file hash
    file_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()

    # Check cache
    if file_hash in cache:
        return cache[file_hash]

    # Parse and cache
    result = docling_parse(pdf_path)
    cache[file_hash] = result
    return result
```

### 4.2 Pipeline Parallelization

```
Current: Serial
PDF → [Parsing 21s] → [Image Analysis 42.5s] → Complete

Optimized: Parallel
PDF → [Parsing 21s] ─────────────────────→ Merge
         └──→ [Image Analysis 42.5s] ────────┘

# Image analysis can start immediately after the first image is parsed
```

### 4.3 Warmup + Model Persistence

```python
# Warm up models at startup
class DoclingParserPool:
    def __init__(self, pool_size=2):
        self.converters = [
            self._create_converter()
            for _ in range(pool_size)
        ]

    def _create_converter(self):
        # Preload models into memory/GPU
        return DocumentConverter(...)

    def parse(self, pdf_path):
        # Get available converter from pool
        converter = self.get_available()
        return converter.convert(pdf_path)
```

---

## Optimization Solution Comparison

| Optimization Solution | Implementation Complexity | Expected Gain | Risk |
|----------|------------|----------|------|
| TableFormer FAST | ⭐ Low | 20-30% | Slight table accuracy reduction |
| Batch Size Tuning | ⭐ Low | 10-20% | Requires more memory |
| Parallel Image Analysis | ⭐⭐ Medium | 30-40% | API rate limiting |
| Image Pre-filtering | ⭐ Low | 10-20% | May miss important images |
| MinerU Replacement | ⭐⭐⭐ High | 60-70% | Requires parser refactoring |
| Local Vision Model | ⭐⭐⭐ High | 50-60% | Requires GPU resources |
| Caching Mechanism | ⭐⭐ Medium | No gain on first run, 90%+ on repeat | Cache invalidation |

---

## Recommended Implementation Path

### Phase 1: Quick Optimization (1-2 hours)
1. ✅ Switch TableFormer to FAST mode
2. ✅ Increase batch_size to 32-64
3. ✅ Image pre-filtering (skip small icons)

**Expected**: 65.5s → 45s (-30%)

### Phase 2: Medium Optimization (1-2 days)
1. Parallelize image analysis
2. Hybrid parser strategy (use PyMuPDF for simple documents)
3. Add parsing result caching

**Expected**: 45s → 25s (-45%)

### Phase 3: Deep Optimization (1-2 weeks)
1. Replace Docling with MinerU (for complex table scenarios)
2. Replace Claude Vision with local vision model
3. Refactor pipeline to streaming processing

**Expected**: 25s → 10-15s (-60%)

---

## References

- [Docling GPU Documentation](https://docling-project.github.io/docling/usage/gpu/)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [Marker GitHub](https://github.com/datalab-to/marker)
- [PDF Parsing Benchmark Paper](https://arxiv.org/html/2410.09871v1)
- [OmniDocBench 2025](https://github.com/opendatalab/OmniDocBench)
