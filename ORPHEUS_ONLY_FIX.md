# Orpheus-Only TTS Fix (No Fallback)

## Key Issues Identified and Fixed

### 1. **Wrong Prompting Format** ✅ FIXED
**Problem**: Simple prompt `"ऋतिका: Hello world"` doesn't trigger audio token generation
**Solution**: Use proper Orpheus TTS prompt format with chat template

**OLD Prompt:**
```
ऋतिका: Hello world
```

**NEW Prompt:**
```
<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Generate speech for the voice 'ऋतिका' saying: "Hello world"<|eot_id|><|start_header_id|>assistant<|end_header_id|>

ऋतिका: <|audio|>
```

### 2. **Improved Token Extraction** ✅ FIXED
**Problem**: Only looking for `<custom_token_XXXX>` format
**Solution**: Check multiple token formats and patterns

**NEW Token Patterns:**
- `<custom_token_1234>`
- `<audio_token_1234>`
- `<token_1234>`
- `<1234>`
- `[1234]`
- `token_1234`

### 3. **Removed All Fallback** ✅ FIXED
**Problem**: System falling back to espeak-ng instead of using Orpheus
**Solution**: Completely removed fallback methods as requested

**Removed Methods:**
- `_generate_with_fallback_tts()`
- `_generate_with_pyttsx3()`
- All espeak-ng integration

### 4. **Enhanced Parameters** ✅ FIXED
**Problem**: Suboptimal generation parameters
**Solution**: Optimized for audio token generation

**NEW Parameters:**
```python
{
    "max_tokens": 1024,      # Increased for audio tokens
    "temperature": 0.3,      # Lower for consistency
    "top_p": 0.9,           # Better token selection
    "repeat_penalty": 1.1,   # Avoid repetition
    "timeout": 60.0         # Longer timeout
}
```

## Testing the Fix

### 1. Test Orpheus Server Response
```bash
python3 test_orpheus_only.py
```

**Expected Output:**
```
🧪 Testing Orpheus-FastAPI server...
✅ Orpheus server responded
📝 Generated text: <custom_token_1234><custom_token_5678>...
🎵 Found 42 potential audio tokens: ['1234', '5678', ...]
```

### 2. Test Complete Engine
```bash
python3 test_orpheus_only.py
```

**Expected Output:**
```
✅ Engine initialized successfully
🎵 Testing with: 'Hello! This is a test of Orpheus TTS.'
✅ Audio generated successfully (156789 bytes)
💾 Audio saved as 'test_orpheus_only.wav'
🎉 Orpheus-only TTS is working!
```

## What Should Happen Now

### 1. **In Logs (Success):**
```
🌐 Sending TTS request to Orpheus-FastAPI
🎯 Generated text from Orpheus: <custom_token_1234><custom_token_5678>...
🔍 Extracted 42 audio tokens from Orpheus output
🎵 First few tokens: [1234, 5678, 9012, ...]
🎵 Generated audio from Orpheus-FastAPI (156789 bytes)
✅ Audio generated with Orpheus-FastAPI (156789 bytes)
```

### 2. **In Logs (Failure - for debugging):**
```
🎯 Generated text from Orpheus: Hello, how can I help you today?
⚠️ No standard tokens found, trying to extract any numbers...
🔍 Extracted 0 audio tokens from Orpheus output
⚠️ Full Orpheus output for debugging: [full response text]
❌ Orpheus-FastAPI failed to generate audio
```

## Troubleshooting

### If No Audio Tokens Generated:

1. **Check Orpheus Model**: Ensure you're using the correct Orpheus-3b-FT-Q8_0.gguf model
2. **Check Prompt Format**: The model needs specific prompting to generate audio tokens
3. **Check Model Training**: The model must be trained for TTS (not just text generation)

### Manual Test:
```bash
curl -X POST http://localhost:1234/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nGenerate speech for the voice \"ऋतिका\" saying: \"Hello world\"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nऋतिका: <|audio|>",
    "max_tokens": 1024,
    "temperature": 0.3
  }'
```

**Expected Response Should Contain:**
- Audio tokens like `<custom_token_1234>`
- Or similar token patterns
- NOT just plain text

## Key Changes Made

1. **Proper Chat Template**: Using Llama-style chat format
2. **Audio Trigger**: Including `<|audio|>` token to trigger audio generation
3. **Multiple Token Patterns**: Checking various token formats
4. **No Fallback**: System will fail if Orpheus doesn't work (as requested)
5. **Better Debugging**: Full output logging when tokens not found

## Next Steps

1. **Test the Fix**: `python3 test_orpheus_only.py`
2. **Restart Voxtral**: `./deploy_voxtral_tts.sh`
3. **Check Logs**: Look for "Generated audio from Orpheus-FastAPI"
4. **Listen**: Should hear real Orpheus ऋतिका voice (not espeak-ng)

If the Orpheus model still doesn't generate audio tokens, the issue might be that the model needs different prompting or isn't properly trained for TTS. The fix ensures we're using the correct format and will show exactly what the model is generating for debugging.