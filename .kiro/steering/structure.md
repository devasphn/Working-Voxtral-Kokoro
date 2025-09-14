# Project Structure & Organization

## Directory Layout

```
voxtral_realtime_streaming/
├── src/                          # Main source code
│   ├── api/                      # Web API and UI servers
│   │   ├── ui_server_realtime.py # Main WebSocket UI server (port 8000)
│   │   └── health_check.py       # Health monitoring (port 8005)
│   ├── models/                   # AI model wrappers
│   │   ├── voxtral_model_realtime.py    # Voxtral STT model
│   │   └── audio_processor_realtime.py  # Audio preprocessing
│   ├── streaming/                # Real-time communication
│   │   ├── websocket_server.py   # WebSocket handling
│   │   └── tcp_server.py         # TCP server (port 8766)
│   ├── tts/                      # Text-to-Speech components
│   │   ├── orpheus_tts_engine.py # Core TTS engine
│   │   └── tts_service.py        # TTS service interface
│   └── utils/                    # Shared utilities
│       ├── config.py             # Configuration management
│       └── logging_config.py     # Logging setup
├── tests/                        # Test suite
│   └── test_streaming.py         # Main test file
├── config.yaml                   # Main configuration
├── requirements.txt              # Python dependencies
├── setup.sh                      # Setup script
├── deploy_voxtral_tts.sh         # Single-command deployment
└── README.md                     # Documentation
```

## Architectural Patterns

### Modular Design
- **Separation of Concerns**: Each module handles specific functionality
- **Lazy Initialization**: Models loaded on-demand for memory efficiency
- **Service Layer Pattern**: High-level services abstract implementation details

### Real-time Processing
- **Async/Await**: Extensive use of asyncio for concurrent processing
- **WebSocket Communication**: Real-time bidirectional data flow
- **Streaming Architecture**: Chunked audio processing for low latency

### Configuration Management
- **Pydantic Models**: Type-safe configuration with validation
- **YAML Configuration**: Human-readable config files
- **Environment Variables**: Runtime configuration overrides

## Code Organization Principles

### Import Patterns
```python
# Standard library imports first
import asyncio
import time
from typing import Optional, List

# Third-party imports
import torch
from fastapi import FastAPI, WebSocket
from transformers import VoxtralForConditionalGeneration

# Local imports last
from src.utils.config import config
from src.models.voxtral_model_realtime import VoxtralModel
```

### Error Handling
- **Comprehensive Exception Handling**: All async operations wrapped in try/catch
- **Graceful Degradation**: Fallback behaviors for model loading failures
- **Structured Logging**: Detailed error reporting with context

### Performance Patterns
- **Model Pre-loading**: All models cached at startup
- **Memory Management**: Explicit GPU memory optimization
- **Threading Locks**: Thread-safe model access
- **Deque Buffers**: Efficient circular buffers for audio chunks

## File Naming Conventions

### Python Modules
- `*_realtime.py`: Real-time processing components
- `*_server.py`: Server implementations
- `*_config.py`: Configuration modules
- `test_*.py`: Test files

### Key Files
- `config.yaml`: Main application configuration
- `requirements.txt`: Python dependencies
- `deploy_*.sh`: Deployment scripts
- `README*.md`: Documentation files

## Development Guidelines

### Module Structure
- Each module should have clear single responsibility
- Use `__init__.py` files for package initialization
- Implement lazy loading for heavy resources (models)
- Include comprehensive docstrings and type hints

### Service Ports
- **8000**: Main UI server with WebSocket
- **8005**: Health check and monitoring
- **8766**: TCP streaming server (alternative interface)

### Logging Strategy
- **Structured Logging**: JSON-formatted logs with timestamps
- **Multiple Loggers**: Separate loggers for different components
- **File + Console**: Dual output for development and production
- **Log Levels**: DEBUG for development, INFO for production

### Testing Organization
- Unit tests in `tests/` directory
- Integration tests at root level (`test_integration.py`)
- Setup validation (`validate_setup.py`)
- Mock external dependencies in tests