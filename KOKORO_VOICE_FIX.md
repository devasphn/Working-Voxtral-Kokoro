# Kokoro TTS Voice Configuration Fix

## 🚨 Issue Identified and Fixed

### Problem: 404 Error on Voice File Download
**Error**: `huggingface_hub.errors.EntryNotFoundError: 404 Client Error. Entry Not Found for url: https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/default.pt`

**Root Cause**: The configuration was using `voice: "default"`, but there is no voice file named "default.pt" in the Kokoro-82M repository.

## ✅ Solution Applied

### 1. **Investigated Available Voices**
Analyzed the hexgrad/Kokoro-82M repository and found 54 available voices across 9 languages:

**American English (lang_code='a')** - 20 voices:
- **af_heart** (Grade A) ⭐ **SELECTED** - Highest quality female voice
- af_bella (Grade A-) - High quality female voice with extensive training
- af_nicole (Grade B-) - Good quality female voice
- Plus 17 other voices (af_alloy, af_aoede, af_jessica, etc.)

**Other Languages Available**:
- British English (8 voices)
- Japanese (5 voices)  
- Mandarin Chinese (8 voices)
- Spanish (3 voices)
- French (1 voice)
- Hindi (4 voices)
- Italian (2 voices)
- Brazilian Portuguese (3 voices)

### 2. **Updated Configuration Files**

**File**: `config.yaml`
```yaml
# Before (BROKEN)
voice: "default"  # This voice doesn't exist!

# After (FIXED)
voice: "af_heart"  # Grade A American English female voice
```

**File**: `src/utils/config.py`
```python
# Before (BROKEN)
voice: str = "default"  # This voice doesn't exist!

# After (FIXED)  
voice: str = "af_heart"  # Grade A American English female voice
```

### 3. **Voice Selection Rationale**

**Selected Voice**: `af_heart`
- **Quality Grade**: A (highest available)
- **Gender**: Female 🚺
- **Language**: American English
- **Special**: ❤️ Heart emoji indicates premium quality
- **Training**: Extensive high-quality training data

**Alternative Recommendations**:
- `af_bella` (Grade A-) - Female, high quality with lots of training
- `af_nicole` (Grade B-) - Female, good quality
- `bf_emma` (Grade B-) - British English female

## 🎯 Expected Results

After this fix, your Kokoro TTS should:

1. ✅ **Download voice files successfully** - No more 404 errors
2. ✅ **Initialize without errors** - Voice file exists and is accessible
3. ✅ **Generate high-quality speech** - Using Grade A voice
4. ✅ **Work as primary TTS** - Reliable fallback from Orpheus

## 🧪 How to Test the Fix

### Option 1: Run Validation Script
```bash
python3 test_kokoro_voice_fix.py
```

### Option 2: Start Your System
```bash
python3 -m src.api.ui_server_realtime
```

### Option 3: Test Kokoro Directly
```python
from kokoro import KPipeline
pipeline = KPipeline(lang_code='a')
generator = pipeline("Hello world", voice='af_heart')
for i, (gs, ps, audio) in enumerate(generator):
    print(f"Generated audio chunk {i}")
    break
```

## 📊 Voice Quality Reference

| Voice | Grade | Gender | Language | Notes |
|-------|-------|--------|----------|-------|
| af_heart | A | 🚺 | American English | ❤️ Premium quality |
| af_bella | A- | 🚺 | American English | 🔥 High quality, extensive training |
| af_nicole | B- | 🚺 | American English | 🎧 Good quality |
| bf_emma | B- | 🚺 | British English | Good quality |
| ff_siwis | B- | 🚺 | French | Only French voice |

## 🔧 Technical Details

### Voice File Structure
- **Repository**: hexgrad/Kokoro-82M
- **Voice Files Location**: `/voices/` directory
- **File Format**: `{voice_name}.pt` (PyTorch model files)
- **File Size**: ~523 KB each
- **Total Voices**: 54 voices across 9 languages

### URL Format
```
https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{voice_name}.pt
```

**Before (BROKEN)**:
```
https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/default.pt
```

**After (FIXED)**:
```
https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/af_heart.pt
```

## 🎵 Voice Naming Convention

Kokoro voices follow this pattern:
- **Language prefix**: `a` (American), `b` (British), `j` (Japanese), etc.
- **Gender**: `f` (female), `m` (male)
- **Name**: Descriptive name like `heart`, `bella`, `emma`

Examples:
- `af_heart` = American Female Heart
- `am_adam` = American Male Adam  
- `bf_emma` = British Female Emma
- `jf_alpha` = Japanese Female Alpha

## 🚀 System Integration

This fix integrates with your Voxtral-Final TTS hierarchy:

```
1. System starts
2. Tries Kokoro TTS with voice='af_heart' ✅
3. Downloads af_heart.pt successfully ✅
4. Initializes Kokoro with high-quality voice ✅
5. If Kokoro fails → Falls back to Orpheus ✅
```

## 🔍 Troubleshooting

### If you still get 404 errors:
1. Check your internet connection
2. Verify Hugging Face access (no authentication needed for this model)
3. Try a different voice: `af_bella` or `af_nicole`

### If voice quality is poor:
1. Try `af_bella` (Grade A-) for different characteristics
2. Adjust `speed` parameter in config (default: 1.0)
3. Check text length (optimal: 100-200 tokens)

### If initialization fails:
1. Ensure `kokoro>=0.9.2` is installed
2. Check that `lang_code='a'` matches voice prefix `af_`
3. Run the validation script for detailed diagnostics

Your Kokoro TTS should now work perfectly with the high-quality `af_heart` voice! 🎉
