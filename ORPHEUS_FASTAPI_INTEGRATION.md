# Voxtral + Orpheus-FastAPI Integration Guide

## Overview

This guide explains the **correct integration** between Voxtral and Orpheus-FastAPI for high-quality TTS with the ऋतिका voice.

### Architecture

```
User Speech → Voxtral Model (VAD + ASR + LLM) → Text Response → Orpheus-FastAPI → ऋतिका Voice Audio
```

**Key Points:**
- **Voxtral**: Complete model with VAD, ASR, and LLM (no separate LLM server needed)
- **Orpheus-FastAPI**: Dedicated TTS service running on port 1234
- **Integration**: HTTP communication between Voxtral and Orpheus-FastAPI
- **Voice**: ऋतिका (Hindi) as default voice

## Quick Setup

### 1. Run the Setup Script
```bash
chmod +x setup_orpheus_fastapi.sh
./setup_orpheus_fastapi.sh
```

### 2. Start the Complete System
```bash
./start_voxtral_with_orpheus.sh
```

### 3. Test the Integration
```bash
python3 test_voxtral_orpheus_integration.py
```

## Manual Setup (Step by Step)

### Step 1: Install llama-cpp-python with CUDA
```bash
# Install with CUDA support
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python[server] --force-reinstall --no-cache-dir
```

### Step 2: Download Orpheus Model
```bash
mkdir -p /workspace/models
cd /workspace/models
wget https://huggingface.co/lex-au/Orpheus-3b-FT-Q8_0.gguf/resolve/main/Orpheus-3b-FT-Q8_0.gguf
```

### Step 3: Start Orpheus-FastAPI Server
```bash
# Terminal 1: Start Orpheus-FastAPI
python -m llama_cpp.server \
    --model /workspace/models/Orpheus-3b-FT-Q8_0.gguf \
    --host 0.0.0.0 \
    --port 1234 \
    --n_gpu_layers -1 &
```

### Step 4: Start Voxtral Application
```bash
# Terminal 2: Start Voxtral with Orpheus integration
./deploy_voxtral_tts.sh
```

## How It Works

### 1. Voxtral Processing
```
User Speech → Voxtral Model:
  ├── VAD: Voice Activity Detection
  ├── ASR: Speech-to-Text
  └── LLM: Text Generation
```

### 2. Orpheus-FastAPI Communication
```python
# Voxtral generates text response
response_text = "Hello, this is the AI response"

# Send to Orpheus-FastAPI
payload = {
    "text": response_text,
    "voice": "ऋतिका",
    "language": "hi"
}

# HTTP POST to Orpheus-FastAPI
audio_data = await http_client.post(
    "http://localhost:1234/generate_speech",
    json=payload
)
```

### 3. Audio Playback
```
Orpheus-FastAPI → WAV Audio → Base64 Encoding → WebSocket → Browser → Audio Playback
```

## Configuration

### Environment Variables (.env)
```bash
# Orpheus-FastAPI Configuration
ORPHEUS_SERVER_URL=http://localhost:1234
ORPHEUS_MODEL_PATH=/workspace/models/Orpheus-3b-FT-Q8_0.gguf
ORPHEUS_DEFAULT_VOICE=ऋतिका

# Server Ports
VOXTRAL_PORT=8000
ORPHEUS_PORT=1234
```

### Config.yaml
```yaml
tts:
  engine: "orpheus-fastapi"
  default_voice: "ऋतिका"
  sample_rate: 24000
  orpheus_server:
    host: "localhost"
    port: 1234
    timeout: 30
```

## Testing

### Test Orpheus-FastAPI Server
```bash
python3 test_orpheus_fastapi.py
```

### Test Complete Integration
```bash
python3 test_voxtral_orpheus_integration.py
```

### Manual API Test
```bash
# Test Orpheus-FastAPI directly
curl -X POST http://localhost:1234/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "ऋतिका: Hello world",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## Voice Configuration

### Default Voice: ऋतिका
The system is configured to use ऋतिका (Hindi) voice throughout:

- **TTS Engine**: `self.default_voice = "ऋतिका"`
- **UI Server**: `voice="ऋतिका"`
- **Config**: `default_voice: "ऋतिका"`

### Voice Mapping
```python
voice_language_map = {
    "ऋतिका": "hi",  # Hindi
    "tara": "en",    # English
    "pierre": "fr",  # French
    # ... other voices
}
```

## Troubleshooting

### Orpheus-FastAPI Server Issues
```bash
# Check if server is running
curl http://localhost:1234/v1/models

