# Mistral-Common Updates Implementation Guide

**Date**: October 21, 2025
**Current Version**: mistral-common[audio]>=1.8.1
**Target Version**: mistral-common[audio]==1.8.5
**Status**: Ready for implementation

---

## 📦 VERSION HISTORY & CHANGES

### v1.8.5 (September 12, 2025) - LATEST
- ✅ Made model field optional in TranscriptionRequest
- ✅ Removed responses/embedding requests
- ✅ Added transcription documentation
- **Impact**: Better flexibility for transcription requests

### v1.8.4 (August 20, 2025)
- ✅ Made sentencepiece optional
- ✅ Added random padding support
- **Impact**: Cleaner dependencies, better performance

### v1.8.3 (July 25, 2025)
- ✅ Added experimental REST API with FastAPI
- **Impact**: Alternative API interface available

### v1.8.2 (July 24, 2025)
- ✅ Added ThinkChunk for reasoning processes
- **Impact**: Support for reasoning tasks

### v1.8.1 (July 16, 2025)
- ✅ Added AudioURLChunk for URLs, file paths, base64
- **Impact**: Flexible audio input handling

### v1.8.0 (July 15, 2025) - MAJOR RELEASE
- ✅ Added comprehensive audio support
- ✅ AudioChunk, RawAudio, TranscriptionRequest
- ✅ Audio.from_file() method
- **Impact**: Foundation for audio processing

---

## 🔄 UPGRADE STEPS

### Step 1: Update requirements.txt

```bash
# Current
mistral-common[audio]>=1.8.1

# Update to
mistral-common[audio]==1.8.5
```

### Step 2: Install Updated Package

```bash
pip install --upgrade mistral-common[audio]==1.8.5
```

### Step 3: Verify Installation

```bash
python3 -c "import mistral_common; print(mistral_common.__version__)"
```

---

## 💻 CODE CHANGES NEEDED

### 1. Update voxtral_model_realtime.py

**Current Code** (lines 1-30):
```python
try:
    from mistral_common.audio import Audio
    from mistral_common.protocol.instruct.messages import AudioChunk, TextChunk, UserMessage
    MISTRAL_COMMON_AVAILABLE = True
except ImportError:
    Audio = None
    AudioChunk = None
    TextChunk = None
    UserMessage = None
    MISTRAL_COMMON_AVAILABLE = False
```

**Updated Code** (v1.8.5):
```python
try:
    from mistral_common.audio import Audio, AudioURLChunk
    from mistral_common.protocol.instruct.messages import (
        AudioChunk, TextChunk, UserMessage, TranscriptionRequest
    )
    MISTRAL_COMMON_AVAILABLE = True
except ImportError:
    Audio = None
    AudioURLChunk = None
    AudioChunk = None
    TextChunk = None
    UserMessage = None
    TranscriptionRequest = None
    MISTRAL_COMMON_AVAILABLE = False
```

**Changes**:
- ✅ Added `AudioURLChunk` import
- ✅ Added `TranscriptionRequest` import
- ✅ Updated fallback handling

---

### 2. Add AudioURLChunk Support

**New Method** in voxtral_model_realtime.py:

```python
async def transcribe_from_url(self, audio_url: str) -> str:
    """Transcribe audio from URL, file path, or base64 string"""
    try:
        # Create AudioURLChunk from URL/path/base64
        audio_chunk = AudioURLChunk(
            url=audio_url,  # Can be URL, file path, or base64 string
            format="wav"  # or "mp3", "flac", etc.
        )
        
        # Create transcription request
        request = TranscriptionRequest(
            audio=audio_chunk,
            model="mistralai/Voxtral-Mini-3B-2507"  # Optional in v1.8.5
        )
        
        # Process transcription
        response = await self.model.transcribe(request)
        return response.text
        
    except Exception as e:
        logger.error(f"Error transcribing from URL: {e}")
        raise
```

---

### 3. Update audio_processor_realtime.py

**Add Support for Multiple Audio Formats**:

```python
async def process_audio_from_url(self, audio_url: str) -> np.ndarray:
    """Process audio from URL, file path, or base64"""
    try:
        # Load audio using Audio.from_file() (v1.8.0+)
        audio = Audio.from_file(audio_url)
        
        # Convert to numpy array
        audio_array = np.array(audio.data)
        
        # Resample if needed
        if audio.sample_rate != self.sample_rate:
            audio_array = librosa.resample(
                audio_array,
                orig_sr=audio.sample_rate,
                target_sr=self.sample_rate
            )
        
        return audio_array
        
    except Exception as e:
        logger.error(f"Error processing audio from URL: {e}")
        raise
```

---

### 4. Update requirements.txt

```txt
# Mistral Common with Audio Support (UPDATED)
mistral-common[audio]==1.8.5
```

---

## 🧪 TESTING CHECKLIST

- [ ] Install mistral-common==1.8.5
- [ ] Verify imports work correctly
- [ ] Test AudioURLChunk with file path
- [ ] Test AudioURLChunk with base64 string
- [ ] Test TranscriptionRequest with optional model field
- [ ] Verify backward compatibility with existing code
- [ ] Test WebSocket streaming with new APIs
- [ ] Verify latency improvements
- [ ] Test on RunPod deployment

---

## ⚠️ BREAKING CHANGES

**None identified** - v1.8.5 is backward compatible with v1.8.1

---

## 🚀 BENEFITS OF UPGRADE

| Feature | v1.8.1 | v1.8.5 | Benefit |
|---------|--------|--------|---------|
| AudioURLChunk | ❌ | ✅ | Flexible audio input |
| Optional model field | ❌ | ✅ | Simpler API calls |
| Sentencepiece optional | ❌ | ✅ | Smaller dependencies |
| Random padding | ❌ | ✅ | Better performance |
| REST API | ❌ | ✅ | Alternative interface |

---

## 📋 IMPLEMENTATION PRIORITY

1. **HIGH**: Update requirements.txt and install v1.8.5
2. **HIGH**: Update imports in voxtral_model_realtime.py
3. **MEDIUM**: Add AudioURLChunk support
4. **MEDIUM**: Add TranscriptionRequest support
5. **LOW**: Implement REST API support (optional)

---

## 🔗 REFERENCES

- **mistral-common GitHub**: https://github.com/mistralai/mistral-common
- **Audio Support Docs**: https://github.com/mistralai/mistral-common/blob/main/docs/audio.md
- **Release Notes**: https://github.com/mistralai/mistral-common/releases

---

**Status**: Ready for implementation
**Estimated Time**: 30-45 minutes
**Risk Level**: LOW (backward compatible)

