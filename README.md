# Voxtral Model - Real-time Voice AI System

A production-ready real-time voice AI system powered by Mistral's **Voxtral model** featuring Voice Activity Detection (VAD), Automatic Speech Recognition (ASR), and Large Language Model (LLM) processing. Optimized for RunPod deployment with sub-500ms end-to-end latency.

## ✨ Features

- **Voice Activity Detection (VAD)**: Smart silence detection and voice segmentation
- **Automatic Speech Recognition (ASR)**: Voxtral model for accurate speech-to-text conversion
- **Large Language Model (LLM)**: Integrated LLM processing for intelligent responses
- **Real-time Processing**: End-to-end latency <500ms
- **WebSocket Streaming**: Bidirectional real-time audio communication
- **Web Interface**: Modern UI with voice controls on port 8000
- **Health Monitoring**: Comprehensive system monitoring on port 8005
- **GPU Optimized**: CUDA acceleration throughout the pipeline
- **Production Ready**: Robust error handling and performance monitoring

## 🏗️ Architecture

```
User Voice Input
    ↓
┌─────────────────────────────────────┐
│  Voice Activity Detection (VAD)     │ ← Silence detection & segmentation
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Audio Preprocessing                │ ← Spectrogram generation
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Voxtral ASR Model                  │ ← Speech-to-Text conversion
│  (mistralai/Voxtral-Mini-3B-2507)   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  LLM Processing                     │ ← Response generation
└─────────────────────────────────────┘
    ↓
    Output (Text/Metadata)
```

### Core Components

- **VAD System**: Voice activity detection with configurable sensitivity
- **Audio Processor**: Real-time audio preprocessing and spectrogram generation
- **Voxtral Model**: Mistral's state-of-the-art speech recognition model
- **Web Interface**: FastAPI-based UI with WebSocket support
- **Health Check**: System monitoring and performance metrics
- **Streaming Servers**: WebSocket and TCP servers for real-time communication

## 📋 Requirements

### System Requirements
- **GPU**: RTX A4500 (recommended) or any CUDA-compatible GPU with 8GB+ VRAM
- **RAM**: 16GB+ recommended
- **Storage**: 30GB+ for model cache
- **OS**: Ubuntu 20.04+ or similar Linux distribution

### Python Dependencies
- Python 3.8+
- PyTorch 2.1.0+
- Transformers 4.56.0+
- FastAPI, WebSockets, Librosa, and more (see requirements.txt)

## 🚀 Quick Start

### Local Installation

```bash
# Clone repository
git clone <your-repository-url>
cd voxtral-model

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# Create necessary directories
mkdir -p model_cache logs

# Start the system
python3 -m src.api.ui_server_realtime
```

The web interface will be available at `http://localhost:8000`

### RunPod Deployment

See [RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md) for detailed RunPod deployment instructions.

## 🎯 Usage

### Web Interface

1. Open the web UI in your browser: `http://localhost:8000`
2. Click "Connect" to establish WebSocket connection
3. Click "Start Recording" to begin audio capture
4. Speak into your microphone
5. Click "Stop Recording" to process audio
6. View the transcribed text and system metrics

### API Endpoints

- **GET `/`** - Web interface
- **GET `/health`** - Health check endpoint
- **GET `/ready`** - Readiness check
- **WebSocket `/ws`** - Real-time audio streaming

### WebSocket Message Format

**Client → Server (Audio):**
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_chunk"
}
```

**Server → Client (Response):**
```json
{
  "type": "transcription",
  "text": "recognized speech",
  "confidence": 0.95,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **VAD Settings**: Sensitivity, thresholds, chunk sizes
- **Audio Settings**: Sample rate, channels, format
- **Server Settings**: Host, ports, connection limits
- **Performance**: Monitoring, latency targets

Example configuration:
```yaml
vad:
  threshold: 0.005
  min_voice_duration_ms: 200
  min_silence_duration_ms: 400
  sensitivity: "ultra_high"

audio:
  sample_rate: 16000
  chunk_size: 1024
  format: "float32"
```

## 📊 Performance Metrics

The system tracks:
- **Processing Latency**: End-to-end processing time (ms)
- **Audio Duration**: Input audio length (s)
- **GPU Memory Usage**: VRAM consumption
- **Connection Count**: Active WebSocket connections
- **Error Rates**: System error frequency

Access metrics via:
```bash
curl http://localhost:8005/health
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

### Test Coverage
- Audio preprocessing pipeline
- Log-mel spectrogram generation
- Model initialization and inference
- WebSocket message handling
- Configuration management
- Health check endpoints

## 🔧 Troubleshooting

### Common Issues

**Issue**: Model loading timeout
- **Solution**: Increase `MODEL_LOAD_TIMEOUT` in `.env`

**Issue**: Out of memory errors
- **Solution**: Reduce `GPU_MEMORY_UTILIZATION` or use smaller batch sizes

**Issue**: WebSocket connection failures
- **Solution**: Check firewall settings and ensure port 8000 is accessible

**Issue**: High latency
- **Solution**: Enable `ENABLE_TORCH_COMPILE` and `ENABLE_FLASH_ATTENTION` in `.env`

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python3 -m src.api.ui_server_realtime
```

## 📝 Environment Variables

See `.env.example` for all available environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key variables:
- `HF_TOKEN`: HuggingFace API token (required)
- `CUDA_VISIBLE_DEVICES`: GPU selection
- `MODEL_CACHE_DIR`: Model cache directory
- `LOG_LEVEL`: Logging verbosity

## 📚 Documentation

- [RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md) - RunPod deployment guide
- [config.yaml](config.yaml) - Configuration reference
- [requirements.txt](requirements.txt) - Python dependencies

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing style conventions
- All tests pass
- Documentation is updated
- Commits are descriptive

## 📄 License

This project is provided as-is for research and production use.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review configuration settings in `config.yaml`
3. Check logs in `./logs/` directory
4. Enable debug mode for detailed output

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Production Ready

