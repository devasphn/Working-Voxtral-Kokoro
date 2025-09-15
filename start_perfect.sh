#!/bin/bash

echo "🚀 Starting Perfect Voxtral + Orpheus TTS System"
echo "==============================================="

# Set environment variables for optimal performance
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export TRANSFORMERS_CACHE="./model_cache"
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:1024
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

# Create necessary directories
mkdir -p logs
mkdir -p model_cache

echo "🎯 Starting perfect system..."
python -m src.api.ui_server_realtime