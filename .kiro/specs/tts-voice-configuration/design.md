# Design Document

## Overview

This design addresses the systematic update of the default TTS voice from "hm_omega" to "hf_alpha" across all system components. The solution ensures configuration consistency by identifying all voice configuration points, implementing a centralized configuration approach, and updating each component to use the new default voice. The design prioritizes maintainability by establishing clear configuration hierarchies and validation mechanisms.

## Architecture

### Current Configuration Architecture
The system currently has voice configuration scattered across multiple files:
- Frontend JavaScript variables and HTML options
- Backend YAML configuration files
- Python class default parameters
- Environment variable templates
- WebSocket handler hardcoded values

### Target Configuration Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Centralized Voice Configuration               │
├─────────────────────────────────────────────────────────────────┤
│  config.yaml (Primary) → Environment Variables → Code Defaults  │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │  Frontend   │    │   Backend    │    │  TTS Models     │   │
│  │  (hf_alpha) │◄──►│ (hf_alpha)   │◄──►│  (hf_alpha)     │   │
│  │             │    │              │    │                 │   │
│  └─────────────┘    └──────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Hierarchy
1. **Primary Source**: config.yaml with `tts.default_voice: "hf_alpha"`
2. **Environment Override**: TTS_DEFAULT_VOICE environment variable
3. **Code Defaults**: Python class defaults as fallback
4. **Frontend Sync**: JavaScript reads from backend configuration API

## Components and Interfaces

### 1. Configuration Management (`src/utils/config.py`)
**Purpose**: Centralized configuration loading with voice default validation

**Key Responsibilities**:
- Load voice configuration from config.yaml
- Validate voice selection against available voices
- Provide configuration access to all components
- Handle environment variable overrides

**Interface Updates**:
```python
class TTSConfig:
    default_voice: str = "hf_alpha"  # Updated from "hm_omega"
    voice: str = "hf_alpha"          # Updated from "hm_omega"
    available_voices: List[str] = [
        "hf_alpha", "af_bella", "af_sarah", "af_nicole", 
        "af_sky", "am_adam", "am_michael", "am_edward"
    ]
    
    def validate_voice(self, voice: str) -> bool:
        return voice in self.available_voices
```

### 2. Frontend Voice Selection (`src/api/ui_server_realtime.py`)
**Purpose**: Update HTML and JavaScript to use new default voice

**Key Responsibilities**:
- Set HTML option "hf_alpha" as selected by default
- Initialize JavaScript selectedVoice variable to "hf_alpha"
- Update voice dropdown ordering to show preferred voice first
- Ensure frontend-backend voice synchronization

**Interface Updates**:
```html
<!-- Updated HTML options -->
<option value="hf_alpha" selected>Heart (Calm & Friendly)</option>
<option value="af_bella">Bella (Energetic & Excited)</option>
<option value="af_sarah">Sarah (Gentle & Empathetic)</option>
<!-- ... other options ... -->
```

```javascript
// Updated JavaScript initialization
let selectedVoice = 'hf_alpha';  // Changed from 'af_heart'
```

### 3. TTS Model Components
**Purpose**: Update all TTS model classes to use new default voice

#### 3.1 Kokoro TTS Model (`src/models/kokoro_model_realtime.py`)
```python
class KokoroTTSModel:
    DEFAULT_VOICE = "hf_alpha"  # Updated from "hm_omega"
    
    def __init__(self, device="cuda", voice="hf_alpha", speed=1.0, lang="h"):
        self.voice = voice or "hf_alpha"  # Updated default
```

#### 3.2 Unified Model Manager (`src/models/unified_model_manager.py`)
```python
def get_kokoro_model(self):
    return KokoroTTSModel(
        device=self.device,
        voice="hf_alpha",  # Updated from "hm_omega"
        speed=1.0,
        lang="h"
    )
```

#### 3.3 Speech-to-Speech Pipeline (`src/models/speech_to_speech_pipeline.py`)
```python
DEFAULT_TTS_CONFIG = {
    'voice': 'hf_alpha',        # Updated from 'hm_omega'
    'speed': 1.0,
    'lang': 'h',
    'sample_rate': 24000
}
```

### 4. WebSocket Handler Updates (`src/api/ui_server_realtime.py`)
**Purpose**: Update WebSocket audio generation to use new default voice

**Key Responsibilities**:
- Update TTS synthesis calls to use "hf_alpha"
- Update audio response metadata to reflect correct voice
- Ensure consistent voice usage in real-time processing

**Interface Updates**:
```python
# Updated WebSocket handler
result = await kokoro_model.synthesize_speech(
    text=response,
    voice="hf_alpha"  # Updated from "hm_omega"
)

# Updated metadata
response_data = {
    "voice": "hf_alpha",  # Updated from "hm_omega"
    "audio": base64_audio,
    "processing_time": processing_time
}
```

### 5. Environment Configuration Templates
**Purpose**: Update environment variable templates and examples

