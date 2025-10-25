# Implementation Roadmap: Achieving <200ms TTFT
## Voxtral Real-time Conversational AI

---

## PHASE 1: Fix Token Batching (5 minutes)

### Problem
Currently waiting for 6 words before sending first chunk, adding 300-500ms latency.

### Solution
Send tokens immediately (1-2 words per chunk).

### Implementation

**File**: `src/models/voxtral_model_realtime.py`  
**Lines**: 646-675

**Current Code**:
```python
# Stream chunks as they're generated
word_buffer = []
first_chunk_received = False

for new_text in streamer:
    if new_text:
        words = new_text.split()
        word_buffer.extend(words)

        # CRITICAL FIX: Log first chunk to detect transcription-only responses
        if not first_chunk_received:
            first_chunk_received = True
            realtime_logger.info(f"📝 [CHUNK {chunk_id}] First generated text: '{new_text}' (mode={mode})")

        # Send chunks of 5-7 words for natural speech
        if len(word_buffer) >= 6:  # ⚠️ BOTTLENECK: Waiting for 6 words
            chunk_text = " ".join(word_buffer[:6])
            word_buffer = word_buffer[6:]
            generated_text += chunk_text + " "

            realtime_logger.debug(f"🎯 Streaming chunk {chunk_index}: '{chunk_text}'")

            yield {
                'success': True,
                'text': chunk_text.strip(),
                'is_final': False,
                'chunk_index': chunk_index,
                'processing_time_ms': (time.time() - chunk_start_time) * 1000
            }
            chunk_index += 1
```

**Fixed Code**:
```python
# Stream chunks as they're generated
word_buffer = []
first_token_time = None
first_chunk_received = False

for new_text in streamer:
    if new_text:
        words = new_text.split()
        word_buffer.extend(words)

        # Track first token latency
        if first_token_time is None:
            first_token_time = time.time() - chunk_start_time
            realtime_logger.info(f"⚡ [CHUNK {chunk_id}] TTFT: {first_token_time*1000:.1f}ms")

        # CRITICAL FIX: Log first chunk to detect transcription-only responses
        if not first_chunk_received:
            first_chunk_received = True
            realtime_logger.info(f"📝 [CHUNK {chunk_id}] First generated text: '{new_text}' (mode={mode})")

        # Send chunks of 1-2 words immediately for real-time streaming
        while len(word_buffer) >= 1:  # ✅ FIXED: Send immediately
            chunk_text = " ".join(word_buffer[:1])  # Send 1 word at a time
            word_buffer = word_buffer[1:]
            generated_text += chunk_text + " "

            realtime_logger.debug(f"🎯 Streaming chunk {chunk_index}: '{chunk_text}'")

            yield {
                'success': True,
                'text': chunk_text.strip(),
                'is_final': False,
                'chunk_index': chunk_index,
                'first_token_latency_ms': int(first_token_time*1000) if first_token_time else None,
                'processing_time_ms': (time.time() - chunk_start_time) * 1000
            }
            chunk_index += 1
```

### Changes Made
1. Changed `if len(word_buffer) >= 6:` to `while len(word_buffer) >= 1:`
2. Changed `word_buffer[:6]` to `word_buffer[:1]` (send 1 word at a time)
3. Added `first_token_time` tracking
4. Added `first_token_latency_ms` to response

### Expected Result
- TTFT: 50-100ms (vs current 300-500ms)
- First word appears immediately
- Remaining words stream continuously

---

## PHASE 2: Fix TTFT Measurement (2 minutes)

### Problem
Currently measuring when first 6-word chunk is ready, not actual first token.

### Solution
Track actual first token generation time separately.

### Implementation

**File**: `src/api/ui_server_realtime.py`  
**Lines**: 1914-1932

**Current Code**:
```python
if text_chunk['success'] and text_chunk['text'].strip():
    # Track first chunk latency
    if first_chunk_time is None:
        first_chunk_time = time.time() - processing_start_time
        streaming_logger.info(f"⚡ First chunk latency: {first_chunk_time*1000:.1f}ms")
```

**Fixed Code**:
```python
if text_chunk['success'] and text_chunk['text'].strip():
    # Track first token latency (from model)
    if first_chunk_time is None:
        first_chunk_time = time.time() - processing_start_time
        first_token_latency = text_chunk.get('first_token_latency_ms')
        streaming_logger.info(f"⚡ TTFT (model): {first_token_latency}ms, First chunk received: {first_chunk_time*1000:.1f}ms")
```

