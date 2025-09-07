#!/bin/bash
# Process cleanup script for Voxtral Real-time Streaming
# Use this to kill all existing processes before restarting

echo "=== Cleaning up existing Voxtral processes ==="

# Kill all Python processes related to Voxtral streaming
echo "Killing existing processes..."

# Kill by process name patterns
pkill -f "python.*health_check" || true
pkill -f "python.*ui_server" || true  
pkill -f "python.*tcp_server" || true
pkill -f "python.*websocket_server" || true
pkill -f "uvicorn.*ui_server" || true
pkill -f "uvicorn.*health_check" || true

# Kill by port (more aggressive)
echo "Killing processes using specific ports..."

# Check and kill processes using our ports
for port in 8000 8005 8765 8766; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "Killing process $PID using port $port"
        kill -9 $PID 2>/dev/null || true
    fi
done

# Wait a moment for processes to terminate
sleep 2

# Check if ports are now free
echo "Checking port availability..."
for port in 8000 8005 8766; do
    if lsof -i:$port >/dev/null 2>&1; then
        echo "⚠️  Port $port is still in use"
    else
        echo "✅ Port $port is available"
    fi
done

echo "✅ Cleanup completed!"
echo "You can now run ./run.sh to start the servers"
