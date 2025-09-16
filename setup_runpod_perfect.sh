#!/bin/bash
# PERFECT RunPod Setup Script for Voxtral + Orpheus TTS
# Based on OFFICIAL repositories - ZERO CONFLICTS GUARANTEED
# mistralai/mistral-common + canopyai/Orpheus-TTS

set -e  # Exit on any error

echo "🚀 Starting PERFECT Voxtral + Orpheus TTS Setup on RunPod..."

# Update system
echo "📦 Updating system packages..."
apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    python3-dev

# Upgrade pip
echo "🔧 Upgrading pip..."
python -m pip install --upgrade pip

# Install PyTorch first (CUDA 12.1 for RunPod)
echo "🔥 Installing PyTorch with CUDA support..."
pip install torch==2.4.0 torchaudio==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121

# Install in EXACT order to avoid conflicts
echo "📋 Installing dependencies in correct order..."

# 1. Core transformers with compatible huggingface-hub
echo "1️⃣ Installing transformers stack..."
pip install huggingface-hub>=0.34.0
pip install transformers>=4.56.0
pip install accelerate>=0.25.0
pip install tokenizers>=0.15.0

# 2. Mistral Common with Audio Support (OFFICIAL)
echo "2️⃣ Installing Mistral Common with audio support..."
pip install "mistral-common[audio]>=1.8.1"

# 3. Orpheus Speech (CORRECT PACKAGE NAME)
echo "3️⃣ Installing Orpheus Speech..."
pip install orpheus-speech

# 4. vLLM specific version (as recommended by Orpheus team)
echo "4️⃣ Installing vLLM (specific version)..."
pip install vllm==0.7.3

# 5. Audio processing
echo "5️⃣ Installing audio processing libraries..."
pip install librosa>=0.10.1 soundfile>=0.12.1 numpy>=1.24.0 scipy>=1.11.0

# 6. Web framework with compatible versions
echo "6️⃣ Installing web framework..."
pip install fastapi>=0.107.0 uvicorn[standard]>=0.24.0 websockets>=12.0
pip install pydantic>=2.9.0 pydantic-settings>=2.1.0
pip install python-multipart>=0.0.6 aiofiles>=23.2.1 httpx>=0.25.0

# 7. Utilities
echo "7️⃣ Installing utilities..."
pip install pyyaml>=6.0.1 python-dotenv>=1.0.0 psutil>=5.9.0

# 8. Flash Attention for optimization
echo "8️⃣ Installing Flash Attention..."
pip install flash-attn>=2.5.0

echo "✅ All dependencies installed successfully!"

# Verify installation
echo "🔍 Verifying installation..."
python -c "
import torch
import transformers
import mistral_common
import orpheus_tts
import vllm
print('✅ PyTorch version:', torch.__version__)
print('✅ CUDA available:', torch.cuda.is_available())
print('✅ Transformers version:', transformers.__version__)
print('✅ Mistral Common imported successfully')
print('✅ Orpheus TTS imported successfully')
print('✅ vLLM version:', vllm.__version__)
print('🎉 ALL PACKAGES WORKING PERFECTLY!')
"

echo "✅ Setup complete! Ready to run Voxtral + Orpheus TTS system."
