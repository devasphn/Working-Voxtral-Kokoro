#!/bin/bash
# Fixed run script for Voxtral Real-time Streaming

set -e

echo "=== Starting Voxtral Real-time Streaming Server ==="

# Clean up any existing processes first
echo "🧹 Cleaning up existing processes..."
./cleanup.sh

# Set environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# Create log directory if it doesn't exist
mkdir -p /workspace/logs

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    pkill -f "python.*tcp_server" || true
    pkill -f "uvicorn.*ui_server" || true
    pkill -f "python.*health_check" || true
    
    # Kill by port as backup
    for port in 8000 8005 8766; do
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PID" ]; then
            kill -9 $PID 2>/dev/null || true
        fi
    done
    exit 0
}

trap cleanup EXIT INT TERM

# Start health check server (port 8005) - FIXED: No reload
echo "🩺 Starting health check server on port 8005..."
uvicorn src.api.health_check:app --host 0.0.0.0 --port 8005 &
HEALTH_PID=$!

# Give health server time to start
echo "⏳ Waiting for health server to start..."
sleep 3

# Start UI server with integrated WebSocket (port 8000) - FIXED: No reload to prevent conflicts  
echo "🌐 Starting UI server with WebSocket on port 8000..."
uvicorn src.api.ui_server:app --host 0.0.0.0 --port 8000 &
UI_PID=$!

# Give UI server time to start
echo "⏳ Waiting for UI server to start..."
sleep 3

# Start TCP streaming server (port 8766) - FIXED: Start last to avoid conflicts
echo "🔗 Starting TCP streaming server on port 8766..."
python -m src.streaming.tcp_server &
TCP_PID=$!

# Wait for all services to fully initialize
echo "⏳ Waiting for all services to initialize..."
sleep 5

# Fixed service check function
check_service() {
    local port=$1
    local service_name=$2
    local max_retries=5
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if lsof -i:$port >/dev/null 2>&1; then
            echo "✅ $service_name is running on port $port"
            return 0
        else
            echo "⏳ Waiting for $service_name on port $port (attempt $((retry+1))/$max_retries)..."
            sleep 2
            retry=$((retry+1))
        fi
    done
    
    echo "❌ $service_name failed to start on port $port after $max_retries attempts"
    return 1
}

echo ""
echo "🔍 Checking service status..."
check_service 8005 "Health Check Server"
check_service 8000 "UI Server + WebSocket"
check_service 8766 "TCP Server"

echo ""
echo "🚀 All servers started successfully!"
echo "📊 Service URLs:"
echo "  - UI Server + WebSocket: http://0.0.0.0:8000"
echo "  - Health Check: http://0.0.0.0:8005/health"
echo "  - WebSocket Endpoint: ws://0.0.0.0:8000/ws"
echo "  - TCP Server: 0.0.0.0:8766"
echo ""
echo "🌐 RunPod Access URLs:"
echo "  - Web UI: https://zsepay17h1p311-8000.proxy.runpod.net"
echo "  - WebSocket: wss://zsepay17h1p311-8000.proxy.runpod.net/ws"
echo "  - Health Check: https://zsepay17h1p311-8005.proxy.runpod.net/health"
echo ""
echo "📝 Logs are saved to: /workspace/logs/voxtral_streaming.log"
echo "🔄 Press Ctrl+C to stop all servers"
echo ""
echo "🎯 Test the WebSocket connection by visiting the web UI and clicking 'Connect'"

# Wait for all processes
wait $HEALTH_PID $UI_PID $TCP_PID
