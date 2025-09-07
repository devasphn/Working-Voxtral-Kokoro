#!/bin/bash
# Setup script for Voxtral Real-time Streaming on RunPod

set -e

echo "=== Voxtral Real-time Streaming Setup ==="

# Create necessary directories
mkdir -p /workspace/logs
mkdir -p /workspace/model_cache
mkdir -p /workspace/audio_buffer

# Update system packages
apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    ffmpeg \
    sox \
    git

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download and cache the Voxtral model
echo "Downloading Voxtral model..."
python -c "
import torch
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import os

model_name = 'mistralai/Voxtral-Mini-3B-2507'
cache_dir = '/workspace/model_cache'

print(f'Loading {model_name}...')
processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
model = VoxtralForConditionalGeneration.from_pretrained(
    model_name, 
    cache_dir=cache_dir,
    torch_dtype=torch.bfloat16,
    device_map='auto'
)
print('Model loaded and cached successfully!')
"

# Set environment variables
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Make scripts executable
chmod +x run.sh

echo "Setup completed successfully!"
echo "Run './run.sh' to start the streaming server"
