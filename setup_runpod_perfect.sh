#!/bin/bash

echo "🚀 RunPod Perfect Voxtral + Orpheus TTS Setup"
echo "=============================================="
echo "Setting up production-ready real-time voice agent on RunPod"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on RunPod
check_runpod_environment() {
    print_step "Checking RunPod environment..."
    
    if [ -d "/workspace" ]; then
        print_status "✅ RunPod environment detected"
        export WORKSPACE_DIR="/workspace"
    else
        print_warning "⚠️ Not running on RunPod, using current directory"
        export WORKSPACE_DIR="$(pwd)"
    fi
    
    # Set environment variables for RunPod optimization
    export PYTHONPATH="${WORKSPACE_DIR}:${PYTHONPATH}"
    export HF_HOME="${WORKSPACE_DIR}/model_cache"
    export CUDA_VISIBLE_DEVICES=0
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
    export OMP_NUM_THREADS=8
    export TOKENIZERS_PARALLELISM=false
    
    # VLLM optimization for Orpheus TTS
    export VLLM_GPU_MEMORY_UTILIZATION=0.8
    export VLLM_MAX_MODEL_LEN=2048
    
    print_status "Environment variables configured for optimal performance"
}

# Check system requirements
check_system_requirements() {
    print_step "Checking system requirements..."
    
    # Check CUDA
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
        print_status "✅ CUDA available: $GPU_INFO"
        
        # Check VRAM
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
        VRAM_GB=$((VRAM_MB / 1024))
        
        if [ $VRAM_GB -ge 8 ]; then
            print_status "✅ Sufficient VRAM: ${VRAM_GB}GB (minimum 8GB required)"
        else
            print_error "❌ Insufficient VRAM: ${VRAM_GB}GB (minimum 8GB required)"
            exit 1
        fi
    else
        print_error "❌ CUDA not available. This setup requires a GPU."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "✅ Python version: $PYTHON_VERSION"
    
    # Check disk space
    DISK_SPACE=$(df -h . | awk 'NR==2 {print $4}')
    print_status "✅ Available disk space: $DISK_SPACE"
}

# Install system dependencies
install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update package list
    apt-get update -qq
    
    # Install essential packages
    apt-get install -y -qq \
        build-essential \
        cmake \
        git \
        wget \
        curl \
        unzip \
        ffmpeg \
        libsndfile1 \
        portaudio19-dev \
        python3-dev \
        python3-pip
    
    print_status "✅ System dependencies installed"
}

# Setup Python environment
setup_python_environment() {
    print_step "Setting up Python environment..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip setuptools wheel
    
    # Install PyTorch with CUDA support (RunPod compatible)
    print_status "Installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    print_status "✅ PyTorch with CUDA installed"
}

# Install exact package versions
install_exact_packages() {
    print_step "Installing exact package versions for compatibility..."
    
    # Core AI/ML packages with exact versions
    pip install \
        transformers==4.54.0 \
        accelerate==0.25.0 \
        tokenizers==0.15.0 \
        "mistral-common[audio]>=1.4.0" \
        librosa==0.10.1 \
        soundfile==0.12.1 \
        numpy==1.24.0 \
        scipy==1.11.0
    
    print_status "✅ Core AI/ML packages installed"
    
    # Install Orpheus TTS
    print_status "Installing Orpheus TTS..."
    pip install orpheus-speech
    
    # Check for vllm version compatibility
    pip install "vllm>=0.7.3,<0.8.0"
    
    print_status "✅ Orpheus TTS installed"
    
    # Web framework packages
    pip install \
        fastapi==0.104.0 \
        "uvicorn[standard]==0.24.0" \
        websockets==12.0 \
        pydantic==2.5.0 \
        pydantic-settings==2.1.0 \
        python-multipart==0.0.6 \
        aiofiles==23.2.1 \
        httpx==0.25.0
    
    print_status "✅ Web framework packages installed"
    
    # Utility packages
    pip install \
        pyyaml==6.0.1 \
        python-dotenv==1.0.0 \
        psutil==5.9.0 \
        huggingface-hub==0.19.0
    
    print_status "✅ Utility packages installed"
    
    # Testing packages
    pip install \
        pytest==7.4.0 \
        pytest-asyncio==0.21.0
    
    print_status "✅ Testing packages installed"
}

