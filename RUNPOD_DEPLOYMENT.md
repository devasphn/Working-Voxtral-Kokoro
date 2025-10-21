# Voxtral Model - RunPod Deployment Guide

Complete step-by-step guide for deploying the Voxtral model (VAD + ASR + LLM) on RunPod.

## 📋 Prerequisites

- RunPod account with GPU pod access
- HuggingFace API token (for model downloads)
- Basic familiarity with terminal/command line

## 🚀 Step 1: Create RunPod Pod

1. Go to [RunPod.io](https://www.runpod.io)
2. Click "Create Pod"
3. Select template: **PyTorch 2.1.0+ with CUDA 12.1**
4. Choose GPU: **RTX A4500** or better (8GB+ VRAM minimum)
5. Configure:
   - **Container Disk**: 50GB minimum
   - **Volume Disk**: Optional (for persistent storage)
   - **HTTP Ports**: 8000, 8005
6. Click "Deploy" and wait for pod to start

## 📥 Step 2: Access Pod Terminal

1. In RunPod dashboard, find your pod
2. Click "Connect" → "Connect to Pod"
3. Select "Web Terminal" or use SSH
4. You'll see a terminal prompt

## 📂 Step 3: Clone Repository

```bash
cd /workspace
git clone <your-repository-url> voxtral-model
cd voxtral-model
```

## 🔑 Step 4: Set HuggingFace Token

```bash
export HF_TOKEN="your_huggingface_token_here"
```

Or create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your HF_TOKEN
nano .env
```

## 🐍 Step 5: Setup Python Environment

```bash
# Update system packages
apt-get update && apt-get install -y python3-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

## 📦 Step 6: Install PyTorch

```bash
# Install PyTorch with CUDA 12.1 support
pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121
```

## 📚 Step 7: Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installation
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
```

## 💾 Step 8: Create Directories

```bash
# Create necessary directories
mkdir -p model_cache
mkdir -p logs

# Verify
ls -la
```

## 🤖 Step 9: Pre-download Models

```bash
# Pre-download Voxtral model to avoid timeout during first run
python3 << 'EOF'
import os
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your_token')

print("📥 Downloading Voxtral model...")
from transformers import VoxtralForConditionalGeneration, AutoProcessor

processor = AutoProcessor.from_pretrained(
    'mistralai/Voxtral-Mini-3B-2507',
    cache_dir='./model_cache'
)
model = VoxtralForConditionalGeneration.from_pretrained(
    'mistralai/Voxtral-Mini-3B-2507',
    cache_dir='./model_cache',
    torch_dtype='auto',
    device_map='auto'
)
print("✅ Voxtral model downloaded successfully!")
EOF
```

## 🚀 Step 10: Start the System

```bash
# Start the UI server in background
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid

# Wait for startup
sleep 15

# Check if running
if kill -0 $(cat .system.pid) 2>/dev/null; then
    echo "✅ System started successfully (PID: $(cat .system.pid))"
else
    echo "❌ System failed to start. Check logs/system.log"
    tail -50 logs/system.log
fi
```

## ✅ Step 11: Verify System

### Health Check
```bash
curl -f http://localhost:8000/health
```

Expected output:
```json
{"status":"healthy","timestamp":"2024-01-01T12:00:00Z","version":"1.0.0"}
```

### Test WebSocket Connection
```bash
python3 << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")
            
            # Send test message
            test_msg = {"type": "ping"}
            await websocket.send(json.dumps(test_msg))
            
            # Receive response
            response = await websocket.recv()
            print(f"Response: {response}")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

asyncio.run(test_websocket())
EOF
```

## 🌐 Step 12: Access Web Interface

### Get RunPod Public URL
```bash
# Your pod URL will be in format: https://[POD_ID]-8000.proxy.runpod.net
echo "🌐 Access your system at:"
echo "   Main UI: https://$(hostname -I | awk '{print $1}')-8000.proxy.runpod.net"
echo "   Health: https://$(hostname -I | awk '{print $1}')-8000.proxy.runpod.net/health"
```

Or check RunPod dashboard:
1. Go to your pod details
2. Look for "Connect" button
3. Find HTTP service on port 8000
4. Click the link to access web interface

## 📊 Step 13: Monitor System

### View Logs
```bash
# Real-time log monitoring
tail -f logs/system.log

# View last 50 lines
tail -50 logs/system.log
```

### Check GPU Usage
```bash
# Monitor GPU in real-time
watch -n 1 nvidia-smi

# One-time check
nvidia-smi
```

### Check System Resources
```bash
# View CPU, memory, disk usage
htop

# Or use top
top
```

### Check Process Status
```bash
ps aux | grep python
```

## 🔧 Troubleshooting

### System Won't Start
```bash
# Check logs
tail -100 logs/system.log

# Verify Python environment
python3 -c "import torch; print(torch.cuda.is_available())"

# Try starting manually
python3 -m src.api.ui_server_realtime
```

### Out of Memory Error
```bash
# Reduce GPU memory usage in .env
export GPU_MEMORY_UTILIZATION=0.7

# Or restart with lower memory
kill $(cat .system.pid)
sleep 5
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid
```

### WebSocket Connection Issues
```bash
# Check if port 8000 is listening
netstat -tulpn | grep :8000

# Check firewall
sudo ufw status

# Restart system
kill $(cat .system.pid) 2>/dev/null || true
sleep 5
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid
```

### Model Download Timeout
```bash
# Increase timeout in .env
export MODEL_LOAD_TIMEOUT=600

# Pre-download manually
python3 << 'EOF'
from transformers import VoxtralForConditionalGeneration, AutoProcessor
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
print("✅ Model downloaded!")
EOF
```

## 🛑 Step 14: Stop System

```bash
# Stop the running system
kill $(cat .system.pid) 2>/dev/null || true

# Verify it's stopped
sleep 2
ps aux | grep python
```

## 📝 Quick Reference Commands

```bash
# Activate environment
source venv/bin/activate

# Start system
nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
echo $! > .system.pid

# Check status
kill -0 $(cat .system.pid) && echo "Running" || echo "Stopped"

# View logs
tail -f logs/system.log

# Stop system
kill $(cat .system.pid)

# Health check
curl http://localhost:8000/health
```

## 🎯 Performance Tips

1. **Enable Flash Attention**: Set `ENABLE_FLASH_ATTENTION=true` in `.env`
2. **Use Torch Compile**: Set `ENABLE_TORCH_COMPILE=true` in `.env`
3. **Optimize VAD**: Adjust sensitivity in `config.yaml` for your use case
4. **Monitor GPU**: Use `nvidia-smi` to track memory usage
5. **Pre-download Models**: Download models before production use

## 📞 Support

If you encounter issues:
1. Check logs: `tail -f logs/system.log`
2. Verify GPU: `nvidia-smi`
3. Test connectivity: `curl http://localhost:8000/health`
4. Review configuration: `cat config.yaml`
5. Check environment: `env | grep -E "HF_TOKEN|CUDA"`

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready

