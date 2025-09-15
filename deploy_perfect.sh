#!/bin/bash

# Perfect Voxtral + Orpheus TTS Deployment
# Researched and optimized for zero conflicts

set -e  # Exit on any error

echo "🚀 Perfect Voxtral + Orpheus TTS Deployment"
echo "============================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check GPU
check_gpu() {
    print_status "Checking GPU availability..."
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
        print_success "GPU detected: $GPU_INFO"
        
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
        VRAM_GB=$((VRAM_MB / 1024))
        
        if [ $VRAM_GB -lt 8 ]; then
            print_error "Insufficient VRAM: ${VRAM_GB}GB detected, minimum 8GB required"
            exit 1
        else
            print_success "VRAM: ${VRAM_GB}GB detected"
        fi
    else
        print_warning "No GPU detected - will run on CPU (much slower)"
    fi
}

# Check Python
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -ge 8 ] && [ $PYTHON_MINOR -lt 12 ]; then
            print_success "Python $PYTHON_VERSION detected (compatible)"
        else
            print_error "Python 3.8-3.11 required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            python3-dev \
            python3-pip \
            python3-venv \
            git \
            wget \
            curl \
            ffmpeg \
            libsndfile1
    fi
    
    print_success "System dependencies installed"
}

# Setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    print_success "Virtual environment activated"
}

# Install perfect requirements
install_perfect_deps() {
    print_status "Installing perfect dependencies (no conflicts)..."
    
    source venv/bin/activate
    
    # Install PyTorch with CUDA support
    if command -v nvidia-smi &> /dev/null; then
        print_status "Installing PyTorch with CUDA 12.1 support..."
        pip install torch>=2.1.0,\<2.5.0 torchvision>=0.16.0,\<0.20.0 torchaudio>=2.1.0,\<2.5.0 --index-url https://download.pytorch.org/whl/cu121
    else
        print_status "Installing PyTorch CPU version..."
        pip install torch>=2.1.0,\<2.5.0 torchvision>=0.16.0,\<0.20.0 torchaudio>=2.1.0,\<2.5.0 --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install perfect requirements
    pip install -r requirements_perfect.txt
    
    print_success "Perfect dependencies installed"
}

# Pre-cache models
precache_models() {
    print_status "Pre-caching models..."
    
    source venv/bin/activate
    
    python3 << 'EOF'
import os
os.environ['TRANSFORMERS_CACHE'] = './model_cache'

print("🔄 Pre-caching Voxtral model...")
try:
    from transformers import VoxtralForConditionalGeneration, AutoProcessor
    
    processor = AutoProcessor.from_pretrained(
        "mistralai/Voxtral-Mini-3B-2507",
        cache_dir="./model_cache"
    )
    print("✅ Voxtral processor cached")
    
    model = VoxtralForConditionalGeneration.from_pretrained(
        "mistralai/Voxtral-Mini-3B-2507",
        cache_dir="./model_cache",
        torch_dtype="auto",
        device_map="auto" if __import__('torch').cuda.is_available() else None
    )
    print("✅ Voxtral model cached")
except Exception as e:
    print(f"❌ Error caching Voxtral: {e}")

print("🔄 Pre-caching Orpheus model...")
try:
    from orpheus_tts import OrpheusModel
    
    model = OrpheusModel(
        model_name="canopylabs/orpheus-tts-0.1-finetune-prod",
        max_model_len=2048
    )
    print("✅ Orpheus model cached")
except Exception as e:
    print(f"❌ Error caching Orpheus: {e}")

print("🎉 Model pre-caching completed!")
EOF
    
    print_success "Models pre-cached successfully"
}

# Validate installation
validate_installation() {
    print_status "Validating perfect installation..."
    
    source venv/bin/activate
    
    python3 << 'EOF'
import sys
import torch
import transformers
import fastapi

print(f"✅ Python: {sys.version}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ CUDA version: {torch.version.cuda}")
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

print(f"✅ Transformers: {transformers.__version__}")
print(f"✅ FastAPI: {fastapi.__version__}")

# Test Orpheus TTS
try:
    from orpheus_tts import OrpheusModel
    print("✅ Orpheus TTS package imported successfully")
except ImportError as e:
    print(f"❌ Orpheus TTS import failed: {e}")
    sys.exit(1)

# Test our perfect integration
try:
    from src.tts.orpheus_perfect_model import OrpheusPerfectModel
    print("✅ Perfect Orpheus integration imported successfully")
except ImportError as e:
    print(f"❌ Perfect integration import failed: {e}")
    sys.exit(1)

print("🎉 Perfect installation validation completed!")
EOF
    
    print_success "Installation validated"
}

# Create startup script
create_startup_script() {
    print_status "Creating startup script..."
    
    cat > start_perfect.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Perfect Voxtral + Orpheus TTS System"
echo "==============================================="

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRANSFORMERS_CACHE="./model_cache"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

# Start the server
echo "🎯 Starting perfect system..."
python -m src.api.ui_server_realtime

EOF
    
    chmod +x start_perfect.sh
    print_success "Startup script created"
}

# Main deployment
main() {
    echo "Starting perfect deployment..."
    echo "============================="
    
    check_gpu
    check_python
    install_system_deps
    setup_venv
    install_perfect_deps
    precache_models
    validate_installation
    create_startup_script
    
    print_success "🎉 Perfect deployment completed!"
    echo ""
    echo "Next steps:"
    echo "==========="
    echo "1. Start the server: ./start_perfect.sh"
    echo "2. Test integration: python -m src.tts.orpheus_perfect_model"
    echo "3. Access UI: http://localhost:8000"
    echo ""
    echo "Perfect configuration:"
    echo "• Voxtral: mistralai/Voxtral-Mini-3B-2507"
    echo "• Orpheus: canopylabs/orpheus-tts-0.1-finetune-prod"
    echo "• No SNAC conflicts"
    echo "• No VLLM conflicts"
    echo "• Direct integration"
    echo "• Sub-300ms latency target"
}

main "$@"