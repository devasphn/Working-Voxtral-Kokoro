# Design Document

## Overview

This design addresses the critical architectural issues in the current Voxtral + Orpheus TTS system by implementing direct model integration, eliminating external server dependencies, and achieving sub-300ms end-to-end latency for real-time voice conversations. The solution transforms the current multi-process, HTTP-dependent architecture into a unified, single-process system with optimized GPU memory sharing and streamlined data flow.

## Architecture

### Current Architecture Problems
- **External Dependencies**: Orpheus-FastAPI server creates initialization complexity and network latency
- **Multi-Process Overhead**: Separate processes for Voxtral and TTS cause memory fragmentation and IPC delays
- **Complex Token Processing**: Current implementation uses incorrect token offset calculations
- **GPU Memory Inefficiency**: Models loaded separately without memory optimization
- **Inconsistent Error Handling**: Failures occur at multiple integration points without clear debugging

### Target Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Python Process                        │
├─────────────────────────────────────────────────────────────────┤
│  Audio Input → Voxtral Model → Text → Orpheus Direct → Audio   │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │   Voxtral   │    │    Shared    │    │  Orpheus Direct │   │
│  │ (STT+LLM)   │◄──►│  GPU Memory  │◄──►│   + SNAC       │   │
│  │             │    │   Manager    │    │                 │   │
│  └─────────────┘    └──────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Changes
1. **Direct Model Loading**: Orpheus model loaded directly in application process
2. **Unified Memory Management**: Shared GPU memory pool between Voxtral and Orpheus
3. **Streamlined Data Flow**: Direct tensor passing without serialization/HTTP overhead
4. **Integrated Error Handling**: Single error handling system across all components

## Components and Interfaces

### 1. Unified Model Manager (`src/models/unified_model_manager.py`)
**Purpose**: Centralized management of both Voxtral and Orpheus models with shared GPU memory

**Key Responsibilities**:
- Initialize both models in correct order for memory optimization
- Implement GPU memory sharing and cleanup
- Provide unified interface for model operations
- Handle model lifecycle and error recovery

**Interface**:
```python
class UnifiedModelManager:
    async def initialize() -> bool
    async def get_voxtral_model() -> VoxtralModel
    async def get_orpheus_model() -> OrpheusDirectModel
    async def cleanup_gpu_memory() -> None
    def get_memory_stats() -> Dict[str, Any]
```

### 2. Orpheus Direct Model (`src/tts/orpheus_direct_model.py`)
**Purpose**: Direct Orpheus model integration without FastAPI dependency

**Key Responsibilities**:
- Load Orpheus model directly using transformers
- Implement correct token processing (token_id - 10 - ((i % 7) * 4096))
- Integrate SNAC codec for audio conversion
- Optimize for <150ms generation time

**Interface**:
```python
class OrpheusDirectModel:
    async def initialize(device: str, shared_memory_pool: Any) -> bool
    async def generate_speech(text: str, voice: str) -> bytes
    async def generate_tokens(text: str, voice: str) -> List[int]
    async def tokens_to_audio(tokens: List[int]) -> bytes
```

### 3. Enhanced TTS Service (`src/tts/tts_service_direct.py`)
**Purpose**: High-level TTS service using direct Orpheus integration

**Key Responsibilities**:
- Provide async interface for TTS generation
- Handle voice selection and validation
- Implement performance monitoring and logging
- Manage audio format conversion and streaming

**Interface**:
```python
class TTSServiceDirect:
    async def initialize() -> bool
    async def generate_speech_async(text: str, voice: str, format: str) -> Dict[str, Any]
    async def stream_speech(text: str, voice: str) -> AsyncGenerator[bytes, None]
    def get_available_voices() -> List[str]
```

### 4. Performance Monitor (`src/utils/performance_monitor.py`)
**Purpose**: Real-time performance tracking and latency optimization

**Key Responsibilities**:
- Track end-to-end latency breakdown
- Monitor GPU memory usage patterns
- Log performance warnings when targets exceeded
- Provide performance analytics and optimization suggestions