**Key Responsibilities**:
- Update .env.example with new default voice
- Ensure deployment scripts use correct voice configuration
- Provide clear documentation for voice configuration

**Interface Updates**:
```bash
# Updated .env.example
TTS_DEFAULT_VOICE=hf_alpha  # Updated from hm_omega
KOKORO_VOICE=hf_alpha       # Updated from hm_omega
```

## Data Models

### 1. Voice Configuration Model
```python
@dataclass
class VoiceConfig:
    voice_id: str
    display_name: str
    language: str
    gender: str
    style: str
    is_default: bool = False

# Voice registry with hf_alpha as default
VOICE_REGISTRY = {
    "hf_alpha": VoiceConfig(
        voice_id="hf_alpha",
        display_name="Heart (Calm & Friendly)",
        language="en",
        gender="female",
        style="calm",
        is_default=True  # Set as default
    ),
    # ... other voices
}
```

### 2. Configuration Validation Model
```python
@dataclass
class ConfigValidationResult:
    is_valid: bool
    voice_conflicts: List[str]
    missing_configurations: List[str]
    recommendations: List[str]
    
    def has_conflicts(self) -> bool:
        return len(self.voice_conflicts) > 0
```

## Error Handling

### 1. Configuration Validation Errors
```python
class VoiceConfigurationError(Exception):
    """Raised when voice configuration is invalid or inconsistent"""
    
class UnsupportedVoiceError(Exception):
    """Raised when requested voice is not available"""
    
class ConfigurationConflictError(Exception):
    """Raised when multiple config sources have conflicting voice settings"""
```

**Recovery Strategy**:
- Validate voice configuration at startup
- Fall back to "hf_alpha" if configured voice is unavailable
- Log configuration conflicts with resolution recommendations
- Provide clear error messages for unsupported voices

### 2. Runtime Voice Switching Errors
```python
class VoiceSwitchError(Exception):
    """Raised when voice switching fails during runtime"""
    
class ModelReloadError(Exception):
    """Raised when voice change requires model reload and fails"""
```

**Recovery Strategy**:
- Maintain current voice if switching fails
- Implement graceful fallback to default voice
- Log voice switching attempts and failures
- Provide user feedback for voice switching issues

## Testing Strategy

### 1. Configuration Testing
**Components to Test**:
- Configuration loading with new default voice
- Voice validation against available voice list
- Environment variable override functionality
- Configuration consistency across all components

**Test Scenarios**:
```python
def test_default_voice_configuration():
    """Test that all components use hf_alpha as default"""
    config = load_config()
    assert config.tts.default_voice == "hf_alpha"
    
def test_voice_consistency():
    """Test voice consistency across all components"""
    # Test frontend, backend, and model defaults match
    pass
```

### 2. Integration Testing
**Test Scenarios**:
- End-to-end voice generation with new default
- Frontend-backend voice synchronization
- Configuration file updates reflected in runtime
- Voice switching functionality with new default

**Test Data**:
- Sample text for TTS generation with hf_alpha voice
- Configuration files with various voice settings
- WebSocket messages for voice selection testing

### 3. Validation Testing
**Metrics to Validate**:
- All configuration sources specify "hf_alpha" as default
- No configuration conflicts between components
- Voice selection works correctly in UI
- Generated audio uses correct voice

**Validation Criteria**:
- Configuration validation passes for all components
- No hardcoded "hm_omega" references remain in codebase
- Voice metadata correctly reflects "hf_alpha" usage
- User experience shows "hf_alpha" as default selection

## Implementation Approach

### 1. Configuration File Updates
**Priority**: High (Foundation for all other changes)
- Update config.yaml with new default voice
- Update .env.example with new environment variables
- Validate configuration loading works correctly

### 2. Backend Model Updates
**Priority**: High (Core functionality)
- Update all Python class default parameters
- Update model initialization calls
- Update WebSocket handler voice usage

### 3. Frontend Updates
**Priority**: Medium (User interface)
- Update HTML option selection
- Update JavaScript variable initialization
- Update voice dropdown ordering

### 4. Validation and Testing
**Priority**: Medium (Quality assurance)
- Create configuration validation tests
- Test end-to-end voice generation
- Validate no configuration conflicts exist

## Deployment Considerations

### 1. Backward Compatibility
- Ensure existing voice selections continue to work
- Provide migration path for users with saved preferences
- Maintain support for all existing voice options

### 2. Configuration Migration
- Update deployment scripts to use new default
- Provide clear documentation for configuration changes
- Include validation steps in deployment process

### 3. Rollback Strategy
- Maintain ability to revert to previous default voice
- Document configuration rollback procedures
- Ensure rollback doesn't break existing functionality

### 4. Monitoring and Validation
- Monitor voice usage after deployment
- Validate configuration consistency in production
- Track any voice-related errors or issues
- Provide clear logging for voice configuration debugging