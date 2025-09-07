#!/bin/bash
# Quick test script to verify Voxtral server functionality (UPDATED)

echo "🧪 Testing Voxtral Real-time Streaming Server"
echo "=============================================="

# Function to check if a service is responding
check_service() {
    local url=$1
    local service_name=$2
    
    echo "Testing $service_name at $url..."
    
    if curl -s --connect-timeout 5 "$url" > /dev/null; then
        echo "✅ $service_name is responding"
        return 0
    else
        echo "❌ $service_name is not responding"
        return 1
    fi
}

# Function to check if a port is open
check_port() {
    local port=$1
    local service_name=$2
    
    echo "Checking port $port for $service_name..."
    
    if lsof -i:$port >/dev/null 2>&1; then
        echo "✅ Port $port is open ($service_name)"
        return 0
    else
        echo "❌ Port $port is not open ($service_name)"
        return 1
    fi
}

echo ""
echo "🔍 Step 1: Checking if servers are running..."
echo "---------------------------------------------"

check_port 8000 "UI Server"
check_port 8005 "Health Check"
check_port 8766 "TCP Server"

echo ""
echo "🌐 Step 2: Testing HTTP endpoints..."
echo "------------------------------------"

check_service "http://localhost:8000" "Web UI"
check_service "http://localhost:8005/health" "Health Check"
check_service "http://localhost:8005/status" "Detailed Status"

echo ""
echo "📊 Step 3: Getting server status..."
echo "-----------------------------------"

echo "Health Check Response:"
curl -s http://localhost:8005/health | jq '.' 2>/dev/null || curl -s http://localhost:8005/health

echo ""
echo "Server Status:"
curl -s http://localhost:8005/status | jq '.model.status, .gpu.gpu_available' 2>/dev/null || echo "Status check failed"

echo ""
echo "🎯 Step 4: WebSocket connectivity test..."
echo "-----------------------------------------"

# Simple WebSocket test using wscat if available
if command -v wscat >/dev/null 2>&1; then
    echo "Testing WebSocket connection..."
    timeout 5 wscat -c ws://localhost:8000/ws --wait 3 || echo "WebSocket test completed"
else
    echo "wscat not available, skipping WebSocket test"
    echo "You can test WebSocket manually at: ws://localhost:8000/ws"
fi

echo ""
echo "🔗 Step 5: RunPod URLs (replace POD_ID)..."
echo "------------------------------------------"
echo "Web UI: https://[POD_ID]-8000.proxy.runpod.net"
echo "WebSocket: wss://[POD_ID]-8000.proxy.runpod.net/ws"
echo "Health: https://[POD_ID]-8005.proxy.runpod.net/health"

echo ""
echo "📝 Step 6: Testing with Python client..."
echo "----------------------------------------"

if [ -f "test_client.py" ]; then
    echo "Running Python test client..."
    timeout 30 python test_client.py --test health 2>/dev/null || echo "Python test completed"
else
    echo "test_client.py not found, skipping Python test"
fi

echo ""
echo "✅ Testing completed!"
echo "===================="
echo ""
if lsof -i:8000 >/dev/null 2>&1 && lsof -i:8005 >/dev/null 2>&1; then
    echo "💡 Servers are running! Visit the web UI to start using Voxtral."
    echo "💡 🌐 Web Interface: http://localhost:8000"
    echo "💡 📊 Health Check: http://localhost:8005/health"
    echo "💡 🎙️  Note: First audio processing may take 30+ seconds for model loading"
else
    echo "💡 Some servers are not running. Try:"
    echo "💡 ./cleanup.sh && ./run.sh"
    echo "💡 Check logs: tail -f /workspace/logs/voxtral_streaming.log"
fi
