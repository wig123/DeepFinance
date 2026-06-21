# MinerU GPU Acceleration Optimization Plan

## Problem Diagnosis

| Metric | Current Value | Expected Value | Gap |
|------|--------|--------|------|
| Processing Speed | 0.16 pages/sec | 1-2 pages/sec | 6-10x |
| GPU Utilization | 0-5% | 70-90% | Severely insufficient |
| 16-page PDF Time | 98s | 8-16s | 6-10x |

**Root Cause**: GPU acceleration not properly enabled or misconfigured

---

## Optimization Plan 1: Adjust OCR Batch Size

### Principle
MinerU's default `rec_batch_num` is too small, causing GPU to process only a few text blocks at a time. Increasing batch size can significantly improve GPU utilization.

### Configuration Method

Edit `~/.magic-pdf.json`:

```json
{
  "device-mode": "cuda",
  "models-dir": "/root/mineru_models",
  "rec_batch_num": 32,  // Default may be 6, increase to 32
  "det_batch_num": 8,   // Detection batch size
  "table-config": {
    "is_table_recog_enable": true,
    "max_time": 400
  }
}
```

### RTX 4090 Recommended Values
- `rec_batch_num`: 32-64 (24GB VRAM is sufficient)
- `det_batch_num`: 8-16

---

## Optimization Plan 2: VLM Backend (Vision Language Model)

### Principle
VLM backend uses vision large models with higher accuracy (90%+ vs pipeline 82%+) and is naturally suited for GPU inference.

### Configuration Method

1. **Start VLM Server**:
```bash
# Use vLLM engine (recommended)
CUDA_VISIBLE_DEVICES=0 mineru-openai-server \
    --engine vllm \
    --port 30000 \
    --model-id "Qwen/Qwen2.5-VL-7B-Instruct"
```

2. **Configure magic-pdf.json**:
```json
{
  "llm-aided-config": {
    "llm_api_type": "custom",
    "llm_api_key": "none",
    "llm_base_url": "http://localhost:30000/v1",
    "llm_models": ["Qwen2.5-VL-7B-Instruct"]
  }
}
```

3. **Parse using VLM backend**:
```bash
mineru -p test.pdf -o output/ -b vlm-auto-engine
```

### Multi-GPU Parallel
```bash
# 2 GPU parallel
CUDA_VISIBLE_DEVICES=0,5 mineru-openai-server \
    --engine vllm \
    --port 30000 \
    --data-parallel-size 2
```

---

## Optimization Plan 3: Verify PaddlePaddle GPU

### Check Script
```python
import paddle
print(f"PaddlePaddle version: {paddle.__version__}")
print(f"CUDA compiled: {paddle.device.is_compiled_with_cuda()}")
print(f"GPU count: {paddle.device.cuda.device_count()}")

# Test GPU computation
if paddle.device.is_compiled_with_cuda():
    x = paddle.randn([1000, 1000])
    paddle.device.cuda.synchronize()
    print("GPU compute test: PASSED")
```

### If PaddlePaddle is Not Using GPU

Reinstall GPU version:
```bash
pip uninstall paddlepaddle
pip install paddlepaddle-gpu==3.0.0b2 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

---

## Optimization Plan 4: Code-Level Optimization

### Modify MinerUParser to Support Batch Configuration

```python
class MinerUParser(BaseTool):
    def __init__(
        self,
        output_base: str | Path = "outputs",
        backend: str = "pipeline",
        lang: str = "en",
        enable_image_analysis: bool = False,
        image_analyzer: "ImageAnalyzer | None" = None,
        # New GPU optimization parameters
        rec_batch_num: int = 32,  # OCR batch size
        det_batch_num: int = 8,   # Detection batch size
        use_cuda: bool = True,
    ):
        # ...
        self.rec_batch_num = rec_batch_num
        self.det_batch_num = det_batch_num
        self.use_cuda = use_cuda
```

---

## Expected Optimization Results

| Optimization Plan | Expected Speed Improvement | Implementation Complexity |
|----------|--------------|------------|
| Batch Size Adjustment | 3-5x | Low (config change) |
| VLM Backend | 2-3x | Medium (requires service deployment) |
| Multi-GPU Parallel | 2x | Medium |
| **Combined Optimization** | **6-10x** | - |

**Target**: Optimize from 98s to 10-16s (16-page PDF)

---

## Testing Steps

### Step 1: Verify Current Configuration
```bash
cat ~/.magic-pdf.json
python3 -c "import paddle; print(paddle.device.is_compiled_with_cuda())"
```

### Step 2: Apply Batch Optimization
```bash
# Backup original configuration
cp ~/.magic-pdf.json ~/.magic-pdf.json.bak

# Modify configuration
cat > ~/.magic-pdf.json << 'EOF'
{
  "device-mode": "cuda",
  "models-dir": "/root/mineru_models",
  "rec_batch_num": 32,
  "det_batch_num": 8,
  "table-config": {
    "is_table_recog_enable": true,
    "max_time": 400
  }
}
EOF
```

### Step 3: Retest
```bash
cd ~/mineru_test
time mineru -p TSLA-Q3-2025.pdf -o output_optimized/
```

### Step 4: Monitor GPU Utilization
```bash
# In another terminal
watch -n 0.5 nvidia-smi
```

---

## References

- [GitHub Discussion #3738](https://github.com/opendatalab/MinerU/discussions/3738) - Batch Processing Optimization
- [GitHub Discussion #1226](https://github.com/opendatalab/MinerU/discussions/1226) - Performance Benchmarks
- [MinerU v2.5 Release Notes](https://github.com/opendatalab/MinerU/releases) - vLLM Migration
