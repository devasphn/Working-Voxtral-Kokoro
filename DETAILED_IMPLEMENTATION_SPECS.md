# Detailed Implementation Specifications
## Phase-by-Phase Breakdown with Exact Code Changes

---

## PHASE 0: Token Batching Fix (5 minutes) ⭐ CRITICAL

### File: `src/models/voxtral_model_realtime.py`
**Lines**: 646-675

### Current Code (WRONG)
```python
# Stream chunks as they're generated
word_buffer = []
first_chunk_received = False

for new_text in streamer:
    if new_text:
        words = new_text.split()
        word_buffer.extend(words)
        
        if not first_chunk_received:
            first_chunk_received = True
            realtime_logger.info(f"📝 First generated text: '{new_text}'")
        
        # BOTTLENECK: Wait for 6 words
        if len(word_buffer) >= 6:
            chunk_text = " ".join(word_buffer[:6])
            word_buffer = word_buffer[6:]
            generated_text += chunk_text + " "
            
            yield {
                'success': True,
                'text': chunk_text.strip(),
                'is_final': False,
                'chunk_index': chunk_index,
                'processing_time_ms': (time.time() - chunk_start_time) * 1000
            }
            chunk_index += 1
```

### Fixed Code (CORRECT)
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
            realtime_logger.info(f"⚡ TTFT: {first_token_time*1000:.1f}ms")
        
        if not first_chunk_received:
            first_chunk_received = True
            realtime_logger.info(f"📝 First generated text: '{new_text}'")
        
        # FIXED: Send immediately (1 word at a time)
        while len(word_buffer) >= 1:
            chunk_text = " ".join(word_buffer[:1])
            word_buffer = word_buffer[1:]
            generated_text += chunk_text + " "
            
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

### Expected Result
- TTFT: 50-100ms (vs current 300-500ms)
- First word appears immediately
- Remaining words stream continuously

---

## PHASE 1: Conversation Manager (4 minutes)

### New File: `src/managers/conversation_manager.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationManager:
    def __init__(self, context_window: int = 5, max_history: int = 100):
        self.history: List[ConversationTurn] = []
        self.context_window = context_window
        self.max_history = max_history
    
    def add_turn(self, role: str, content: str, latency_ms: Optional[int] = None, 
                 metadata: Optional[Dict] = None) -> None:
        """Add a turn to conversation history"""
        turn = ConversationTurn(
            role=role,
            content=content,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
        self.history.append(turn)
        
        # Keep history size under limit
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_context(self, num_turns: Optional[int] = None) -> str:
        """Get conversation context for LLM prompt"""
        num_turns = num_turns or self.context_window
        recent_turns = self.history[-num_turns:]
        
        context = ""
        for turn in recent_turns:
            context += f"{turn.role.upper()}: {turn.content}\n"
        
        return context
    
    def get_last_user_message(self) -> Optional[str]:
        """Get last user message"""
        for turn in reversed(self.history):
            if turn.role == "user":
                return turn.content
        return None
    
    def clear_history(self) -> None:
        """Clear all history"""
        self.history.clear()
    
    def export_conversation(self) -> Dict[str, Any]:
        """Export conversation as JSON"""
        return {
            "turns": [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp.isoformat(),
                    "latency_ms": turn.latency_ms
                }
                for turn in self.history
            ],
            "total_turns": len(self.history)
        }
```

### Modify: `src/api/ui_server_realtime.py`
**Add at top**:
```python
from src.managers.conversation_manager import ConversationManager

# Initialize conversation manager
conversation_manager = ConversationManager(context_window=5, max_history=100)
```

**Modify WebSocket handler** (around line 1911):
```python
# After receiving user transcription
conversation_manager.add_turn("user", transcribed_text)

# Get context for LLM
context = conversation_manager.get_context()

# Pass context to model (see Phase 1b)
```

### Modify: `src/models/voxtral_model_realtime.py`
**Update prompt generation** (around line 581):
```python
# Add context to prompt
context = conversation_manager.get_context()
prompt_text = f"""You are a helpful conversational AI. 
Previous conversation:
{context}

Listen to what the user said and respond conversationally."""
```

### Expected Result
- Conversation history tracked
- Context passed to LLM
- Responses aware of previous turns

---

## PHASE 2: TTS Integration - Chatterbox (5 minutes)

### New File: `src/models/tts_manager.py`

```python
import torch
from typing import Optional, Dict, Any
import logging

tts_logger = logging.getLogger("tts_manager")

