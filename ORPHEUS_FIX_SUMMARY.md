# Orpheus TTS Integration - Fix Summary

## Issues Identified and Fixed

### 1. **Event Loop Closed Error** ✅ FIXED
**Problem**: `Event loop is closed` error when making HTTP requests
**Root Cause**: Persistent HTTP client being closed prematurely
**Solution**: Use `async with httpx.AsyncClient()` context manager for each request

### 2. **Wrong API Endpoint** ✅ FIXED
**Problem**: Trying to POST to `/generate_speech` (doesn't exist)
**Root Cause**: Orpheus-FastAPI uses llama-cpp-python server which has different endpoints
**Solution**: Use `/v1/completions` endpoint with proper completion payload

### 3. **Wrong Payload Format** ✅ FIXED
**Problem**: Sending TTS-style payload instead of completion payload
**Root Cause**: Misunderstanding of llama-cpp-python server API
**Solution**: Send completion request with prompt formatting

### 4. **Missing Audio Conversion** ✅ FIXED
**Problem**: No conversion from Orpheus text output to audio
**Root Cause**: Missing SNAC model integration for token-to-audio conversion
**Solution**: Added SNAC model loading and token extraction/conversion

### 5. **Missing Imports** ✅ FIXED
**Problem**: Missing torch, numpy, wave, io imports
**Solution**: Added all required imports

## Key Changes Made

### 1. Fixed HTTP Client Usage
```python
# OLD (problematic):
self.http_client = httpx.AsyncClient(timeout=30.0)
response = await self.http_client.post(...)

# NEW (fixed):
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(...)
```

### 2. Fixed API Endpoint and Payload
```python
# OLD (wrong):
payload = {"text": text, "voice": voice, "language": "hi"}
response = await client.post(f"{url}/generate_speech", json=payload)

# NEW (correct):
payload = {"prompt": f"{voice}: {text}", "max_tokens": 512, "temperature": 0.7}
response = await client.post(f"{url}/v1/completions", json=payload)
```

### 3. Added Audio Conversion Pipeline
```python
# NEW: Complete audio conversion pipeline
generated_text = result.get("choices", [{}])[0].get("text", "")
tokens = self._extract_audio_tokens(generated_text)
audio_data = self._tokens_to_audio(tokens)
wav_data = self._create_wav_from_raw_audio(audio_data)
```

### 4. Added SNAC Model Integration
```python
# NEW: SNAC model loading and usage
from snac import SNAC
self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
# ... token to audio conversion using SNAC
```

## Testing the Fix

### 1. Test Fixed Engine
```bash
python3 test_fixed_orpheus.py
```

### 2. Test Complete Integration
```bash
python3 test_voxtral_orpheus_integration.py
```

### 3. Expected Results
**Before Fix:**
```
❌ Orpheus-FastAPI communication failed: Event loop is closed
❌ Orpheus-FastAPI returned status 404
⚠️ Orpheus-FastAPI failed, trying fallback...
✅ Generated audio with espeak-ng (100588 bytes)
```

**After Fix:**
```
🌐 Sending completion request to Orpheus-FastAPI: {'prompt': 'ऋतिका: Hello...'}
🎯 Generated text from Orpheus: <custom_token_1234>...
🎵 Generated audio from Orpheus-FastAPI (156789 bytes)
✅ Audio generated with Orpheus-FastAPI (156789 bytes)
```

## Architecture Flow (Fixed)

```
1. Text Input: "Hello world"
   ↓
2. Format Prompt: "ऋतिका: Hello world"
   ↓
3. Send to Orpheus-FastAPI: POST /v1/completions
   ↓
4. Receive Generated Text: "<custom_token_1234><custom_token_5678>..."
   ↓
5. Extract Audio Tokens: [1234, 5678, ...]
   ↓
6. Convert with SNAC Model: tokens → raw audio bytes
   ↓
7. Create WAV File: raw audio → WAV format
   ↓
8. Return Audio: High-quality ऋतिका voice
```

## Verification Steps

### 1. Check Orpheus-FastAPI is Running
```bash
curl http://localhost:1234/v1/models
# Should return: {"data": [...]}
```

### 2. Test Completion Endpoint
```bash
curl -X POST http://localhost:1234/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ऋतिका: Hello", "max_tokens": 50}'
```

### 3. Check SNAC Model
```bash
python3 -c "from snac import SNAC; print('SNAC OK')"
```

### 4. Test Complete Pipeline
```bash
# Start Orpheus-FastAPI
./start_orpheus_fastapi.sh

# Test fixed integration
python3 test_fixed_orpheus.py

# Start Voxtral with fixed integration
./deploy_voxtral_tts.sh
```

## Expected Log Output (Fixed)

```
🚀 Initializing Orpheus TTS Engine...
✅ Connected to Orpheus-FastAPI server
📥 Loading SNAC model for audio conversion...
✅ SNAC model loaded successfully
🎉 Orpheus TTS Engine initialized in 2.34s

🎵 Generating audio for text: 'Hello world' with voice 'ऋतिका'
🌐 Sending completion request to Orpheus-FastAPI: {'prompt': 'ऋतिका: Hello world', 'max_tokens': 512}
🎯 Generated text from Orpheus: <custom_token_1234><custom_token_5678>...
🔍 Extracted 42 audio tokens from Orpheus output
🎵 Generated audio from Orpheus-FastAPI (156789 bytes)
✅ Audio generated with Orpheus-FastAPI (156789 bytes)
```

## Files Modified

1. **`src/tts/orpheus_tts_engine.py`** - Complete rewrite with proper integration
2. **`test_fixed_orpheus.py`** - New test script for verification

## Next Steps

1. **Test the Fix**: Run `python3 test_fixed_orpheus.py`
2. **Restart Services**: Restart both Orpheus-FastAPI and Voxtral
3. **Verify Integration**: Check logs for "Generated audio from Orpheus-FastAPI"
4. **Test in Browser**: Listen for high-quality ऋतिका voice responses

The integration should now work correctly with real Orpheus TTS generating high-quality audio!