**Interface**:
```python
class PerformanceMonitor:
    def start_timing(operation: str) -> str
    def end_timing(timing_id: str) -> float
    def log_latency_breakdown(components: Dict[str, float]) -> None
    def check_performance_targets() -> Dict[str, bool]
```

### 5. GPU Memory Manager (`src/utils/gpu_memory_manager.py`)
**Purpose**: Optimized GPU memory allocation and sharing between models

**Key Responsibilities**:
- Implement memory pool for efficient allocation
- Handle memory cleanup and garbage collection
- Validate VRAM requirements before model loading
- Provide memory usage monitoring and alerts

**Interface**:
```python
class GPUMemoryManager:
    def validate_vram_requirements() -> bool
    def create_shared_memory_pool() -> Any
    def cleanup_unused_memory() -> None
    def get_memory_stats() -> Dict[str, Any]
```

## Data Models

### 1. Audio Processing Pipeline
```python
@dataclass
class AudioChunk:
    data: torch.Tensor
    sample_rate: int
    timestamp: float
    chunk_id: str
    duration_ms: float

@dataclass
class ProcessingResult:
    text: str
    processing_time_ms: float
    chunk_id: str
    success: bool
    metadata: Dict[str, Any]
```

### 2. TTS Generation Pipeline
```python
@dataclass
class TTSRequest:
    text: str
    voice: str
    format: str = "wav"
    quality: str = "high"
    streaming: bool = False

@dataclass
class TTSResponse:
    audio_data: bytes
    generation_time_ms: float
    audio_duration_ms: float
    success: bool
    metadata: Dict[str, Any]
```

### 3. Performance Metrics
```python
@dataclass
class LatencyBreakdown:
    voxtral_processing_ms: float
    text_generation_ms: float
    orpheus_generation_ms: float
    audio_conversion_ms: float
    total_latency_ms: float
    target_met: bool

@dataclass
class MemoryStats:
    total_vram_gb: float
    used_vram_gb: float
    voxtral_memory_gb: float
    orpheus_memory_gb: float
    available_vram_gb: float
```

## Error Handling

### 1. Initialization Error Recovery
```python
class ModelInitializationError(Exception):
    """Raised when model initialization fails"""
    
class InsufficientVRAMError(Exception):
    """Raised when VRAM requirements not met"""
    
class ModelLoadingError(Exception):
    """Raised when model loading fails"""
```

**Recovery Strategy**:
- Attempt model loading with reduced precision (fp16 → fp32)
- Implement graceful degradation with CPU fallback
- Provide clear error messages with resolution steps
- Log detailed initialization state for debugging

### 2. Runtime Error Handling
```python
class AudioGenerationError(Exception):
    """Raised when TTS generation fails"""
    
class TokenProcessingError(Exception):
    """Raised when token extraction/processing fails"""
    
class MemoryError(Exception):
    """Raised when GPU memory operations fail"""
```

**Recovery Strategy**:
- Implement automatic retry with exponential backoff
- Clear GPU memory and attempt recovery
- Fallback to alternative voice if specific voice fails
- Maintain error statistics for pattern analysis

### 3. Performance Error Handling
```python
class LatencyExceededError(Exception):
    """Raised when latency targets are exceeded"""
    
class PerformanceDegradationError(Exception):
    """Raised when performance degrades significantly"""
```

**Recovery Strategy**:
- Log performance warnings with detailed breakdown
- Implement automatic performance tuning adjustments
- Provide performance optimization recommendations
- Monitor trends and predict performance issues

## Testing Strategy

### 1. Unit Testing
**Components to Test**:
- Orpheus direct model loading and initialization
- Token processing accuracy with known inputs
- SNAC audio conversion with reference outputs
- GPU memory management operations
- Performance monitoring accuracy

**Test Framework**: pytest with async support
**Coverage Target**: >90% for critical components

