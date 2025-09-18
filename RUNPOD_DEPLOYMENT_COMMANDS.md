# 🚀 RUNPOD DEPLOYMENT COMMANDS
## Complete Step-by-Step Voxtral Speech-to-Speech System Deployment

### 📋 **PREREQUISITES**
- RunPod instance with NVIDIA GPU (RTX 4090 or A100 recommended)
- CUDA 12.1+ support
- Your HuggingFace token ready

---

## 🔧 **STEP 1: INITIAL SYSTEM SETUP**

### Navigate to workspace and clone repository:
```bash
cd /workspace
git clone https://github.com/devasphn/Voxtral-Final.git
cd Voxtral-Final
```

**Expected output:**
```
Cloning into 'Voxtral-Final'...
remote: Enumerating objects: ...
remote: Total ... (delta ...), reused ... (delta ...)
Receiving objects: 100% (...), done.
```

### Verify repository structure:
```bash
ls -la
```

**Expected files:**
```
drwxr-xr-x  src/
-rw-r--r--  requirements.txt
-rw-r--r--  config.yaml
-rw-r--r--  deploy_production.sh
-rw-r--r--  README.md
```

---

## 🌍 **STEP 2: ENVIRONMENT SETUP**

### Set HuggingFace token (REQUIRED):
```bash
export HF_TOKEN="your_actual_huggingface_token_here"
echo "export HF_TOKEN=your_actual_huggingface_token_here" >> ~/.bashrc
```

### Set CUDA and optimization environment variables:
```bash
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
```

### Add to bashrc for persistence:
```bash
cat >> ~/.bashrc << 'EOF'
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
EOF
```