# Create necessary directories
create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p "${WORKSPACE_DIR}/logs"
    mkdir -p "${WORKSPACE_DIR}/model_cache"
    mkdir -p "${WORKSPACE_DIR}/temp"
    
    print_status "✅ Directories created"
}

# Download and cache models
download_models() {
    print_step "Downloading and caching models..."
    
    # Download Voxtral model
    print_status "Downloading Voxtral model (this may take several minutes)..."
    python3 -c "
from transformers import AutoProcessor, VoxtralForConditionalGeneration
import os

model_name = 'mistralai/Voxtral-Mini-3B-2507'
cache_dir = '${WORKSPACE_DIR}/model_cache'

print('Downloading Voxtral processor...')
processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
print('✅ Voxtral processor downloaded')

print('Downloading Voxtral model...')
model = VoxtralForConditionalGeneration.from_pretrained(
    model_name,
    cache_dir=cache_dir,
    torch_dtype='bfloat16',
    device_map='auto',
    low_cpu_mem_usage=True,
    trust_remote_code=True
)
print('✅ Voxtral model downloaded')
"
    
    print_status "✅ Voxtral model cached"
    
    # Pre-load Orpheus model
    print_status "Pre-loading Orpheus model..."
    python3 -c "
from orpheus_tts import OrpheusModel
import os

model_name = 'canopylabs/orpheus-tts-0.1-finetune-prod'
print('Pre-loading Orpheus model...')
model = OrpheusModel(model_name=model_name)
print('✅ Orpheus model pre-loaded')
"
    
    print_status "✅ Models downloaded and cached"
}

# Test the installation
test_installation() {
    print_step "Testing installation..."
    
    # Test imports
    python3 -c "
import torch
import transformers
import mistral_common
import orpheus_tts
import fastapi
import websockets

print('✅ All packages imported successfully')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device: {torch.cuda.get_device_name(0)}')
    print(f'CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB')
"
    
    # Test the perfect system
    if [ -f "test_perfect_system.py" ]; then
        print_status "Running system integration test..."
        python3 test_perfect_system.py
    else
        print_warning "⚠️ test_perfect_system.py not found, skipping integration test"
    fi
    
    print_status "✅ Installation test completed"
}

# Create RunPod startup script
create_startup_script() {
    print_step "Creating RunPod startup script..."
    
    cat > "${WORKSPACE_DIR}/start_runpod.sh" << 'EOF'
#!/bin/bash

echo "🚀 Starting Voxtral + Orpheus TTS on RunPod"
echo "==========================================="

# Set environment variables
export PYTHONPATH="/workspace:${PYTHONPATH}"
export HF_HOME="/workspace/model_cache"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export VLLM_GPU_MEMORY_UTILIZATION=0.8
export VLLM_MAX_MODEL_LEN=2048

# Change to workspace directory
cd /workspace

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the perfect system
echo "🎯 Starting perfect system..."
python3 -m src.api.ui_server_realtime

EOF
    
    chmod +x "${WORKSPACE_DIR}/start_runpod.sh"
    print_status "✅ RunPod startup script created: ${WORKSPACE_DIR}/start_runpod.sh"
}

# Main installation process
main() {
    echo "Starting RunPod Perfect Setup..."
    echo "This will install and configure Voxtral + Orpheus TTS for production use"
    echo ""
    
    check_runpod_environment
    check_system_requirements
    install_system_dependencies
    setup_python_environment
    install_exact_packages
    create_directories
    download_models
    test_installation
    create_startup_script
    
    echo ""
    echo "🎉 RunPod Perfect Setup Completed Successfully!"
    echo "=============================================="
    echo ""
    echo "Next steps:"
    echo "1. Start the server: ./start_runpod.sh"
    echo "2. Access the UI at: http://localhost:8000"
    echo "3. For RunPod HTTP proxy: https://[POD_ID]-8000.proxy.runpod.net"
    echo "4. For RunPod WebSocket: wss://[POD_ID]-8000.proxy.runpod.net/ws"
    echo ""
    echo "The system is now ready for real-time voice conversations!"
}

# Run main function
main "$@"
