# 🚀 PRODUCTION-READY RUNPOD DEPLOYMENT GUIDE
## Voxtral + Orpheus TTS Speech-to-Speech System with <300ms Latency

### 📋 **PRE-DEPLOYMENT REQUIREMENTS**

#### **RunPod Instance Specifications**
- **GPU**: NVIDIA RTX 4090 (24GB VRAM) or A100 (40GB VRAM)
- **CPU**: 8+ cores, 32GB+ RAM
- **Storage**: 100GB+ SSD
- **Template**: PyTorch 2.1+ with CUDA 12.1

#### **Port Configuration**
```bash
# Required ports to expose in RunPod:
HTTP_PORT=8000    # Main UI and API
WS_PORT=8765      # WebSocket streaming
HEALTH_PORT=8005  # Health checks
METRICS_PORT=8766 # Performance monitoring
```

#### **Environment Variables**
```bash
# Required in RunPod environment variables:
HF_TOKEN=your_huggingface_token_here
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### 🔧 **STEP-BY-STEP DEPLOYMENT COMMANDS**

#### **Step 1: Initial Setup**
```bash
# Navigate to workspace
cd /workspace

# Clone repository
git clone https://github.com/devasphn/Voxtral-Final.git
cd Voxtral-Final

# Verify system requirements
nvidia-smi
python3 --version
```

#### **Step 2: Environment Setup**
```bash
# Set HuggingFace token (REQUIRED)
export HF_TOKEN="your_actual_token_here"
echo "export HF_TOKEN=your_actual_token_here" >> ~/.bashrc

# Set optimization environment variables
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
```

#### **Step 3: Dependency Installation (EXACT ORDER)**
```bash
# Upgrade pip first
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 12.1 support
pip install torch>=2.1.0 torchaudio>=2.1.0 torchvision>=0.16.0 --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies in correct order
pip install transformers>=4.56.0
pip install huggingface-hub>=0.34.0
pip install accelerate>=0.25.0
pip install tokenizers>=0.15.0

# Install Mistral Common with audio support
pip install "mistral-common[audio]>=1.8.1"

# Install Orpheus TTS (correct package name)
pip install orpheus-speech>=0.1.0

# Install vLLM for optimized inference
pip install "vllm>=0.6.0,<0.8.0"

# Install audio processing libraries
pip install librosa>=0.10.1
pip install soundfile>=0.12.1
pip install numpy>=1.24.0
pip install scipy>=1.11.0

# Install web framework
pip install fastapi>=0.107.0
pip install "uvicorn[standard]>=0.24.0"
pip install websockets>=12.0
pip install pydantic>=2.9.0
pip install pydantic-settings>=2.1.0
pip install python-multipart>=0.0.6

# Install utilities
pip install pyyaml>=6.0.1
pip install python-dotenv>=1.0.0
pip install psutil>=5.9.0

# Install Flash Attention (optional, for optimization)
pip install flash-attn>=2.5.0 || echo "Flash Attention installation failed - continuing without it"

# Install remaining requirements
pip install -r requirements.txt || echo "Some packages may have failed - system should still work"
```

#### **Step 4: Model Pre-downloading and Caching**
```bash
# Create cache directories
mkdir -p model_cache
mkdir -p logs

# Pre-download Voxtral model
python3 -c "
import os
os.environ['HF_TOKEN'] = '$HF_TOKEN'
from transformers import VoxtralForConditionalGeneration, AutoProcessor
print('Downloading Voxtral model...')
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print('✅ Voxtral model cached successfully')
"

# Pre-download Orpheus model
python3 -c "
import os
os.environ['HF_TOKEN'] = '$HF_TOKEN'
try:
    from orpheus_tts import OrpheusModel
    print('Downloading Orpheus model...')
    model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod')
    print('✅ Orpheus model cached successfully')
except Exception as e:
    print(f'⚠️ Orpheus model download failed: {e}')
    print('Model will be downloaded on first use')
"
```

#### **Step 5: Configuration Verification**
```bash
# Test Python imports
python3 -c "
import torch
import transformers
import fastapi
import websockets
print('✅ Core packages imported successfully')
print(f'✅ PyTorch CUDA available: {torch.cuda.is_available()}')
print(f'✅ GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')
"