### Verify GPU availability:
```bash
nvidia-smi
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2  |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA RTX 4090     Off  | 00000000:01:00.0 Off |                  Off |
| 30%   35C    P8    25W / 450W |      0MiB / 24564MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

---

## 🐍 **STEP 3: PYTHON ENVIRONMENT SETUP**

### Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

**Expected output:**
```
(venv) root@container-id:/workspace/Voxtral-Final#
```

### Upgrade pip and essential tools:
```bash
python -m pip install --upgrade pip setuptools wheel
```

**Expected output:**
```
Successfully installed pip-23.x.x setuptools-68.x.x wheel-0.x.x
```

---

## 📦 **STEP 4: DEPENDENCY INSTALLATION (EXACT ORDER)**

### Install PyTorch with CUDA 12.1 support:
```bash
pip install torch>=2.1.0 torchaudio>=2.1.0 torchvision>=0.16.0 --index-url https://download.pytorch.org/whl/cu121
```

**Expected output:**
```
Successfully installed torch-2.x.x torchaudio-2.x.x torchvision-0.x.x
```

### Install core transformers stack:
```bash
pip install transformers>=4.56.0
pip install huggingface-hub>=0.34.0
pip install accelerate>=0.25.0
pip install tokenizers>=0.15.0
```

### Install Mistral Common with audio support:
```bash
pip install "mistral-common[audio]>=1.8.1"
```

### Install Orpheus TTS:
```bash
pip install orpheus-speech>=0.1.0
```

### Install vLLM for optimized inference:
```bash
pip install "vllm>=0.6.0,<0.8.0"
```

### Install audio processing libraries:
```bash
pip install librosa>=0.10.1
pip install soundfile>=0.12.1
pip install "numpy>=1.24.0,<2.0.0"
pip install scipy>=1.11.0
```

### Install web framework:
```bash
pip install fastapi>=0.107.0
pip install "uvicorn[standard]>=0.24.0"
pip install websockets>=12.0
pip install pydantic>=2.9.0
pip install pydantic-settings>=2.1.0
pip install python-multipart>=0.0.6
```

### Install utilities:
```bash
pip install pyyaml>=6.0.1
pip install python-dotenv>=1.0.0
pip install psutil>=5.9.0
pip install aiofiles>=23.2.1
pip install httpx>=0.25.0
```

### Install Flash Attention (optional, for optimization):
```bash
pip install flash-attn>=2.5.0 || echo "Flash Attention installation failed - continuing without it"
```

### Install remaining requirements:
```bash
pip install -r requirements.txt || echo "Some packages may have failed - system should still work"
```

---

## 🔍 **STEP 5: SYSTEM VERIFICATION**

### Test core imports:
```bash
python3 -c "
import torch
import transformers
import fastapi
import websockets
print('✅ Core packages imported successfully')
print(f'✅ PyTorch CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU device: {torch.cuda.get_device_name(0)}')
    print(f'✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
else:
    print('❌ CUDA not available')
"
```

**Expected output:**
```
✅ Core packages imported successfully
✅ PyTorch CUDA available: True
✅ GPU device: NVIDIA RTX 4090
✅ VRAM: 24.0GB
```

### Test Voxtral availability:
```bash
python3 -c "
try:
    from transformers import VoxtralForConditionalGeneration
    print('✅ Voxtral classes available')
except ImportError as e:
    print(f'❌ Voxtral import failed: {e}')
"
```

### Test configuration loading:
```bash
python3 -c "
try:
    from src.utils.config import config
    print('✅ Configuration loaded successfully')
    print(f'   Server HTTP port: {config.server.http_port}')
    print(f'   Model name: {config.model.name}')
    print(f'   TTS engine: {config.tts.engine}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

**Expected output:**
```
✅ Configuration loaded successfully
   Server HTTP port: 8000
   Model name: mistralai/Voxtral-Mini-3B-2507
   TTS engine: orpheus-direct
```

---

## 📥 **STEP 6: MODEL PRE-DOWNLOADING**

### Create cache directories:
```bash
mkdir -p model_cache
mkdir -p logs
```

### Pre-download Voxtral model:
```bash
python3 -c "
import os
os.environ['HF_TOKEN'] = '$HF_TOKEN'
from transformers import VoxtralForConditionalGeneration, AutoProcessor
print('Downloading Voxtral model...')
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print('✅ Voxtral model cached successfully')
"
```

**Expected output:**
```
Downloading Voxtral model...
Downloading (…)rocessor_config.json: 100%|██████████| 1.23k/1.23k [00:00<00:00, 2.45MB/s]
Downloading (…)okenizer_config.json: 100%|██████████| 2.54k/2.54k [00:00<00:00, 5.08MB/s]
...
✅ Voxtral model cached successfully
```

### Pre-download Orpheus model (optional):
```bash
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

---

## 🚀 **STEP 7: SYSTEM STARTUP**

### Start the speech-to-speech system:
```bash
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid
```

### Wait for startup (15 seconds):
```bash
sleep 15
```

### Check if system is running:
```bash
if kill -0 $(cat .system.pid) 2>/dev/null; then
    echo "✅ System started successfully (PID: $(cat .system.pid))"
else
    echo "❌ System failed to start. Check logs/system.log"
fi
```

---

## ✅ **STEP 8: SYSTEM VERIFICATION**

### Health check:
```bash
curl -f http://localhost:8000/health
```

**Expected output:**
```json
{"status":"healthy","timestamp":"2024-01-01T12:00:00Z","version":"1.0.0"}
```

### Test WebSocket connection:
```bash
python3 -c "
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri, timeout=10) as websocket:
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            print('✅ WebSocket connection successful')
            print(f'Response: {response}')
    except Exception as e:
        print(f'❌ WebSocket test failed: {e}')

asyncio.run(test_websocket())
"
```

### Run comprehensive tests:
```bash
python3 test_production_system.py
```

**Expected output:**
```
🧪 Starting comprehensive production system tests...
✅ health_endpoint: PASSED
✅ model_status: PASSED
✅ websocket_connection: PASSED
✅ latency_performance: PASSED
✅ audio_processing: PASSED
✅ stress_load: PASSED
🎉 PRODUCTION SYSTEM IS READY!
```

---

## 🌐 **STEP 9: ACCESS WEB INTERFACE**

### Get RunPod public URL:
```bash
echo "🌐 Access your speech-to-speech system at:"
echo "   Main UI: https://$(hostname -I | awk '{print $1}')-8000.proxy.runpod.net"
echo "   Health: https://$(hostname -I | awk '{print $1}')-8000.proxy.runpod.net/health"
```

### Alternative - Check RunPod dashboard:
- Go to your RunPod dashboard
- Click on your pod
- Look for "Connect" button and HTTP service on port 8000

---

## 🔧 **TROUBLESHOOTING COMMANDS**

### Check system logs:
```bash
tail -f logs/system.log
```

### Monitor GPU usage:
```bash
watch -n 1 nvidia-smi
```

### Check system resources:
```bash
htop
```

### Check process status:
```bash
ps aux | grep python
```

### Check port usage:
```bash
netstat -tulpn | grep :8000
netstat -tulpn | grep :8765
```

### Restart system if needed:
```bash
# Stop system
kill $(cat .system.pid) 2>/dev/null || true

# Wait a moment
sleep 5

# Restart
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid
```

### Check configuration:
```bash
python3 -c "
from src.utils.config import config
import json
print(json.dumps({
    'server_port': config.server.http_port,
    'model_name': config.model.name,
    'tts_engine': config.tts.engine,
    'latency_target': config.speech_to_speech.latency_target_ms
}, indent=2))
"
```

### Memory usage check:
```bash
python3 -c "
import psutil
import torch
print(f'CPU Memory: {psutil.virtual_memory().percent}% used')
if torch.cuda.is_available():
    print(f'GPU Memory: {torch.cuda.memory_allocated(0) / 1024**3:.1f}GB / {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
"
```

---

## 🎯 **SUCCESS INDICATORS**

✅ **Deployment Successful When:**
- Health check returns `{"status":"healthy"}`
- WebSocket connection test passes
- GPU memory shows model loaded
- UI accessible via RunPod proxy URL
- Test suite shows all tests passing

✅ **Performance Targets:**
- End-to-end latency: <300ms
- GPU memory usage: <80% of available VRAM
- CPU usage: <70% during operation
- WebSocket response time: <50ms

---

## 🚀 **QUICK DEPLOYMENT SCRIPT**

Save this as `quick_deploy.sh` for one-command deployment:

```bash
#!/bin/bash
set -e

echo "🚀 Quick Voxtral Deployment Starting..."

# Set environment
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false

# Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install PyTorch
pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121

# Install requirements
pip install -r requirements.txt

# Start system
mkdir -p logs
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid

echo "✅ Deployment complete! Check logs/system.log for status."
```

**Usage:**
```bash
chmod +x quick_deploy.sh
export HF_TOKEN="your_token_here"
./quick_deploy.sh
```

---

## ⚡ **CONDENSED COPY-PASTE COMMANDS**

For quick deployment, copy and paste these command blocks in sequence:

### Block 1 - Initial Setup:
```bash
cd /workspace
git clone https://github.com/devasphn/Voxtral-Final.git
cd Voxtral-Final
export HF_TOKEN="your_actual_huggingface_token_here"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false
```

### Block 2 - Python Environment:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### Block 3 - Core Dependencies:
```bash
pip install torch>=2.1.0 torchaudio>=2.1.0 torchvision>=0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install transformers>=4.56.0 huggingface-hub>=0.34.0 accelerate>=0.25.0
pip install "mistral-common[audio]>=1.8.1" orpheus-speech>=0.1.0
pip install fastapi>=0.107.0 "uvicorn[standard]>=0.24.0" websockets>=12.0
pip install pydantic>=2.9.0 pydantic-settings>=2.1.0
```

### Block 4 - Audio & ML Libraries:
```bash
pip install librosa>=0.10.1 soundfile>=0.12.1 "numpy>=1.24.0,<2.0.0" scipy>=1.11.0
pip install pyyaml>=6.0.1 python-dotenv>=1.0.0 psutil>=5.9.0
pip install -r requirements.txt || echo "Continuing despite some package failures"
```

### Block 5 - System Startup:
```bash
mkdir -p model_cache logs
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid
sleep 15
```

### Block 6 - Verification:
```bash
curl -f http://localhost:8000/health
python3 test_production_system.py
echo "🌐 Access UI at: https://$(hostname -I | awk '{print $1}')-8000.proxy.runpod.net"
```
