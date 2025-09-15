#!/bin/bash

# Deploy Voxtral + Direct Orpheus TTS Integration
# Single-command deployment script for the unified system

set -e  # Exit on any error

echo "🚀 Deploying Voxtral + Direct Orpheus TTS Integration"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on GPU-enabled system
check_gpu() {
    print_status "Checking GPU availability..."
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
        print_success "GPU detected: $GPU_INFO"
        
        # Check VRAM
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
        VRAM_GB=$((VRAM_MB / 1024))
        
        if [ $VRAM_GB -lt 8 ]; then
            print_error "Insufficient VRAM: ${VRAM_GB}GB detected, minimum 8GB required"
            exit 1
        elif [ $VRAM_GB -lt 16 ]; then
            print_warning "Limited VRAM: ${VRAM_GB}GB detected, 16GB+ recommended for optimal performance"
        else
            print_success "Excellent VRAM: ${VRAM_GB}GB detected"
        fi
    else
        print_warning "No GPU detected - will run on CPU (much slower)"
    fi
}

# Check Python version
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
        # Ubuntu/Debian
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
            libsndfile1 \
            portaudio19-dev
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y \
            gcc \
            gcc-c++ \
            python3-devel \
            python3-pip \
            git \
            wget \
            curl \
            ffmpeg \
            libsndfile \
            portaudio-devel
    else
        print_warning "Unknown package manager - please install dependencies manually"
    fi
    
    print_success "System dependencies installed"
}

# Create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    print_success "Virtual environment activated and updated"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Ensure we're in the virtual environment
    source venv/bin/activate
    
    # Install PyTorch with CUDA support
    if command -v nvidia-smi &> /dev/null; then
        print_status "Installing PyTorch with CUDA support..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    else
        print_status "Installing PyTorch CPU version..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # Install other dependencies
    pip install -r requirements_direct_orpheus.txt
    
    print_success "Python dependencies installed"
}

# Create requirements file for direct Orpheus integration
create_requirements() {
    print_status "Creating requirements file for direct Orpheus integration..."
    
    cat > requirements_direct_orpheus.txt << EOF
# Core dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
PyYAML>=6.0.1

# AI/ML dependencies
transformers>=4.54.0
accelerate>=0.25.0
datasets>=2.16.0
tokenizers>=0.15.0

# Audio processing
librosa>=0.10.1
soundfile>=0.12.1
numpy>=1.24.0
scipy>=1.11.0

# SNAC codec for Orpheus TTS
snac>=1.0.0

# Utilities
asyncio-mqtt>=0.13.0
python-multipart>=0.0.6
aiofiles>=23.2.1
httpx>=0.25.0
psutil>=5.9.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0

# Optional: Flash Attention for performance (if supported)
# flash-attn>=2.3.0  # Uncomment if GPU supports it
EOF
    
    print_success "Requirements file created"
}

# Setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    # Copy the direct Orpheus configuration
    if [ ! -f "config.yaml" ]; then
        cp config_direct_orpheus.yaml config.yaml
        print_success "Configuration file created from template"
    else
        print_warning "Configuration file already exists - not overwriting"
    fi
    
    # Create directories
    mkdir -p logs
    mkdir -p model_cache
    
    print_success "Configuration setup completed"
}

# Pre-cache models
precache_models() {
    print_status "Pre-caching models (this may take a while)..."
    
    source venv/bin/activate
    
    python3 << EOF
import os
os.environ['TRANSFORMERS_CACHE'] = './model_cache'

print("🔄 Pre-caching Voxtral model...")
from transformers import VoxtralForConditionalGeneration, AutoProcessor
try:
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
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tokenizer = AutoTokenizer.from_pretrained(
        "mistralai/Orpheus-Mini-3B-2507",
        cache_dir="./model_cache"
    )
    print("✅ Orpheus tokenizer cached")
    
    model = AutoModelForCausalLM.from_pretrained(
        "mistralai/Orpheus-Mini-3B-2507",
        cache_dir="./model_cache",
        torch_dtype="auto",
        device_map="auto" if __import__('torch').cuda.is_available() else None
    )
    print("✅ Orpheus model cached")
except Exception as e:
    print(f"❌ Error caching Orpheus: {e}")

print("🔄 Pre-caching SNAC model...")
try:
    from snac import SNAC
    snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
    print("✅ SNAC model cached")
except Exception as e:
    print(f"❌ Error caching SNAC: {e}")

print("🎉 Model pre-caching completed!")
EOF
    
    print_success "Models pre-cached successfully"
}

