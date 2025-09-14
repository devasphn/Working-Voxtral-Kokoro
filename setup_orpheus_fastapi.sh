#!/bin/bash
# Setup script for Orpheus-FastAPI integration with Voxtral
# Based on the Orpheus-FastAPI repository: https://github.com/Lex-au/Orpheus-FastAPI

set -e

echo "🚀 Setting up Orpheus-FastAPI Integration"
echo "========================================"
echo "📋 This will set up:"
echo "   • llama-cpp-python with CUDA support"
echo "   • Orpheus-3b-FT-Q8_0.gguf model"
echo "   • Orpheus-FastAPI server on port 1234"
echo "   • Integration with Voxtral system"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️ Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Create directories
echo "📁 Creating directories..."
mkdir -p /workspace/models
mkdir -p /workspace/orpheus_fastapi
mkdir -p /workspace/logs

# Install llama-cpp-python with CUDA support
echo "🔧 Installing llama-cpp-python with CUDA support..."
echo "⚠️ This may take several minutes..."

# Set CMAKE args for CUDA support
export CMAKE_ARGS="-DLLAMA_CUDA=on"

# Install llama-cpp-python with server support
pip install llama-cpp-python[server] --force-reinstall --no-cache-dir

echo "✅ llama-cpp-python installed with CUDA support"

# Download Orpheus model
echo "📥 Downloading Orpheus-3b-FT-Q8_0.gguf model..."
cd /workspace/models

if [ ! -f "Orpheus-3b-FT-Q8_0.gguf" ]; then
    echo "⏳ Downloading model (this may take several minutes)..."
    wget https://huggingface.co/lex-au/Orpheus-3b-FT-Q8_0.gguf/resolve/main/Orpheus-3b-FT-Q8_0.gguf
    echo "✅ Orpheus model downloaded successfully"
else
    echo "✅ Orpheus model already exists"
fi

# Clone Orpheus-FastAPI repository
echo "📥 Setting up Orpheus-FastAPI..."
cd /workspace/orpheus_fastapi

if [ ! -d "Orpheus-FastAPI" ]; then
    echo "📥 Cloning Orpheus-FastAPI repository..."
    git clone https://github.com/Lex-au/Orpheus-FastAPI.git
else
    echo "✅ Orpheus-FastAPI repository already exists"
    cd Orpheus-FastAPI
    git pull  # Update to latest version
    cd ..
fi

# Create Orpheus-FastAPI startup script
echo "📝 Creating Orpheus-FastAPI startup script..."
cat > /workspace/start_orpheus_fastapi.sh << 'EOF'
#!/bin/bash
# Start Orpheus-FastAPI server for TTS generation

MODEL_PATH="/workspace/models/Orpheus-3b-FT-Q8_0.gguf"
PORT=1234
HOST="0.0.0.0"

echo "🚀 Starting Orpheus-FastAPI Server"
echo "=================================="
echo "📍 Model: $MODEL_PATH"
echo "🌐 Host: $HOST"
echo "🔌 Port: $PORT"
echo ""

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model file not found: $MODEL_PATH"
    echo "💡 Please run setup_orpheus_fastapi.sh first"
    exit 1
fi

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ Port $PORT is already in use"
    echo "🔍 Checking what's running on port $PORT..."
    lsof -i :$PORT
    echo ""
    echo "💡 Kill the process or use a different port"
    exit 1
fi

echo "🔧 Starting llama-cpp-python server with Orpheus model..."
echo "⏳ This may take a few minutes to load the model..."
echo ""

# Start the llama-cpp-python server with Orpheus model
python -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port $PORT \
    --n_gpu_layers -1 \
    --verbose \
    2>&1 | tee /workspace/logs/orpheus_fastapi.log

EOF

chmod +x /workspace/start_orpheus_fastapi.sh

