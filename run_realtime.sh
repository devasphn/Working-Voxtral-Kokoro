#!/bin/bash
# FIXED Real-time run script for Voxtral Real-TIME Streaming Server
# Properly handles Python module imports and paths

set -e

echo "=== Starting Voxtral REAL-TIME Streaming Server ==="
echo "🚀 Version 2.0 - TRUE Real-time Continuous Streaming"
echo ""

# Clean up any existing processes first
echo "🧹 Cleaning up existing processes..."
./cleanup.sh

# Set environment variables for optimal real-time performance
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# CRITICAL: Set Python path to current directory so 'src' module can be found
export PYTHONPATH="/workspace/Voxtral-Final:$PYTHONPATH"

echo "🔧 Environment variables and Python path set for real-time performance"
echo "📁 PYTHONPATH: $PYTHONPATH"

# Create log directory with enhanced structure
mkdir -p /workspace/logs/realtime
mkdir -p /workspace/logs/audio
mkdir -p /workspace/logs/model

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Real-time Streaming Server..."
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
            sleep 3
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
echo "⏳ Waiting for health server to start..."
sleep 3

# Start REAL-TIME UI server (using Python module execution)
echo "🌐 Starting REAL-TIME UI Server on port 8000..."
echo "📋 Using enhanced real-time streaming components"
python -m src.api.ui_server_realtime &
UI_PID=$!

# Give UI server more time to start
echo "⏳ Waiting for UI server to start..."
sleep 5

# Start TCP streaming server (using Python module execution)
echo "🔗 Starting TCP streaming server on port 8766..."
echo "📋 Note: Model initialization will happen on first request"
python -m src.streaming.tcp_server &
TCP_PID=$!

# Enhanced service startup verification
echo ""
echo "🔍 Verifying service startup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Health check should be quick (5 attempts = 15 seconds max)
check_service 8005 "Health Check Server" 5

# UI server needs time for real-time components (10 attempts = 30 seconds max)  
check_service 8000 "Real-time UI Server" 10

# TCP server needs time for model prep (15 attempts = 45 seconds max)
check_service 8766 "TCP Streaming Server" 15

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
    echo "🎉 ALL SERVICES STARTED SUCCESSFULLY!"
else
    echo "❌ Some services failed to start. Check the logs above."
    exit 1
fi

echo ""
echo "📊 Voxtral Real-time Streaming Server Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌐 Real-time UI + WebSocket: http://0.0.0.0:8000"
echo "  🩺 Health Check API:         http://0.0.0.0:8005/health"  
echo "  🔗 TCP Streaming Server:     tcp://0.0.0.0:8766"
echo "  🎙️  WebSocket Endpoint:       ws://0.0.0.0:8000/ws"
echo ""
echo "🌐 RunPod Access URLs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎯 Web UI:        https://[POD_ID]-8000.proxy.runpod.net"
echo "  🔌 WebSocket:     wss://[POD_ID]-8000.proxy.runpod.net/ws"  
echo "  ❤️  Health Check:  https://[POD_ID]-8005.proxy.runpod.net/health"
echo ""
echo "📝 Log Files:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📄 Main Logs:     /workspace/logs/voxtral_streaming.log"
echo "  🎵 Audio Logs:    /workspace/logs/audio/"
echo "  🤖 Model Logs:    /workspace/logs/model/"
echo "  ⚡ Real-time:     /workspace/logs/realtime/"
echo ""
echo "🎯 REAL-TIME STREAMING FEATURES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Continuous audio capture (no start/stop buttons!)"
echo "  ✅ 1-second audio chunks processed in real-time"
echo "  ✅ Live audio visualization and volume meter"
echo "  ✅ Real-time response streaming"
echo "  ✅ Performance metrics and latency monitoring"
echo "  ✅ Comprehensive logging for debugging"
echo ""
echo "🚀 How to Use:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. 🔗 Open the Web UI in your browser"
echo "  2. 🎵 Click 'Connect' to establish WebSocket connection"
echo "  3. 🎙️  Click 'Start Real-time Stream' to begin continuous streaming"
echo "  4. 🗣️  Start talking - audio is processed automatically every second!"
echo "  5. 📱 Watch real-time transcriptions appear as you speak"
echo "  6. 🛑 Click 'Stop Stream' when done"
echo ""

# Wait for first model initialization
echo "📋 First-time Setup Notes:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⏳ First audio processing may take 30-60 seconds (model loading)"
echo "  ⚡ Subsequent processing will be much faster (<200ms target)"
echo "  📊 Check logs in real-time with: tail -f /workspace/logs/voxtral_streaming.log"
echo "  🔍 Monitor real-time metrics in the web interface"
echo ""

echo "🔄 Server is now running in REAL-TIME mode!"
echo "📊 Monitor performance and watch for any startup errors above"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo "💡 View logs: tail -f /workspace/logs/voxtral_streaming.log"
echo ""

# Wait for all processes to complete (servers run indefinitely)
wait $HEALTH_PID $UI_PID $TCP_PID
