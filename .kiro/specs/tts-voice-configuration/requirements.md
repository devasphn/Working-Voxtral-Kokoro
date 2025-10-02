# Requirements Document

## Introduction

The current TTS system uses "hm_omega" as the default voice across multiple configuration files and components. This creates inconsistency and requires users to manually change voice settings in multiple places. This spec addresses centralizing and updating the default TTS voice to "hf_alpha" (Heart - Calm & Friendly) across all system components to provide a better default user experience with a more natural and appealing voice.

## Requirements

### Requirement 1: Update Frontend Voice Selection

**User Story:** As a user of the voice AI system, I want the default voice selection to be "hf_alpha" (Heart - Calm & Friendly) when I first load the interface, so that I get the best voice experience without needing to manually change settings.

#### Acceptance Criteria

1. WHEN the UI loads THEN the voice dropdown SHALL default to "hf_alpha" (Heart - Calm & Friendly)
2. WHEN the voice selection is initialized THEN "hf_alpha" SHALL be marked as selected in the HTML options
3. WHEN JavaScript initializes THEN the selectedVoice variable SHALL be set to "hf_alpha"
4. WHEN the voice dropdown is rendered THEN "hf_alpha" SHALL appear as the first/default option
5. WHEN users access the system for the first time THEN they SHALL hear the "hf_alpha" voice without configuration

### Requirement 2: Update Backend Configuration Files

**User Story:** As a system administrator, I want all backend configuration files to use "hf_alpha" as the default TTS voice, so that the system consistently uses the preferred voice across all components.

#### Acceptance Criteria

1. WHEN the system reads config.yaml THEN the default_voice SHALL be set to "hf_alpha"
2. WHEN TTS configuration is loaded THEN the voice parameter SHALL default to "hf_alpha"
3. WHEN environment variables are used THEN TTS_DEFAULT_VOICE SHALL be set to "hf_alpha"
4. WHEN the system starts THEN all configuration sources SHALL consistently specify "hf_alpha"
5. WHEN configuration is validated THEN there SHALL be no conflicts between different config sources

### Requirement 3: Update TTS Model Components

**User Story:** As a developer maintaining the TTS system, I want all TTS model classes and services to use "hf_alpha" as their default voice parameter, so that voice consistency is maintained throughout the codebase.

#### Acceptance Criteria

1. WHEN KokoroTTSModel initializes THEN the default voice parameter SHALL be "hf_alpha"
2. WHEN UnifiedModelManager creates Kokoro models THEN it SHALL pass "hf_alpha" as the default voice
3. WHEN TTSServiceDirect is instantiated THEN it SHALL use "hf_alpha" as the default voice
4. WHEN speech synthesis is requested without specifying voice THEN "hf_alpha" SHALL be used
5. WHEN model constants are defined THEN DEFAULT_VOICE SHALL be set to "hf_alpha"

### Requirement 4: Update Speech-to-Speech Pipeline

**User Story:** As a user having voice conversations, I want the speech-to-speech pipeline to use "hf_alpha" voice by default, so that all generated responses use the preferred voice without manual configuration.

#### Acceptance Criteria

1. WHEN the speech-to-speech pipeline initializes THEN the default TTS config SHALL specify "hf_alpha"
2. WHEN audio responses are generated THEN they SHALL use "hf_alpha" voice unless explicitly overridden
3. WHEN WebSocket handlers process TTS requests THEN they SHALL default to "hf_alpha"
4. WHEN audio metadata is returned THEN it SHALL indicate "hf_alpha" as the voice used
5. WHEN pipeline configuration is loaded THEN "hf_alpha" SHALL be the consistent default across all stages

### Requirement 5: Ensure Configuration Consistency

**User Story:** As a system administrator, I want to ensure that changing the default voice is applied consistently across all system components, so that there are no mismatches or conflicts between different parts of the system.

#### Acceptance Criteria

1. WHEN the system starts THEN all components SHALL use the same default voice "hf_alpha"
2. WHEN configuration files are read THEN there SHALL be no conflicting voice defaults
3. WHEN voice selection is made THEN it SHALL be consistent between frontend and backend
4. WHEN the system is deployed THEN voice configuration SHALL be validated for consistency
5. WHEN debugging voice issues THEN the default voice source SHALL be clearly traceable