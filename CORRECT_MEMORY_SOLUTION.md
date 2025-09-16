# 🧠 **CORRECT MEMORY SOLUTION**

## **THE REAL ISSUE:**
The memory error occurs in VLLM (which Orpheus TTS uses internally), NOT in OrpheusModel parameters.

## **CORRECT SOLUTION:**
Use environment variables to control VLLM memory usage:

```bash
# Set VLLM memory optimization BEFORE running Python
export VLLM_GPU_MEMORY_UTILIZATION=0.8
export VLLM_MAX_MODEL_LEN=1024
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

## **CORRECT ORPHEUS INITIALIZATION:**
```python
# CORRECT - exactly as in your Flask example
from orpheus_tts import OrpheusModel
model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
```

## **WRONG APPROACH (what I did):**
```python
# WRONG - these parameters don't exist
model = OrpheusModel(
    model_name="canopylabs/orpheus-tts-0.1-finetune-prod",
    max_model_len=1024,  # ❌ This parameter doesn't exist
    gpu_memory_utilization=0.8  # ❌ This parameter doesn't exist
)
```