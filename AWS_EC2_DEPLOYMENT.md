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

### Inbound Rules (CRITICAL - Must be configured):
```
Protocol | Port/Range      | Source        | Purpose
---------|-----------------|---------------|------------------
TCP      | 22              | Your IP/0.0.0 | SSH access
TCP      | 80              | 0.0.0.0/0     | HTTP (redirect to HTTPS)
TCP      | 443             | 0.0.0.0/0     | HTTPS (WebRTC signaling)
TCP      | 8000            | 0.0.0.0/0     | FastAPI WebSocket/HTTP (CRITICAL)
TCP      | 3000-3100       | 0.0.0.0/0     | WebRTC data channels
UDP      | 3000-3100       | 0.0.0.0/0     | WebRTC media (RTP/RTCP)
UDP      | 5000-6000       | 0.0.0.0/0     | STUN/TURN (optional)
```

**⚠️ CRITICAL**: Port 8000 MUST be open for WebSocket connections. If this port is not open, you will get WebSocket error 1006 (abnormal closure).

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
sudo apt install -y build-essential git curl wget python3 python3-venv python3-dev
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev
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
python3 -m venv voxtral_env
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
pip install pyaudio
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

## 4.5 HTTPS SETUP (REQUIRED for Microphone Access)

**⚠️ CRITICAL**: Browsers require HTTPS for microphone access on remote servers (except localhost).

### Quick Start: Test with Localhost (Fastest)

If you want to test immediately without setting up HTTPS:

```bash
# On your local machine, SSH with port forwarding
ssh -i your-key.pem -L 8000:localhost:8000 ubuntu@98.89.99.129

# Then access via browser
http://localhost:8000/

# Microphone will work (localhost is allowed over HTTP)
```

### Option A: Using Let's Encrypt (Recommended - Free)

```bash
# 1. Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. Get certificate (replace example.com with your domain)
sudo certbot certonly --standalone -d example.com -d www.example.com

# 3. Create nginx config
sudo tee /etc/nginx/sites-available/voxtral > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}
EOF

# 4. Enable nginx config
sudo ln -sf /etc/nginx/sites-available/voxtral /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 5. Auto-renew certificates
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Option B: Using Self-Signed Certificate (Development Only)

```bash
# 1. Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/voxtral.key \
  -out /etc/ssl/certs/voxtral.crt \
  -subj "/CN=98.89.99.129"

# 2. Create nginx config
sudo tee /etc/nginx/sites-available/voxtral > /dev/null << 'EOF'
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/ssl/certs/voxtral.crt;
    ssl_certificate_key /etc/ssl/private/voxtral.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
}
EOF

# 3. Enable and restart nginx
sudo ln -sf /etc/nginx/sites-available/voxtral /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option C: Access via Localhost (Development Only)

If you don't want to set up HTTPS, you can access the application via localhost:

```bash
# 1. SSH into EC2 with port forwarding
ssh -i your-key.pem -L 8000:localhost:8000 ubuntu@98.89.99.129

# 2. Access via browser
http://localhost:8000/
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

### WebSocket Error 1006 (Abnormal Closure)

**Root Cause**: WebSocket connection fails without proper handshake. Usually caused by:
1. Port 8000 not open in Security Group
2. WebSocket URL missing port number
3. Server not listening on 0.0.0.0

**Fix**:
```bash
# 1. Verify Security Group allows port 8000
# Go to AWS Console > EC2 > Security Groups > Select your group
# Add inbound rule: TCP 8000 from 0.0.0.0/0

# 2. Verify server is running and listening
sudo netstat -tlnp | grep 8000
# Should show: tcp  0  0 0.0.0.0:8000  0.0.0.0:*  LISTEN

# 3. Test WebSocket connection from EC2
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws

# 4. Test from external machine
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://98.83.35.212:8000/ws
```

**Verification**:
1. Open browser console (F12)
2. Check WebSocket URL: Should be `ws://98.83.35.212:8000/ws` (with port)
3. Check server logs: `tail -f logs/voxtral_streaming.log`
4. Should see: `[CONVERSATION] Client connected: 98.83.35.212:xxxxx`

### Microphone Access Errors: "MediaDevices API not supported" or "getUserMedia undefined"

**Root Cause**: Browsers require HTTPS for microphone access on remote servers (except localhost).

**Error Details** (you may see one of these):
```
❌ Microphone Access Error: Your browser does not support the MediaDevices API
TypeError: Cannot read properties of undefined (reading 'getUserMedia')
    at startConversation ((index):1266:60)
```

**Why This Happens**:
1. You're accessing via HTTP (e.g., `http://98.89.99.129:8000/`)
2. Browsers block microphone access over HTTP for security reasons
3. When accessing via HTTP on remote server, browser HIDES `navigator.mediaDevices` API
4. This makes it appear as if the browser doesn't support the API
5. Exception: localhost and 127.0.0.1 are allowed over HTTP (API is available)

**Key Insight**: The error "MediaDevices API not supported" when accessing via HTTP on remote server actually means "HTTPS Required", not "browser incompatible"

**Solutions** (in order of preference):

**Option 1: Set up HTTPS (Recommended)**
```bash
# Follow the HTTPS setup instructions in Section 4.5
# Use Let's Encrypt for free SSL certificates
# Then access via: https://your-domain.com
```

**Option 2: Access via Localhost (Development)**
```bash
# SSH with port forwarding
ssh -i your-key.pem -L 8000:localhost:8000 ubuntu@98.89.99.129

# Access via browser
http://localhost:8000/
```

**Option 3: Use Self-Signed Certificate (Development)**
```bash
# Follow Option B in Section 4.5
# Then access via: https://98.89.99.129
# Note: Browser will show security warning (click "Advanced" > "Proceed")
```

**Verification**:
1. Open browser console (F12)
2. Look for log message:
   - ✅ If HTTPS: `🎯 [WEBSOCKET] URL detected: wss://...`
   - ❌ If HTTP on remote: `❌ Microphone Access Error: HTTPS Required`
3. Check browser address bar:
   - ✅ Should show `https://` (with lock icon)
   - ❌ Should NOT show `http://` (without lock icon)

### WebRTC Connection Issues
- Check Security Group rules
- Verify firewall allows UDP/TCP ports
- Check browser console for errors

---

**Status**: ✅ Production-Ready Deployment Guide

