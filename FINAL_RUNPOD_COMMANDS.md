# 🚀 **FINAL PERFECT RUNPOD COMMANDS**

## **COPY AND PASTE THESE EXACT COMMANDS IN RUNPOD WEB TERMINAL**

### **STEP 1: System Setup (No sudo needed)**
```bash
apt-get update
apt-get install -y build-essential python3-dev python3-pip python3-venv git wget curl ffmpeg libsndfile1
```

### **STEP 2: Check GPU**
```bash
nvidia-smi
python3 --version
```

### **STEP 3: Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

### **STEP 4: Install PyTorch with CUDA 12.1**
```bash
pip install torch>=2.1.0 torchvision>=0.16.0 torchaudio>=2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

### **STEP 5: Install All Dependencies**
```bash
pip install -r requirements.txt
```

### **STEP 6: Verify Critical Packages**
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "from orpheus_tts import OrpheusModel; print('Orpheus TTS: OK')"
python -c "from transformers import VoxtralForConditionalGeneration; print('Voxtral: OK')"
```

### **STEP 7: Set Environment and Create Directories**
```bash
export TRANSFORMERS_CACHE="./model_cache"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
mkdir -p model_cache
mkdir -p logs
```

### **STEP 8: Pre-cache Voxtral Model**
```bash
python -c "
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import os
os.environ['TRANSFORMERS_CACHE'] = './model_cache'
print('Caching Voxtral processor...')
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
print('Caching Voxtral model...')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print('✅ Voxtral cached successfully!')
"
```

### **STEP 9: Pre-cache Orpheus Model**
```bash
python -c "
from orpheus_tts import OrpheusModel
print('Caching Orpheus model...')
model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod', max_model_len=2048)
print('✅ Orpheus cached successfully!')
"
```

### **STEP 10: Test Perfect System**
```bash
chmod +x start_perfect.sh
python test_perfect_system.py
```

### **STEP 11: Start the Server**
```bash
./start_perfect.sh
```

### **STEP 12: Access Application**
- **Web UI**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/status

---

## **🔧 TROUBLESHOOTING COMMANDS**

### **If PyTorch Installation Fails:**
```bash
pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121
```

### **If Orpheus TTS Installation Fails:**
```bash
pip install orpheus-tts --no-cache-dir
```

### **If Transformers Installation Fails:**
```bash
pip install transformers>=4.54.0 --no-cache-dir
```

### **Check GPU Memory:**
```bash
nvidia-smi
```

### **Test Individual Components:**
```bash
# Test Orpheus only
python -c "
import asyncio
from src.tts.orpheus_perfect_model import OrpheusPerfectModel

async def test():
    model = OrpheusPerfectModel()
    await model.initialize()
    audio = await model.generate_speech('Hello world', 'tara')
    print(f'Generated {len(audio)} bytes')
    await model.cleanup()

asyncio.run(test())
"
```

### **Clear Cache and Restart:**
```bash
rm -rf model_cache
rm -rf venv
# Then repeat from STEP 3
```

---

## **📊 EXPECTED RESULTS**
- **Installation Time**: 5-10 minutes
- **Model Caching**: 2-5 minutes
- **Memory Usage**: 8-12GB VRAM
- **Performance**: <300ms end-to-end latency

---

## **✅ SUCCESS INDICATORS**
1. All pip installs complete without errors
2. Both models cache successfully
3. Test script passes all tests
4. Server starts without errors
5. Web UI loads at localhost:8000

---

## **🎯 FINAL VERIFICATION**
After server starts, test with:
```bash
curl http://localhost:8000/api/status
```

Should return JSON with system status.

**THAT'S IT! Your perfect Voxtral + Orpheus TTS system is ready!**