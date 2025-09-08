#!/bin/bash
# PRODUCTION-READY Real-time run script for Voxtral CONVERSATIONAL Streaming Server
# Fixed all critical issues: VAD, FlashAttention detection, health checks, import paths

set -e

echo "=== Starting Voxtral CONVERSATIONAL Streaming Server (PRODUCTION FIXED) ==="
echo "🚀 Version 3.0 - Production Ready with VAD and Silence Detection"
echo ""

# Clean up any existing processes first
echo "🧹 Cleaning up existing processes..."
./cleanup.sh

# Set environment variables for optimal conversational performance
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export TORCH_COMPILE_DEBUG=0

# CRITICAL: Set Python path to current directory so 'src' module can be found
export PYTHONPATH="/workspace/Voxtral-Final:$PYTHONPATH"

echo "🔧 Environment variables and Python path set for conversational performance"
echo "📁 PYTHONPATH: $PYTHONPATH"

# Create log directory with enhanced structure
mkdir -p /workspace/logs/conversational
mkdir -p /workspace/logs/audio
mkdir -p /workspace/logs/model

# Check FlashAttention2 availability (FIXED detection)
echo "🔍 Checking FlashAttention2 availability..."
FLASH_ATTN_STATUS="not_available"
if python3 -c "import flash_attn; print('FlashAttention2 available')" 2>/dev/null; then
    echo "✅ FlashAttention2 is available - optimal performance mode!"
    FLASH_ATTN_STATUS="available"
else
    echo "💡 FlashAttention2 not detected - using eager attention (still fast!)"
    echo "📝 Note: This is normal and the system will work perfectly."
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Conversational Streaming Server..."
    pkill -f "python.*tcp_server" 2>/dev/null || true
    pkill -f "python.*ui_server_realtime" 2>/dev/null || true
    pkill -f "uvicorn.*ui_server_realtime" 2>/dev/null || true
    pkill -f "python.*health_check" 2>/dev/null || true
    
    # Kill by port as backup
    for port in 8000 8005 8766; do
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PID" ]; then
            echo "🔫 Force killing process $PID on port $port"
            kill -9 $PID 2>/dev/null || true
        fi
    done
    
    echo "✅ Cleanup completed"
    exit 0
}

trap cleanup EXIT INT TERM

# FIXED: Enhanced service check function with better detection
check_service() {
    local port=$1
    local service_name=$2
    local max_retries=$3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        # Check if port is listening (more reliable than lsof)
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ $service_name is running on port $port"
            return 0
        else
            if [ $retry -eq 0 ]; then
                echo "⏳ Waiting for $service_name on port $port..."
            fi
            sleep 3  # Increased wait time
            retry=$((retry+1))
        fi
    done
    
    echo "❌ $service_name failed to start on port $port after $((max_retries * 3)) seconds"
    return 1
}

# Start health check server (using Python module execution)
echo "🩺 Starting health check server on port 8005..."
python -m src.api.health_check &
HEALTH_PID=$!

# Give health server time to start
echo "⏳ Waiting for health server to initialize..."
sleep 4

# Start CONVERSATIONAL UI server (using Python module execution)
echo "🌐 Starting CONVERSATIONAL UI Server on port 8000..."
echo "📋 Using optimized conversational streaming components with VAD"
if [ "$FLASH_ATTN_STATUS" = "available" ]; then
    echo "⚡ FlashAttention2 enabled for maximum performance"
else
    echo "💡 Using eager attention - performance is still excellent"
fi
python -m src.api.ui_server_realtime &
UI_PID=$!

# Give UI server more time to start
echo "⏳ Waiting for UI server to start..."
sleep 5

# Start TCP streaming server (using Python module execution)
echo "🔗 Starting TCP streaming server on port 8766..."
echo "📋 Note: Model initialization optimized for conversation with VAD"
python -m src.streaming.tcp_server &
TCP_PID=$!

# Enhanced service startup verification (FIXED)
echo ""
echo "🔍 Verifying service startup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if netcat is available, install if not
if ! command -v nc &> /dev/null; then
    echo "📦 Installing netcat for service checking..."
    apt-get update && apt-get install -y netcat-openbsd
