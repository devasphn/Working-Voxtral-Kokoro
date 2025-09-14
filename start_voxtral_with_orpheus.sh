#!/bin/bash
# Start complete Voxtral + Orpheus-FastAPI system

echo "🚀 Starting Voxtral + Orpheus-FastAPI System"
echo "============================================"

# Function to check if port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Check if Orpheus-FastAPI is already running
if port_in_use 1234; then
    echo "✅ Orpheus-FastAPI already running on port 1234"
else
    echo "🔧 Starting Orpheus-FastAPI server..."
    ./start_orpheus_fastapi.sh &
    ORPHEUS_PID=$!
    
    # Wait for Orpheus-FastAPI to start
    echo "⏳ Waiting for Orpheus-FastAPI to start (this may take a few minutes)..."
    sleep 30
    
    # Test Orpheus-FastAPI server
    python3 test_orpheus_fastapi.py
    if [ $? -eq 0 ]; then
        echo "✅ Orpheus-FastAPI server is ready"
    else
        echo "❌ Orpheus-FastAPI server failed to start properly"
        echo "🔍 Check logs: tail -f /workspace/logs/orpheus_fastapi.log"
        exit 1
    fi
fi

# Start Voxtral application
echo ""
echo "🎙️ Starting Voxtral application with Orpheus-FastAPI integration..."
./deploy_voxtral_tts.sh

echo ""
echo "🎉 Complete Voxtral + Orpheus-FastAPI system is running!"
echo "🌐 Web Interface: https://[POD_ID]-8000.proxy.runpod.net"
echo "🤖 Orpheus-FastAPI: http://localhost:1234"
echo "🎯 Default Voice: ऋतिका"