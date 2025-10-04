# 🏗️ Voxtral-Kokoro Architecture Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Configuration Management](#configuration-management)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Performance Optimization](#performance-optimization)
8. [Deployment Guide](#deployment-guide)

---

## 🎯 System Overview

**Voxtral-Kokoro** is a real-time Speech-to-Speech AI system that provides:
- **Sub-500ms latency** end-to-end voice conversation
- **GPU-optimized pipeline** using CUDA acceleration
- **Multi-modal processing**: Speech → Text → LLM → Speech
- **Production-ready** with comprehensive error handling and monitoring

### Key Technologies
- **Voxtral Model** (Mistral AI): Speech-to-Text (STT)
- **Kokoro TTS**: High-quality Text-to-Speech (24 voices, 8 languages)
- **FastAPI**: Web framework for HTTP/WebSocket servers
- **PyTorch**: Deep learning framework with CUDA support
- **WebSocket**: Real-time bidirectional communication

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Web UI      │  │  WebSocket   │  │  Health Monitor      │  │
│  │  Port 8000   │  │  /ws         │  │  Port 8005           │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘  │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ui_server_realtime.py - Main HTTP + WebSocket Server   │  │
│  │  health_check.py - Health & Metrics Endpoints           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE ORCHESTRATION                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  speech_to_speech_pipeline.py                            │  │
│  │  - Coordinates STT → LLM → TTS workflow                  │  │
│  │  - Manages conversation state                            │  │
│  │  - Tracks performance metrics                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────┬─────────────────┬─────────────────┬────────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  VOXTRAL STT │  │  LLM LOGIC   │  │  KOKORO TTS      │
│  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────────┐  │
│  │ Audio  │  │  │  │ Text   │  │  │  │ Text       │  │
│  │ Process│  │  │  │ Process│  │  │  │ → Speech   │  │
│  └────────┘  │  │  └────────┘  │  │  └────────────┘  │
└──────────────┘  └──────────────┘  └──────────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     UTILITY LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ GPU Memory   │  │ Error        │  │ Performance          │  │
│  │ Manager      │  │ Handler      │  │ Monitor              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Config       │  │ Logging      │  │ Latency              │  │
│  │ Manager      │  │ System       │  │ Optimizer            │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Details

### 1. API Layer

#### **ui_server_realtime.py**
- **Purpose**: Main web server with UI and WebSocket endpoint
- **Key Features**:
  - Serves interactive web UI with voice controls
  - Handles WebSocket connections for real-time audio streaming
  - Manages conversation state and VAD (Voice Activity Detection)
  - Supports both text-only and speech-to-speech modes
- **Endpoints**:
  - `GET /` - Web UI
  - `WebSocket /ws` - Real-time audio streaming
- **Dependencies**: FastAPI, WebSockets, NumPy

#### **health_check.py**
- **Purpose**: System health monitoring and metrics
- **Key Features**:
  - Real-time system metrics (CPU, GPU, memory)
  - Model initialization status
  - Performance metrics tracking
  - Speech-to-speech pipeline monitoring
- **Endpoints**:
  - `GET /health` - Basic health check
  - `GET /status` - Detailed system status
  - `GET /ready` - Readiness probe
  - `GET /speech-to-speech/metrics` - S2S metrics
  - `GET /speech-to-speech/performance` - Performance analysis

---

### 2. Model Layer

#### **voxtral_model_realtime.py**
- **Purpose**: Voxtral speech recognition model wrapper
- **Key Features**:
  - Async model initialization
  - Audio preprocessing and validation
  - Transcription and understanding modes
  - GPU memory optimization
- **Model**: `mistralai/Voxtral-Mini-3B-2507`
- **Precision**: bfloat16 for optimal performance

#### **kokoro_model_realtime.py**
- **Purpose**: Kokoro TTS model wrapper
- **Key Features**:
  - Multi-voice support (24 voices, 8 languages)
  - Emotional voice selection
  - Speed control (0.8x - 1.2x)
  - Streaming audio generation
- **Voices**: 
  - English: af_heart, af_bella, af_nicole, af_sarah
  - Hindi: hf_alpha, hf_beta, hm_psi

#### **audio_processor_realtime.py**
- **Purpose**: Audio preprocessing and validation
- **Key Features**:
  - Audio format conversion (int16 ↔ float32)
  - Resampling (any rate → 16kHz)
  - Log-mel spectrogram generation
  - VAD (Voice Activity Detection)
- **Processing**: Librosa, NumPy, PyTorch

#### **speech_to_speech_pipeline.py**
- **Purpose**: End-to-end conversation orchestration
- **Key Features**:
  - STT → LLM → TTS workflow
  - Conversation state management
  - Performance tracking (<300ms target)
  - Emotional context analysis
- **Latency Breakdown**:
  - STT: ~100ms
  - LLM: ~50ms
  - TTS: ~150ms
  - Total: <300ms

#### **unified_model_manager.py**
- **Purpose**: Centralized model lifecycle management
- **Key Features**:
  - Lazy model loading
  - Memory-efficient initialization
  - Model warmup and caching
  - Health status tracking

---

### 3. Streaming Layer

#### **websocket_server.py**
- **Purpose**: Standalone WebSocket server for audio streaming
- **Key Features**:
  - Client connection management
  - Audio data handling
  - Speech-to-speech processing
  - RunPod proxy compatibility
- **Protocol**: WebSocket with JSON messages

---

### 4. Utility Layer

#### **config.py**
- **Purpose**: Centralized configuration management
- **Key Features**:
  - YAML-based configuration
  - Environment variable overrides
  - Pydantic validation
  - Type-safe config access
- **Config Sections**:
  - Server, Model, Audio, Spectrogram
  - VAD, Streaming, TTS, Performance
  - Speech-to-Speech, Logging

#### **error_handling.py**
- **Purpose**: Comprehensive error handling and recovery
- **Key Features**:
  - Error classification (Memory, Network, Performance, etc.)
  - Automatic recovery strategies
  - Error pattern detection
  - Recovery success tracking
- **Recovery Strategies**:
  - GPU memory cleanup
  - Model reinitialization
  - Performance optimization
  - Connection retry

#### **gpu_memory_manager.py**
- **Purpose**: GPU memory allocation and optimization
- **Key Features**:
  - VRAM validation (min 8GB, recommended 16GB)
  - Shared memory pool management
  - Memory cleanup and monitoring
  - Optimization recommendations
- **Memory Allocation**:
  - Voxtral: ~4.5GB
  - Kokoro: ~1.5GB
  - Total: ~6GB minimum

#### **performance_monitor.py**
- **Purpose**: Real-time performance tracking
- **Key Features**:
  - Operation timing (start/end)
  - Latency breakdown logging
  - System metrics monitoring
  - Performance summary reports
- **Metrics**:
  - CPU/GPU usage
  - Memory consumption
  - Processing latency
  - Throughput

#### **latency_optimizer.py**
- **Purpose**: Latency reduction optimizations
- **Key Features**:
  - Model compilation (torch.compile)
  - KV caching
  - Batch processing
  - Memory optimization

#### **logging_config.py**
- **Purpose**: Centralized logging configuration
- **Key Features**:
  - File and console logging
  - Structured log format
  - Log level management
  - Log rotation

---

## 🔄 Data Flow

### Speech-to-Speech Conversation Flow

```
1. USER SPEAKS
   ↓
2. BROWSER captures audio (16kHz, mono)
   ↓
3. VAD detects speech vs silence
   ↓
4. WebSocket sends audio data (base64 encoded)
   ↓
5. UI SERVER receives audio
   ↓
6. SPEECH-TO-SPEECH PIPELINE processes:
   ├─ AUDIO PROCESSOR validates & preprocesses
   ├─ VOXTRAL MODEL transcribes (STT)
   ├─ LLM generates response
   └─ KOKORO TTS synthesizes speech
   ↓
7. PIPELINE returns:
   ├─ Transcription text
   ├─ Response text
   └─ Response audio (WAV)
   ↓
8. UI SERVER sends via WebSocket:
   ├─ 'transcription' message
   ├─ 'response_text' message
   └─ 'speech_response' message
   ↓
9. BROWSER plays audio response
   ↓
10. CONVERSATION COMPLETE
```

### Message Types (WebSocket)

| Type | Direction | Purpose |
|------|-----------|---------|
| `connection` | Server → Client | Connection established |
| `audio` | Client → Server | Audio data for processing |
| `transcription` | Server → Client | STT result |
| `response_text` | Server → Client | LLM response text |
| `speech_response` | Server → Client | TTS audio data |
| `conversation_complete` | Server → Client | Processing finished |
| `error` | Server → Client | Error notification |
| `ping/pong` | Bidirectional | Keep-alive |

---

## ⚙️ Configuration Management

### Configuration Hierarchy

```
1. config.yaml (base configuration)
2. Environment variables (overrides)
3. Runtime modifications (temporary)
```

### Key Configuration Sections

#### **Model Configuration**
```yaml
model:
  name: "mistralai/Voxtral-Mini-3B-2507"
  device: "cuda"
  torch_dtype: "bfloat16"
  max_memory_per_gpu: "8GB"
  ultra_fast_mode: true
```

#### **Audio Configuration**
```yaml
audio:
  sample_rate: 16000
  chunk_size: 1024
  format: "float32"
  channels: 1
```

#### **VAD Configuration**
```yaml
vad:
  threshold: 0.005
  min_voice_duration_ms: 200
  min_silence_duration_ms: 400
  sensitivity: "ultra_high"
```

#### **TTS Configuration**
```yaml
tts:
  engine: "kokoro"
  default_voice: "hf_alpha"
  sample_rate: 16000
  speed: 1.0
  performance:
    target_latency_ms: 150
```

---

## 🛡️ Error Handling Strategy

### Error Categories

1. **INITIALIZATION** - Model loading failures
2. **RUNTIME** - Processing errors
3. **PERFORMANCE** - Latency issues
4. **MEMORY** - GPU/RAM exhaustion
5. **NETWORK** - Connection problems
6. **VALIDATION** - Invalid input data

### Error Severity Levels

- **LOW**: Minor issues, system continues
- **MEDIUM**: Degraded performance, retry recommended
- **HIGH**: Operation failed, manual intervention may be needed
- **CRITICAL**: System failure, immediate action required

### Recovery Strategies

| Error Type | Recovery Action |
|------------|----------------|
| CUDA OOM | Clear GPU cache, reduce batch size |
| Model Init Failed | Cleanup memory, retry initialization |
| Performance Degradation | Reset performance counters, optimize settings |
| Connection Error | Exponential backoff retry |

---

## 🚀 Performance Optimization

### Latency Targets

| Component | Target | Typical |
|-----------|--------|---------|
| STT (Voxtral) | 100ms | 80-120ms |
| LLM Processing | 50ms | 30-70ms |
| TTS (Kokoro) | 150ms | 120-180ms |
| **Total E2E** | **300ms** | **250-350ms** |

### Optimization Techniques

1. **Model Compilation**: `torch.compile()` for 20-30% speedup
2. **Mixed Precision**: bfloat16 reduces memory and increases speed
3. **KV Caching**: Reuse computed attention keys/values
4. **Batch Processing**: Process multiple requests together
5. **Memory Pooling**: Pre-allocate GPU memory
6. **Async Processing**: Non-blocking operations

### GPU Memory Optimization

```python
# Memory allocation strategy
- Reserve 90% of VRAM for models
- Enable CUDA memory pooling
- Aggressive cache cleanup
- Monitor memory usage continuously
```

---

## 🚢 Deployment Guide

### System Requirements

**Minimum**:
- GPU: 8GB VRAM (RTX 3070, RTX 4060 Ti)
- RAM: 16GB
- Storage: 50GB
- OS: Ubuntu 20.04+

**Recommended**:
- GPU: 16GB+ VRAM (RTX A4500, RTX 4090)
- RAM: 32GB
- Storage: 100GB SSD
- OS: Ubuntu 22.04

### Deployment Steps

1. **Install System Packages**
   ```bash
   bash deploy_production.sh
   ```

2. **Set Environment Variables**
   ```bash
   export HF_TOKEN="your_huggingface_token"
   export CUDA_VISIBLE_DEVICES=0
   ```

3. **Start Services**
   ```bash
   # Health Check Server (Port 8005)
   python -m src.api.health_check &
   
   # Main UI Server (Port 8000)
   python -m src.api.ui_server_realtime
   ```

4. **Verify Deployment**
   ```bash
   curl http://localhost:8005/health
   curl http://localhost:8005/ready
   ```

### RunPod Deployment

1. **Pod Configuration**:
   - Template: PyTorch 2.1.0+ with CUDA 12.1
   - GPU: RTX A4500 or better
   - Container Disk: 50GB minimum
   - Expose Ports: 8000, 8005

2. **Access URLs**:
   - Web UI: `https://[POD_ID]-8000.proxy.runpod.net`
   - Health: `https://[POD_ID]-8005.proxy.runpod.net/health`
   - WebSocket: `wss://[POD_ID]-8000.proxy.runpod.net/ws`

---

## 📊 Monitoring & Metrics

### Health Check Endpoints

```bash
# Basic health
GET /health

# Detailed status
GET /status

# Readiness probe
GET /ready

# S2S metrics
GET /speech-to-speech/metrics

# Performance analysis
GET /speech-to-speech/performance
```

### Key Metrics

- **Latency**: Average, min, max processing time
- **Throughput**: Conversations per minute
- **Success Rate**: % of successful completions
- **Memory Usage**: GPU/RAM consumption
- **Error Rate**: Errors per hour

---

## 🔧 Troubleshooting

### Common Issues

**1. CUDA Out of Memory**
- Reduce `max_memory_per_gpu` in config
- Enable memory cleanup after each generation
- Use lower precision (fp16 instead of fp32)

**2. High Latency**
- Check GPU utilization
- Enable `ultra_fast_mode`
- Reduce audio chunk size
- Use greedy decoding instead of sampling

**3. Model Loading Fails**
- Verify HuggingFace token
- Check internet connectivity
- Ensure sufficient disk space
- Clear model cache and retry

**4. WebSocket Connection Issues**
- Verify port exposure (8000)
- Check firewall settings
- Use correct URL format for RunPod
- Enable CORS headers

---

## 📝 Code Quality Standards

### Best Practices

1. **Type Hints**: All functions have type annotations
2. **Error Handling**: Try-catch blocks for all I/O operations
3. **Logging**: Structured logging with appropriate levels
4. **Documentation**: Docstrings for all classes and functions
5. **Testing**: Unit tests for critical components
6. **Performance**: Async/await for I/O-bound operations

### Code Structure

```python
# Standard structure for async functions
async def process_audio(audio_data: np.ndarray) -> Dict[str, Any]:
    """
    Process audio data through the pipeline.
    
    Args:
        audio_data: Input audio as numpy array
        
    Returns:
        Dictionary with processing results
        
    Raises:
        AudioProcessingError: If processing fails
    """
    try:
        # Validation
        if not validate_audio(audio_data):
            raise AudioProcessingError("Invalid audio format")
        
        # Processing
        result = await model.process(audio_data)
        
        # Return
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        await error_handler.handle_error(e)
        raise
```

---

## 🎯 Future Enhancements

### Planned Features

1. **Multi-language Support**: Expand beyond English/Hindi
2. **Streaming TTS**: Word-by-word audio generation
3. **Conversation Memory**: Context-aware responses
4. **Voice Cloning**: Custom voice training
5. **Batch Processing**: Multiple concurrent conversations
6. **Cloud Storage**: S3/GCS integration for audio logs
7. **Analytics Dashboard**: Real-time metrics visualization
8. **A/B Testing**: Voice quality comparison

---

## 📚 References

- [Voxtral Model](https://huggingface.co/mistralai/Voxtral-Mini-3B-2507)
- [Kokoro TTS](https://github.com/hexgrad/kokoro)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)

---

**Last Updated**: 2025-10-04  
**Version**: 2.2.0  
**Maintainer**: Development Team