# Check server logs
tail -f /workspace/logs/orpheus_fastapi.log

# Restart server
pkill -f llama_cpp.server
./start_orpheus_fastapi.sh
```

### Model Issues
```bash
# Verify model file
ls -la /workspace/models/Orpheus-3b-FT-Q8_0.gguf

# Check model size (should be ~3.8GB)
du -h /workspace/models/Orpheus-3b-FT-Q8_0.gguf
```

### Integration Issues
```bash
# Test HTTP communication
python3 -c "
import requests
response = requests.get('http://localhost:1234/v1/models')
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:200]}...')
"
```

### Port Conflicts
```bash
# Check what's using port 1234
lsof -i :1234

# Kill process on port 1234
lsof -ti:1234 | xargs kill -9
```

## Performance Optimization

### For Better Quality
- Use full precision model (not quantized)
- Increase context size
- Use more GPU layers

### For Faster Generation
- Use quantized model (Q4_K_M or Q8_0)
- Reduce max_tokens
- Optimize GPU memory allocation

### Orpheus-FastAPI Server Optimization
```bash
python -m llama_cpp.server \
    --model /workspace/models/Orpheus-3b-FT-Q8_0.gguf \
    --host 0.0.0.0 \
    --port 1234 \
    --n_gpu_layers -1 \
    --n_ctx 2048 \
    --n_batch 512 \
    --threads 8 \
    --verbose
```

## RunPod Deployment

### Port Configuration
- **Voxtral UI**: 8000 (HTTP)
- **Health Check**: 8005 (HTTP)
- **TCP Server**: 8766 (TCP)
- **Orpheus-FastAPI**: 1234 (HTTP, internal only)

### Access URLs
- **Web Interface**: `https://[POD_ID]-8000.proxy.runpod.net`
- **Health Check**: `https://[POD_ID]-8005.proxy.runpod.net/health`
- **WebSocket**: `wss://[POD_ID]-8000.proxy.runpod.net/ws`

### Startup Command
```bash
# Single command to start everything
./start_voxtral_with_orpheus.sh
```

## Expected Results

### When Working Correctly
```
🎵 Generating audio for text: 'Hello...' with voice 'ऋतिका'
🌐 Sending request to Orpheus-FastAPI: {'text': 'Hello...', 'voice': 'ऋतिका', 'language': 'hi'}
🎵 Received audio from Orpheus-FastAPI (156789 bytes)
✅ Audio generated with Orpheus-FastAPI (156789 bytes)
```

### In Browser
- High-quality ऋतिका voice audio
- Natural-sounding Hindi pronunciation
- Fast response times (<2 seconds)
- No fallback messages in logs

## File Structure

```
/workspace/
├── models/
│   └── Orpheus-3b-FT-Q8_0.gguf          # Orpheus TTS model
├── orpheus_fastapi/
│   └── Orpheus-FastAPI/                  # Cloned repository
├── logs/
│   └── orpheus_fastapi.log               # Server logs
├── setup_orpheus_fastapi.sh              # Setup script
├── start_orpheus_fastapi.sh              # Start Orpheus server
├── start_voxtral_with_orpheus.sh         # Start complete system
├── test_orpheus_fastapi.py               # Test Orpheus server
├── test_voxtral_orpheus_integration.py   # Test integration
└── .env                                  # Environment config
```

## API Endpoints

### Orpheus-FastAPI (Port 1234)
- **Models**: `GET /v1/models`
- **Completion**: `POST /v1/completions`
- **Chat**: `POST /v1/chat/completions`

### Voxtral Application (Port 8000)
- **Web UI**: `GET /`
- **WebSocket**: `WS /ws`
- **Health**: `GET /health` (port 8005)

## Next Steps

1. **Run Setup**: `./setup_orpheus_fastapi.sh`
2. **Start System**: `./start_voxtral_with_orpheus.sh`
3. **Test Integration**: `python3 test_voxtral_orpheus_integration.py`
4. **Access Web UI**: Open your RunPod URL
5. **Test Voice**: Speak and listen for ऋतिका voice responses

The system now provides **real Orpheus TTS** with the ऋतिका voice using the correct architecture!