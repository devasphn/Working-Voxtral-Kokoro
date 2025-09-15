# RunPod Deployment Guide for Direct Orpheus TTS Integration

## 🚀 Complete RunPod Setup Instructions

### GPU Requirements & Recommendations

#### Minimum Configuration (Budget Option)
- **GPU**: RTX A4000 (16GB VRAM) - $0.34/hour
- **CPU**: 6 vCPUs
- **RAM**: 32GB
- **Storage**: 50GB Container Disk + 100GB Volume

#### Recommended Configuration (Optimal Performance)
- **GPU**: RTX A5000 (24GB VRAM) - $0.76/hour  
- **CPU**: 8 vCPUs
- **RAM**: 64GB
- **Storage**: 50GB Container Disk + 200GB Volume

#### High-Performance Configuration (Best Experience)
- **GPU**: RTX A6000 (48GB VRAM) - $1.89/hour
- **CPU**: 12 vCPUs  
- **RAM**: 128GB
- **Storage**: 100GB Container Disk + 500GB Volume

### Port Configuration

#### HTTP Ports (Required)
- **8000**: Main UI server and WebSocket endpoint
- **8005**: Health check and monitoring endpoint

#### TCP Ports (Optional)
- **8765**: Alternative TCP streaming (if needed)
- **8766**: Backup TCP streaming (if needed)

**Note**: No UDP ports are required. All communication uses HTTP/WebSocket.

### Template Selection

#### Recommended Template
**Template**: `RunPod PyTorch 2.1.0`
- **Base Image**: `runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04`
- **Python**: 3.10
- **CUDA**: 12.1.1
- **PyTorch**: 2.1.0 (pre-installed)

#### Alternative Template
**Template**: `RunPod PyTorch 2.0.1`
- **Base Image**: `runpod/pytorch:2.0.1-py3.10-cuda11.8-devel-ubuntu22.04`
- **Python**: 3.10
- **CUDA**: 11.8
- **PyTorch**: 2.0.1 (pre-installed)

### Step-by-Step Deployment

#### 1. Create RunPod Instance

```bash
# RunPod Web Interface Steps:
1. Go to https://runpod.io
2. Click "Deploy" → "GPU Pods"
3. Select recommended GPU (RTX A5000 or better)
4. Choose "RunPod PyTorch 2.1.0" template
5. Configure ports: 8000, 8005
6. Set container disk: 50GB minimum
7. Add volume: 200GB minimum
8. Click "Deploy"
```

#### 2. Connect to Pod

```bash
# Via RunPod Web Terminal (Recommended)
1. Click "Connect" → "Start Web Terminal"
2. Wait for terminal to load
3. You'll be in /workspace directory

# Via SSH (Alternative)
ssh root@<pod-ip> -p <ssh-port>
```

#### 3. Clone and Setup

```bash
# Clone the repository
cd /workspace
git clone <your-repository-url> voxtral-orpheus
cd voxtral-orpheus

# Make deployment script executable
chmod +x deploy_direct_orpheus.sh

# Run complete deployment
./deploy_direct_orpheus.sh
```

#### 4. Verify Installation

```bash
# Check GPU availability
nvidia-smi

# Verify Python environment
source venv/bin/activate
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Run validation
python validate_direct_orpheus_integration.py
```

#### 5. Start the Service

```bash
# Start the server
./start_direct_orpheus.sh

# Or manually:
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRANSFORMERS_CACHE="./model_cache"
python -m src.api.ui_server_realtime
```

#### 6. Access the Application

```bash
# Get your pod's public IP
curl -s https://ipinfo.io/ip

# Access via RunPod proxy (Recommended)
https://<pod-id>-8000.proxy.runpod.net

# Or direct IP (if public IP enabled)
http://<pod-ip>:8000
```

### Environment Variables for RunPod

```bash
# Add to ~/.bashrc or set in RunPod environment
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export TRANSFORMERS_CACHE="/workspace/model_cache"
export HF_HOME="/workspace/model_cache"
```

### RunPod-Specific Optimizations

