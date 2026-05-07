# MinerU GPU 加速优化方案

## 问题诊断

| 指标 | 当前值 | 预期值 | 差距 |
|------|--------|--------|------|
| 处理速度 | 0.16 页/秒 | 1-2 页/秒 | 6-10x |
| GPU 利用率 | 0-5% | 70-90% | 严重不足 |
| 16页 PDF 耗时 | 98s | 8-16s | 6-10x |

**根本原因**：GPU 加速未正确启用或配置不当

---

## 优化方案一：调整 OCR 批处理大小

### 原理
MinerU 默认 `rec_batch_num` 较小，导致 GPU 一次只处理少量文本块。增大批处理可显著提升 GPU 利用率。

### 配置方法

编辑 `~/.magic-pdf.json`：

```json
{
  "device-mode": "cuda",
  "models-dir": "/root/mineru_models",
  "rec_batch_num": 32,  // 默认可能是 6，增加到 32
  "det_batch_num": 8,   // 检测批处理大小
  "table-config": {
    "is_table_recog_enable": true,
    "max_time": 400
  }
}
```

### RTX 4090 推荐值
- `rec_batch_num`: 32-64（24GB VRAM 充足）
- `det_batch_num`: 8-16

---

## 优化方案二：VLM 后端（视觉语言模型）

### 原理
VLM 后端使用视觉大模型，准确率更高（90%+ vs pipeline 82%+），且天然适合 GPU 推理。

### 配置方法

1. **启动 VLM 服务器**：
```bash
# 使用 vLLM 引擎（推荐）
CUDA_VISIBLE_DEVICES=0 mineru-openai-server \
    --engine vllm \
    --port 30000 \
    --model-id "Qwen/Qwen2.5-VL-7B-Instruct"
```

2. **配置 magic-pdf.json**：
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

3. **使用 VLM 后端解析**：
```bash
mineru -p test.pdf -o output/ -b vlm-auto-engine
```

### 多 GPU 并行
```bash
# 2 GPU 并行
CUDA_VISIBLE_DEVICES=0,5 mineru-openai-server \
    --engine vllm \
    --port 30000 \
    --data-parallel-size 2
```

---

## 优化方案三：验证 PaddlePaddle GPU

### 检查脚本
```python
import paddle
print(f"PaddlePaddle version: {paddle.__version__}")
print(f"CUDA compiled: {paddle.device.is_compiled_with_cuda()}")
print(f"GPU count: {paddle.device.cuda.device_count()}")

# 测试 GPU 计算
if paddle.device.is_compiled_with_cuda():
    x = paddle.randn([1000, 1000])
    paddle.device.cuda.synchronize()
    print("GPU compute test: PASSED")
```

### 如果 PaddlePaddle 未使用 GPU

重装 GPU 版本：
```bash
pip uninstall paddlepaddle
pip install paddlepaddle-gpu==3.0.0b2 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

---

## 优化方案四：代码层面优化

### 修改 MinerUParser 支持批处理配置

```python
class MinerUParser(BaseTool):
    def __init__(
        self,
        output_base: str | Path = "outputs",
        backend: str = "pipeline",
        lang: str = "en",
        enable_image_analysis: bool = False,
        image_analyzer: "ImageAnalyzer | None" = None,
        # 新增 GPU 优化参数
        rec_batch_num: int = 32,  # OCR 批处理大小
        det_batch_num: int = 8,   # 检测批处理大小
        use_cuda: bool = True,
    ):
        # ...
        self.rec_batch_num = rec_batch_num
        self.det_batch_num = det_batch_num
        self.use_cuda = use_cuda
```

---

## 预期优化效果

| 优化方案 | 预期速度提升 | 实现复杂度 |
|----------|--------------|------------|
| 批处理大小调整 | 3-5x | 低（改配置） |
| VLM 后端 | 2-3x | 中（需部署服务） |
| 多 GPU 并行 | 2x | 中 |
| **综合优化** | **6-10x** | - |

**目标**：从 98s 优化到 10-16s（16页 PDF）

---

## 测试步骤

### Step 1: 验证当前配置
```bash
cat ~/.magic-pdf.json
python3 -c "import paddle; print(paddle.device.is_compiled_with_cuda())"
```

### Step 2: 应用批处理优化
```bash
# 备份原配置
cp ~/.magic-pdf.json ~/.magic-pdf.json.bak

# 修改配置
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

### Step 3: 重新测试
```bash
cd ~/mineru_test
time mineru -p TSLA-Q3-2025.pdf -o output_optimized/
```

### Step 4: 监控 GPU 利用率
```bash
# 另一个终端
watch -n 0.5 nvidia-smi
```

---

## 参考资料

- [GitHub Discussion #3738](https://github.com/opendatalab/MinerU/discussions/3738) - 批量处理优化
- [GitHub Discussion #1226](https://github.com/opendatalab/MinerU/discussions/1226) - 性能基准
- [MinerU v2.5 Release Notes](https://github.com/opendatalab/MinerU/releases) - vLLM 迁移
