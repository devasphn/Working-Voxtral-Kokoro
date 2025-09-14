# Complete Startup Guide for Voxtral + Orpheus-FastAPI

## Quick Start Commands

### 1. Make Scripts Executable
```bash
chmod +x make_executable.sh
./make_executable.sh
```

### 2. Start Orpheus-FastAPI Server (Terminal 1)
```bash
./start_orpheus_fastapi.sh
```
**Wait for this message:** `llama_server_context: model loaded`

### 3. Test Orpheus-FastAPI (Terminal 2)
```bash
python3 simple_orpheus_test.py
```
**Expected:** `🎉 Orpheus-FastAPI is working!`

### 4. Start Voxtral Application (Terminal 2)
```bash
./deploy_voxtral_tts.sh
```

## Step-by-Step Instructions

### Step 1: Fix Dependencies
```bash
# Fix numpy and h11 version conflicts
pip install numpy==1.26.0 h11==0.14.0
```

### Step 2: Make Scripts Executable
```bash
chmod +x start_orpheus_fastapi.sh
chmod +x start_voxtral_with_orpheus.sh
chmod +x test_orpheus_fastapi.py
chmod +x simple_orpheus_test.py
```

### Step 3: Start Orpheus-FastAPI Server
```bash
# Terminal 1: Start Orpheus server
./start_orpheus_fastapi.sh
```

**What to expect:**
- Model loading messages
- `llama_server_context: model loaded` (this means it's ready)
- Server listening on `http://0.0.0.0:1234`

### Step 4: Test Orpheus-FastAPI
```bash
# Terminal 2: Test the server
python3 simple_orpheus_test.py
```

**Expected output:**
```
🧪 Testing Orpheus-FastAPI connection...
✅ Orpheus-FastAPI server is running
🧪 Testing Orpheus-FastAPI completion...
✅ Completion successful: ...
🎉 Orpheus-FastAPI is working!
```

### Step 5: Start Voxtral Application
```bash
# Terminal 2: Start Voxtral with Orpheus integration
./deploy_voxtral_tts.sh
```

**What to expect:**
- Voxtral model loading
- TTS service initialization with Orpheus-FastAPI
- Web server starting on port 8000

## Verification

### Check Orpheus-FastAPI is Running
```bash
curl http://localhost:1234/v1/models
```

### Check Voxtral is Running
```bash
curl http://localhost:8000/health
```

### Test Complete Integration
```bash
# After both services are running
python3 test_voxtral_orpheus_integration.py
```

## Expected Log Messages

### Orpheus-FastAPI Startup
```
🚀 Starting Orpheus-FastAPI Server
📍 Model: /workspace/models/Orpheus-3b-FT-Q8_0.gguf
🌐 Host: 0.0.0.0
🔌 Port: 1234

llama_model_loader: loaded meta data with 20 key-value pairs
llama_server_context: model loaded
```

### Voxtral with Orpheus Integration
```
🚀 Initializing Orpheus TTS Engine...
✅ Connected to Orpheus-FastAPI server
🎉 Orpheus TTS Engine initialized
✅ TTS service pre-loaded successfully
```

### Working TTS Generation
```
🎵 Generating audio for text: 'Hello...' with voice 'ऋतिका'
🌐 Sending request to Orpheus-FastAPI
🎵 Received audio from Orpheus-FastAPI (156789 bytes)
✅ Audio generated with Orpheus-FastAPI
```

## Troubleshooting

### Port 1234 Already in Use
```bash
# Kill existing process
lsof -ti:1234 | xargs kill -9
# Then restart
./start_orpheus_fastapi.sh
```

### Model Not Found
```bash
# Check if model exists
ls -la /workspace/models/Orpheus-3b-FT-Q8_0.gguf
# If missing, re-run setup
./setup_orpheus_fastapi.sh
```

### Import Errors
```bash
# Fix numpy version conflict
pip install numpy==1.26.0 h11==0.14.0
```

### Connection Refused
```bash
# Check if Orpheus-FastAPI is running
curl http://localhost:1234/v1/models
# If not, start it first
./start_orpheus_fastapi.sh
```

## File Structure After Setup

```
/workspace/Voxtral-Final/
├── start_orpheus_fastapi.sh          # Start Orpheus server
├── start_voxtral_with_orpheus.sh     # Start complete system
├── test_orpheus_fastapi.py           # Test Orpheus server
├── simple_orpheus_test.py            # Simple connection test
├── test_voxtral_orpheus_integration.py # Full integration test
├── deploy_voxtral_tts.sh              # Start Voxtral app
└── src/tts/orpheus_tts_engine.py     # Orpheus integration code

/workspace/models/
└── Orpheus-3b-FT-Q8_0.gguf          # 3.8GB Orpheus model

/workspace/logs/
└── orpheus_fastapi.log               # Server logs
```

## Success Indicators

✅ **Orpheus-FastAPI Ready**: `llama_server_context: model loaded`
✅ **Connection Test**: `🎉 Orpheus-FastAPI is working!`
✅ **Voxtral Integration**: `✅ Connected to Orpheus-FastAPI server`
✅ **TTS Working**: `✅ Audio generated with Orpheus-FastAPI`
✅ **Web Interface**: Browser shows voice controls
✅ **Audio Playback**: Hear ऋतिका voice responses

## Access URLs

- **Web Interface**: `https://[POD_ID]-8000.proxy.runpod.net`
- **Health Check**: `https://[POD_ID]-8005.proxy.runpod.net/health`
- **Orpheus-FastAPI**: `http://localhost:1234` (internal only)

## Final Test

1. Open web interface in browser
2. Click "Connect" → WebSocket connected
3. Click "Start Conversation" → Models loaded
4. Speak into microphone → Voice detected
5. See text response → Voxtral working
6. **Hear ऋतिका voice response** → Orpheus-FastAPI working!

The system is working when you hear high-quality Hindi voice responses from ऋतिका!