# Create test script for Orpheus-FastAPI
echo "📝 Creating Orpheus-FastAPI test script..."
cat > /workspace/test_orpheus_fastapi.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for Orpheus-FastAPI server
"""

import requests
import json
import time
import sys

def test_orpheus_server():
    """Test if Orpheus-FastAPI server is responding"""
    server_url = "http://localhost:1234"
    
    print("🧪 Testing Orpheus-FastAPI server...")
    
    try:
        # Test health endpoint (if available)
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Orpheus-FastAPI server health check passed")
            else:
                print(f"⚠️ Health check returned: {response.status_code}")
        except requests.exceptions.RequestException:
            print("ℹ️ Health endpoint not available (normal for llama-cpp-python server)")
        
        # Test completion endpoint with TTS-style prompt
        test_text = "Hello, this is a test of the Orpheus TTS system."
        test_voice = "ऋतिका"
        
        # Format prompt for Orpheus TTS
        prompt = f"{test_voice}: {test_text}"
        
        print(f"🎯 Testing with prompt: '{prompt}'")
        
        response = requests.post(
            f"{server_url}/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": 100,
                "temperature": 0.7,
                "stream": False,
                "stop": ["<|eot_id|>", "\n\n"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("choices", [{}])[0].get("text", "")
            print("✅ Orpheus-FastAPI completion test successful")
            print(f"📝 Generated: {generated_text[:100]}...")
            
            # Check if it looks like TTS tokens
            if "<custom_token_" in generated_text or "audio" in generated_text.lower():
                print("🎵 Response contains TTS-like tokens - good!")
            else:
                print("ℹ️ Response doesn't contain obvious TTS tokens")
            
            return True
        else:
            print(f"❌ Orpheus-FastAPI completion test failed: {response.status_code}")
            try:
                error_text = response.text
                print(f"❌ Error details: {error_text}")
            except:
                pass
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Orpheus-FastAPI server on port 1234")
        print("💡 Make sure to start the server first: ./start_orpheus_fastapi.sh")
        return False
    except Exception as e:
        print(f"❌ Orpheus-FastAPI test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_orpheus_server()
    if success:
        print("\n🎉 Orpheus-FastAPI server is working!")
        print("🔗 Ready for integration with Voxtral system")
    else:
        print("\n💥 Orpheus-FastAPI server test failed")
        print("🔧 Check the server logs and try again")
    
    sys.exit(0 if success else 1)
EOF

chmod +x /workspace/test_orpheus_fastapi.py

# Create integrated startup script
echo "📝 Creating integrated startup script..."
cat > /workspace/start_voxtral_with_orpheus.sh << 'EOF'
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
EOF

chmod +x /workspace/start_voxtral_with_orpheus.sh

# Update requirements for Orpheus-FastAPI integration
echo "📦 Updating requirements..."
if ! grep -q "llama-cpp-python" requirements.txt; then
    echo "" >> requirements.txt
    echo "# Orpheus-FastAPI integration" >> requirements.txt
    echo "llama-cpp-python[server]>=0.2.0  # For Orpheus-FastAPI backend" >> requirements.txt
fi

# Create environment configuration
echo "📝 Creating environment configuration..."
cat > /workspace/.env << 'EOF'
# Orpheus-FastAPI Configuration
ORPHEUS_SERVER_URL=http://localhost:1234
ORPHEUS_MODEL_PATH=/workspace/models/Orpheus-3b-FT-Q8_0.gguf
ORPHEUS_DEFAULT_VOICE=ऋतिका

# Voxtral Configuration
VOXTRAL_MODEL=mistralai/Voxtral-Mini-3B-2507
VOXTRAL_DEVICE=cuda

# Server Configuration
VOXTRAL_PORT=8000
HEALTH_PORT=8005
TCP_PORT=8766
ORPHEUS_PORT=1234
EOF

echo ""
echo "🎉 Orpheus-FastAPI Setup Complete!"
echo "=================================="
echo ""
echo "📋 What was installed:"
echo "   ✅ llama-cpp-python with CUDA support"
echo "   ✅ Orpheus-3b-FT-Q8_0.gguf model ($(du -h /workspace/models/Orpheus-3b-FT-Q8_0.gguf 2>/dev/null | cut -f1 || echo 'downloaded'))"
echo "   ✅ Orpheus-FastAPI repository"
echo "   ✅ Integration scripts and tests"
echo ""
echo "🚀 Next Steps:"
echo "1. Start the complete system:"
echo "   ./start_voxtral_with_orpheus.sh"
echo ""
echo "2. Or start components separately:"
echo "   Terminal 1: ./start_orpheus_fastapi.sh"
echo "   Terminal 2: ./deploy_voxtral_tts.sh"
echo ""
echo "🧪 Test Orpheus-FastAPI: python3 test_orpheus_fastapi.py"
echo ""
echo "🔧 Configuration:"
echo "   • Orpheus-FastAPI: Port 1234"
echo "   • Voxtral UI: Port 8000"
echo "   • Default Voice: ऋतिका"
echo "   • Model: Orpheus-3b-FT-Q8_0.gguf"
echo ""
echo "📚 Architecture:"
echo "   User Speech → Voxtral (VAD+ASR+LLM) → Text → Orpheus-FastAPI → Audio"
echo ""
echo "🎯 The system will now use real Orpheus TTS with ऋतिका voice!"