#!/bin/bash

# 🚀 PRODUCTION DEPLOYMENT SCRIPT FOR RUNPOD
# Voxtral + Orpheus TTS Speech-to-Speech System
# Automated deployment with comprehensive error handling

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

# Check if HF_TOKEN is set
check_hf_token() {
    if [ -z "$HF_TOKEN" ]; then
        error "HF_TOKEN environment variable is not set!"
        echo "Please set your HuggingFace token:"
        echo "export HF_TOKEN='your_token_here'"
        exit 1
    fi
    success "HuggingFace token is configured"
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check GPU
    if ! command -v nvidia-smi &> /dev/null; then
        error "NVIDIA GPU not detected! This system requires CUDA support."
        exit 1
    fi
    
    # Check VRAM
    VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
    if [ "$VRAM" -lt 16000 ]; then
        warn "GPU has only ${VRAM}MB VRAM. 16GB+ recommended for optimal performance."
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found!"
        exit 1
    fi
    
    success "System requirements check passed"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    # Set optimization environment variables
    export CUDA_VISIBLE_DEVICES=0
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
    export TOKENIZERS_PARALLELISM=false
    export OMP_NUM_THREADS=8
    export MKL_NUM_THREADS=8
    
    # Create directories
    mkdir -p model_cache
    mkdir -p logs
    mkdir -p temp
    
    success "Environment setup completed"
}

# Create and activate virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        success "Virtual environment created"
    else
        log "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    success "Virtual environment activated"
    
    # Upgrade pip
    python -m pip install --upgrade pip setuptools wheel
    success "Pip upgraded"
}

# Install dependencies in correct order
install_dependencies() {
    log "Installing dependencies in correct order..."
    
    # Install PyTorch with CUDA support
    log "Installing PyTorch with CUDA 12.1 support..."
    pip install torch>=2.1.0 torchaudio>=2.1.0 torchvision>=0.16.0 --index-url https://download.pytorch.org/whl/cu121
    
    # Install core transformers
    log "Installing transformers stack..."
    pip install transformers>=4.56.0
    pip install huggingface-hub>=0.34.0
    pip install accelerate>=0.25.0
    pip install tokenizers>=0.15.0
    
    # Install Mistral Common
    log "Installing Mistral Common with audio support..."
    pip install "mistral-common[audio]>=1.8.1"
    
    # Install Orpheus TTS
    log "Installing Orpheus TTS..."
    pip install orpheus-speech>=0.1.0
    
    # Install vLLM
    log "Installing vLLM..."
    pip install "vllm>=0.6.0,<0.8.0"
    
    # Install audio processing
    log "Installing audio processing libraries..."
    pip install librosa>=0.10.1
    pip install soundfile>=0.12.1
    pip install numpy>=1.24.0
    pip install scipy>=1.11.0
    
    # Install web framework
    log "Installing web framework..."
    pip install fastapi>=0.107.0
    pip install "uvicorn[standard]>=0.24.0"
    pip install websockets>=12.0
    pip install pydantic>=2.9.0
    pip install pydantic-settings>=2.1.0
    pip install python-multipart>=0.0.6
    
    # Install utilities
    log "Installing utilities..."
    pip install pyyaml>=6.0.1
    pip install python-dotenv>=1.0.0
    pip install psutil>=5.9.0
    
    # Install Flash Attention (optional)
    log "Installing Flash Attention (optional)..."
    pip install flash-attn>=2.5.0 || warn "Flash Attention installation failed - continuing without it"
    
    success "Dependencies installed successfully"
}

