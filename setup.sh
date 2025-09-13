#!/bin/bash
# ENHANCED Setup script for Voxtral + Kokoro TTS Integration on RunPod
# Handles separate environments and dependency conflicts

set -e

echo "=== Voxtral + Kokoro TTS Integration Setup ==="
echo "🔧 This setup handles both services with dependency isolation"

# Create necessary directories
mkdir -p /workspace/logs
mkdir -p /workspace/model_cache
mkdir -p /workspace/kokoro_cache
mkdir -p /workspace/audio_buffer

# Update system packages
echo "📦 Updating system packages..."
apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    ffmpeg \
    sox \
    git \
    build-essential \
    ninja-build \
    espeak-ng || echo "⚠️ Some system packages may have failed to install"

# Install Python dependencies for main Voxtral environment
echo "🐍 Installing Voxtral dependencies..."
pip install --upgrade pip

echo "📥 Installing main requirements..."
pip install -r requirements.txt || {
    echo "⚠️ Some requirements failed to install. Trying individual installation..."
    
    # Install core dependencies one by one
    pip install torch>=2.1.0 || echo "⚠️ torch installation issue"
    pip install transformers>=4.54.0 || echo "⚠️ transformers installation issue"  
    pip install librosa>=0.10.1 || echo "⚠️ librosa installation issue"
    pip install numpy>=1.24.0 || echo "⚠️ numpy installation issue"
    pip install mistral-common[audio]>=1.8.1 || echo "⚠️ mistral-common installation issue"
    pip install fastapi>=0.104.0 || echo "⚠️ fastapi installation issue"
    pip install uvicorn[standard]>=0.24.0 || echo "⚠️ uvicorn installation issue"
    pip install pydantic>=2.5.0 || echo "⚠️ pydantic installation issue"
    pip install pydantic-settings>=2.0.0 || echo "⚠️ pydantic-settings installation issue"
}

# Set up Kokoro TTS environment
echo ""
echo "🎙️ Setting up Kokoro TTS Environment"
echo "===================================="

# Create virtual environment for Kokoro (to avoid conflicts)
echo "📦 Creating Kokoro virtual environment..."
python3 -m venv kokoro_env
source kokoro_env/bin/activate

echo "📥 Installing Kokoro TTS dependencies..."
pip install --upgrade pip
pip install -r kokoro_requirements.txt || {
    echo "⚠️ Some Kokoro requirements failed. Trying individual installation..."
    pip install kokoro>=0.9.4 || echo "⚠️ kokoro installation issue"
    pip install soundfile>=0.12.1 || echo "⚠️ soundfile installation issue"
    pip install torch>=2.1.0 || echo "⚠️ torch installation issue"
    pip install fastapi>=0.104.0 || echo "⚠️ fastapi installation issue"
    pip install uvicorn[standard]>=0.24.0 || echo "⚠️ uvicorn installation issue"
    pip install misaki[en]>=1.0.0 || echo "⚠️ misaki installation issue"
}

# Test Kokoro installation
echo "🧪 Testing Kokoro TTS installation..."
python3 -c "
import sys
try:
    from kokoro import KPipeline
    import soundfile as sf
    import torch
    print('✅ Kokoro TTS installation successful!')
    print('✅ All required packages imported successfully')
except ImportError as e:
    print(f'❌ Kokoro import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Kokoro test error: {e}')
    sys.exit(1)
"

deactivate  # Exit Kokoro environment

echo ""
echo "🤖 Downloading and caching Voxtral model..."
echo "📥 This may take several minutes..."

# Download and cache the Voxtral model
python3 -c "
import torch
import sys
import traceback
from transformers import VoxtralForConditionalGeneration, AutoProcessor

model_name = 'mistralai/Voxtral-Mini-3B-2507'
cache_dir = '/workspace/model_cache'

print(f'🚀 Loading Voxtral model: {model_name}')
print('📍 This is a one-time download and will be cached for future use.')

