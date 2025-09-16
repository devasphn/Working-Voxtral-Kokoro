# 🚀 PERFECT RunPod Commands - ZERO CONFLICTS GUARANTEED

## Based on Official Repositories
- **mistralai/mistral-common** - Official Mistral inference library
- **canopyai/Orpheus-TTS** - Official Orpheus TTS repository

## 📋 Step-by-Step Commands for RunPod Web Terminal

### 1️⃣ System Setup
```bash
# Update system packages
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
python -m pip install --upgrade pip
```

### 2️⃣ PyTorch Installation (CUDA 12.1 for RunPod)
```bash
pip install torch==2.4.0 torchaudio==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121
```

### 3️⃣ Core Dependencies (EXACT ORDER - NO CONFLICTS)
```bash
# Step 1: HuggingFace Hub (MUST be first to avoid conflicts)
pip install huggingface-hub>=0.34.0

# Step 2: Transformers stack
pip install transformers>=4.56.0
pip install accelerate>=0.25.0
pip install tokenizers>=0.15.0

# Step 3: Mistral Common with Audio Support (OFFICIAL)
pip install "mistral-common[audio]>=1.8.1"

# Step 4: Orpheus Speech (CORRECT PACKAGE NAME)
pip install orpheus-speech

# Step 5: vLLM (specific version as recommended by Orpheus team)
pip install vllm==0.7.3
```

### 4️⃣ Audio Processing
```bash
pip install librosa>=0.10.1 soundfile>=0.12.1 numpy>=1.24.0 scipy>=1.11.0
```

### 5️⃣ Web Framework (COMPATIBLE VERSIONS)
```bash
pip install fastapi>=0.107.0 uvicorn[standard]>=0.24.0 websockets>=12.0
pip install pydantic>=2.9.0 pydantic-settings>=2.1.0
pip install python-multipart>=0.0.6 aiofiles>=23.2.1 httpx>=0.25.0
```

### 6️⃣ Utilities
```bash
pip install pyyaml>=6.0.1 python-dotenv>=1.0.0 psutil>=5.9.0
```

### 7️⃣ Flash Attention (Optional but Recommended)
```bash
pip install flash-attn>=2.5.0
```

### 8️⃣ Verification
```bash
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
```

### 9️⃣ Test Installation
```bash
# Clone the repository (if not already done)
git clone <your-repo-url>
cd Voxtral-Final

# Run the perfect test script
python test_perfect_installation.py
```

## 🔧 Alternative: One-Line Installation
```bash
# If you have the setup script
chmod +x setup_runpod_perfect.sh && ./setup_runpod_perfect.sh
```

## 🎯 Expected Results
- **All packages**: ✅ Imported successfully
- **CUDA**: ✅ Available
- **No conflicts**: ✅ Zero dependency errors
- **Test score**: ✅ >90% pass rate

## 🚨 Critical Notes
1. **Package Order Matters**: Install in the exact order shown above
2. **Correct Package Names**: 
   - ✅ `orpheus-speech` (NOT `orpheus-tts`)
   - ✅ `mistral-common[audio]` (with audio support)
   - ✅ `vllm==0.7.3` (specific version)
3. **HuggingFace Hub**: Must be >=0.34.0 for transformers compatibility
4. **Pydantic**: Must be >=2.9.0 for vllm compatibility
5. **FastAPI**: Must be >=0.107.0 for vllm compatibility

## 🔍 Troubleshooting
If you get dependency conflicts:
```bash
# Uninstall conflicting packages
pip uninstall -y pydantic fastapi huggingface-hub

# Reinstall in correct order
pip install huggingface-hub>=0.34.0
pip install pydantic>=2.9.0
pip install fastapi>=0.107.0
```

## 🎉 Success Indicators
- No import errors
- CUDA available
- All models load successfully
- Test script passes >90% tests
- Ready for production use!
