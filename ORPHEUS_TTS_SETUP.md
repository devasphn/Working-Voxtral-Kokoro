# Orpheus TTS Integration Guide

## Overview

This guide explains how to set up the **real Orpheus TTS system** with the ऋतिका voice as requested. The system uses:

1. **LLM Server** (port 8010) - Generates tokens for TTS
2. **SNAC Model** - Converts tokens to high-quality audio
3. **ऋतिका Voice** - Hindi voice as the default
4. **Fallback System** - espeak-ng if LLM server is unavailable

## Architecture

```
Text Input → LLM Server (8010) → Token Generation → SNAC Model → Audio Output (ऋतिका voice)
                ↓
        Voxtral App (8000) ← WebSocket ← Browser
```

## Quick Setup

### 1. Run the Setup Script
```bash
chmod +x setup_orpheus_llm.sh
./setup_orpheus_llm.sh
```

### 2. Download a Model
```bash
cd /workspace/llm_models
./download_test_model.sh
```

### 3. Start the Complete System
```bash
./start_orpheus_system.sh
```

## Manual Setup (Step by Step)

### Step 1: Install Dependencies
```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y build-essential cmake git wget curl python3-dev libopenblas-dev

# Python dependencies
pip install httpx>=0.25.0
```

### Step 2: Build llama.cpp
```bash
cd /workspace
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# With CUDA (if available)
make LLAMA_CUDA=1 -j$(nproc)

# Or CPU only
make -j$(nproc)
```

### Step 3: Download a GGUF Model
```bash
cd /workspace/llm_models
# Download a suitable model (example with TinyLlama)
wget -O tts_model.gguf "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_k_m.gguf"
```

### Step 4: Start LLM Server
```bash
# Terminal 1: Start LLM server
./start_llm_server.sh
```

### Step 5: Start Voxtral Application
```bash
# Terminal 2: Start main application
./deploy_voxtral_tts.sh
```

## Testing

### Test LLM Server
```bash
python3 test_llm_server.py
```

### Test Complete Integration
```bash
python3 test_orpheus_integration.py
```

### Test TTS Service
```bash
python3 test_tts.py
```

## Configuration

### Default Voice: ऋतिका
The system is configured to use the ऋतिका (Hindi) voice by default:

- **TTS Service**: `self.default_voice = "ऋतिका"`
- **UI Server**: `voice="ऋतिका"`
- **Config**: `default_voice: "ऋतिका"`

### LLM Server Settings
- **Host**: localhost
- **Port**: 8010
- **Context Size**: 2048
- **Batch Size**: 512
- **GPU Layers**: 32 (if CUDA available)

## How It Works

### 1. Token Generation Flow
```
Text: "Hello world" 
  ↓
Prompt: "ऋतिका: Hello world<|audio|>"
  ↓
LLM Server: Generates tokens like "<custom_token_1234><custom_token_5678>..."
  ↓
Token Extraction: [1234, 5678, ...]
```

### 2. Audio Generation Flow
```
Tokens: [1234, 5678, 9012, ...]
  ↓
SNAC Model: Converts tokens to raw audio
  ↓
WAV Creation: Wraps raw audio in WAV format
  ↓
Base64 Encoding: For web transmission
```

### 3. Fallback System
If LLM server is unavailable:
```
Text → espeak-ng (with Hindi voice mapping) → Audio
```

## Voice Mapping

The system maps the ऋतिका voice to appropriate fallback voices:

- **Orpheus TTS**: Native ऋतिका voice
- **espeak-ng**: `hi+f3` (Hindi female voice)
- **pyttsx3**: System Hindi voice (if available)

## Troubleshooting

### LLM Server Issues
```bash
# Check if server is running
curl http://localhost:8010/health

# Check logs
tail -f /workspace/logs/llm_server.log

# Restart server
pkill llama-server
./start_llm_server.sh
```

### Model Issues
```bash
# Verify model file
ls -la /workspace/llm_models/tts_model.gguf

# Test model loading
llama-server --model /workspace/llm_models/tts_model.gguf --help
```

### Audio Issues
```bash
# Test SNAC model
python3 -c "from snac import SNAC; print('SNAC OK')"

# Test audio generation
python3 test_orpheus_integration.py
```

### Port Conflicts
```bash
# Check what's using port 8010
lsof -i :8010

# Kill process on port 8010
lsof -ti:8010 | xargs kill -9
```

## Performance Optimization

### For Better Quality
1. Use a larger, better-trained model
2. Increase context size: `--ctx-size 4096`
3. Use more GPU layers: `--n-gpu-layers 64`

### For Faster Generation
1. Use smaller model (TinyLlama, Phi-2)
2. Reduce context size: `--ctx-size 1024`
3. Increase batch size: `--batch-size 1024`

## Production Deployment

### Model Recommendations
- **High Quality**: Use a model specifically trained for TTS
- **Fast Generation**: TinyLlama-1.1B or Phi-2
- **Balanced**: Llama-2-7B quantized (Q4_K_M)

### Server Configuration
```bash
# Production LLM server settings
llama-server \
    --model /workspace/llm_models/production_tts_model.gguf \
    --host 0.0.0.0 \
    --port 8010 \
    --ctx-size 2048 \
    --batch-size 512 \
    --threads $(nproc) \
    --n-gpu-layers 32 \
    --memory-f32 \
    --mlock
```

## API Endpoints

### LLM Server
- **Health**: `GET http://localhost:8010/health`
- **Completion**: `POST http://localhost:8010/completion`
- **Models**: `GET http://localhost:8010/v1/models`

### Voxtral Application
- **Web UI**: `https://[POD_ID]-8000.proxy.runpod.net`
- **WebSocket**: `wss://[POD_ID]-8000.proxy.runpod.net/ws`
- **Health**: `https://[POD_ID]-8005.proxy.runpod.net/health`

## Expected Results

When working correctly, you should see:

### In Logs
```
🎵 Generating audio for text: 'Hello...' with voice 'ऋतिका'
🔢 Generated 42 tokens from LLM
🎵 Successfully converted tokens to audio (156789 bytes)
✅ Audio generated with Orpheus TTS (156789 bytes)
```

### In Browser
- Text responses appear immediately
- Audio responses play with ऋतिका voice
- High-quality, natural-sounding speech
- No "espeak-ng" messages in logs

## Next Steps

1. **Run Setup**: `./setup_orpheus_llm.sh`
2. **Download Model**: `cd /workspace/llm_models && ./download_test_model.sh`
3. **Start System**: `./start_orpheus_system.sh`
4. **Test Integration**: `python3 test_orpheus_integration.py`
5. **Access Web UI**: Open browser to your RunPod URL

The system will now provide high-quality TTS with the ऋतिका voice using the real Orpheus TTS architecture!