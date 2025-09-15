# Implementation Plan

- [x] 1. Create GPU Memory Manager for shared model memory
  - Implement GPUMemoryManager class with VRAM validation and memory pool creation
  - Add memory cleanup and garbage collection functions
  - Create memory usage monitoring and statistics reporting
  - Write unit tests for memory allocation and cleanup operations
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 2. Implement Orpheus Direct Model integration
  - [x] 2.1 Create OrpheusDirectModel class with transformer integration
    - Load Orpheus model directly using transformers without FastAPI dependency
    - Implement model initialization with shared GPU memory pool
    - Add device management and model placement optimization
    - Write unit tests for model loading and initialization
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 Implement correct token processing algorithm
    - Create token extraction function using regex pattern matching
    - Implement Orpheus-FastAPI token processing formula: token_id - 10 - ((i % 7) * 4096)
    - Add token validation and range checking
    - Write unit tests with known token sequences and expected outputs
    - _Requirements: 1.2, 5.2_

  - [x] 2.3 Integrate SNAC codec for audio conversion
    - Load SNAC model (hubertsiuzdak/snac_24khz) with GPU optimization
    - Implement tokens_to_audio conversion with proper tensor reshaping
    - Add audio slice extraction using correct range [:, :, 2048:4096]
    - Optimize GPU processing with minimal CPU transfers
    - Write unit tests for token-to-audio conversion accuracy
    - _Requirements: 1.2, 2.2, 4.2_

- [x] 3. Create Unified Model Manager for coordinated initialization
  - [x] 3.1 Implement UnifiedModelManager class
    - Create centralized manager for both Voxtral and Orpheus models
    - Implement sequential model loading with memory optimization
    - Add model lifecycle management and cleanup
    - Create unified interface for model access
    - _Requirements: 1.1, 1.3, 3.1, 4.1_

  - [x] 3.2 Implement shared GPU memory management
    - Create memory pool sharing between Voxtral and Orpheus models
    - Add memory allocation tracking and optimization
    - Implement memory cleanup and garbage collection coordination
    - Write integration tests for memory sharing efficiency
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 4. Create Enhanced TTS Service with direct integration
  - [x] 4.1 Implement TTSServiceDirect class
    - Create async interface for TTS generation using direct Orpheus model
    - Add voice selection and validation logic
    - Implement audio format conversion and streaming support
    - Create comprehensive error handling for TTS operations
    - _Requirements: 1.1, 1.2, 2.2, 5.1_

  - [x] 4.2 Add performance monitoring and optimization
    - Implement timing tracking for each TTS generation stage
    - Add latency breakdown logging (token extraction, SNAC conversion, etc.)
    - Create performance target validation (<150ms for TTS generation)
    - Write performance tests to validate latency requirements
    - _Requirements: 2.1, 2.2, 2.4, 5.4_

- [x] 5. Implement Performance Monitor for latency tracking
  - Create PerformanceMonitor class with timing operations
  - Add end-to-end latency breakdown tracking
  - Implement performance target validation and warning system
  - Create performance analytics and optimization recommendations
  - Write unit tests for timing accuracy and performance calculations
  - _Requirements: 2.4, 5.4, 5.5_

- [x] 6. Create comprehensive error handling system
  - [x] 6.1 Implement initialization error recovery
    - Add ModelInitializationError and InsufficientVRAMError exception classes
    - Create graceful degradation with precision fallback (fp16 → fp32)
    - Implement CPU fallback mechanisms for GPU failures
    - Add detailed error logging with resolution steps
    - _Requirements: 1.4, 4.4, 5.1, 5.3_

  - [x] 6.2 Add runtime error handling and recovery
    - Implement AudioGenerationError and TokenProcessingError exceptions
    - Create automatic retry mechanisms with exponential backoff
    - Add alternative voice fallback for voice-specific failures
    - Implement error statistics tracking and pattern analysis
    - _Requirements: 1.5, 2.4, 5.1, 5.3_

- [x] 7. Update existing services to use direct integration
  - [x] 7.1 Modify main UI server to use UnifiedModelManager
    - Update src/api/ui_server_realtime.py to initialize UnifiedModelManager
    - Replace existing TTS service calls with TTSServiceDirect
    - Add performance monitoring integration to WebSocket handlers
    - Update error handling to use new exception types
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 7.2 Update Voxtral model integration
    - Modify VoxtralModel to work with UnifiedModelManager
    - Update model initialization to use shared GPU memory
    - Integrate performance monitoring for Voxtral processing
    - Ensure compatibility with existing audio processing pipeline
    - _Requirements: 1.3, 3.1, 4.1, 4.2_

- [x] 8. Create comprehensive test suite
  - [x] 8.1 Write unit tests for all new components
    - Test OrpheusDirectModel initialization and audio generation
    - Test token processing accuracy with reference data
    - Test SNAC conversion with known audio outputs
    - Test GPUMemoryManager memory operations
    - _Requirements: 1.4, 1.5, 4.4, 5.1_

  - [x] 8.2 Create integration tests for end-to-end pipeline
    - Test complete voice processing: Audio → Voxtral → Text → Orpheus → Audio
    - Test model initialization under various GPU configurations
    - Test error recovery and graceful degradation scenarios
    - Test performance under sustained load conditions
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2_

  - [x] 8.3 Implement performance validation tests
    - Create latency validation tests for sub-300ms end-to-end target
    - Test GPU memory usage stability under extended operation
    - Validate performance targets across different hardware configurations
    - Create load testing for concurrent voice generation requests
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 4.2, 4.3_

- [x] 9. Update configuration and deployment
  - [x] 9.1 Update configuration management
    - Add configuration options for direct Orpheus integration
    - Update GPU memory allocation settings
    - Add performance tuning parameters for latency optimization
    - Create environment-specific configuration templates
    - _Requirements: 3.5, 4.5_

  - [x] 9.2 Update deployment scripts and documentation
    - Modify setup scripts to install direct Orpheus dependencies
    - Update deployment documentation with new hardware requirements
    - Create troubleshooting guide for common initialization issues
    - Add performance tuning guide for different hardware configurations
    - _Requirements: 3.5, 4.5, 5.5_

- [x] 10. Final integration and validation
  - [x] 10.1 Complete system integration testing
    - Test entire system with direct Orpheus integration
    - Validate all requirements are met with comprehensive testing
    - Perform end-to-end latency validation and optimization
    - Test system stability under extended operation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 10.2 Performance optimization and tuning
    - Optimize GPU memory usage and model loading order
    - Fine-tune performance parameters for target latency
    - Implement final caching and optimization strategies
    - Validate performance targets across all supported hardware
    - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 4.4_