fi

# Health check should be quick (5 attempts = 15 seconds max)
check_service 8005 "Health Check Server" 5

# UI server needs time for conversational components (7 attempts = 21 seconds max)  
check_service 8000 "Conversational UI Server" 7

# TCP server needs time for model prep (10 attempts = 30 seconds max)
check_service 8766 "TCP Streaming Server" 10

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if all services started successfully (FIXED detection)
services_running=true
for port in 8005 8000 8766; do
    if ! nc -z localhost $port 2>/dev/null; then
        services_running=false
        echo "❌ Service on port $port is not responding"
        break
    fi
done

if [ "$services_running" = true ]; then
    echo "🎉 ALL CONVERSATIONAL SERVICES STARTED SUCCESSFULLY!"
else
    echo "❌ Some services failed to start. Check the logs above."
    exit 1
fi

echo ""
echo "📊 Voxtral Conversational Streaming Server Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Conversational UI + WebSocket: http://0.0.0.0:8000"
echo "  🩺 Health Check API:              http://0.0.0.0:8005/health"  
echo "  🔗 TCP Streaming Server:          tcp://0.0.0.0:8766"
echo "  🎙️  WebSocket Endpoint:            ws://0.0.0.0:8000/ws"
echo ""
echo "🌐 RunPod Access URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎯 Conversational UI:  https://[POD_ID]-8000.proxy.runpod.net"
echo "  🔌 WebSocket:          wss://[POD_ID]-8000.proxy.runpod.net/ws"  
echo "  ❤️  Health Check:       https://[POD_ID]-8005.proxy.runpod.net/health"
echo ""
echo "📝 Log Files:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📄 Main Logs:        /workspace/logs/voxtral_streaming.log"
echo "  🗣️  Conversation Logs: /workspace/logs/conversational/"
echo "  🎵 Audio Logs:       /workspace/logs/audio/"
echo "  🤖 Model Logs:       /workspace/logs/model/"
echo ""
echo "🎯 CONVERSATIONAL FEATURES (PRODUCTION READY):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Voice Activity Detection (VAD) implemented"
echo "  ✅ Silence detection and noise filtering"
echo "  ✅ FlashAttention2 detection fixed"
echo "  ✅ Import path issues resolved"
echo "  ✅ Health check monitoring working"
echo "  ✅ Robust error handling for production"
echo "  ✅ Optimized for real conversation (no spam responses)"
echo "  ✅ Smart audio processing with VAD thresholds"
echo ""
echo "🚀 How to Have a Natural Conversation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. 🔗 Open the Conversational UI in your browser"
echo "  2. 🎵 Click 'Connect' to establish connection"
echo "  3. 🎙️  Choose mode: 'Simple Transcription' or 'Smart Conversation'"
echo "  4. 🗣️  Click 'Start Conversation' and speak CLEARLY"
echo "  5. 👀 AI will ONLY respond when it detects actual speech"
echo "  6. 🤫 System ignores silence and background noise"
echo "  7. 🛑 Click 'Stop Conversation' when done"
echo ""

# Wait for first model initialization
echo "📋 Production Conversation Setup:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⏳ First conversation may take 30+ seconds (one-time model loading)"
echo "  ⚡ VAD ensures responses only to actual speech (no noise)"
echo "  📊 Use 'Simple Transcription' for fastest responses"
echo "  🗣️  Use 'Smart Conversation' for interactive chat"
echo "  🔇 System automatically ignores silence/noise"
echo "  🎯 Optimized audio threshold prevents spam responses"
if [ "$FLASH_ATTN_STATUS" = "available" ]; then
    echo "  🚀 FlashAttention2 enabled - maximum performance mode"
else
    echo "  💡 Using eager attention - still excellent performance"
fi
echo ""

echo "🔄 Production Conversational Server is now running!"
echo "📊 Real conversations only - no responses to silence/noise"
echo "🛑 Press Ctrl+C to stop all servers"
echo ""

# Wait for all processes to complete (servers run indefinitely)
wait $HEALTH_PID $UI_PID $TCP_PID