class TTSManager:
    def __init__(self, model_name: str = "chatterbox", device: str = "cuda"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None
        self.is_initialized = False
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize TTS model"""
        try:
            if self.model_name == "chatterbox":
                from transformers import AutoModel, AutoProcessor
                
                self.processor = AutoProcessor.from_pretrained(
                    "resemble-ai/chatterbox"
                )
                self.model = AutoModel.from_pretrained(
                    "resemble-ai/chatterbox"
                ).to(self.device)
                
                self.is_initialized = True
                tts_logger.info("✅ Chatterbox TTS initialized")
        except Exception as e:
            tts_logger.error(f"❌ TTS initialization failed: {e}")
            self.is_initialized = False
    
    async def synthesize(self, text: str, language: str = "en", 
                        emotion: str = "neutral") -> Optional[bytes]:
        """Synthesize text to speech"""
        if not self.is_initialized:
            tts_logger.error("TTS not initialized")
            return None
        
        try:
            with torch.no_grad():
                inputs = self.processor(
                    text=text,
                    language=language,
                    return_tensors="pt"
                ).to(self.device)
                
                outputs = self.model.generate(**inputs)
                
                # Convert to audio bytes
                audio_bytes = self._convert_to_audio_bytes(outputs)
                return audio_bytes
        
        except Exception as e:
            tts_logger.error(f"❌ Synthesis failed: {e}")
            return None
    
    def _convert_to_audio_bytes(self, outputs) -> bytes:
        """Convert model outputs to audio bytes"""
        # Implementation depends on model output format
        # This is a placeholder
        return b""
```

### Modify: `requirements.txt`
**Add**:
```
chatterbox-tts>=0.1.0
transformers>=4.56.0
librosa>=0.10.0
soundfile>=0.12.0
```

### Modify: `src/api/ui_server_realtime.py`
**Add TTS endpoint**:
```python
@app.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    """TTS streaming endpoint"""
    await websocket.accept()
    
    tts_manager = TTSManager()
    
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text")
            language = data.get("language", "en")
            
            audio_bytes = await tts_manager.synthesize(text, language)
            
            await websocket.send_bytes(audio_bytes)
    
    except Exception as e:
        streaming_logger.error(f"TTS error: {e}")
    finally:
        await websocket.close()
```

### Expected Result
- Chatterbox TTS loaded
- Audio generated for text
- TTS endpoint available

---

## PHASE 3: Streaming Audio Pipeline (4 minutes)

### Modify: `src/models/voxtral_model_realtime.py`
**Update streaming loop** (around line 650):
```python
# Import TTS manager
from src.models.tts_manager import TTSManager

# In process_realtime_chunk_streaming method
tts_manager = TTSManager()

for new_text in streamer:
    if new_text:
        words = new_text.split()
        word_buffer.extend(words)
        
        # Send 1-word chunks to TTS
        while len(word_buffer) >= 1:
            chunk_text = word_buffer[0]
            word_buffer = word_buffer[1:]
            
            # Generate audio for this chunk
            audio_bytes = await tts_manager.synthesize(chunk_text)
            
            yield {
                'success': True,
                'text': chunk_text,
                'audio': audio_bytes,  # NEW: Include audio
                'is_final': False,
                'chunk_index': chunk_index,
                'processing_time_ms': (time.time() - chunk_start_time) * 1000
            }
            chunk_index += 1
```

### Modify: `src/api/ui_server_realtime.py`
**Update WebSocket handler** (around line 1924):
```python
# Send text AND audio chunks
await websocket.send_json({
    "type": "text_chunk",
    "chunk_id": f"{chunk_id}_{chunk_counter}",
    "text": text_chunk['text'],
    "has_audio": text_chunk.get('audio') is not None,
    "is_final": text_chunk.get('is_final', False),
    "processing_time_ms": int(chunk_time * 1000)
})

# Send audio separately if available
if text_chunk.get('audio'):
    await websocket.send_bytes(text_chunk['audio'])
```

### Expected Result
- 1-word chunks sent to TTS
- Audio generated for each chunk
- Audio chunks streamed to browser

---

## PHASE 4: Browser Audio Playback (3 minutes)

### Modify: `src/api/ui_server_realtime.py` (HTML/JavaScript)
**Add audio queue and playback**:
```javascript
let audioQueue = [];
let isPlayingAudio = false;
let audioContext = null;

async function playAudioChunk(audioBytes) {
    audioQueue.push(audioBytes);
    
    if (!isPlayingAudio) {
        await playNextAudioChunk();
    }
}

async function playNextAudioChunk() {
    if (audioQueue.length === 0) {
        isPlayingAudio = false;
        return;
    }
    
    isPlayingAudio = true;
    const audioBytes = audioQueue.shift();
    
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    const audioBuffer = await audioContext.decodeAudioData(audioBytes);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    
    source.onended = () => playNextAudioChunk();
    source.start(0);
}

// In WebSocket message handler
case 'audio_chunk':
    const audioData = new Uint8Array(data);
    await playAudioChunk(audioData.buffer);
    break;
```

### Expected Result
- Audio chunks queued
- Continuous playback
- No gaps between chunks

---

## PHASE 5: Language Support (4 minutes)

### Modify: `src/models/tts_manager.py`
**Add language routing**:
```python
LANGUAGE_MODELS = {
    "en": "chatterbox",      # English
    "hi": "chatterbox",      # Hindi
    "es": "chatterbox",      # Spanish
    "ms": "dia-tts",         # Malaysian
    "ta": "indic-tts",       # Tamil
    "te": "indic-tts",       # Telugu
    "mr": "indic-tts",       # Marathi
}

async def synthesize_with_fallback(self, text: str, language: str = "en"):
    """Synthesize with language-specific TTS"""
    model_name = LANGUAGE_MODELS.get(language, "chatterbox")
    
    if model_name == "chatterbox":
        return await self.synthesize_chatterbox(text, language)
    elif model_name == "dia-tts":
        return await self.synthesize_dia(text, language)
    elif model_name == "indic-tts":
        return await self.synthesize_indic(text, language)
```

### Expected Result
- Language selection works
- Fallback TTS used for unsupported languages
- Multilingual support

---

## PHASE 6: WebRTC Audio Streaming (3 minutes)

### Modify: `src/api/ui_server_realtime.py`
**Enable WebRTC** (line 466):
```javascript
// OLD
let useWebRTC = false;

// NEW
let useWebRTC = true;
```

### Expected Result
- WebRTC enabled
- Lower latency (30-80ms savings)
- Better audio quality

---

## PHASE 7: Emotional Expressiveness (5 minutes)

### New File: `src/utils/emotion_detector.py`
```python
class EmotionDetector:
    def __init__(self):
        self.emotions = ["neutral", "happy", "sad", "angry", "surprised"]
    
    def detect_emotion(self, text: str) -> str:
        """Detect emotion from text"""
        # Simple keyword-based detection
        if any(word in text.lower() for word in ["happy", "great", "wonderful"]):
            return "happy"
        elif any(word in text.lower() for word in ["sad", "bad", "terrible"]):
            return "sad"
        elif any(word in text.lower() for word in ["angry", "furious", "mad"]):
            return "angry"
        return "neutral"
```

### Modify: `src/models/tts_manager.py`
**Add emotion control**:
```python
async def synthesize(self, text: str, language: str = "en", 
                    emotion: str = "neutral", intensity: float = 1.0):
    """Synthesize with emotion control"""
    # Chatterbox supports intensity control
    inputs = self.processor(
        text=text,
        language=language,
        intensity=intensity,  # 0.0-2.0
        return_tensors="pt"
    )
```

### Expected Result
- Emotion detected from user speech
- Emotion passed to TTS
- Emotionally appropriate responses

---

## ROLLBACK PROCEDURES

### Rollback Phase 0
```bash
git checkout HEAD~1 src/models/voxtral_model_realtime.py
```

### Rollback Phase 1
```bash
rm src/managers/conversation_manager.py
git checkout HEAD~1 src/api/ui_server_realtime.py
git checkout HEAD~1 src/models/voxtral_model_realtime.py
```

### Rollback All
```bash
git reset --hard HEAD~7
```

---

## TESTING CHECKLIST

- [ ] Phase 0: TTFT 50-100ms
- [ ] Phase 1: Conversation history stored
- [ ] Phase 2: Audio generated
- [ ] Phase 3: Audio chunks streamed
- [ ] Phase 4: Audio plays continuously
- [ ] Phase 5: Language selection works
- [ ] Phase 6: WebRTC enabled
- [ ] Phase 7: Emotion detected

---

## NEXT STEPS

1. Review this specification
2. Approve implementation approach
3. I will implement Phase 0 first
4. Test and verify
5. Proceed to Phase 1-7 sequentially

**Status**: AWAITING APPROVAL

