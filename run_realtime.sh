#!/bin/bash
# FIXED Real-time run script for Voxtral CONVERSATIONAL Streaming Server
# Resolved FlashAttention2 issues with proper fallback handling

set -e

echo "=== Starting Voxtral CONVERSATIONAL Streaming Server (FIXED) ==="
echo "🚀 Version 2.2 - FlashAttention2 Issues Resolved"
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

# Check FlashAttention2 availability
echo "🔍 Checking FlashAttention2 availability..."
if python3 -c "import flash_attn" 2>/dev/null; then
    echo "✅ FlashAttention2 is available - optimal performance mode!"
    FLASH_ATTN_STATUS="available"
else
    echo "💡 FlashAttention2 not available - using eager attention (still fast!)"
    echo "📝 Note: This is normal and the system will work perfectly."
    FLASH_ATTN_STATUS="not_available"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Conversational Streaming Server..."
    pkill -f "python.*tcp_server" || true
    pkill -f "python.*ui_server_realtime" || true
    pkill -f "uvicorn.*ui_server_realtime" || true
    pkill -f "python.*health_check" || true
    
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

# Enhanced service check function
check_service() {
    local port=$1
    local service_name=$2
    local max_retries=$3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if lsof -i:$port >/dev/null 2>&1; then
            echo "✅ $service_name is running on port $port"
            return 0
        else
            if [ $retry -eq 0 ]; then
                echo "⏳ Waiting for $service_name on port $port..."
            fi
            sleep 2
            retry=$((retry+1))
        fi
    done
    
    echo "❌ $service_name failed to start on port $port after $((max_retries * 2)) seconds"
    return 1
}

# Start health check server (using Python module execution)
echo "🩺 Starting health check server on port 8005..."
python -m src.api.health_check &
HEALTH_PID=$!

# Give health server time to start
echo "⏳ Waiting for health server to start..."
sleep 2

# Start CONVERSATIONAL UI server (using Python module execution)
echo "🌐 Starting CONVERSATIONAL UI Server on port 8000..."
echo "📋 Using optimized conversational streaming components"
if [ "$FLASH_ATTN_STATUS" = "available" ]; then
    echo "⚡ FlashAttention2 enabled for maximum performance"
else
    echo "💡 Using eager attention - performance is still excellent"
fi
python -m src.api.ui_server_realtime &
UI_PID=$!

# Give UI server more time to start
echo "⏳ Waiting for UI server to start..."
sleep 3

# Start TCP streaming server (using Python module execution)
echo "🔗 Starting TCP streaming server on port 8766..."
echo "📋 Note: Model initialization optimized for conversation"
python -m src.streaming.tcp_server &
TCP_PID=$!

# Enhanced service startup verification
echo ""
echo "🔍 Verifying service startup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health check should be quick (3 attempts = 6 seconds max)
check_service 8005 "Health Check Server" 3

# UI server needs time for conversational components (5 attempts = 10 seconds max)  
check_service 8000 "Conversational UI Server" 5

# TCP server needs time for model prep (8 attempts = 16 seconds max)
check_service 8766 "TCP Streaming Server" 8

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if all services started successfully
services_running=true
for port in 8005 8000 8766; do
    if ! lsof -i:$port >/dev/null 2>&1; then
        services_running=false
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
echo "🎯 CONVERSATIONAL FEATURES (FIXED):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ FlashAttention2 issues resolved (fallback to eager attention)"
echo "  ✅ Natural conversation mode (optimized prompts)"
echo "  ✅ Reduced latency for better conversation flow"
echo "  ✅ Smart conversation interface with message history"
echo "  ✅ Simple transcription OR smart conversation modes"
echo "  ✅ Performance warnings for high latency"
echo "  ✅ Enhanced error handling for smooth conversation"
echo "  ✅ Works with or without FlashAttention2"
echo ""
echo "🚀 How to Have a Conversation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. 🔗 Open the Conversational UI in your browser"
echo "  2. 🎵 Click 'Connect' to establish connection"
echo "  3. 🎙️  Choose mode: 'Simple Transcription' or 'Smart Conversation'"
echo "  4. 🗣️  Click 'Start Conversation' and start talking naturally!"
echo "  5. 👀 Watch the conversation appear in real-time"
echo "  6. 🛑 Click 'Stop Conversation' when done"
echo ""

# Wait for first model initialization
echo "📋 Conversation Setup Notes (FIXED):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⏳ First conversation may take 30+ seconds (model loading)"
echo "  ⚡ Subsequent responses optimized for <300ms target"
echo "  📊 Use 'Simple Transcription' mode for fastest responses"
echo "  🗣️  Use 'Smart Conversation' mode for interactive chat"
echo "  🔍 Monitor conversation metrics in the web interface"
if [ "$FLASH_ATTN_STATUS" = "available" ]; then
    echo "  🚀 FlashAttention2 enabled - maximum performance mode"
else
    echo "  💡 Using eager attention - still excellent performance"
    echo "  📝 To install FlashAttention2 later: pip install flash-attn --no-build-isolation"
fi
echo ""

echo "🔄 Conversational Server is now running!"
echo "📊 Monitor performance and watch for any startup errors above"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo "💡 View logs: tail -f /workspace/logs/voxtral_streaming.log"
echo ""

# Wait for all processes to complete (servers run indefinitely)
wait $HEALTH_PID $UI_PID $TCP_PID
