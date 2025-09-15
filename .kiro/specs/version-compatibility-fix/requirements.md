# Requirements Document

## Introduction

The current Voxtral + Orpheus TTS system has critical version compatibility issues that prevent successful deployment and operation. The system uses incorrect model names, incompatible package versions, and outdated API calls. This spec addresses the exact version requirements for both Voxtral and Orpheus models, ensuring perfect compatibility and reliable operation.

## Requirements

### Requirement 1: Correct Voxtral Model Version and Configuration

**User Story:** As a developer deploying the voice AI system, I want to use the correct and stable Voxtral model version with proper transformers compatibility, so that speech recognition works reliably without version conflicts.

#### Acceptance Criteria

1. WHEN the system initializes THEN it SHALL use `mistralai/Voxtral-Mini-3B-2507` as the correct multimodal model (confirmed working)
2. WHEN transformers library is installed THEN it SHALL be version `>=4.54.0,<4.60.0` for Voxtral compatibility
3. WHEN mistral-common is installed THEN it SHALL be version `>=1.4.0` for latest chunking improvements
4. WHEN the model loads THEN it SHALL use the updated processor API with proper audio chunking
5. WHEN audio processing occurs THEN it SHALL use the latest mistral_common.audio.Audio API with streaming support

### Requirement 2: Correct Orpheus TTS Integration with Official Package

**User Story:** As a developer integrating TTS functionality, I want to use the official Orpheus TTS package with the correct model identifier, so that text-to-speech generation works without complex token processing.

#### Acceptance Criteria

1. WHEN Orpheus TTS is installed THEN it SHALL use the official `orpheus-tts>=0.1.0` package
2. WHEN the Orpheus model loads THEN it SHALL use `canopylabs/orpheus-tts-0.1-finetune-prod` as the model identifier
3. WHEN speech is generated THEN it SHALL use the official `OrpheusModel.generate_speech()` API
4. WHEN audio is produced THEN it SHALL return properly formatted WAV audio without SNAC conversion
5. WHEN the system starts THEN it SHALL NOT require external FastAPI servers or complex token processing

### Requirement 3: Compatible PyTorch and CUDA Versions

**User Story:** As a system administrator deploying on GPU infrastructure, I want compatible PyTorch and CUDA versions that support both models efficiently, so that GPU acceleration works without memory or compatibility issues.

#### Acceptance Criteria

1. WHEN PyTorch is installed THEN it SHALL be version `>=2.1.0,<2.5.0` for model compatibility
2. WHEN CUDA is used THEN it SHALL be version `12.1` or `12.4` for optimal performance
3. WHEN models load THEN they SHALL share GPU memory efficiently without conflicts
4. WHEN Flash Attention is available THEN it SHALL be version `>=2.5.0` for Voxtral compatibility
5. WHEN memory management occurs THEN it SHALL prevent OOM errors through proper cleanup

### Requirement 4: Streamlined Dependencies Without Legacy Packages

**User Story:** As a developer maintaining the system, I want clean, minimal dependencies without legacy or conflicting packages, so that installation is reliable and maintenance is straightforward.

#### Acceptance Criteria

1. WHEN dependencies are installed THEN the system SHALL NOT include `snac` package (not needed)
2. WHEN dependencies are installed THEN the system SHALL NOT include `orpheus-fastapi` (not needed)
3. WHEN the system runs THEN it SHALL use only official HuggingFace and Orpheus TTS packages
4. WHEN packages are updated THEN version conflicts SHALL be prevented through proper pinning
5. WHEN deployment occurs THEN it SHALL complete without package resolution errors

### Requirement 5: Updated API Calls and Method Signatures

**User Story:** As a developer working with the latest model APIs, I want all method calls to use current, non-deprecated APIs, so that the system works with modern package versions without warnings or failures.

#### Acceptance Criteria

1. WHEN Voxtral processes audio THEN it SHALL use `Audio.from_file()` instead of deprecated methods
2. WHEN chat templates are applied THEN it SHALL use `processor.apply_chat_template()` with current signature
3. WHEN Orpheus generates speech THEN it SHALL use `model.generate_speech(prompt=text, voice=voice)`
4. WHEN audio chunks are processed THEN it SHALL use `AudioChunk.from_audio()` with proper format
5. WHEN the system logs information THEN it SHALL indicate which API versions are being used

### Requirement 6: Performance Optimization for Correct Versions

**User Story:** As a user expecting fast voice responses, I want the system optimized for the correct model versions to achieve sub-300ms latency, so that conversations feel natural and responsive.

#### Acceptance Criteria

1. WHEN Voxtral processes audio THEN it SHALL complete speech recognition in <100ms
2. WHEN Orpheus generates speech THEN it SHALL complete TTS generation in <150ms
3. WHEN audio is streamed THEN it SHALL reach the client in <50ms
4. WHEN Flash Attention is used THEN it SHALL be properly configured for Voxtral architecture
5. WHEN performance is measured THEN it SHALL meet or exceed the original Voxtral performance targets

### Requirement 7: Comprehensive Version Validation and Testing

**User Story:** As a developer deploying the system, I want comprehensive validation that all versions are compatible and working correctly, so that I can be confident the deployment will succeed.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL validate all package versions are compatible
2. WHEN models are loaded THEN it SHALL test basic functionality of both Voxtral and Orpheus
3. WHEN validation runs THEN it SHALL check GPU compatibility and memory requirements
4. WHEN errors occur THEN it SHALL provide clear guidance on version requirements
5. WHEN deployment completes THEN it SHALL confirm all components are working with correct versions