# Pre-download models
predownload_models() {
    log "Pre-downloading models for faster startup..."
    
    # Download Voxtral model
    log "Downloading Voxtral model..."
    python3 -c "
import os
os.environ['HF_TOKEN'] = '$HF_TOKEN'
try:
    from transformers import VoxtralForConditionalGeneration, AutoProcessor
    print('Downloading Voxtral model...')
    processor = AutoProcessor.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache')
    model = VoxtralForConditionalGeneration.from_pretrained('mistralai/Voxtral-Mini-3B-2507', cache_dir='./model_cache', torch_dtype='auto', device_map='auto')
    print('✅ Voxtral model cached successfully')
except Exception as e:
    print(f'❌ Voxtral download failed: {e}')
    exit(1)
"
    
    # Download Orpheus model
    log "Downloading Orpheus model..."
    python3 -c "
import os
os.environ['HF_TOKEN'] = '$HF_TOKEN'
try:
    from orpheus_tts import OrpheusModel
    print('Downloading Orpheus model...')
    model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod')
    print('✅ Orpheus model cached successfully')
except Exception as e:
    print(f'⚠️ Orpheus model download failed: {e}')
    print('Model will be downloaded on first use')
"
    
    success "Model pre-downloading completed"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Test core imports
    python3 -c "
import torch
import transformers
import fastapi
import websockets
print('✅ Core packages imported successfully')
print(f'✅ PyTorch CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU device: {torch.cuda.get_device_name(0)}')
else:
    print('❌ CUDA not available')
    exit(1)
"
    
    # Test Voxtral
    python3 -c "
try:
    from transformers import VoxtralForConditionalGeneration
    print('✅ Voxtral classes available')
except ImportError as e:
    print(f'❌ Voxtral import failed: {e}')
    exit(1)
"
    
    # Test configuration
    python3 -c "
try:
    from src.utils.config import config
    print('✅ Configuration loaded successfully')
    print(f'   Server port: {config.server.http_port}')
    print(f'   Model name: {config.model.name}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"
    
    success "Installation verification passed"
}

# Start system
start_system() {
    log "Starting the speech-to-speech system..."
    
    # Start the system in background
    nohup python3 -m src.api.ui_server_realtime > logs/system.log 2>&1 &
    SYSTEM_PID=$!
    
    # Wait for startup
    log "Waiting for system startup..."
    sleep 15
    
    # Check if process is still running
    if ! kill -0 $SYSTEM_PID 2>/dev/null; then
        error "System failed to start. Check logs/system.log for details."
        exit 1
    fi
    
    success "System started successfully (PID: $SYSTEM_PID)"
    echo $SYSTEM_PID > .system.pid
}

# Verify system is working
verify_system() {
    log "Verifying system functionality..."
    
    # Health check
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Health check passed"
    else
        error "Health check failed"
        return 1
    fi
    
    # WebSocket test
    python3 -c "
import asyncio
import websockets
import json
import sys

async def test_websocket():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri, timeout=10) as websocket:
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            print('✅ WebSocket connection successful')
            return True
    except Exception as e:
        print(f'❌ WebSocket test failed: {e}')
        return False

result = asyncio.run(test_websocket())
sys.exit(0 if result else 1)
" || {
        error "WebSocket test failed"
        return 1
    }
    
    success "System verification completed successfully"
}

# Main deployment function
main() {
    log "🚀 Starting PRODUCTION deployment of Voxtral + Orpheus TTS system"
    
    check_hf_token
    check_system_requirements
    setup_environment
    setup_python_env
    install_dependencies
    predownload_models
    verify_installation
    start_system
    verify_system
    
    success "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo ""
    echo "📊 System Information:"
    echo "   🌐 UI: http://localhost:8000"
    echo "   🔌 WebSocket: ws://localhost:8765"
    echo "   ❤️ Health: http://localhost:8000/health"
    echo "   📈 Metrics: http://localhost:8000/api/performance/metrics"
    echo ""
    echo "📝 Monitoring Commands:"
    echo "   tail -f logs/system.log        # Application logs"
    echo "   tail -f logs/voxtral_streaming.log  # Streaming logs"
    echo "   htop                           # System resources"
    echo "   watch -n 1 nvidia-smi         # GPU usage"
    echo ""
    echo "🛑 To stop the system:"
    echo "   kill \$(cat .system.pid)"
}

# Run main function
main "$@"
