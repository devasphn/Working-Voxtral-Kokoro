# Comprehensive Design Document: Speech-to-Speech Pipeline
## Voxtral Conversational AI with TTS Integration

**Status**: DESIGN PHASE - AWAITING APPROVAL  
**Target**: Replicate Sesame.com Maya experience with open-source components  
**Timeline**: 5 phases × 4-5 minutes each = 20-25 minutes total  

---

## PART 1: CONVERSATION MANAGER ANALYSIS

### Current State
**Finding**: NO conversation memory/context management exists in codebase
- Each interaction processed independently
- `addToSpeechHistory()` function disabled (ui_server_realtime.py:748-750)
- No dialogue history tracking
- No context awareness

### Design: Conversation Manager

**Architecture**:
```
ConversationManager
├── conversation_history: List[Dict]
│   └── Each turn: {role, content, timestamp, latency}
├── context_window: int (default: 5 turns)
├── max_history_size: int (default: 100 turns)
└── Methods:
    ├── add_turn(role, content, metadata)
    ├── get_context(num_turns)
    ├── clear_history()
    └── export_conversation()
```

**Integration Points**:
1. **Input**: After Voxtral ASR transcription
2. **Processing**: Pass context to Voxtral LLM prompt
3. **Output**: Store AI response in history
4. **WebSocket**: Send conversation state to frontend

**Implementation Complexity**: LOW (50-100 lines of code)

**Files to Create**:
- `src/managers/conversation_manager.py` (new)

**Files to Modify**:
- `src/api/ui_server_realtime.py` (integrate history)
- `src/models/voxtral_model_realtime.py` (use context in prompt)

---

## PART 2: TTS RESEARCH & RECOMMENDATION

### TTS Models Comparison

| Model | License | Languages | Quality | Latency | Indian | SEA | Notes |
|-------|---------|-----------|---------|---------|--------|-----|-------|
| **Kokoro** | MIT ✅ | English | Excellent | Very Fast | ❌ | ❌ | Fastest, English-only |
| **Chatterbox** | MIT ✅ | 23 langs | Excellent | Fast | ✅ Hindi | ? | Multilingual, production-grade |
| **Orpheus** | Apache 2.0 ✅ | Multilingual | Excellent | Medium | ? | ? | Flexible, expressive |
| **Dia** | Apache 2.0 ✅ | Multi | Good | Medium | ❌ | ✅ Malaysian | SEA focused |
| **FireRedTTS** | Open ✅ | Multi | Good | Medium | ? | ✅ | Multilingual |
| **Indic-TTS** | Open ✅ | 13 Indian | Good | Medium | ✅ All | ❌ | Indian specialist |

### Recommended Solution: HYBRID APPROACH

**Primary TTS**: **Chatterbox TTS** (MIT License)
- ✅ 23 languages including Hindi
- ✅ MIT License (commercial use allowed)
- ✅ Production-grade quality
- ✅ Multilingual, zero-shot
- ✅ Exaggeration/intensity control
- ✅ 0.5B Llama backbone (lightweight)

**Fallback for SEA**: **Dia-TTS** (Apache 2.0)
- ✅ Malaysian language support
- ✅ Apache 2.0 License
- ✅ Can be used for Tagalog/Filipino

**Fallback for Indian**: **Indic-TTS** (AI4Bharat)
- ✅ 13 Indian languages
- ✅ Open source
- ✅ Specialized for Indian languages

**Language Coverage**:
```
Chatterbox (Primary):
├── English ✅
├── Hindi ✅
├── Spanish ✅
├── Mandarin ✅
├── Arabic ✅
└── 18 more languages

Dia-TTS (SEA Fallback):
├── Malaysian ✅
├── Chinese ✅
├── English ✅
└── Japanese ✅

Indic-TTS (Indian Fallback):
├── Hindi ✅
├── Tamil ✅
├── Telugu ✅
├── Marathi ✅
└── 9 more Indian languages
```

### Licensing Verification
- ✅ Chatterbox: MIT (commercial use allowed)
- ✅ Dia-TTS: Apache 2.0 (commercial use allowed)
- ✅ Indic-TTS: Open source (commercial use allowed)

---

## PART 3: SPEECH-TO-SPEECH PIPELINE ARCHITECTURE

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ SPEECH-TO-SPEECH PIPELINE                                   │
└─────────────────────────────────────────────────────────────┘

1. AUDIO INPUT
   ├─ Microphone → Browser → WebSocket/WebRTC
   └─ 16kHz, mono, float32

2. VAD (Voice Activity Detection)
   ├─ Detect speech start/end
   └─ Buffer audio chunks

3. VOXTRAL ASR (Speech-to-Text)
   ├─ Transcribe audio to text
   └─ Output: "Hello, how are you?"

