# Design Document

## Overview

The chunked streaming feature enhances the VoxtralModel to provide real-time text generation in small, natural chunks (3-5 words) rather than waiting for complete response generation. This improves perceived responsiveness and enables more natural conversational interactions by streaming partial responses as they are generated.

## Architecture

### Core Components

1. **Chunked Streaming Method**: `process_realtime_chunk_streaming()` - Main entry point for chunked streaming
2. **Token-by-Token Generation**: Generates text incrementally using the model's generation capabilities
3. **Chunk Management**: Buffers and manages word chunks for natural speech boundaries
4. **Stream Yielding**: Asynchronous generator that yields chunks as they become available

### Integration Points

- Integrates with existing VoxtralModel initialization and audio processing pipeline
- Uses the same audio preprocessing and speech detection as standard processing
- Leverages existing model, processor, and device management
- Compatible with current conversation template and prompt formatting

## Components and Interfaces

### Main Streaming Method

```python
async def process_realtime_chunk_streaming(
    self, 
    audio_data: Union[torch.Tensor, np.ndarray], 
    chunk_id: str, 
    mode: str = "conversation"
) -> AsyncGenerator[Dict[str, Any], None]
```

**Input Parameters:**
- `audio_data`: Audio input as tensor or numpy array
- `chunk_id`: Unique identifier for tracking the processing session
- `mode`: Processing mode (default: "conversation")

**Output Format:**
Each yielded chunk contains:
```python
{
    'success': bool,           # Processing success status
    'text': str,              # Generated text chunk
    'is_final': bool,         # Whether this is the final chunk
    'chunk_index': int,       # Sequential chunk number
    'processing_time_ms': float  # Time elapsed since start
}
```

### Supporting Components

#### Audio Processing
- Reuses existing audio conversion and speech detection logic
- Supports both torch.Tensor and numpy.ndarray inputs
- Maintains compatibility with current energy-based speech detection

#### Text Generation Engine
- Uses TextIteratorStreamer for token-by-token generation
- Implements background thread generation to avoid blocking
- Configurable generation parameters (temperature, top_p, max_tokens)

#### Chunk Buffering System
- Word-level buffering with configurable chunk sizes (default: 4 words)
- Natural boundary detection for smoother speech synthesis
- Timeout-based chunk completion for responsiveness

## Data Models

### Chunk Response Model
```python
ChunkResponse = {
    'success': bool,
    'text': str,
    'is_final': bool, 
    'chunk_index': int,
    'processing_time_ms': float,
    'error': Optional[str]  # Only present on error
}
```

### Configuration Parameters
```python
StreamingConfig = {
    'max_new_tokens': 50,      # Maximum tokens to generate
    'temperature': 0.7,        # Generation randomness
    'top_p': 0.9,             # Nucleus sampling threshold
    'chunk_size_words': 4,     # Words per chunk
    'timeout_ms': 60000        # Streamer timeout
}
```

## Error Handling

### Error Categories

1. **Initialization Errors**: Model not initialized
   - Response: Raise RuntimeError with clear message
   
2. **Audio Processing Errors**: Invalid audio data or speech detection failure
   - Response: Yield error chunk with appropriate message
   
3. **Generation Errors**: Model generation failures
   - Response: Yield fallback response with error logging
   
4. **Resource Cleanup Errors**: Temporary file cleanup failures
   - Response: Log warning but continue processing

### Error Response Format
```python
{
    'success': False,
    'text': 'Sorry, I didn\'t understand that.',
    'is_final': True,
    'chunk_index': 0,
    'error': str(exception_message)
}
```

### Fallback Mechanisms
- Graceful degradation to error messages on processing failures
- Automatic cleanup of temporary resources
- Comprehensive error logging for debugging

## Testing Strategy

### Unit Tests
1. **Audio Input Validation**
   - Test torch.Tensor and numpy.ndarray input handling
   - Verify proper audio format conversion
   - Test speech detection with various energy levels

2. **Chunk Generation Logic**
   - Test word buffering and chunk boundary detection
   - Verify chunk indexing and sequencing
   - Test final chunk marking

3. **Error Handling**
   - Test uninitialized model error handling
   - Test audio processing error scenarios
   - Verify proper error response formatting

### Integration Tests
1. **End-to-End Streaming**
   - Test complete audio-to-chunks pipeline
   - Verify chunk timing and ordering
   - Test with various audio samples and lengths

2. **Performance Testing**
   - Measure chunk generation latency
   - Test memory usage during streaming
   - Verify resource cleanup

### Mock Testing
1. **Model Generation Mocking**
   - Mock TextIteratorStreamer for predictable output
   - Test chunk logic with controlled text generation
   - Verify error handling with mocked failures

## Implementation Considerations

### Performance Optimizations
- Background thread generation to avoid blocking main thread
- Efficient word buffering to minimize memory allocation
- Configurable timeouts to prevent hanging operations

### Resource Management
- Automatic cleanup of temporary audio files
- Proper tensor memory management
- Thread-safe operations for concurrent access

### Configuration Integration
- Leverages existing config.yaml settings for audio and model parameters
- Supports runtime configuration of chunk sizes and generation parameters
- Maintains backward compatibility with existing processing methods

### Streaming Protocol
- Asynchronous generator pattern for efficient streaming
- Clear chunk boundaries and sequencing
- Proper final chunk indication for downstream processing