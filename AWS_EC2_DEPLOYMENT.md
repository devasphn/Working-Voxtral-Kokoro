# AWS EC2 Deployment Guide - Voxtral Conversational AI with WebRTC

## 1. INSTANCE SPECIFICATIONS

### Recommended Instance Type: **g5.xlarge**
- **GPU**: 1x NVIDIA A10G Tensor GPU (24GB VRAM)
- **vCPU**: 4 vCPU (Intel Xeon)
- **Memory**: 16 GB RAM
- **Network**: Up to 10 Gbps
- **Storage**: 100 GB EBS (gp3)
- **Cost**: ~$1.08/hour (on-demand)

**Why g5.xlarge?**
- A10G GPU has 24GB VRAM (sufficient for Voxtral-Mini-3B model)
- 4 vCPU handles concurrent WebRTC connections
- 16GB RAM for audio buffering and processing
- Cost-effective for production workloads

---

## 2. AMI SELECTION

### Recommended AMI: **Ubuntu 22.04 LTS (GPU-optimized)**
- **AMI ID**: `ami-0c55b159cbfafe1f0` (us-east-1, Ubuntu 22.04 LTS)
- **Architecture**: x86_64
- **Root Volume**: 100 GB gp3
- **Pre-installed**: NVIDIA drivers (optional, we'll install fresh)

**Alternative**: Amazon Linux 2 with GPU support (if preferred)

---

## 3. SECURITY GROUP CONFIGURATION

### Inbound Rules:
```
Protocol | Port/Range      | Source        | Purpose
---------|-----------------|---------------|------------------
TCP      | 22              | Your IP/0.0.0 | SSH access
TCP      | 80              | 0.0.0.0/0     | HTTP (redirect to HTTPS)
TCP      | 443             | 0.0.0.0/0     | HTTPS (WebRTC signaling)
TCP      | 3000-3100       | 0.0.0.0/0     | WebRTC data channels
UDP      | 3000-3100       | 0.0.0.0/0     | WebRTC media (RTP/RTCP)
TCP      | 8000            | 0.0.0.0/0     | FastAPI (internal)
UDP      | 5000-6000       | 0.0.0.0/0     | STUN/TURN (optional)
```

### Outbound Rules:
```
Protocol | Port/Range | Destination | Purpose
---------|------------|-------------|------------------
TCP      | 443        | 0.0.0.0/0   | HTTPS (model downloads)
TCP      | 80         | 0.0.0.0/0   | HTTP (package downloads)
UDP      | 53         | 0.0.0.0/0   | DNS
```

---

## 4. STEP-BY-STEP DEPLOYMENT COMMANDS

### Step 1: Connect to EC2 Instance
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

### Step 2: System Updates
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential git curl wget python3.10 python3.10-venv python3.10-dev
```

### Step 3: NVIDIA Driver Installation (for g5.xlarge GPU)
```bash
# Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA driver
sudo apt update
sudo apt install -y nvidia-driver-535
sudo reboot
```

### Step 4: CUDA Toolkit Installation (after reboot)
```bash
# Verify GPU is detected
nvidia-smi

# Install CUDA 12.1
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
sudo apt update
sudo apt install -y cuda-12-1
```

### Step 5: Python Virtual Environment
```bash
cd /home/ubuntu
python3.10 -m venv voxtral_env
source voxtral_env/bin/activate
pip install --upgrade pip setuptools wheel
```

### Step 6: Clone Repository
```bash
git clone https://github.com/devasphn/Working-Voxtral-Kokoro.git
cd Working-Voxtral-Kokoro
```

### Step 7: Install Dependencies
```bash
source ~/voxtral_env/bin/activate
pip install -r requirements.txt
```

### Step 8: Create Directory Structure
```bash
mkdir -p logs models cache
chmod 755 logs models cache
```

### Step 9: Environment Configuration
```bash
# Create .env file
cat > .env << 'EOF'
CUDA_VISIBLE_DEVICES=0
PYTHONUNBUFFERED=1
HF_HOME=/home/ubuntu/Working-Voxtral-Kokoro/cache
TRANSFORMERS_CACHE=/home/ubuntu/Working-Voxtral-Kokoro/cache
EOF

# Set environment variables
export CUDA_VISIBLE_DEVICES=0
export PYTHONUNBUFFERED=1
export HF_HOME=/home/ubuntu/Working-Voxtral-Kokoro/cache
export TRANSFORMERS_CACHE=/home/ubuntu/Working-Voxtral-Kokoro/cache
```

### Step 10: Start Application (Development)
```bash
source ~/voxtral_env/bin/activate
cd /home/ubuntu/Working-Voxtral-Kokoro
python3 -m src.api.ui_server_realtime
```

### Step 11: Production Deployment (Systemd Service)
```bash
# Create systemd service file
sudo tee /etc/systemd/system/voxtral.service > /dev/null << 'EOF'
[Unit]
Description=Voxtral Conversational AI with WebRTC
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Working-Voxtral-Kokoro
Environment="PATH=/home/ubuntu/voxtral_env/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="PYTHONUNBUFFERED=1"
Environment="HF_HOME=/home/ubuntu/Working-Voxtral-Kokoro/cache"
ExecStart=/home/ubuntu/voxtral_env/bin/python3 -m src.api.ui_server_realtime
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable voxtral
sudo systemctl start voxtral
sudo systemctl status voxtral
```

### Step 12: Verify Deployment
```bash
# Check service status
sudo systemctl status voxtral

# Check logs
sudo journalctl -u voxtral -f

# Test API endpoint
curl http://localhost:8000/health

# Check GPU usage
nvidia-smi
```

---

## 5. VERIFICATION STEPS

### Health Check
```bash
curl -X GET http://your-instance-ip:8000/health
```

### Expected Response:
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "unified_system": {
    "initialized": true,
    "voxtral_ready": true
  }
}
```

### WebRTC Connection Test
1. Open browser: `https://your-instance-ip`
2. Click "Connect"
3. Click "Start Conversation"
4. Speak naturally
5. Verify AI responds conversationally

---

## 6. MONITORING & MAINTENANCE

### View Logs
```bash
sudo journalctl -u voxtral -f --lines=100
```

### Monitor GPU
```bash
watch -n 1 nvidia-smi
```

### Restart Service
```bash
sudo systemctl restart voxtral
```

### Stop Service
```bash
sudo systemctl stop voxtral
```

---

## 7. COST OPTIMIZATION

- **Reserved Instances**: Save 40% with 1-year commitment
- **Spot Instances**: Save 70% (for non-critical workloads)
- **Auto-scaling**: Scale down during off-peak hours
- **Data Transfer**: Use CloudFront CDN for static assets

---

## 8. TROUBLESHOOTING

### GPU Not Detected
```bash
nvidia-smi  # Should show GPU info
lspci | grep -i nvidia  # Should list GPU
```

### Out of Memory
```bash
# Reduce max_memory_per_gpu in config.yaml
# Or use smaller model variant
```

### WebRTC Connection Issues
- Check Security Group rules
- Verify firewall allows UDP/TCP ports
- Check browser console for errors

---

**Status**: ✅ Production-Ready Deployment Guide

