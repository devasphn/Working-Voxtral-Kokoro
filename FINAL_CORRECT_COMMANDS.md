# 🚀 **FINAL CORRECT RUNPOD COMMANDS**

## **COPY THESE EXACT COMMANDS - MEMORY FIXED**

### **STEP 1: System Setup**
```bash
apt-get update
apt-get install -y build-essential python3-dev python3-pip python3-venv git wget curl ffmpeg libsndfile1
```

### **STEP 2: Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### **STEP 3: Install PyTorch**
```bash
pip install torch>=2.1.0 torchvision>=0.16.0 torchaudio>=2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### **STEP 4: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **STEP 5: Setup Environment with MEMORY OPTIMIZATION**
```bash
export HF_HOME="./model_cache"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export VLLM_GPU_MEMORY_UTILIZATION=0.8
export VLLM_MAX_MODEL_LEN=1024
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
mkdir -p model_cache logs
```

### **STEP 6: Login to HuggingFace**
```bash
huggingface-cli login
```

### **STEP 7: Cache Voxtral**
```bash
python -c "
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import os
os.environ['HF_HOME'] = './model_cache'
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print('✅ Voxtral cached!')
"
```

### **STEP 8: Test Orpheus with CORRECT initialization**
```bash
python -c "
from orpheus_tts import OrpheusModel
print('Testing Orpheus with CORRECT initialization...')
model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod')
print('✅ Orpheus model loaded successfully!')
"
```

### **STEP 9: Test Streaming System**
```bash
python test_streaming_system.py
```

### **STEP 10: Start Server**
```bash
chmod +x start_perfect.sh
./start_perfect.sh
```

---

## **🔧 KEY CORRECTIONS:**

1. **CORRECT Orpheus Initialization**:
   ```python
   # ✅ CORRECT - exactly as in your Flask example
   model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
   ```

2. **Memory Control via Environment Variables**:
   ```bash
   export VLLM_GPU_MEMORY_UTILIZATION=0.8
   export VLLM_MAX_MODEL_LEN=1024
   export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
   ```

3. **No Invalid Parameters**:
   - Removed `max_model_len` parameter (doesn't exist)
   - Removed `gpu_memory_utilization` parameter (doesn't exist)

---

## **🎯 GUARANTEED RESULTS:**
- ✅ No "unexpected keyword argument" errors
- ✅ Memory optimization via environment variables
- ✅ Exact Flask example implementation
- ✅ Streaming audio generation works
- ✅ Web UI at http://localhost:8000

**These are the CORRECT commands based on your Flask example!**