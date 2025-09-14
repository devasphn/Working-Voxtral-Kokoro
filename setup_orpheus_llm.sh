#!/bin/bash
# Setup script for Orpheus TTS with LLM server integration
# This script sets up llama.cpp server for token generation

set -e

echo "🚀 Setting up Orpheus TTS with LLM Server"
echo "=========================================="

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
mkdir -p /workspace/llm_models
mkdir -p /workspace/llama_cpp
mkdir -p /workspace/logs

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3-dev \
    libopenblas-dev \
    pkg-config

# Check if we need to build llama.cpp
if ! command_exists llama-server; then
    echo "🔧 Building llama.cpp..."
    
    cd /workspace/llama_cpp
    
    # Clone llama.cpp if not exists
    if [ ! -d "llama.cpp" ]; then
        git clone https://github.com/ggerganov/llama.cpp.git
    fi
    
    cd llama.cpp
    git pull  # Get latest version
    
    # Build with CUDA support if available
    if command_exists nvcc; then
        echo "🚀 Building with CUDA support..."
        make clean
        make LLAMA_CUDA=1 -j$(nproc)
    else
        echo "🔧 Building with CPU support..."
        make clean
        make -j$(nproc)
    fi
    
    # Create symlink for easier access
    ln -sf /workspace/llama_cpp/llama.cpp/llama-server /usr/local/bin/llama-server
    
    echo "✅ llama.cpp built successfully"
else
    echo "✅ llama.cpp already available"
fi

# Download a suitable model for TTS token generation
echo "📥 Downloading TTS-compatible model..."
cd /workspace/llm_models

# Use a smaller, faster model suitable for TTS token generation
MODEL_URL="https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/pytorch_model.bin"
MODEL_NAME="tts_model.gguf"

# For now, we'll use a placeholder - in production you'd want a model specifically trained for TTS
if [ ! -f "$MODEL_NAME" ]; then
    echo "⚠️ TTS model not found. You need to provide a GGUF model file."
    echo "💡 Please download a suitable GGUF model and place it at: /workspace/llm_models/$MODEL_NAME"
    echo "💡 For testing, you can use any small GGUF model (e.g., TinyLlama, Phi-2)"
    
    # Create a placeholder script to download a test model
    cat > download_test_model.sh << 'EOF'
#!/bin/bash
# Download a test model for TTS token generation
echo "📥 Downloading test model (TinyLlama)..."
wget -O tts_model.gguf "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.q4_k_m.gguf"
echo "✅ Test model downloaded"
EOF
    chmod +x download_test_model.sh
    
    echo "🔧 Run './download_test_model.sh' to download a test model"
fi

# Create LLM server startup script
echo "📝 Creating LLM server startup script..."
cat > /workspace/start_llm_server.sh << 'EOF'
#!/bin/bash
# Start LLM server for Orpheus TTS token generation

MODEL_PATH="/workspace/llm_models/tts_model.gguf"
PORT=8010

echo "🚀 Starting LLM server for Orpheus TTS..."
echo "📍 Model: $MODEL_PATH"
echo "🌐 Port: $PORT"

if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model file not found: $MODEL_PATH"
    echo "💡 Please download a GGUF model file first"
    exit 1
fi

# Start llama-server with TTS-optimized settings
llama-server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port $PORT \
    --ctx-size 2048 \
    --batch-size 512 \
    --threads $(nproc) \
    --n-gpu-layers 32 \
    --verbose \
    --log-format text \
    2>&1 | tee /workspace/logs/llm_server.log
EOF

chmod +x /workspace/start_llm_server.sh

# Create test script for LLM server
echo "📝 Creating LLM server test script..."
cat > /workspace/test_llm_server.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for LLM server connectivity
"""

import requests
import json
import time

def test_llm_server():
    """Test if LLM server is responding"""
    server_url = "http://localhost:8010"
    
    print("🧪 Testing LLM server connectivity...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{server_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ LLM server is healthy")
        else:
            print(f"⚠️ LLM server health check returned: {response.status_code}")
        
        # Test completion endpoint
        test_prompt = "ऋतिका: Hello, this is a test."
        
        response = requests.post(
            f"{server_url}/completion",
            json={
                "prompt": test_prompt,
                "max_tokens": 50,
                "temperature": 0.7,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ LLM server completion test successful")
            print(f"📝 Generated: {result.get('content', 'No content')[:100]}...")
            return True
        else:
            print(f"❌ LLM server completion test failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LLM server on port 8010")
        print("💡 Make sure to start the LLM server first: ./start_llm_server.sh")
        return False
    except Exception as e:
        print(f"❌ LLM server test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_server()
    exit(0 if success else 1)
EOF

chmod +x /workspace/test_llm_server.py

# Create integrated startup script
echo "📝 Creating integrated startup script..."
cat > /workspace/start_orpheus_system.sh << 'EOF'
#!/bin/bash
# Start complete Orpheus TTS system with LLM server

echo "🚀 Starting Complete Orpheus TTS System"
echo "======================================="

# Check if LLM server is already running
if lsof -Pi :8010 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ LLM server already running on port 8010"
else
    echo "🔧 Starting LLM server..."
    ./start_llm_server.sh &
    LLM_PID=$!
    
    # Wait for LLM server to start
    echo "⏳ Waiting for LLM server to start..."
    sleep 10
    
    # Test LLM server
    python3 test_llm_server.py
    if [ $? -eq 0 ]; then
        echo "✅ LLM server is ready"
    else
        echo "❌ LLM server failed to start properly"
        exit 1
    fi
fi

# Start Voxtral application
echo "🎙️ Starting Voxtral + Orpheus TTS application..."
./deploy_voxtral_tts.sh

echo "🎉 Complete Orpheus TTS system is running!"
echo "🌐 Web Interface: https://[POD_ID]-8000.proxy.runpod.net"
echo "🤖 LLM Server: http://localhost:8010"
EOF

chmod +x /workspace/start_orpheus_system.sh

# Update requirements for LLM integration
echo "📦 Adding LLM integration dependencies..."
if ! grep -q "httpx" requirements.txt; then
    echo "httpx>=0.25.0  # For LLM server communication" >> requirements.txt
fi

echo ""
echo "🎉 Orpheus TTS + LLM Setup Complete!"
echo "===================================="
echo ""
echo "📋 Next Steps:"
echo "1. Download a GGUF model:"
echo "   cd /workspace/llm_models && ./download_test_model.sh"
echo ""
echo "2. Start the complete system:"
echo "   ./start_orpheus_system.sh"
echo ""
echo "3. Or start components separately:"
echo "   Terminal 1: ./start_llm_server.sh"
echo "   Terminal 2: ./deploy_voxtral_tts.sh"
echo ""
echo "🔧 Configuration:"
echo "   • LLM Server: Port 8010"
echo "   • Voxtral UI: Port 8000"
echo "   • Default Voice: ऋतिका"
echo ""
echo "🧪 Test LLM server: python3 test_llm_server.py"
echo ""
echo "📚 The system will now use:"
echo "   1. LLM server (port 8010) for token generation"
echo "   2. SNAC model for token-to-audio conversion"
echo "   3. ऋतिका voice as default"
echo "   4. Fallback to espeak-ng if LLM server is unavailable"