4. CONVERSATION MANAGER
   ├─ Add user turn to history
   ├─ Retrieve context (last 5 turns)
   └─ Build prompt with context

5. VOXTRAL LLM (Text-to-Text)
   ├─ Generate response with context
   ├─ Stream 1-word chunks
   └─ Output: "I'm doing great, thanks for asking!"

6. CHUNKED STREAMING (1-word chunks)
   ├─ Chunk 1: "I'm"
   ├─ Chunk 2: "doing"
   ├─ Chunk 3: "great,"
   └─ Chunk N: "asking!"

7. TTS (Text-to-Speech) - STREAMING
   ├─ Receive 1-word chunk
   ├─ Generate audio for chunk
   ├─ Stream audio to browser
   └─ Latency: 50-100ms per chunk

8. AUDIO OUTPUT
   ├─ Browser receives audio chunks
   ├─ Queue audio for playback
   ├─ Play continuously
   └─ User hears natural speech

TOTAL LATENCY:
├─ Audio input: 0ms
├─ VAD: 50-100ms
├─ ASR: 100-200ms
├─ Conversation Manager: 10-20ms
├─ LLM (first token): 50-100ms
├─ TTS (first chunk): 50-100ms
└─ TOTAL TTFT: 260-520ms (acceptable for natural conversation)
```

### Streaming Integration Design

**Key Principle**: Stream 1-word chunks from LLM directly to TTS

```python
# Pseudo-code
async for word_chunk in voxtral_llm.stream_tokens():
    # Add to conversation history
    conversation_manager.add_partial_response(word_chunk)
    
    # Send to TTS immediately
    audio_chunk = await tts.synthesize(word_chunk)
    
    # Stream audio to browser
    await websocket.send_audio(audio_chunk)
    
    # Browser plays audio immediately
```

**Benefits**:
- First word heard in 50-100ms (TTFT)
- Natural streaming experience
- No waiting for full response
- Perceived latency very low

---

## PART 4: UPDATED PHASE BREAKDOWN

### PHASE 0: Token Batching Fix (5 min) ⭐ CRITICAL
**Status**: Already designed in previous analysis
- Fix: Send 1-word chunks instead of 6-word chunks
- File: `src/models/voxtral_model_realtime.py:661`
- Expected: TTFT 50-100ms

### PHASE 1: Conversation Manager (4 min)
**What**: Create conversation history tracking
- Create: `src/managers/conversation_manager.py`
- Modify: `src/api/ui_server_realtime.py` (integrate)
- Modify: `src/models/voxtral_model_realtime.py` (use context)
- Expected: Context-aware responses

### PHASE 2: TTS Integration - Chatterbox (5 min)
**What**: Add Chatterbox TTS for text-to-speech
- Create: `src/models/tts_manager.py`
- Modify: `requirements.txt` (add chatterbox)
- Modify: `src/api/ui_server_realtime.py` (add TTS endpoint)
- Expected: Audio output for responses

### PHASE 3: Streaming Audio Pipeline (4 min)
**What**: Stream 1-word chunks to TTS
- Modify: `src/models/voxtral_model_realtime.py` (stream to TTS)
- Modify: `src/api/ui_server_realtime.py` (send audio chunks)
- Expected: Real-time audio streaming

### PHASE 4: Browser Audio Playback (3 min)
**What**: Receive and play audio chunks in browser
- Modify: `src/api/ui_server_realtime.py` (HTML/JS)
- Add: Audio queue and playback logic
- Expected: Continuous audio playback

### PHASE 5: Language Support (4 min)
**What**: Add language selection and fallback TTS
- Modify: `src/models/tts_manager.py` (language routing)
- Add: Dia-TTS for Malaysian
- Add: Indic-TTS for Indian languages
- Expected: Multilingual support

### PHASE 6: WebRTC Audio Streaming (3 min)
**What**: Enable WebRTC for lower latency
- Modify: `src/api/ui_server_realtime.py` (enable WebRTC)
- Expected: 30-80ms additional savings

### PHASE 7: Sesame.com Maya Features (5 min)
**What**: Add emotional expressiveness
- Modify: `src/models/tts_manager.py` (emotion control)
- Modify: `src/models/voxtral_model_realtime.py` (emotion detection)
- Expected: Natural, expressive responses

---

## PART 5: SESAME.COM MAYA REPLICATION PLAN

### Feature Comparison

| Feature | Sesame Maya | Our Implementation | Status |
|---------|-------------|-------------------|--------|
| Real-time voice chat | ✅ | ✅ (Phase 0-3) | Ready |
| Low latency (<500ms) | ✅ | ✅ (Phase 0-3) | Ready |
| Emotional intelligence | ✅ | ⏳ (Phase 7) | Planned |
| Can interrupt | ✅ | ⏳ (Phase 8) | Future |
| Natural pauses | ✅ | ⏳ (Phase 7) | Planned |
| Laugh/expressions | ✅ | ⏳ (Phase 7) | Planned |
| Conversation memory | ✅ | ✅ (Phase 1) | Ready |
| Multilingual | ✅ | ✅ (Phase 5) | Ready |
| Voice presence | ✅ | ⏳ (Phase 7) | Planned |

### Gap Analysis

**Immediate Gaps** (Phases 0-6):
- ❌ Emotional expressiveness
- ❌ Natural pauses/breathing
- ❌ Interruption handling

**Medium-term Gaps** (Phase 7):
- ⏳ Emotion detection from user speech
- ⏳ Emotion control in TTS
- ⏳ Natural prosody

**Long-term Gaps** (Future):
- ⏳ Interruption detection and handling
- ⏳ Real-time emotion analysis
- ⏳ Voice cloning

### Implementation Roadmap

**Phase 7: Emotional Expressiveness**
- Detect emotion from user speech (anger, joy, sadness, etc.)
- Pass emotion to TTS (Chatterbox supports intensity control)
- Generate emotionally appropriate responses
- Add natural pauses between sentences

**Phase 8: Interruption Handling** (Future)
- Detect user speech while AI is speaking
- Stop TTS playback
- Process new user input
- Generate new response

**Phase 9: Voice Cloning** (Future)
- Use user's voice characteristics
- Generate responses in user's voice style
- Create personalized experience

---

## PART 6: IMPLEMENTATION PLAN

### Dependencies to Add
```
# TTS Models
chatterbox-tts>=0.1.0  # Primary TTS
dia-tts>=0.1.0         # SEA languages
indic-tts>=0.1.0       # Indian languages

