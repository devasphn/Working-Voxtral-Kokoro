#!/bin/bash
# Voxtral + TTS Integrated Deployment Script for RunPod
# Complete setup and deployment with pre-loaded models

set -e

echo "========================================================================"
echo "🚀 Voxtral + TTS Integrated Real-time Voice Application"
echo "========================================================================"
echo "📋 Features:"
echo "   • Real-time Speech-to-Text (Voxtral-Mini-3B-2507)"
echo "   • Intelligent Text Generation (LLM)"
echo "   • High-quality Text-to-Speech (Orpheus TTS)"
echo "   • Voice Activity Detection (VAD)"
echo "   • WebSocket-based real-time communication"
echo "   • Pre-loaded models for instant conversation"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check service availability
check_service() {
    local port=$1
    local service_name=$2
    local max_attempts=${3:-10}
    local attempt=1
    
    echo "🔍 Checking $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ $service_name is running on port $port"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts - waiting for $service_name..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Clean up any existing processes
cleanup_processes() {
    echo "🧹 Cleaning up existing processes..."
    
    # Kill processes on our ports
    for port in 8000 8005 8766; do
        if lsof -ti:$port >/dev/null 2>&1; then
            echo "🔄 Stopping process on port $port..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # Kill any Python processes related to our application
    pkill -f "ui_server_realtime" 2>/dev/null || true
    pkill -f "health_check" 2>/dev/null || true
    pkill -f "tcp_server" 2>/dev/null || true
    
    sleep 2
    echo "✅ Cleanup completed"
}

# Set up environment variables
setup_environment() {
    echo "🔧 Setting up environment variables..."
    
    export CUDA_VISIBLE_DEVICES=0
    export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
    export OMP_NUM_THREADS=8
    export TOKENIZERS_PARALLELISM=false
    export TORCH_COMPILE_DEBUG=0
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    echo "✅ Environment variables configured"
}

# Install system dependencies
install_system_deps() {
    echo "📦 Installing system dependencies..."
    
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
        netcat-openbsd \
        lsof \
        htop \
        ffmpeg \
        portaudio19-dev \
        python3-dev \
        espeak-ng \
        espeak-ng-data
    
    echo "✅ System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    echo "🐍 Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install PyTorch with CUDA support
    echo "⚡ Installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    # Install other requirements
    echo "📚 Installing application requirements..."
    pip install -r requirements.txt
    
    echo "✅ Python dependencies installed"
}

# Download and cache models
cache_models() {
    echo "🤖 Downloading and caching models..."
    
    # Create model cache directory
    mkdir -p /workspace/model_cache
    
    # Cache Voxtral model
    echo "📥 Caching Voxtral model (this may take several minutes)..."
    python3 -c "
import torch
from transformers import VoxtralForConditionalGeneration, AutoProcessor

model_name = 'mistralai/Voxtral-Mini-3B-2507'
cache_dir = '/workspace/model_cache'

print('📥 Loading AutoProcessor...')
processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
print('✅ AutoProcessor cached successfully')

print('📥 Loading Voxtral model...')
model = VoxtralForConditionalGeneration.from_pretrained(
    model_name, 
    cache_dir=cache_dir,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    attn_implementation='eager',
    low_cpu_mem_usage=True,
    trust_remote_code=True
)
print('✅ Voxtral model cached successfully')
"
    
    # Cache SNAC model for TTS
    echo "📥 Caching SNAC TTS model..."
    python3 -c "
from snac import SNAC
print('📥 Loading SNAC model...')
model = SNAC.from_pretrained('hubertsiuzdak/snac_24khz')
print('✅ SNAC model cached successfully')
"
    
    echo "✅ All models cached successfully"
}

# Start services
start_services() {
    echo "🚀 Starting integrated services..."
    
    # Start health check server
    echo "🩺 Starting health check server on port 8005..."
    python -m src.api.health_check &
    HEALTH_PID=$!
    sleep 3
    
    # Start main UI server with integrated TTS
    echo "🌐 Starting Voxtral + TTS UI Server on port 8000..."
    echo "📋 Features: STT + LLM + TTS + VAD + WebSocket streaming"
    python -m src.api.ui_server_realtime &
    UI_PID=$!
    sleep 8
    
    # Start TCP streaming server
    echo "🔗 Starting TCP streaming server on port 8766..."
    python -m src.streaming.tcp_server &
    TCP_PID=$!
    sleep 5
    
    # Store PIDs for cleanup
    echo "$HEALTH_PID $UI_PID $TCP_PID" > /tmp/voxtral_pids.txt
    
    echo "✅ All services started"
}

# Verify services
verify_services() {
    echo ""
    echo "🔍 Verifying service startup..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Install netcat if not available
    if ! command_exists nc; then
        echo "📦 Installing netcat..."
        apt-get install -y netcat-openbsd
    fi
    
    # Check each service
    check_service 8005 "Health Check Server" 5
    check_service 8000 "Voxtral + TTS UI Server" 10
    check_service 8766 "TCP Streaming Server" 8
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Final verification
    services_running=true
    for port in 8005 8000 8766; do
        if ! nc -z localhost $port 2>/dev/null; then
            services_running=false
            echo "❌ Service on port $port is not responding"
            break
        fi
    done
    
    if [ "$services_running" = true ]; then
        echo "🎉 ALL SERVICES RUNNING SUCCESSFULLY!"
        return 0
    else
        echo "❌ Some services failed to start"
        return 1
    fi
}

# Display final information
show_completion_info() {
    echo ""
    echo "🎉 VOXTRAL + TTS DEPLOYMENT COMPLETE!"
    echo "========================================================================"
    echo ""
    echo "🌐 Access URLs (replace [POD_ID] with your RunPod ID):"
    echo "   • Web Interface: https://[POD_ID]-8000.proxy.runpod.net"
    echo "   • Health Check:  https://[POD_ID]-8005.proxy.runpod.net/health"
    echo "   • WebSocket:     wss://[POD_ID]-8000.proxy.runpod.net/ws"
    echo ""
    echo "🎯 How to Use:"
    echo "   1. Open the Web Interface in your browser"
    echo "   2. Click 'Connect' to establish WebSocket connection"
    echo "   3. Click 'Start Conversation' to begin real-time interaction"
    echo "   4. Speak into your microphone"
    echo "   5. Receive AI text responses AND audio responses"
    echo ""
    echo "🔧 Features Enabled:"
    echo "   ✅ Real-time Speech-to-Text (Voxtral)"
    echo "   ✅ Intelligent Text Generation"
    echo "   ✅ High-quality Text-to-Speech (Orpheus)"
    echo "   ✅ Voice Activity Detection"
    echo "   ✅ Pre-loaded models (no startup delay)"
    echo "   ✅ WebSocket streaming"
    echo ""
    echo "📊 Performance:"
    echo "   • Models pre-loaded at startup"
    echo "   • GPU-optimized processing"
    echo "   • <200ms latency target"
    echo "   • Real-time audio streaming"
    echo ""
    echo "🛑 To stop services: pkill -f 'src.api' && pkill -f 'src.streaming'"
    echo "========================================================================"
}

# Main deployment function
main() {
    echo "Starting deployment process..."
    
    cleanup_processes
    setup_environment
    install_system_deps
    install_python_deps
    cache_models
    start_services
    
    if verify_services; then
        show_completion_info
        
        # Keep the script running to maintain services
        echo ""
        echo "🔄 Services are running. Press Ctrl+C to stop all services."
        echo ""
        
        # Wait for interrupt
        trap 'echo ""; echo "🛑 Stopping services..."; cleanup_processes; exit 0' INT
        while true; do
            sleep 10
            # Check if services are still running
            if ! nc -z localhost 8000 2>/dev/null; then
                echo "❌ Main service stopped unexpectedly"
                break
            fi
        done
    else
        echo "❌ Deployment failed - some services could not start"
        cleanup_processes
        exit 1
    fi
}

# Run main function
main "$@"