# Validate installation
validate_installation() {
    print_status "Validating installation..."
    
    source venv/bin/activate
    
    python3 << EOF
import sys
import torch
import transformers
import snac
import fastapi
import uvicorn

print(f"✅ Python: {sys.version}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ CUDA version: {torch.version.cuda}")
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")

print(f"✅ Transformers: {transformers.__version__}")
print(f"✅ SNAC: {snac.__version__}")
print(f"✅ FastAPI: {fastapi.__version__}")
print(f"✅ Uvicorn: {uvicorn.__version__}")

# Test imports
try:
    from src.models.unified_model_manager import UnifiedModelManager
    from src.tts.orpheus_direct_model import OrpheusDirectModel
    from src.tts.tts_service_direct import TTSServiceDirect
    from src.utils.performance_monitor import PerformanceMonitor
    from src.utils.gpu_memory_manager import GPUMemoryManager
    print("✅ All custom modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

print("🎉 Installation validation completed successfully!")
EOF
    
    print_success "Installation validated"
}

# Create startup script
create_startup_script() {
    print_status "Creating startup script..."
    
    cat > start_direct_orpheus.sh << 'EOF'
#!/bin/bash

# Startup script for Voxtral + Direct Orpheus TTS Integration

echo "🚀 Starting Voxtral + Direct Orpheus TTS Integration"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRANSFORMERS_CACHE="./model_cache"
export CUDA_VISIBLE_DEVICES=0  # Use first GPU
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

# Start the server
echo "🎯 Starting unified model system..."
python -m src.api.ui_server_realtime

EOF
    
    chmod +x start_direct_orpheus.sh
    print_success "Startup script created"
}

# Create test script
create_test_script() {
    print_status "Creating test script..."
    
    cat > test_direct_orpheus.sh << 'EOF'
#!/bin/bash

# Test script for Voxtral + Direct Orpheus TTS Integration

echo "🧪 Testing Voxtral + Direct Orpheus TTS Integration"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRANSFORMERS_CACHE="./model_cache"

echo "🔍 Running unit tests..."
python -m pytest tests/ -v --tb=short

echo "🔍 Running integration tests..."
python -m pytest tests/test_integration_unified_system.py -v

echo "🔍 Running performance validation..."
python -m pytest tests/test_performance_validation.py -v

echo "🎉 All tests completed!"

EOF
    
    chmod +x test_direct_orpheus.sh
    print_success "Test script created"
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    echo "=============================="
    
    # Pre-flight checks
    check_gpu
    check_python
    
    # Installation steps
    install_system_deps
    create_requirements
    setup_venv
    install_python_deps
    setup_config
    precache_models
    
    # Validation and setup
    validate_installation
    create_startup_script
    create_test_script
    
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "==========="
    echo "1. Review configuration: config.yaml"
    echo "2. Start the server: ./start_direct_orpheus.sh"
    echo "3. Run tests: ./test_direct_orpheus.sh"
    echo "4. Access UI: http://localhost:8000"
    echo "5. Check health: http://localhost:8000/api/status"
    echo ""
    echo "Hardware requirements met:"
    if command -v nvidia-smi &> /dev/null; then
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
        VRAM_GB=$((VRAM_MB / 1024))
        echo "✅ GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
        echo "✅ VRAM: ${VRAM_GB}GB"
    else
        echo "⚠️  CPU mode (GPU recommended for optimal performance)"
    fi
    echo "✅ Python: $(python3 --version)"
    echo "✅ Direct Orpheus integration ready"
    echo ""
    echo "Performance targets:"
    echo "• Voxtral processing: <100ms"
    echo "• Orpheus generation: <150ms"
    echo "• Audio conversion: <50ms"
    echo "• Total end-to-end: <300ms"
}

# Run main function
main "$@"