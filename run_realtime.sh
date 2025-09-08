#!/bin/bash
# PRODUCTION-READY Real-time run script for Voxtral CONVERSATIONAL Streaming Server
# FIXED all import issues and added proper service health checking

set -e

echo "=== Starting Voxtral CONVERSATIONAL Streaming Server (PRODUCTION) ==="
echo "🚀 Version 3.0 - PRODUCTION READY with VAD and Silence Detection"
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

# FIXED: Enhanced service check function with proper timeout handling
check_service() {
    local port=$1
    local service_name=$2
    local max_retries=15  # Increased retries
    local retry=0
    
    echo "🔍 Checking $service_name on port $port..."
    
    while [ $retry -lt $max_retries ]; do
        if lsof -i:$port >/dev/null 2>&1; then
            echo "✅ $service_name is running on port $port"
            # Double check with HTTP request for web services
            if [ $port -eq 8000 ] || [ $port -eq 8005 ]; then
                if curl -s --connect-timeout 2 "http://localhost:$port/health" >/dev/null 2>&1 || 
                   curl -s --connect-timeout 2 "http://localhost:$port/" >/dev/null 2>&1; then
                    echo "✅ $service_name HTTP endpoint is responding"
                    return 0
                fi
            else
                return 0
            fi
        fi
        
        if [ $retry -eq 0 ]; then
            echo "⏳ Waiting for $service_name on port $port..."
        fi
        
        sleep 2
        retry=$((retry+1))
        
        # Show progress
        if [ $((retry % 5)) -eq 0 ]; then
            echo "⏳ Still waiting for $service_name... (${retry}/${max_retries})"
        fi
    done
    
    echo "❌ $service_name failed to start on port $port after $((max_retries * 2)) seconds"
    return 1
}

# Start health check server with explicit Python path
echo "🩺 Starting health check server on port 8005..."
cd /workspace/Voxtral-Final
python -m src.api.health_check > /workspace/logs/health.log 2>&1 &
HEALTH_PID=$!
echo "📝 Health server PID: $HEALTH_PID"

# Give health server time to start
echo "⏳ Waiting for health server to initialize..."
sleep 3

# Start CONVERSATIONAL UI server with explicit Python path
echo "🌐 Starting CONVERSATIONAL UI Server on port 8000..."
echo "📋 Using production-ready conversational streaming with VAD"
python -m src.api.ui_server_realtime > /workspace/logs/ui.log 2>&1 &
UI_PID=$!
echo "📝 UI server PID: $UI_PID"

# Give UI server more time to start
echo "⏳ Waiting for UI server to initialize..."
sleep 5

# Start TCP streaming server with explicit Python path  
echo "🔗 Starting TCP streaming server on port 8766..."
echo "📋 Note: Model initialization optimized with VAD and silence detection"
python -m src.streaming.tcp_server > /workspace/logs/tcp.log 2>&1 &
TCP_PID=$!
echo "📝 TCP server PID: $TCP_PID"

# Enhanced service startup verification
echo ""
echo "🔍 Verifying service startup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check services with proper timeouts
services_ok=true

if ! check_service 8005 "Health Check Server"; then
    services_ok=false
    echo "❌ Health Check Server failed to start"
    echo "📋 Check logs: tail -f /workspace/logs/health.log"
fi

if ! check_service 8000 "Conversational UI Server"; then
    services_ok=false
    echo "❌ UI Server failed to start"  
    echo "📋 Check logs: tail -f /workspace/logs/ui.log"
fi

if ! check_service 8766 "TCP Streaming Server"; then
    services_ok=false
    echo "❌ TCP Server failed to start"
    echo "📋 Check logs: tail -f /workspace/logs/tcp.log"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$services_ok" = true ]; then
    echo "🎉 ALL CONVERSATIONAL SERVICES STARTED SUCCESSFULLY!"
else
    echo "❌ Some services failed to start. Check the logs above."
    echo ""
    echo "📋 Debug Information:"
    echo "Health PID: $HEALTH_PID (running: $(ps -p $HEALTH_PID > /dev/null && echo 'yes' || echo 'no'))"
    echo "UI PID: $UI_PID (running: $(ps -p $UI_PID > /dev/null && echo 'yes' || echo 'no'))"  
    echo "TCP PID: $TCP_PID (running: $(ps -p $TCP_PID > /dev/null && echo 'yes' || echo 'no'))"
    echo ""
    echo "📋 Log files for debugging:"
    echo "- Health: /workspace/logs/health.log"
    echo "- UI: /workspace/logs/ui.log"
    echo "- TCP: /workspace/logs/tcp.log"
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
echo "  📄 Main System:      /workspace/logs/voxtral_streaming.log"
echo "  🩺 Health Check:     /workspace/logs/health.log"
echo "  🌐 UI Server:        /workspace/logs/ui.log"
echo "  🔗 TCP Server:       /workspace/logs/tcp.log"
echo "  🗣️  Conversation:     /workspace/logs/conversational/"
echo ""
echo "🎯 PRODUCTION FEATURES (NEW):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Voice Activity Detection (VAD) implemented"
echo "  ✅ Silence detection and filtering"
echo "  ✅ Robust audio validation with amplitude thresholds"
echo "  ✅ Fixed import paths and module resolution"
echo "  ✅ Enhanced error handling and logging"
echo "  ✅ Production-ready service health monitoring"
echo "  ✅ Optimized for real conversation flow"
echo ""
echo "🚀 How to Have a Production Conversation:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. 🔗 Open the Conversational UI in your browser"
echo "  2. 🎵 Click 'Connect' to establish connection"
echo "  3. 🎙️  Choose mode: 'Simple Transcription' or 'Smart Conversation'"
echo "  4. 🗣️  Click 'Start Conversation' and speak clearly!"
echo "  5. 🤫 System will detect silence and won't respond to quiet periods"
echo "  6. 👀 Watch natural conversation responses appear"
echo "  7. 🛑 Click 'Stop Conversation' when done"
echo ""
echo "📋 Production Notes:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ⏳ First conversation initializes model (30-45 seconds)"
echo "  ⚡ Subsequent responses optimized for <300ms target"
echo "  🔇 VAD prevents responses to silent audio"
echo "  🎚️  Amplitude threshold filters background noise"
echo "  📊 Enhanced logging for production monitoring"
echo "  🔧 All import paths and dependencies resolved"
echo ""

echo "🔄 Production Conversational Server is now running!"
echo "📊 Monitor logs in real-time: tail -f /workspace/logs/*.log"
echo ""
echo "🛑 Press Ctrl+C to stop all servers"
echo ""

# Wait for all processes to complete (servers run indefinitely)
wait $HEALTH_PID $UI_PID $TCP_PID
