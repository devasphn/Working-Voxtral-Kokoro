# Implementation Plan

- [x] 1. Update primary configuration files

  - Update config.yaml to set default_voice and voice to "hf_alpha"
  - Update .env.example to set TTS_DEFAULT_VOICE and KOKORO_VOICE to "hf_alpha"
  - Validate configuration loading works with new defaults
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Update TTS model component defaults

  - [x] 2.1 Update KokoroTTSModel default voice parameter

    - Modify src/models/kokoro_model_realtime.py to set DEFAULT_VOICE = "hf_alpha"
    - Update **init** method default voice parameter to "hf_alpha"
    - Update voice fallback logic to use "hf_alpha"
    - _Requirements: 3.1, 3.5_

  - [x] 2.2 Update UnifiedModelManager Kokoro model creation
    - Modify src/models/unified_model_manager.py get_kokoro_model method
    - Change voice parameter from "hm_omega" to "hf_alpha" in KokoroTTSModel instantiation
    - Ensure consistent voice usage across model manager
    - _Requirements: 3.2, 3.5_

- [x] 3. Update speech-to-speech pipeline configuration

  - Modify src/models/speech_to_speech_pipeline.py DEFAULT_TTS_CONFIG
  - Change 'voice' key from 'hm_omega' to 'hf_alpha'
  - Update any other voice references in pipeline configuration
  - Validate pipeline uses new default voice consistently
  - _Requirements: 4.1, 4.2, 4.5_

- [x] 4. Update main UI server WebSocket handlers

  - [x] 4.1 Update WebSocket TTS synthesis calls

    - Modify src/api/ui_server_realtime.py WebSocket handler
    - Change kokoro_model.synthesize_speech voice parameter to "hf_alpha"
    - Update any hardcoded voice references in WebSocket processing
    - _Requirements: 4.3, 4.4_

  - [x] 4.2 Update audio response metadata
    - Modify audio response metadata to indicate "hf_alpha" as voice used
    - Update any voice logging or debugging information
    - Ensure consistent voice reporting in WebSocket responses
    - _Requirements: 4.4, 5.5_

- [x] 5. Update frontend voice selection interface

  - [x] 5.1 Update HTML voice dropdown options

    - Modify src/api/ui_server_realtime.py HTML section
    - Add "selected" attribute to hf_alpha option
    - Remove "selected" attribute from current default option
    - Reorder options to show hf_alpha first if desired
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 5.2 Update JavaScript voice initialization
    - Modify JavaScript selectedVoice variable initialization to 'hf_alpha'
    - Update any other JavaScript voice default references
    - Ensure frontend voice selection synchronizes with backend
    - _Requirements: 1.3, 1.5, 5.3_

- [x] 6. Update TTS service components

  - [x] 6.1 Update TTSServiceDirect default voice

    - Modify src/tts/tts_service_direct.py (if exists) to use "hf_alpha" default
    - Update any TTS service initialization with new default voice
    - Ensure service-level voice consistency
    - _Requirements: 3.3, 3.4_

  - [x] 6.2 Update any additional TTS configuration files
    - Search for and update src/tts/kokoro_tts.py if it exists
    - Update any other TTS-related configuration files with new default
    - Ensure no orphaned "hm_omega" references remain
    - _Requirements: 3.5, 5.1_

- [x] 7. Create configuration validation system

  - [x] 7.1 Implement voice configuration validation

    - Create validation function to check voice consistency across components
    - Add startup validation to ensure all components use same default voice
    - Implement configuration conflict detection and reporting
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 7.2 Add configuration testing
    - Write unit tests to validate voice configuration loading
    - Create integration tests for voice consistency across components
    - Add tests for environment variable override functionality
    - _Requirements: 5.3, 5.4, 5.5_

- [-] 8. Update any remaining hardcoded voice references

  - [x] 8.1 Search and replace remaining "hm_omega" references

    - Use grep/search to find any remaining "hm_omega" references in codebase
    - Update any missed configuration files or code comments
    - Ensure complete migration from old default voice
    - _Requirements: 5.1, 5.2_

  - [-] 8.2 Validate no configuration conflicts exist
    - Run comprehensive search for voice configuration inconsistencies
    - Test system startup with new configuration
    - Verify end-to-end voice generation uses "hf_alpha"
    - _Requirements: 5.3, 5.4, 5.5_

- [ ] 9. Test and validate complete voice configuration update

  - [ ] 9.1 Test frontend voice selection

    - Verify UI loads with "hf_alpha" selected by default
    - Test voice dropdown shows correct default selection
    - Validate frontend-backend voice synchronization
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 9.2 Test backend voice generation
    - Test TTS generation uses "hf_alpha" voice by default
    - Verify WebSocket responses indicate correct voice usage
    - Test speech-to-speech pipeline uses new default voice
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 10. Final validation and cleanup

  - [ ] 10.1 Perform comprehensive system testing

    - Test complete voice conversation flow with new default voice
    - Validate configuration consistency across all components
    - Test system startup and initialization with new defaults
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 10.2 Update documentation and deployment notes
    - Document voice configuration changes for deployment
    - Update any user documentation about default voice
    - Create migration notes for existing installations
    - _Requirements: 5.4, 5.5_