# Audio Processing
librosa>=0.10.0        # Audio analysis
soundfile>=0.12.0      # Audio I/O
```

### New Files to Create
1. `src/managers/conversation_manager.py` (100 lines)
2. `src/models/tts_manager.py` (150 lines)
3. `src/utils/emotion_detector.py` (100 lines, Phase 7)

### Files to Modify
1. `src/api/ui_server_realtime.py` (add TTS endpoints, audio streaming)
2. `src/models/voxtral_model_realtime.py` (stream to TTS, use context)
3. `requirements.txt` (add TTS dependencies)
4. `config.yaml` (add TTS configuration)

### Backward Compatibility
- ✅ All changes are additive
- ✅ Existing ASR-only mode still works
- ✅ TTS is optional (can be disabled)
- ✅ Rollback: Remove TTS endpoints, revert streaming

---

## PART 7: TESTING & VALIDATION STRATEGY

### Phase 0 Testing
- [ ] Verify 1-word chunks sent immediately
- [ ] Measure TTFT: should be 50-100ms
- [ ] Check browser console for token-by-token updates

### Phase 1 Testing
- [ ] Verify conversation history stored
- [ ] Check context passed to LLM
- [ ] Verify responses use previous context

### Phase 2 Testing
- [ ] Verify Chatterbox TTS loads
- [ ] Test audio generation for sample text
- [ ] Check audio quality

### Phase 3 Testing
- [ ] Verify 1-word chunks sent to TTS
- [ ] Check audio chunks generated
- [ ] Measure TTS latency per chunk

### Phase 4 Testing
- [ ] Verify audio chunks received in browser
- [ ] Check audio playback
- [ ] Verify continuous playback without gaps

### Phase 5 Testing
- [ ] Test language selection
- [ ] Verify fallback TTS works
- [ ] Test Indian and SEA languages

### Phase 6 Testing
- [ ] Enable WebRTC
- [ ] Measure latency improvement
- [ ] Verify audio quality

### Phase 7 Testing
- [ ] Detect emotion from speech
- [ ] Verify emotion passed to TTS
- [ ] Check emotional expressiveness

---

## APPROVAL CHECKLIST

Before implementation, please confirm:

- [ ] Conversation Manager design approved
- [ ] Chatterbox TTS as primary model approved
- [ ] Speech-to-Speech pipeline architecture approved
- [ ] 7-phase breakdown approved
- [ ] Sesame.com Maya replication plan approved
- [ ] Ready to proceed with Phase 0 implementation

---

## NEXT STEPS

1. **Review this design document**
2. **Approve each component**
3. **Confirm phase breakdown**
4. **I will implement Phase 0 first** (token batching fix)
5. **Then Phase 1-7 sequentially**
6. **Test after each phase**
7. **Deploy to production**

**Status**: AWAITING YOUR APPROVAL