### 2. Integration Testing
**Test Scenarios**:
- End-to-end voice processing pipeline
- Model initialization under various GPU configurations
- Memory sharing between Voxtral and Orpheus
- Error recovery and graceful degradation
- Performance under sustained load

**Test Data**: 
- Reference audio samples for each supported voice
- Known text inputs with expected token outputs
- Performance benchmarks for latency validation

### 3. Performance Testing
**Metrics to Validate**:
- Sub-300ms end-to-end latency consistently achieved
- GPU memory usage remains stable under load
- No memory leaks during extended operation
- Performance targets met across different hardware configurations

**Load Testing**:
- Concurrent voice generation requests
- Extended operation (24+ hours) stability testing
- Memory pressure testing with limited VRAM
- Performance degradation under high load

### 4. Hardware Compatibility Testing
**Target Configurations**:
- RTX A4500 (primary RunPod target)
- RTX 3070/4060 Ti (minimum VRAM)
- Various CUDA versions and driver combinations
- Different system RAM configurations

**Validation Criteria**:
- Successful initialization on all target hardware
- Performance targets met within acceptable variance
- Stable operation without crashes or memory errors
- Clear error messages for unsupported configurations

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
1. Implement UnifiedModelManager with basic model loading
2. Create OrpheusDirectModel with transformer integration
3. Implement GPUMemoryManager for memory optimization
4. Basic error handling and logging infrastructure

### Phase 2: Direct Integration (Days 3-4)
1. Implement correct token processing algorithm
2. Integrate SNAC codec for audio conversion
3. Create TTSServiceDirect with async interface
4. Implement PerformanceMonitor for latency tracking

### Phase 3: Optimization (Days 5-6)
1. Optimize GPU memory sharing between models
2. Implement performance tuning and caching
3. Add comprehensive error recovery mechanisms
4. Optimize for sub-300ms latency targets

### Phase 4: Testing & Validation (Days 7-8)
1. Comprehensive unit and integration testing
2. Performance validation across target hardware
3. Load testing and stability validation
4. Documentation and deployment preparation

## Performance Optimization Strategies

### 1. Model Loading Optimization
- Pre-allocate GPU memory pools before model loading
- Load models in optimal order (Voxtral first, then Orpheus)
- Use memory mapping for faster model loading
- Implement model caching for faster restarts

### 2. Inference Optimization
- Use mixed precision (fp16) for faster inference
- Implement KV-cache optimization for Orpheus
- Batch token processing where possible
- Optimize SNAC conversion with vectorized operations

### 3. Memory Optimization
- Implement memory pooling for tensor allocations
- Use in-place operations where possible
- Clear intermediate tensors promptly
- Monitor and prevent memory fragmentation

### 4. Latency Optimization
- Pipeline audio processing and TTS generation
- Use async/await for non-blocking operations
- Implement audio streaming for perceived latency reduction
- Optimize tensor data transfers between CPU/GPU

## Deployment Considerations

### 1. Hardware Requirements
**Minimum Configuration**:
- GPU: RTX 3070 or RTX 4060 Ti (8GB VRAM)
- RAM: 16GB system memory
- Storage: 50GB for model cache
- CUDA: 12.1+ with compatible drivers

**Recommended Configuration**:
- GPU: RTX A4500 or better (16GB+ VRAM)
- RAM: 32GB system memory
- Storage: 100GB NVMe for optimal model loading
- CUDA: Latest stable version

### 2. Environment Setup
- Python 3.8+ (3.12 not supported due to model compatibility)
- PyTorch 2.1.0+ with CUDA 12.1 support
- Transformers 4.54.0+ for Voxtral compatibility
- SNAC package for audio codec
- FastAPI for API endpoints (if needed)

### 3. Configuration Management
- Environment-specific configuration files
- GPU memory allocation settings
- Performance tuning parameters
- Voice and model selection options

### 4. Monitoring and Maintenance
- Real-time performance monitoring
- GPU memory usage tracking
- Error rate and recovery monitoring
- Performance trend analysis and alerting