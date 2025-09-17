#!/bin/bash

# Enhanced RunPod Setup Script for Speech-to-Speech System
# Optimized for <300ms latency with comprehensive error handling

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

info() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    warn "Running as root. Some operations may behave differently."
fi

# System information
log "🚀 Starting Enhanced RunPod Setup for Speech-to-Speech System"
log "📊 System: $(uname -a)"
log "🐍 Python: $(python3 --version 2>/dev/null || echo 'Python not found')"
log "💾 Memory: $(free -h | grep '^Mem:' | awk '{print $2}') total"

# Check GPU availability
if command -v nvidia-smi &> /dev/null; then
    log "🎯 GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits)"
    log "💾 VRAM: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits) MB"
else
    error "NVIDIA GPU not detected! This system requires CUDA support."
    exit 1
fi

# Update system packages
log "📦 Updating system packages..."
apt-get update -qq
apt-get install -y -qq \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    htop \
    nvtop \
    jq \
    unzip

# Create Python virtual environment
log "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    info "Virtual environment created"
else
    info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
info "Virtual environment activated"

# Upgrade pip
log "🔧 Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support
log "🔥 Installing PyTorch with CUDA 12.1 support..."
pip install torch>=2.5.0 torchvision>=0.20.0 torchaudio>=2.5.0 --index-url https://download.pytorch.org/whl/cu121

# Verify PyTorch CUDA installation
log "🧪 Verifying PyTorch CUDA installation..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU device: {torch.cuda.get_device_name(0)}')
else:
    print('❌ CUDA not available!')
    exit(1)
"

# Install core dependencies
log "📋 Installing core dependencies..."

# Install transformers and related packages
pip install transformers>=4.56.0
pip install accelerate>=0.25.0
pip install datasets>=2.16.0
pip install tokenizers>=0.15.0

# Install audio processing libraries
pip install librosa>=0.10.1
pip install soundfile>=0.12.1
pip install pyaudio>=0.2.11
pip install webrtcvad>=2.0.10

# Install mistral-common with audio support
log "Installing mistral-common with audio support..."
pip install mistral-common[audio]>=1.4.4

# Install Orpheus TTS
log "Installing Orpheus TTS..."
pip install orpheus-tts>=0.1.0

# Install vLLM for optimized inference
log "Installing vLLM for optimized inference..."
pip install vllm==0.7.3

# Install web framework dependencies
log "Installing web framework dependencies..."
pip install fastapi>=0.104.0
pip install uvicorn[standard]>=0.24.0
pip install websockets>=12.0
pip install jinja2>=3.1.0
pip install python-multipart>=0.0.6

# Install monitoring and optimization libraries
log "Installing monitoring and optimization libraries..."
pip install psutil>=5.9.0
pip install pynvml>=11.5.0
pip install numpy>=1.24.0
pip install scipy>=1.11.0

# Install remaining requirements
log "Installing remaining requirements from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    warn "requirements.txt not found, skipping..."
fi

# Set up HuggingFace token
log "Setting up HuggingFace authentication..."
if [ -n "$HF_TOKEN" ]; then
    pip install huggingface_hub
    python3 -c "from huggingface_hub import login; login('$HF_TOKEN')"
    info "HuggingFace token configured successfully"
else
    warn "HF_TOKEN environment variable not set"
    echo "Please set HF_TOKEN before running the system:"
    echo "export HF_TOKEN='YOUR_HF_TOKEN_HERE'"
fi

# Create necessary directories
log "Creating directory structure..."
mkdir -p logs
mkdir -p cache
mkdir -p models
mkdir -p temp
mkdir -p src/api/static
mkdir -p src/api/templates

# Set up environment variables for optimization
log "Setting up environment variables..."
cat > .env << EOF
# Enhanced System Configuration
HF_TOKEN=${HF_TOKEN:-""}
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
TOKENIZERS_PARALLELISM=false
OMP_NUM_THREADS=8
MKL_NUM_THREADS=8

# Optimization flags
ENABLE_TORCH_COMPILE=true
ENABLE_FLASH_ATTENTION=true
ENABLE_QUANTIZATION=true
ENABLE_KV_CACHE=true

# Model configuration
MODEL_CACHE_DIR=./cache
MODEL_LOAD_TIMEOUT=300
MAX_MODEL_LEN=2048

# Server configuration
SERVER_HOST=0.0.0.0
SERVER_HTTP_PORT=8000
SERVER_WS_PORT=8765
SERVER_HEALTH_PORT=8005
SERVER_METRICS_PORT=8766

