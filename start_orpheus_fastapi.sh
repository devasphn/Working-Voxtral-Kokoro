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
    2>&1 | tee /workspace/logs/orpheus_fastapi.log