# Test Voxtral availability
python3 -c "
try:
    from transformers import VoxtralForConditionalGeneration
    print('✅ Voxtral classes available')
except ImportError as e:
    print(f'❌ Voxtral import failed: {e}')
"

# Test configuration loading
python3 -c "
try:
    from src.utils.config import config
    print('✅ Configuration loaded successfully')
    print(f'   Server port: {config.server.http_port}')
    print(f'   Model name: {config.model.name}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

#### **Step 6: System Startup and Validation**
```bash
# Start the system
python3 -m src.api.ui_server_realtime &

# Wait for startup
sleep 10

# Verify system is running
curl -f http://localhost:8000/health || echo "❌ Health check failed"

# Test WebSocket connection
python3 -c "
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            print('✅ WebSocket connection successful')
            print(f'Response: {response}')
    except Exception as e:
        print(f'❌ WebSocket test failed: {e}')

asyncio.run(test_websocket())
"
```

### 🧪 **VERIFICATION & TESTING**

#### **Health Check Commands**
```bash
# System health
curl http://localhost:8000/health | jq '.'

# Model status
curl http://localhost:8000/api/system/status | jq '.model_info'

# Performance metrics
curl http://localhost:8000/api/performance/metrics | jq '.'
```

#### **Performance Testing**
```bash
# Latency test
curl -X POST http://localhost:8000/api/performance/test \
  -H "Content-Type: application/json" \
  -d '{"test_type": "latency", "iterations": 10}' | jq '.'

# Load test
python3 test_production_readiness.py
```

#### **Log Monitoring**
```bash
# Monitor application logs
tail -f logs/voxtral_streaming.log

# Monitor system resources
htop

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### 🛠️ **TROUBLESHOOTING**

#### **Common Issues and Solutions**

**1. CUDA Out of Memory**
```bash
# Reduce memory usage
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256
# Restart system
pkill -f ui_server_realtime
python3 -m src.api.ui_server_realtime
```

**2. Model Loading Timeout**
```bash
# Increase timeout and pre-download models
export MODEL_LOAD_TIMEOUT=600
# Clear cache and re-download
rm -rf model_cache/*
# Re-run model download commands from Step 4
```

**3. WebSocket Connection Issues**
```bash
# Check port availability
netstat -tulpn | grep :8765
# Restart WebSocket server
pkill -f websocket_server
python3 -m src.streaming.websocket_server
```

**4. High Latency (>300ms)**
```bash
# Enable all optimizations
export ENABLE_TORCH_COMPILE=true
export ENABLE_FLASH_ATTENTION=true
export ENABLE_QUANTIZATION=true
# Restart with optimizations
python3 -m src.api.ui_server_realtime
```

### 📊 **PERFORMANCE MONITORING**

#### **Real-time Metrics**
- **UI Dashboard**: `http://your-runpod-url:8000`
- **API Metrics**: `http://your-runpod-url:8000/api/performance/metrics`
- **Health Status**: `http://your-runpod-url:8000/health`

#### **Performance Targets**
| Component | Target | Optimized |
|-----------|--------|-----------|
| VAD Detection | <10ms | <5ms |
| ASR Processing | <100ms | <50ms |
| LLM Generation | <150ms | <100ms |
| TTS Synthesis | <100ms | <50ms |
| **Total Pipeline** | **<300ms** | **<200ms** |

### ✅ **SUCCESS CRITERIA**

- [ ] All dependencies installed without errors
- [ ] Models pre-downloaded and cached
- [ ] Health check returns "healthy" status
- [ ] WebSocket connection established successfully
- [ ] Latency test shows <300ms end-to-end
- [ ] System stable for 10+ minutes of operation
- [ ] GPU memory usage <80% of available VRAM
- [ ] No error messages in application logs

### 🎯 **PRODUCTION DEPLOYMENT COMPLETE**

Your Voxtral + Orpheus TTS speech-to-speech system is now production-ready with <300ms latency performance on RunPod!
