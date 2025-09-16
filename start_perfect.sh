#!/bin/bash

# 🚀 PERFECT STARTUP SCRIPT - Voxtral + Orpheus TTS
# Optimized for RunPod with memory constraints
# CRITICAL: This script handles both models with careful memory management

set -e

echo "🚀 Starting PERFECT Voxtral + Orpheus TTS System..."
echo "📊 System: $(uname -a)"
echo "🐍 Python: $(python3 --version)"
echo "🔥 PyTorch: $(python3 -c 'import torch; print(torch.__version__)')"

# Check GPU availability
if ! python3 -c "import torch; print('CUDA Available:', torch.cuda.is_available())"; then
    echo "❌ CUDA not available! This system requires GPU support."
    exit 1
fi

echo "🎯 GPU Memory: $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits) MB"

# Create necessary directories
mkdir -p logs
mkdir -p model_cache

# CRITICAL: Set environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:256,roundup_power2_divisions:16

# CRITICAL: Set HuggingFace token for Orpheus TTS access
# Use provided token for model access
export HF_TOKEN="${HF_TOKEN:-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}"
export HUGGING_FACE_HUB_TOKEN="${HUGGING_FACE_HUB_TOKEN:-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}"

# System optimization
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

# CRITICAL: VLLM memory optimization for Orpheus TTS (extremely reduced for Voxtral coexistence)
export VLLM_GPU_MEMORY_UTILIZATION=0.02
export VLLM_MAX_MODEL_LEN=32

# Disable VLLM logging spam
export VLLM_LOGGING_LEVEL=WARNING

# Model paths - FIXED to match config.yaml
export VOXTRAL_MODEL_PATH="mistralai/Voxtral-Mini-3B-2507"
export ORPHEUS_MODEL_PATH="canopylabs/orpheus-tts-0.1-finetune-prod"

echo "🔧 Environment configured successfully"
echo "📝 Starting unified model system..."

# Start the unified system via the correct entry point
python3 -u -m src.api.ui_server_realtime 2>&1 | tee logs/voxtral_streaming.log

echo "🎉 System startup complete!"
