# PDF Parsing 优化深度调研报告

## 当前状态

| 子阶段 | 耗时 | 占比 | 技术栈 |
|--------|------|------|--------|
| Docling 解析 | 21s | 32% | TableFormer ACCURATE + MPS |
| 图片分析 | 42.5s | 65% | Claude Vision (串行) |
| 其他处理 | 2s | 3% | bbox 提取、Markdown 生成 |
| **总计** | **65.5s** | 100% | |

---

## 优化方向 1: Docling 配置优化

### 1.1 TableFormer 模式切换

```python
# 当前: ACCURATE 模式
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# 优化: FAST 模式
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
```

| 模式 | L4 GPU | M3 Max (MPS) | x86 CPU |
|------|--------|--------------|---------|
| FAST | 400ms/表 | 704ms/表 | 1.74s/表 |
| ACCURATE | ~2x FAST | ~2x FAST | ~2x FAST |

**预期收益**: 表格处理时间减少 40-50%

### 1.2 批处理大小调优

```python
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

pipeline_options = ThreadedPdfPipelineOptions(
    ocr_batch_size=64,      # 默认 4 → 64
    layout_batch_size=64,   # 默认 4 → 64
    table_batch_size=4,     # 目前不支持 GPU 批处理
)
```

**预期收益**: GPU 利用率提升，整体提速 20-30%

### 1.3 加速器显式配置

```python
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

accelerator_options = AcceleratorOptions(
    num_threads=8,                    # 增加 CPU 线程
    device=AcceleratorDevice.MPS,     # 显式指定 MPS
)
```

---

## 优化方向 2: 替换解析器

### 2.1 解析器性能对比 (2025 Benchmark)

| 解析器 | 速度 | 表格精度 | GPU 支持 | 特点 |
|--------|------|----------|----------|------|
| **pypdfium2** | 0.003s ⚡ | 无 | ❌ | 纯文本提取，极快 |
| **PyMuPDF4LLM** | 0.12s ⚡ | 差 | ❌ | 速度快，表格差 |
| **MinerU** | 0.21s/页 | 优 | ✅ CUDA | 4x 快于 Marker |
| **Marker** | 0.86s/页 | 优 | ✅ CUDA/MPS | 结构保真度高 |
| **Docling** | 4s/页 | 97.9% | ✅ CUDA/MPS | 表格最准 |

### 2.2 推荐替换方案

#### 方案 A: 混合策略 (速度 + 质量)

```python
# 简单文档 → PyMuPDF4LLM (0.12s)
# 复杂表格 → Docling (4s)

def smart_parse(pdf_path):
    # 快速预检测
    if has_complex_tables(pdf_path):
        return docling_parse(pdf_path)
    else:
        return pymupdf4llm_parse(pdf_path)
```

#### 方案 B: MinerU 替换

```bash
pip install magic-pdf
```

```python
from magic_pdf.data.data_reader_writer import FileBasedDataReader
from magic_pdf.pipe.UNIPipe import UNIPipe

# MinerU 配置
reader = FileBasedDataReader("")
pipe = UNIPipe(pdf_bytes, model_list=[])
pipe.pipe_parse()
md_content = pipe.pipe_mk_markdown()
```

**优势**:
- 速度: 0.21s/页 (vs Docling 4s/页) = **19x 提速**
- 表格: 复杂表格渲染为 HTML
- 多语言: 支持 109 种语言 OCR

---

## 优化方向 3: 图片分析优化

### 3.1 批量异步处理 (已实现但未启用)

当前代码已有 `analyze_images_batch` 但可能未充分利用：

```python
# 当前: 可能串行
for img_path in image_paths:
    result = analyze_image(img_path)

# 优化: 并行批处理
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

**预期收益**: 17 张图片从 42.5s → 10-12s (3-4 批并行)

### 3.2 图片分类预筛选

```python
def should_analyze(image_path: Path) -> bool:
    """快速判断是否需要深度分析"""
    from PIL import Image
    img = Image.open(image_path)

    # 跳过太小的图片 (可能是图标)
    if img.width < 100 or img.height < 100:
        return False

    # 跳过纯色/简单图片
    colors = img.getcolors(maxcolors=100)
    if colors and len(colors) < 10:
        return False

    return True
