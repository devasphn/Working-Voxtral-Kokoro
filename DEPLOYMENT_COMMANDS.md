# Complete Deployment Commands for Voxtral + Orpheus-FastAPI

## 🚀 **Step-by-Step Deployment Commands**

### 1. Initial Setup
```bash
cd /workspace
git clone https://github.com/devasphn/Voxtral-Final.git
cd Voxtral-Final
```

### 2. Make Scripts Executable
```bash
chmod +x deploy_voxtral_tts.sh
chmod +x setup_orpheus_fastapi.sh
chmod +x start_orpheus_fastapi.sh
```

### 3. Deploy Voxtral System
```bash
./deploy_voxtral_tts.sh
```

### 4. Fix Dependencies (if needed)
```bash
pip install h11==0.14.0 numpy==1.26.0
```

### 5. Setup Orpheus-FastAPI Server
```bash
./setup_orpheus_fastapi.sh
```

### 6. Start Orpheus-FastAPI Server (in background)
```bash
./start_orpheus_fastapi.sh &
```

### 7. Wait for Server to Start (30 seconds)
```bash
sleep 30
```

### 8. Debug Orpheus Response (IMPORTANT)
```bash
python debug_orpheus_response.py
python check_orpheus_model.py
```

# 9. Test Integration
```bash
python test_orpheus_integration.py
```

### 9. Start Main Voxtral System
```bash
python -m src.api.ui_server_realtime
```

## 🔧 **Troubleshooting Commands**

### Check if Orpheus Server is Running
```bash
curl http://localhost:1234/v1/models
```

### Check Server Logs
```bash
tail -f orpheus_server.log
```

### Restart Orpheus Server
```bash
pkill -f "orpheus"
./start_orpheus_fastapi.sh &
```

### Check Port Usage
```bash
netstat -tulpn | grep 1234
```

## 🎯 **Expected Results**

1. **Orpheus Server**: Should respond on port 1234
2. **Integration Test**: Should generate audio file `test_orpheus_output.wav`
3. **Main System**: Should use ऋतिका voice by default
4. **No Fallback**: System should fail gracefully if server unavailable

## 📝 **Important Notes**

- Orpheus-FastAPI server MUST be running before starting Voxtral
- Default voice is set to ऋतिका (Hindi)
- No fallback TTS systems are used
- All unnecessary test files have been removed