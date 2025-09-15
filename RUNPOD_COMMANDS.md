# 🚀 **PERFECT RUNPOD DEPLOYMENT COMMANDS**

## **STEP 1: System Setup (Run these commands in RunPod Web Terminal)**

```bash
# Update system and install dependencies
apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1

# Check GPU
nvidia-smi

# Check Python version (should be 3.8-3.11)
python3 --version
```

## **STEP 2: Create Virtual Environment**

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

## **STEP 3: Install Perfect Dependencies**

```bash
# Install PyTorch with CUDA 12.1 support
pip install torch>=2.1.0,\<2.5.0 torchvision>=0.16.0,\<0.20.0 torchaudio>=2.1.0,\<2.5.0 --index-url https://download.pytorch.org/whl/cu121

# Install all other dependencies
pip install -r requirements.txt

# Verify critical packages
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "from orpheus_tts import OrpheusModel; print('Orpheus TTS: OK')"
python -c "from transformers import VoxtralForConditionalGeneration; print('Voxtral: OK')"
```

## **STEP 4: Pre-cache Models**

```bash
# Set environment variables
export TRANSFORMERS_CACHE="./model_cache"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create cache directory
mkdir -p model_cache

# Pre-cache Voxtral model
python -c "
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import os
os.environ['TRANSFORMERS_CACHE'] = './model_cache'

print('Caching Voxtral...')
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print('Voxtral cached successfully!')
"

# Pre-cache Orpheus model
python -c "
from orpheus_tts import OrpheusModel
print('Caching Orpheus...')
model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod', max_model_len=2048)
print('Orpheus cached successfully!')
"
```

## **STEP 5: Test Perfect System**

```bash
# Make scripts executable
chmod +x start_perfect.sh
chmod +x deploy_perfect.sh

# Test the complete system
python test_perfect_system.py
```

## **STEP 6: Start the Server**

```bash
# Start the perfect system
./start_perfect.sh
```

## **STEP 7: Access the Application**

- **Web UI**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/api/status`
- **API Docs**: `http://localhost:8000/docs`

## **🔧 Troubleshooting Commands**

### Check GPU Memory
```bash
nvidia-smi
```

### Check Python Environment
```bash
source venv/bin/activate
pip list | grep -E "(torch|transformers|orpheus|mistral)"
```

### Test Individual Components
```bash
# Test Orpheus TTS only
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

# Test Voxtral only
python -c "
import asyncio
from src.models.voxtral_model_realtime import VoxtralModel
import torch

async def test():
    model = VoxtralModel()
    await model.initialize()
    result = await model.process_realtime_chunk(torch.randn(16000) * 0.1, 1)
    print(f'Result: {result}')

asyncio.run(test())
"
```

### Clear Cache and Restart
```bash
rm -rf model_cache
rm -rf venv
# Then repeat from STEP 2
```

## **📊 Expected Performance**

- **Voxtral Processing**: <100ms
- **Orpheus Generation**: <150ms  
- **Total End-to-End**: <300ms
- **Memory Usage**: ~8-12GB VRAM
- **Model Loading**: ~30-60 seconds

## **✅ Success Indicators**

1. ✅ All packages install without conflicts
2. ✅ Models cache successfully
3. ✅ Test script passes all tests
4. ✅ Server starts without errors
5. ✅ Web UI loads at localhost:8000
6. ✅ Voice conversations work with <300ms latency

## **🚨 Common Issues & Solutions**

### Issue: "orpheus_tts not found"
```bash
pip install orpheus-tts>=0.1.0
```

### Issue: "CUDA out of memory"
```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Issue: "Transformers version conflict"
```bash
pip install transformers>=4.54.0,\<4.60.0 --force-reinstall
```

### Issue: "Model loading timeout"
```bash
# Increase timeout and check internet connection
export HF_HUB_DOWNLOAD_TIMEOUT=300
```