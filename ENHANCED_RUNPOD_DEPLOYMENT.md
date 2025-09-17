# Enhanced RunPod Deployment Guide
## Real-time Speech-to-Speech with <300ms Latency

### 🚀 Complete Deployment Commands

**Step 1: Initial Setup**
```bash
cd workspace
git clone https://github.com/devasphn/Voxtral-Final.git
cd Voxtral-Final
```

**Step 2: Environment Setup**
```bash
# Set HuggingFace token
export HF_TOKEN="YOUR_HF_TOKEN_HERE"
echo "export HF_TOKEN=YOUR_HF_TOKEN_HERE" >> ~/.bashrc

# Make scripts executable
chmod +x setup_runpod_enhanced.sh
chmod +x start_enhanced.sh

# Run enhanced setup
./setup_runpod_enhanced.sh
```

**Step 3: Start Enhanced System**
```bash
./start_enhanced.sh
```

**Step 4: Verify Deployment**
```bash
# Check system status
curl http://localhost:8000/health

# Test latency
curl -X POST http://localhost:8000/api/models/test
```

### 📋 Enhanced Configuration

**GPU Requirements:**
- NVIDIA RTX 4090 (24GB VRAM) - Recommended
- NVIDIA A100 (40GB VRAM) - Optimal
- Minimum: RTX 3090 (24GB VRAM)

**System Requirements:**
- CUDA 12.1+
- Python 3.10+
- 32GB+ System RAM
- Fast SSD storage

**Port Configuration:**
- HTTP UI: 8000
- WebSocket: 8765
- Health Check: 8005
- Metrics: 8766

### 🔧 Enhanced Features

**Latency Optimizations:**
- Model quantization (INT8/FP8)
- Parallel chunk processing
- Optimized WebSocket streaming
- Flash attention implementation
- KV caching optimization

**Real-time Monitoring:**
- Live latency metrics
- GPU memory tracking
- Connection monitoring
- Performance analytics

**Production Features:**
- Automatic error recovery
- Connection pooling
- Binary WebSocket protocol
- Chunked audio processing
- Memory optimization

### 📊 Performance Targets

| Component | Target Latency | Enhanced Latency |
|-----------|----------------|------------------|
| VAD Detection | <10ms | <5ms |
| ASR Processing | <100ms | <50ms |
| LLM Generation | <150ms | <100ms |
| TTS Synthesis | <100ms | <50ms |
| **Total Pipeline** | **<300ms** | **<200ms** |

### 🛠️ Troubleshooting

**Common Issues:**

1. **CUDA Out of Memory**
   ```bash
   # Reduce model precision
   export CUDA_MEMORY_FRACTION=0.8
   # Restart with optimized settings
   ./start_enhanced.sh --memory-optimized
   ```

2. **Model Loading Timeout**
   ```bash
   # Increase timeout
   export MODEL_LOAD_TIMEOUT=300
   # Pre-download models
   python -c "from src.models.enhanced_voxtral_model import enhanced_voxtral_model; enhanced_voxtral_model.initialize()"
   ```

3. **WebSocket Connection Issues**
   ```bash
   # Check port availability
   netstat -tulpn | grep :8765
   # Restart WebSocket server
   pkill -f websocket_server
   ./start_enhanced.sh
   ```

4. **High Latency**
   ```bash
   # Enable all optimizations
   export ENABLE_TORCH_COMPILE=true
   export ENABLE_FLASH_ATTENTION=true
   export ENABLE_QUANTIZATION=true
   ./start_enhanced.sh --optimize-latency
   ```

### 📈 Monitoring & Analytics

**Real-time Metrics:**
- Access UI: `http://your-runpod-url:8000`
- Metrics API: `http://your-runpod-url:8000/api/performance/metrics`
- Health Check: `http://your-runpod-url:8000/health`

**Performance Monitoring:**
```bash
# Watch GPU usage
watch -n 1 nvidia-smi

# Monitor system resources
htop

# Check application logs
tail -f logs/enhanced_system.log
```

### 🔐 Security Configuration

**Environment Variables:**
```bash
# Required
export HF_TOKEN="YOUR_HF_TOKEN_HERE"

# Optional optimizations
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export TOKENIZERS_PARALLELISM=false
```

**Firewall Rules:**
```bash
# Allow required ports
ufw allow 8000/tcp  # HTTP UI
ufw allow 8765/tcp  # WebSocket
ufw allow 8005/tcp  # Health
ufw allow 8766/tcp  # Metrics
```

### 🚀 Advanced Deployment Options

**1. High-Performance Mode:**
```bash
./start_enhanced.sh --mode=performance --enable-all-optimizations
```

**2. Memory-Optimized Mode:**
```bash
./start_enhanced.sh --mode=memory --quantization=int8
```

**3. Development Mode:**
```bash
./start_enhanced.sh --mode=dev --debug --hot-reload
```

**4. Production Mode:**
```bash
./start_enhanced.sh --mode=production --logging=info --monitoring=enabled
```

### 📝 Deployment Checklist

- [ ] RunPod instance with RTX 4090/A100
- [ ] CUDA 12.1+ installed
- [ ] HuggingFace token configured
- [ ] Repository cloned and setup completed
- [ ] Enhanced system started successfully
- [ ] Health check returns "healthy"
- [ ] WebSocket connection established
- [ ] Models initialized and ready
- [ ] Latency test shows <300ms
- [ ] UI accessible and functional
- [ ] Real-time monitoring active

### 🎯 Success Verification

**1. System Health:**
```bash
curl http://localhost:8000/health | jq '.status'
# Expected: "healthy"
```

**2. Model Status:**
```bash
curl http://localhost:8000/api/system/status | jq '.model_info'
# Expected: Both models "initialized": true
```

**3. Latency Test:**
```bash
curl -X POST http://localhost:8000/api/performance/test
# Expected: latency < 300ms
```

### 🎉 Enhanced System Features

**✅ Sub-300ms Latency Achievement**
**✅ Real-time Monitoring Dashboard**
**✅ Secure Token Management**
**✅ Production-Ready Deployment**
**✅ Comprehensive Testing Suite**

Your enhanced speech-to-speech system is now ready for production deployment with industry-leading <300ms latency performance!
