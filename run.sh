#!/bin/bash
# Run script for Voxtral Real-time Streaming (FIXED)

set -e

echo "=== Starting Voxtral Real-time Streaming Server ==="

# Set environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# Create log directory if it doesn't exist
mkdir -p /workspace/logs

# Function to cleanup on exit
cleanup() {
    echo "Shutting down servers..."
    pkill -f "python.*tcp_server" || true
    pkill -f "uvicorn.*ui_server" || true
    pkill -f "python.*health_check.py" || true
    exit 0
}

trap cleanup EXIT INT TERM

# Start health check server (port 8005)
echo "Starting health check server on port 8005..."
python -m src.api.health_check &
HEALTH_PID=$!

# Start UI server with integrated WebSocket (port 8000)  
echo "Starting UI server with WebSocket on port 8000..."
uvicorn src.api.ui_server:app --host 0.0.0.0 --port 8000 --reload &
UI_PID=$!

# Start only TCP streaming server (port 8766) - WebSocket now integrated in UI server
echo "Starting TCP streaming server on port 8766..."
python -m src.streaming.tcp_server &
TCP_PID=$!

echo "All servers started successfully!"
echo "  - UI Server + WebSocket: http://0.0.0.0:8000"
echo "  - Health Check: http://0.0.0.0:8005/health"
echo "  - WebSocket Endpoint: ws://0.0.0.0:8000/ws"
echo "  - TCP Server: 0.0.0.0:8766"
echo ""
echo "🌐 RunPod Access URLs:"
echo "  - Web UI: https://[POD_ID]-8000.proxy.runpod.net"
echo "  - WebSocket: wss://[POD_ID]-8000.proxy.runpod.net/ws"
echo "  - Health Check: https://[POD_ID]-8005.proxy.runpod.net/health"

# Wait for all processes
wait $HEALTH_PID $UI_PID $TCP_PID
