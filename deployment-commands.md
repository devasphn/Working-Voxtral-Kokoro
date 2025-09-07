# Voxtral Real-time Streaming - RunPod Deployment Commands

## 1. Initial Setup Commands

# Connect to your RunPod terminal and run these commands:

# Update system and install dependencies
sudo apt-get update && sudo apt-get install -y portaudio19-dev libasound2-dev libsndfile1-dev ffmpeg sox git

# Clone or upload your project files to /workspace
cd /workspace

# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh

## 2. RunPod Pod Configuration

# When creating your RunPod pod, use these settings:

# Template: PyTorch (or Custom)
# GPU: RTX A4500 (as requested)
# Container Disk: 50GB minimum (for model cache)
# Volume: 20GB (optional, for persistent logs)

# Expose these ports in RunPod:
# - HTTP Ports: 8000, 8005 
# - TCP Ports: 8765, 8766

## 3. Environment Variables (Optional)

export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

## 4. Starting the Server

# Make run script executable
chmod +x run.sh

# Option 1: Start all services
./run.sh

# Option 2: Start individual components
python -m src.api.health_check &
uvicorn src.api.ui_server:app --host 0.0.0.0 --port 8000 &
python -m src.streaming.websocket_server &
python -m src.streaming.tcp_server &

## 5. Testing the Setup

# Test health endpoint
curl http://localhost:8005/health

# Test status endpoint  
curl http://localhost:8005/status

# Access web UI
# Open: http://[your-pod-id]-8000.proxy.runpod.net

## 6. Accessing Your Services

# Web UI: https://[POD_ID]-8000.proxy.runpod.net
# Health Check: https://[POD_ID]-8005.proxy.runpod.net/health
# WebSocket: ws://[POD_ID]-8765.proxy.runpod.net (via HTTP proxy)
# TCP: Connect directly to RunPod public IP on assigned port

## 7. Monitoring

# View logs
tail -f /workspace/logs/voxtral_streaming.log

# Monitor GPU usage
nvidia-smi

# Monitor system resources
htop

## 8. Troubleshooting

# If model download fails:
python -c "from transformers import VoxtralForConditionalGeneration, AutoProcessor; VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507')"

# If audio processing fails:
python -c "import librosa, torch, torchaudio; print('Audio libraries OK')"

# If ports are not accessible:
# Check RunPod pod configuration - ensure ports are exposed
# Bind to 0.0.0.0, not 127.0.0.1

# If GPU not detected:
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

## 9. Performance Optimization

# For lower latency:
# - Use torch.compile() (enabled automatically if available)
# - Reduce max_new_tokens in model generation
# - Use smaller audio chunks
# - Enable mixed precision training

## 10. Scaling (Optional)

# For multiple instances:
# - Use a load balancer
# - Implement session affinity for WebSocket connections
# - Use external storage for model cache
# - Monitor memory usage across instances

## QUICK START SUMMARY:
1. Upload all files to /workspace on RunPod
2. Run: chmod +x setup.sh && ./setup.sh
3. Run: chmod +x run.sh && ./run.sh
4. Access UI at: https://[POD_ID]-8000.proxy.runpod.net
5. WebSocket: ws://[POD_ID]-8765.proxy.runpod.net

Required RunPod Settings:
- GPU: RTX A4500
- HTTP Ports: 8000, 8005
- TCP Ports: 8765, 8766
- Container Disk: 50GB minimum