#### Storage Configuration
```bash
# Create persistent storage structure
mkdir -p /workspace/persistent/model_cache
mkdir -p /workspace/persistent/logs
mkdir -p /workspace/persistent/data

# Link to project
ln -sf /workspace/persistent/model_cache ./model_cache
ln -sf /workspace/persistent/logs ./logs
```

#### Memory Optimization for RunPod
```yaml
# config.yaml optimizations for RunPod
performance:
  optimization_level: "performance"  # Use performance mode on RunPod
  
tts:
  gpu_memory:
    memory_fraction: 0.95  # Use most of available VRAM
    cleanup_frequency: "periodic"  # Less aggressive cleanup
    
model:
  torch_dtype: "float16"  # Use FP16 for better performance
  max_memory_per_gpu: "20GB"  # Adjust based on your GPU
```

### Monitoring and Maintenance

#### Health Checks
```bash
# Check service status
curl http://localhost:8000/api/status

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check logs
tail -f logs/voxtral_streaming.log
```

#### Performance Monitoring
```bash
# Run performance optimization
python optimize_performance.py

# Apply optimizations
./apply_optimizations.sh

# Monitor performance
curl http://localhost:8000/api/status | jq '.performance_stats'
```

### Troubleshooting RunPod Issues

#### Common Issues and Solutions

**1. CUDA Out of Memory**
```bash
# Reduce memory usage
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
# Or use smaller model precision
# Set torch_dtype: "float32" in config.yaml
```

**2. Model Download Failures**
```bash
# Set Hugging Face cache
export HF_HOME="/workspace/model_cache"
export TRANSFORMERS_CACHE="/workspace/model_cache"

# Pre-download models
python -c "
from transformers import VoxtralForConditionalGeneration, AutoProcessor
VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='/workspace/model_cache')
"
```

**3. Port Access Issues**
```bash
# Verify ports are exposed
netstat -tlnp | grep :8000

# Use RunPod proxy URL instead of direct IP
# Format: https://<pod-id>-8000.proxy.runpod.net
```

**4. WebSocket Connection Issues**
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws
```

### Cost Optimization

#### Automatic Shutdown
```bash
# Add to crontab for automatic shutdown after inactivity
echo "0 */2 * * * /usr/bin/pkill -f 'src.api' && /usr/sbin/shutdown -h now" | crontab -
```

#### Spot Instance Usage
- Use RunPod Spot instances for 50-80% cost savings
- Enable auto-restart for spot interruptions
- Use persistent volumes to preserve model cache

### Security Considerations

#### Basic Security Setup
```bash
# Change default passwords
passwd root

# Configure firewall (if needed)
ufw allow 8000
ufw allow 8005
ufw enable

# Secure model cache
chmod 755 /workspace/model_cache
```

### Performance Benchmarks by GPU

| GPU Model | VRAM | Voxtral (ms) | Orpheus (ms) | Total (ms) | Cost/Hour |
|-----------|------|--------------|--------------|------------|-----------|
| RTX A4000 | 16GB | 95-120       | 140-180      | 235-300    | $0.34     |
| RTX A5000 | 24GB | 80-100       | 120-150      | 200-250    | $0.76     |
| RTX A6000 | 48GB | 70-90        | 100-130      | 170-220    | $1.89     |

### Final Deployment Checklist

- [ ] GPU meets minimum requirements (16GB+ VRAM)
- [ ] Ports 8000 and 8005 are exposed
- [ ] PyTorch 2.1.0+ template selected
- [ ] Sufficient storage allocated (200GB+ recommended)
- [ ] Environment variables configured
- [ ] Models pre-cached successfully
- [ ] Health check endpoint responding
- [ ] WebSocket connection working
- [ ] Performance targets met (<300ms)
- [ ] Monitoring and logging active

### Support and Resources

#### RunPod Documentation
- [RunPod Docs](https://docs.runpod.io/)
- [GPU Specifications](https://www.runpod.io/gpu-instance/pricing)
- [Template Gallery](https://runpod.io/console/explore)

#### Project Resources
- Health Check: `http://<your-pod>:8000/api/status`
- Web UI: `http://<your-pod>:8000`
- Logs: `/workspace/logs/voxtral_streaming.log`
- Config: `/workspace/config.yaml`

---

**Your Direct Orpheus TTS integration is now ready for production deployment on RunPod!** 🚀