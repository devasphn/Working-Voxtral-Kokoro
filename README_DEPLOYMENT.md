# Voxtral + TTS Integrated Real-time Voice Application

## 🚀 Complete Voice AI System

This integrated system provides real-time voice conversation with AI, featuring:

- **Speech-to-Text**: Voxtral-Mini-3B-2507 model for accurate transcription
- **Text Generation**: Intelligent LLM responses
- **Text-to-Speech**: Orpheus TTS with 24 voices across 8 languages
- **Voice Activity Detection**: Smart silence detection
- **Real-time Streaming**: WebSocket-based communication
- **Pre-loaded Models**: Instant conversation startup

## 📋 Architecture Overview

```
User Voice Input → VAD → STT (Voxtral) → LLM → TTS (Orpheus) → Audio Output
                    ↓
              WebSocket Communication
                    ↓
         Web Interface (Port 8000)
```

### System Components

1. **Web UI Server** (Port 8000): Main interface with WebSocket support
2. **Health Check Server** (Port 8005): System monitoring
3. **TCP Server** (Port 8766): Alternative streaming interface
4. **Integrated TTS Engine**: Orpheus-FastAPI TTS system
5. **Model Pre-loading**: All models loaded at startup

## 🛠️ RunPod Deployment

### Single Command Deployment

```bash
cd workspace
git clone <your-repository-url> Voxtral-Final
cd Voxtral-Final
bash deploy_voxtral_tts.sh
```

### Manual Step-by-Step Deployment

If you prefer manual control:

```bash
# 1. Navigate to workspace
cd workspace

# 2. Clone repository
git clone <your-repository-url> Voxtral-Final
cd Voxtral-Final

# 3. Install system dependencies
apt-get update
apt-get install -y build-essential cmake git wget curl unzip netcat-openbsd lsof htop ffmpeg portaudio19-dev python3-dev

# 4. Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 5. Set environment variables
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 6. Cache models (one-time setup)
mkdir -p /workspace/model_cache
python3 -c "
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import torch
model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='/workspace/model_cache', torch_dtype=torch.bfloat16, device_map='auto', attn_implementation='eager', low_cpu_mem_usage=True, trust_remote_code=True)
processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='/workspace/model_cache')
"

python3 -c "
from snac import SNAC
model = SNAC.from_pretrained('hubertsiuzdak/snac_24khz')
"

# 7. Start services
python -m src.api.health_check &
sleep 3
python -m src.api.ui_server_realtime &
sleep 8
python -m src.streaming.tcp_server &
sleep 5

# 8. Verify services
nc -z localhost 8000 && echo "✅ Main service running"
nc -z localhost 8005 && echo "✅ Health check running"
nc -z localhost 8766 && echo "✅ TCP server running"
```

## 🌐 Access URLs

Replace `[POD_ID]` with your RunPod instance ID:

- **Web Interface**: `https://[POD_ID]-8000.proxy.runpod.net`
- **Health Check**: `https://[POD_ID]-8005.proxy.runpod.net/health`
- **WebSocket**: `wss://[POD_ID]-8000.proxy.runpod.net/ws`

## 🎯 Usage Instructions

### Web Interface Usage

1. **Connect**: Open the web interface and click "Connect"
2. **Start Conversation**: Click "Start Conversation" to begin
3. **Speak**: Talk into your microphone
4. **Receive Responses**: Get both text and audio responses from AI

### Voice Selection

The system supports 24 voices across 8 languages:

- **English**: tara, leah, jess, leo, dan, mia, zac, zoe
- **French**: pierre, amelie, marie
- **German**: jana, thomas, max
- **Korean**: 유나, 준서
- **Hindi**: ऋतिका
- **Mandarin**: 长乐, 白芷
- **Spanish**: javi, sergio, maria
- **Italian**: pietro, giulia, carlo

## ⚙️ Configuration

### Main Configuration (config.yaml)

```yaml
server:
  host: "0.0.0.0"
  http_port: 8000
  health_port: 8005

model:
  name: "mistralai/Voxtral-Mini-3B-2507"
  device: "cuda"
  torch_dtype: "bfloat16"

tts:
  engine: "orpheus"
  default_voice: "tara"
  sample_rate: 24000
  enabled: true
```

### Environment Variables

```bash
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
OMP_NUM_THREADS=8
TOKENIZERS_PARALLELISM=false
```

## 🔧 Performance Optimization

### GPU Requirements

- **Minimum**: 8GB VRAM (RTX 3070/4060 Ti)
- **Recommended**: 12GB+ VRAM (RTX 4070/3080+)
- **Optimal**: 16GB+ VRAM (RTX 4080/4090)

### Performance Features

- **Model Pre-loading**: All models loaded at startup
- **GPU Optimization**: CUDA acceleration throughout
- **Streaming Processing**: Real-time audio processing
- **VAD Integration**: Smart silence detection
- **Memory Management**: Optimized GPU memory usage

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   lsof -ti:8005 | xargs kill -9
   lsof -ti:8766 | xargs kill -9
   ```

2. **CUDA Out of Memory**
   ```bash
   export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
   ```

3. **Model Loading Fails**
   ```bash
   rm -rf /workspace/model_cache
   # Re-run model caching step
   ```

4. **Audio Issues**
   ```bash
   apt-get install -y portaudio19-dev
   pip install --upgrade sounddevice
   ```

### Service Management

```bash
# Stop all services
pkill -f 'src.api'
pkill -f 'src.streaming'

# Check service status
nc -z localhost 8000 && echo "Main service: ✅" || echo "Main service: ❌"
nc -z localhost 8005 && echo "Health check: ✅" || echo "Health check: ❌"
nc -z localhost 8766 && echo "TCP server: ✅" || echo "TCP server: ❌"

# View logs
tail -f /workspace/logs/voxtral_streaming.log
```

## 📊 System Requirements

### Hardware
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **RAM**: 16GB+ system RAM
- **CPU**: 8+ cores recommended
- **Storage**: 20GB+ free space

### Software
- **OS**: Ubuntu 20.04+ or compatible Linux
- **Python**: 3.8-3.11 (3.12 not supported)
- **CUDA**: 11.8+ or 12.1+
- **PyTorch**: 2.1.0+

## 🔒 Security Notes

- Services bind to `0.0.0.0` for RunPod compatibility
- Use RunPod's built-in proxy for secure access
- No authentication required for demo purposes
- Consider adding authentication for production use

## 📈 Monitoring

### Health Check Endpoint

```bash
curl https://[POD_ID]-8005.proxy.runpod.net/health
```

### Performance Metrics

The system provides real-time metrics:
- Processing latency
- Audio generation speed
- Model performance
- Memory usage

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify all dependencies are installed
4. Ensure sufficient GPU memory

---

**🎉 Enjoy your real-time AI voice conversation system!**