```

**预期收益**: 减少 30-50% 无效 API 调用

### 3.3 本地视觉模型替代

```python
# 替代 Claude Vision 的本地方案
# 1. LLaVA-1.6 (7B)
# 2. Qwen2-VL (7B)
# 3. InternVL2 (8B)

# 示例: 使用 Ollama + LLaVA
import ollama

response = ollama.generate(
    model='llava:7b',
    prompt='Analyze this financial chart...',
    images=[image_path]
)
```

**优势**:
- 无 API 调用延迟
- 无成本
- 可批量处理

**劣势**:
- 需要 GPU 内存 (7B 模型约 14GB VRAM)
- 质量可能略低于 Claude Vision

---

## 优化方向 4: 架构级优化

### 4.1 增量解析 + 缓存

```python
import hashlib
from diskcache import Cache

cache = Cache('.cache/pdf_parse')

def cached_parse(pdf_path: Path):
    # 计算文件哈希
    file_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()

    # 检查缓存
    if file_hash in cache:
        return cache[file_hash]

    # 解析并缓存
    result = docling_parse(pdf_path)
    cache[file_hash] = result
    return result
```

### 4.2 流水线并行化

```
当前: 串行
PDF → [解析 21s] → [图片分析 42.5s] → 完成

优化: 并行
PDF → [解析 21s] ─────────────────────→ 合并
         └──→ [图片分析 42.5s] ────────┘

# 图片分析可以在解析第一张图片后立即开始
```

### 4.3 预热 + 模型常驻

```python
# 启动时预热模型
class DoclingParserPool:
    def __init__(self, pool_size=2):
        self.converters = [
            self._create_converter()
            for _ in range(pool_size)
        ]

    def _create_converter(self):
        # 预加载模型到内存/GPU
        return DocumentConverter(...)

    def parse(self, pdf_path):
        # 从池中获取可用的 converter
        converter = self.get_available()
        return converter.convert(pdf_path)
```

---

## 优化方案对比

| 优化方案 | 实现复杂度 | 预期收益 | 风险 |
|----------|------------|----------|------|
| TableFormer FAST | ⭐ 低 | 20-30% | 表格精度略降 |
| 批处理大小调优 | ⭐ 低 | 10-20% | 需要更多内存 |
| 图片并行分析 | ⭐⭐ 中 | 30-40% | API 限流 |
| 图片预筛选 | ⭐ 低 | 10-20% | 可能漏掉重要图片 |
| MinerU 替换 | ⭐⭐⭐ 高 | 60-70% | 需要重构解析器 |
| 本地视觉模型 | ⭐⭐⭐ 高 | 50-60% | 需要 GPU 资源 |
| 缓存机制 | ⭐⭐ 中 | 首次无效，重复 90%+ | 缓存失效 |

---

## 推荐实施路径

### 阶段 1: 快速优化 (1-2 小时)
1. ✅ TableFormer 切换到 FAST 模式
2. ✅ 增加 batch_size 到 32-64
3. ✅ 图片预筛选 (跳过小图标)

**预期**: 65.5s → 45s (-30%)

### 阶段 2: 中等优化 (1-2 天)
1. 图片分析并行化
2. 解析器混合策略 (简单文档用 PyMuPDF)
3. 添加解析结果缓存

**预期**: 45s → 25s (-45%)

### 阶段 3: 深度优化 (1-2 周)
1. MinerU 替换 Docling (复杂表格场景)
2. 本地视觉模型替代 Claude Vision
3. 流水线重构为流式处理

**预期**: 25s → 10-15s (-60%)

---

## 参考资源

- [Docling GPU 文档](https://docling-project.github.io/docling/usage/gpu/)
- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [Marker GitHub](https://github.com/datalab-to/marker)
- [PDF 解析 Benchmark 论文](https://arxiv.org/html/2410.09871v1)
- [OmniDocBench 2025](https://github.com/opendatalab/OmniDocBench)