### Expected Result
- Separate tracking of TTFT and first chunk time
- Better understanding of latency breakdown
- Accurate performance metrics

---

## PHASE 3: Enable WebRTC (2 minutes)

### Problem
WebRTC is implemented but disabled, adding 30-80ms overhead.

### Solution
Enable WebRTC in JavaScript.

### Implementation

**File**: `src/api/ui_server_realtime.py`  
**Line**: 466

**Change**:
```javascript
// OLD
let useWebRTC = false;

// NEW
let useWebRTC = true;
```

### Expected Result
- Additional 30-80ms latency reduction
- Lower overhead than WebSocket
- Better for real-time streaming

---

## PHASE 4: Optimize Configuration (3 minutes)

### Problem
Configuration values not matching implementation.

### Solution
Update config to match optimized values.

### Implementation

**File**: `config.yaml`

**Changes**:
```yaml
# Line 57: Update latency targets
streaming:
  latency_target_ms: 100  # TTFT target

# Add new section for targets
performance_targets:
  ttft_ms: 100           # Time to first token
  total_latency_ms: 1000 # Total generation time

# Line 62-63: Update chunk configuration
chunked_response:
  min_words_per_chunk: 1  # Send immediately
  max_words_per_chunk: 2  # Max 2 words per chunk
  chunk_timeout_ms: 50    # Send after 50ms if no more words
```

### Expected Result
- Configuration matches implementation
- Clear performance targets
- Better metrics tracking

---

## PHASE 5: Additional Optimizations (10 minutes)

### Optional Improvements

1. **Reduce Spectrogram Computation**
   - Reduce n_mels from 32 to 16
   - Increase hop_length from 80 to 160
   - Expected: 20-30ms savings

2. **Enable torch.compile**
   - Add torch.compile to model initialization
   - Expected: 50-100ms savings

3. **Optimize Audio Preprocessing**
   - Skip unnecessary normalization
   - Use faster audio conversion
   - Expected: 20-30ms savings

---

## TESTING PROCEDURE

### Test 1: Verify Token Streaming
```bash
# Access via localhost
ssh -L 8000:localhost:8000 ubuntu@98.89.99.129

# Open browser console
http://localhost:8000/

# Speak a sentence
# Check console for token-by-token updates
# Should see: "Hello" then "there" then "how" etc.
# NOT: "Hello there how are you" all at once
```

### Test 2: Measure TTFT
```bash
# Check server logs
tail -f logs/voxtral_streaming.log

# Look for:
# "⚡ TTFT (model): 75ms"
# Should be 50-100ms
```

### Test 3: Measure Total Latency
```bash
# Check server logs
# Look for:
# "✅ CHUNKED STREAMING complete: 15 chunks in 650ms"
# Should be 500-1000ms
```

### Test 4: Verify WebRTC
```bash
# Check browser console
# Should see: "🎯 [WebRTC] Connected with client ID: ..."
# NOT: "WebSocket connected"
```

---

## DEPLOYMENT CHECKLIST

- [ ] Phase 1: Token batching fixed
- [ ] Phase 2: TTFT measurement fixed
- [ ] Phase 3: WebRTC enabled
- [ ] Phase 4: Configuration updated
- [ ] Phase 5: Additional optimizations (optional)
- [ ] All tests passing
- [ ] Performance metrics verified
- [ ] Deployed to AWS EC2
- [ ] Production monitoring active

---

## ROLLBACK PROCEDURE

If issues occur:

1. Revert to previous version: `git checkout HEAD~1`
2. Restart server: `python3 -m src.api.ui_server_realtime`
3. Verify WebSocket still works

---

## EXPECTED PERFORMANCE TIMELINE

| Phase | Change | TTFT | Total | Time |
|-------|--------|------|-------|------|
| Current | Baseline | 300-500ms | 819-6154ms | - |
| Phase 1 | Token batching | 50-100ms | 500-1000ms | 5 min |
| Phase 2 | TTFT tracking | 50-100ms | 500-1000ms | 2 min |
| Phase 3 | WebRTC | 50-100ms | 450-950ms | 2 min |
| Phase 4 | Config | 50-100ms | 450-950ms | 3 min |
| Phase 5 | Optimizations | 50-100ms | 400-900ms | 10 min |

---

## NEXT STEPS

1. Review this roadmap
2. Approve implementation
3. Execute Phase 1-5 in order
4. Test after each phase
5. Deploy to production
6. Monitor performance

**Ready to proceed?**