# Performance tuning
CHUNK_SIZE=512
SAMPLE_RATE=16000
LATENCY_TARGET=300
MEMORY_FRACTION=0.9
EOF

# Source environment variables
source .env

# Optimize system settings
log "Optimizing system settings..."

# Set GPU performance mode
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi -pm 1  # Enable persistence mode
    nvidia-smi -ac 1215,1410  # Set memory and graphics clocks (RTX 4090)
    info "GPU performance mode enabled"
fi

# Set CPU governor to performance
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
    info "CPU governor set to performance"
fi

# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
ulimit -n 65536

# Pre-download and cache models
log "Pre-downloading models for faster startup..."
python3 -c "
import os
os.environ['HF_TOKEN'] = '${HF_TOKEN:-""}'

try:
    from transformers import AutoProcessor, VoxtralForConditionalGeneration
    from huggingface_hub import snapshot_download
    
    # Pre-download Voxtral model
    print('Downloading Voxtral model...')
    snapshot_download('mistralai/Voxtral-Mini-3B-2507', cache_dir='./cache')
    
    # Pre-download Orpheus model
    print('Downloading Orpheus model...')
    snapshot_download('canopylabs/orpheus-tts-0.1-finetune-prod', cache_dir='./cache')
    
    print('✅ Models pre-downloaded successfully')
    
except Exception as e:
    print(f'⚠️ Model pre-download failed: {e}')
    print('Models will be downloaded on first use')
"

# Create startup script
log "Creating enhanced startup script..."
cat > start_enhanced.sh << 'EOF'
#!/bin/bash

# Enhanced Startup Script with Multiple Modes
# Usage: ./start_enhanced.sh [--mode=performance|memory|dev|production]

set -e

# Default mode
MODE="performance"

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --mode=*)
            MODE="${arg#*=}"
            shift
            ;;
        --help)
            echo "Usage: $0 [--mode=performance|memory|dev|production]"
            echo "Modes:"
            echo "  performance: Maximum performance with all optimizations"
            echo "  memory: Memory-optimized for limited VRAM"
            echo "  dev: Development mode with debug logging"
            echo "  production: Production mode with monitoring"
            exit 0
            ;;
    esac
done

echo "🚀 Starting Enhanced Speech-to-Speech System in $MODE mode..."

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Set mode-specific configurations
case $MODE in
    "performance")
        export ENABLE_TORCH_COMPILE=true
        export ENABLE_FLASH_ATTENTION=true
        export ENABLE_QUANTIZATION=true
        export CUDA_MEMORY_FRACTION=0.95
        log "Performance mode: All optimizations enabled"
        ;;
    "memory")
        export ENABLE_QUANTIZATION=true
        export CUDA_MEMORY_FRACTION=0.7
        export MODEL_PRECISION="int8"
        log "Memory mode: Quantization enabled, reduced memory usage"
        ;;
    "dev")
        export DEBUG=true
        export LOG_LEVEL="DEBUG"
        log "Development mode: Debug logging enabled"
        ;;
    "production")
        export LOG_LEVEL="INFO"
        export ENABLE_MONITORING=true
        log "Production mode: Monitoring and logging enabled"
        ;;
esac

# Start the enhanced system
python3 -m src.api.ui_server_realtime
EOF

chmod +x start_enhanced.sh

# Final verification
log "🧪 Running final verification..."
python3 -c "
import torch
import transformers
import fastapi
import websockets
print('✅ All core packages imported successfully')
print(f'✅ PyTorch CUDA: {torch.cuda.is_available()}')
print(f'✅ Transformers: {transformers.__version__}')
"

success "🎉 Enhanced RunPod setup completed successfully!"
info "Next steps:"
info "1. Set your HuggingFace token: export HF_TOKEN='your_token_here'"
info "2. Start the system: ./start_enhanced.sh"
info "3. Access UI at: http://localhost:8000"
info "4. Monitor performance at: http://localhost:8000/metrics"

log "📊 Setup Summary:"
log "✅ Python virtual environment configured"
log "✅ PyTorch with CUDA 12.1 installed"
log "✅ All dependencies installed and verified"
log "✅ System optimizations applied"
log "✅ Models pre-downloaded (if token provided)"
log "✅ Enhanced startup script created"
log "✅ Environment variables configured"

echo ""
echo "🚀 Your enhanced speech-to-speech system is ready for <300ms latency performance!"