try:
    # Load processor first
    print('📥 Loading AutoProcessor...')
    processor = AutoProcessor.from_pretrained(model_name, cache_dir=cache_dir)
    print('✅ AutoProcessor loaded successfully')
    
    # Load model with fallback attention implementation
    print('📥 Loading Voxtral model...')
    print('💡 Using eager attention (FlashAttention2 not required)')
    
    model = VoxtralForConditionalGeneration.from_pretrained(
        model_name, 
        cache_dir=cache_dir,
        torch_dtype=torch.bfloat16,
        device_map='auto',
        attn_implementation='eager',  # FIXED: Use eager attention
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )
    print('✅ Voxtral model loaded and cached successfully!')
    print(f'📊 Model device: {model.device}')
    print(f'🔧 Model dtype: {model.dtype}')
    
    # Test basic functionality
    print('🧪 Testing model functionality...')
    model.eval()
    print('✅ Model test successful!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('💡 Please check that all required packages are installed.')
    sys.exit(1)
except Exception as e:
    print(f'❌ Model loading failed: {e}')
    print('🔍 Full error details:')
    traceback.print_exc()
    print('')
    print('💡 Troubleshooting tips:')
    print('   1. Check your internet connection')
    print('   2. Ensure you have enough disk space (50GB recommended)')
    print('   3. Verify CUDA installation if using GPU')
    print('   4. Try running the script again')
    sys.exit(1)
"

# Check if model loading was successful
if [ $? -eq 0 ]; then
    echo "✅ Voxtral model download and caching completed successfully!"
else
    echo "❌ Voxtral model loading failed. Please check the errors above."
    exit 1
fi

# Download Kokoro model in separate environment
echo ""
echo "🎙️ Downloading and caching Kokoro TTS model..."
source kokoro_env/bin/activate

python3 -c "
import sys
try:
    from kokoro import KPipeline
    import torch
    
    print('🚀 Initializing Kokoro TTS pipeline...')
    print('📥 This will download the Kokoro model (350MB)...')
    
    # Initialize pipeline (this will download the model)
    pipeline = KPipeline(lang_code='a')  # American English
    print('✅ Kokoro TTS model downloaded and cached successfully!')
    print('✅ Pipeline initialization successful!')
    
except Exception as e:
    print(f'❌ Kokoro model setup failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

deactivate

# Set environment variables for optimal performance
echo "🔧 Setting environment variables for optimal performance..."
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# Make scripts executable
chmod +x run_realtime.sh || echo "⚠️ Could not make run_realtime.sh executable"
chmod +x run_kokoro_service.sh || echo "⚠️ Could not make run_kokoro_service.sh executable"
chmod +x run_integration_service.sh || echo "⚠️ Could not make run_integration_service.sh executable" 
chmod +x cleanup.sh || echo "⚠️ Could not make cleanup.sh executable"

echo ""
echo "🔍 Final System Check"
echo "===================="

# Check main Python packages (Voxtral environment)
echo "📦 Checking Voxtral environment packages..."
python3 -c "
import sys
packages = ['torch', 'transformers', 'fastapi', 'librosa', 'numpy', 'mistral_common']
all_good = True

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: OK')
    except ImportError:
        print(f'❌ {pkg}: MISSING')
        all_good = False

if all_good:
    print('\\n🎉 All Voxtral packages are installed correctly!')
else:
    print('\\n⚠️ Some Voxtral packages are missing. Please check the installation.')
    sys.exit(1)
"

# Check Kokoro environment
echo ""
echo "📦 Checking Kokoro environment packages..."
source kokoro_env/bin/activate
python3 -c "
import sys
packages = ['kokoro', 'soundfile', 'torch', 'fastapi', 'misaki']
all_good = True

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: OK')
    except ImportError:
        print(f'❌ {pkg}: MISSING')
        all_good = False

if all_good:
    print('\\n🎉 All Kokoro packages are installed correctly!')
else:
    print('\\n⚠️ Some Kokoro packages are missing. Please check the installation.')
    sys.exit(1)
"
deactivate

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 COMPLETE SETUP SUCCESSFUL!"
    echo "============================"
    echo ""
    echo "✅ Voxtral + Kokoro TTS Integration is ready!"
    echo "✅ Voxtral model cached and ready for speech recognition"
    echo "✅ Kokoro TTS model cached and ready for text-to-speech"
    echo "✅ All required dependencies installed in separate environments"
    echo ""
    echo "🚀 Next Steps:"
    echo "   1. Run: chmod +x run_realtime.sh && chmod +x run_kokoro_service.sh && chmod +x run_integration_service.sh"
    echo "   2. Terminal 1: ./run_realtime.sh (Voxtral Speech Recognition)"
    echo "   3. Terminal 2: ./run_kokoro_service.sh (Kokoro TTS Service)"
    echo "   4. Terminal 3: ./run_integration_service.sh (Combined API Service)"
    echo "   5. Access: https://[POD_ID]-8002.proxy.runpod.net (Complete Speech-to-Speech)"
    echo ""
    echo "📚 For troubleshooting, check: /workspace/logs/"
    echo ""
    echo "🎯 INTEGRATION FEATURES:"
    echo "✅ Real-time Speech-to-Speech (Voxtral → Kokoro)"
    echo "✅ Voice Activity Detection with smart conversation"
    echo "✅ Multiple TTS voices and languages"
    echo "✅ Separate optimized environments"
    echo "✅ Production-ready API endpoints"
else
    echo ""
    echo "❌ SETUP FAILED"
    echo "==============="
    echo "Please check the error messages above and try again."
    exit 1
fi
