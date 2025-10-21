"""
Voice Configuration Validation System
Validates voice consistency across all system components and detects configuration conflicts
"""
import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from src.utils.config import config, TTSConfig

# Setup logging
validator_logger = logging.getLogger("voice_config_validator")

@dataclass
class VoiceConfigValidationResult:
    """Result of voice configuration validation"""
    is_valid: bool
    voice_conflicts: List[str]
    missing_configurations: List[str]
    recommendations: List[str]
    component_voices: Dict[str, str]
    
    def has_conflicts(self) -> bool:
        """Check if there are any configuration conflicts"""
        return len(self.voice_conflicts) > 0
    
    def has_missing_configs(self) -> bool:
        """Check if there are missing configurations"""
        return len(self.missing_configurations) > 0

class VoiceConfigurationValidator:
    """
    Validates voice configuration consistency across all system components
    """
    
    def __init__(self):
        self.expected_default_voice = "hf_alpha"
        self.available_voices = [
            "hf_alpha", "af_bella", "af_nicole", "af_sarah", "af_sky",
            "am_adam", "am_michael", "am_edward", "hf_beta", "hm_psi"
        ]
        
    def validate_voice_consistency(self) -> VoiceConfigValidationResult:
        """
        Validate voice consistency across all system components
        
        Returns:
            VoiceConfigValidationResult with validation details
        """
        validator_logger.info("🔍 Starting voice configuration validation...")
        
        conflicts = []
        missing_configs = []
        recommendations = []
        component_voices = {}
        
        try:
            # 1. Validate config.yaml
            config_voice = self._validate_config_yaml(component_voices, conflicts, missing_configs)
            
            # 2. Validate environment variables
            self._validate_environment_variables(component_voices, conflicts, missing_configs)
            
            # 3. Validate Python code defaults
            self._validate_python_code_defaults(component_voices, conflicts, missing_configs)
            
            # 4. Validate frontend configuration
            self._validate_frontend_configuration(component_voices, conflicts, missing_configs)
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(conflicts, missing_configs, component_voices)
            
            # Determine overall validity
            is_valid = len(conflicts) == 0 and len(missing_configs) == 0
            
            result = VoiceConfigValidationResult(
                is_valid=is_valid,
                voice_conflicts=conflicts,
                missing_configurations=missing_configs,
                recommendations=recommendations,
                component_voices=component_voices
            )
            
            if is_valid:
                validator_logger.info("✅ Voice configuration validation passed")
            else:
                validator_logger.warning(f"⚠️ Voice configuration validation failed: {len(conflicts)} conflicts, {len(missing_configs)} missing configs")
            
            return result
            
        except Exception as e:
            validator_logger.error(f"❌ Voice configuration validation error: {e}")
            return VoiceConfigValidationResult(
                is_valid=False,
                voice_conflicts=[f"Validation error: {str(e)}"],
                missing_configurations=[],
                recommendations=["Fix validation system errors before proceeding"],
                component_voices=component_voices
            )
    
    def _validate_config_yaml(self, component_voices: Dict[str, str], 
                             conflicts: List[str], missing_configs: List[str]) -> Optional[str]:
        """Validate config.yaml voice configuration"""
        try:
            config_path = Path("config.yaml")
            if not config_path.exists():
                missing_configs.append("config.yaml file not found")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Check TTS configuration
            tts_config = config_data.get('tts', {})
            
            # Check default_voice
            default_voice = tts_config.get('default_voice')
            if default_voice:
                component_voices['config.yaml:tts.default_voice'] = default_voice
                if default_voice != self.expected_default_voice:
                    conflicts.append(f"config.yaml:tts.default_voice is '{default_voice}', expected '{self.expected_default_voice}'")
            else:
                missing_configs.append("config.yaml:tts.default_voice not set")
            
            # Check voice parameter
            voice = tts_config.get('voice')
            if voice:
                component_voices['config.yaml:tts.voice'] = voice
                if voice != self.expected_default_voice:
                    conflicts.append(f"config.yaml:tts.voice is '{voice}', expected '{self.expected_default_voice}'")
            else:
                missing_configs.append("config.yaml:tts.voice not set")
            
            return default_voice
            
        except Exception as e:
            validator_logger.error(f"❌ Error validating config.yaml: {e}")
            conflicts.append(f"Error reading config.yaml: {str(e)}")
            return None
    
    def _validate_environment_variables(self, component_voices: Dict[str, str], 
                                      conflicts: List[str], missing_configs: List[str]):
        """Validate environment variable configuration"""
        try:
            # Check .env.example file
            env_example_path = Path(".env.example")
            if env_example_path.exists():
                with open(env_example_path, 'r', encoding='utf-8') as f:
                    env_content = f.read()
                
                # Check TTS_DEFAULT_VOICE
                if "TTS_DEFAULT_VOICE=" in env_content:
                    for line in env_content.split('\n'):
                        if line.startswith("TTS_DEFAULT_VOICE="):
                            env_voice = line.split('=', 1)[1].strip()
                            component_voices['.env.example:TTS_DEFAULT_VOICE'] = env_voice
                            if env_voice != self.expected_default_voice:
                                conflicts.append(f".env.example:TTS_DEFAULT_VOICE is '{env_voice}', expected '{self.expected_default_voice}'")
                            break
                else:
                    missing_configs.append(".env.example:TTS_DEFAULT_VOICE not found")
                
                # Check KOKORO_VOICE
                if "KOKORO_VOICE=" in env_content:
                    for line in env_content.split('\n'):
                        if line.startswith("KOKORO_VOICE="):
                            kokoro_voice = line.split('=', 1)[1].strip()
                            component_voices['.env.example:KOKORO_VOICE'] = kokoro_voice
                            if kokoro_voice != self.expected_default_voice:
                                conflicts.append(f".env.example:KOKORO_VOICE is '{kokoro_voice}', expected '{self.expected_default_voice}'")
                            break
                else:
                    missing_configs.append(".env.example:KOKORO_VOICE not found")
            else:
                missing_configs.append(".env.example file not found")
            
            # Check runtime environment variables
            runtime_tts_voice = os.getenv("TTS_DEFAULT_VOICE")
            if runtime_tts_voice:
                component_voices['runtime:TTS_DEFAULT_VOICE'] = runtime_tts_voice
                if runtime_tts_voice != self.expected_default_voice:
                    conflicts.append(f"Runtime TTS_DEFAULT_VOICE is '{runtime_tts_voice}', expected '{self.expected_default_voice}'")
            
            runtime_kokoro_voice = os.getenv("KOKORO_VOICE")
            if runtime_kokoro_voice:
                component_voices['runtime:KOKORO_VOICE'] = runtime_kokoro_voice
                if runtime_kokoro_voice != self.expected_default_voice:
                    conflicts.append(f"Runtime KOKORO_VOICE is '{runtime_kokoro_voice}', expected '{self.expected_default_voice}'")
                    
        except Exception as e:
            validator_logger.error(f"❌ Error validating environment variables: {e}")
            conflicts.append(f"Error validating environment variables: {str(e)}")
    
    def _validate_python_code_defaults(self, component_voices: Dict[str, str], 
                                     conflicts: List[str], missing_configs: List[str]):
        """Validate Python code default voice parameters"""
        try:
            # Check KokoroTTSModel DEFAULT_VOICE
            kokoro_model_path = Path("src/models/kokoro_model_realtime.py")
            if kokoro_model_path.exists():
                with open(kokoro_model_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for DEFAULT_VOICE definition
                for line in content.split('\n'):
                    if 'DEFAULT_VOICE' in line and '=' in line:
                        # Extract the voice value
                        voice_part = line.split('=', 1)[1].strip().strip('"\'')
                        component_voices['kokoro_model_realtime.py:DEFAULT_VOICE'] = voice_part
                        if voice_part != self.expected_default_voice:
                            conflicts.append(f"KokoroTTSModel.DEFAULT_VOICE is '{voice_part}', expected '{self.expected_default_voice}'")
                        break
                else:
                    missing_configs.append("KokoroTTSModel.DEFAULT_VOICE not found")
            else:
                missing_configs.append("src/models/kokoro_model_realtime.py not found")
            
            # Check speech-to-speech pipeline DEFAULT_TTS_CONFIG
            pipeline_path = Path("src/models/speech_to_speech_pipeline.py")
            if pipeline_path.exists():
                with open(pipeline_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for DEFAULT_TTS_CONFIG voice setting
                in_default_config = False
                for line in content.split('\n'):
                    if 'DEFAULT_TTS_CONFIG' in line and '{' in line:
                        in_default_config = True
                    elif in_default_config and "'voice'" in line and ':' in line:
                        voice_part = line.split(':', 1)[1].strip().strip(',').strip('"\'')
                        # Remove comments from the voice value
                        if '#' in voice_part:
                            voice_part = voice_part.split('#')[0].strip().strip(',').strip('"\'')
                        component_voices['speech_to_speech_pipeline.py:DEFAULT_TTS_CONFIG.voice'] = voice_part
                        if voice_part != self.expected_default_voice:
                            conflicts.append(f"DEFAULT_TTS_CONFIG voice is '{voice_part}', expected '{self.expected_default_voice}'")
                        break
                    elif in_default_config and '}' in line:
                        break
                else:
                    pass  # speech_to_speech_pipeline.py was removed in cleanup
                
        except Exception as e:
            validator_logger.error(f"❌ Error validating Python code defaults: {e}")
            conflicts.append(f"Error validating Python code defaults: {str(e)}")
    
    def _validate_frontend_configuration(self, component_voices: Dict[str, str], 
                                       conflicts: List[str], missing_configs: List[str]):
        """Validate frontend voice configuration"""
        try:
            # Check ui_server_realtime.py for HTML and JavaScript configuration
            ui_server_path = Path("src/api/ui_server_realtime.py")
            if ui_server_path.exists():
                with open(ui_server_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check HTML option selected attribute
                if 'value="hf_alpha" selected' in content:
                    component_voices['ui_server_realtime.py:HTML_option_selected'] = "hf_alpha"
                elif 'selected' in content and 'hf_alpha' not in content:
                    # Find which voice is selected
                    for line in content.split('\n'):
                        if 'selected' in line and 'value=' in line:
                            # Extract voice from value="voice" selected
                            import re
                            match = re.search(r'value="([^"]+)"[^>]*selected', line)
                            if match:
                                selected_voice = match.group(1)
                                component_voices['ui_server_realtime.py:HTML_option_selected'] = selected_voice
                                conflicts.append(f"HTML option selected is '{selected_voice}', expected '{self.expected_default_voice}'")
                                break
                else:
                    missing_configs.append("HTML option selected attribute not found for hf_alpha")
                
                # Check JavaScript selectedVoice initialization
                if "selectedVoice = 'hf_alpha'" in content:
                    component_voices['ui_server_realtime.py:JS_selectedVoice'] = "hf_alpha"
                else:
                    # Look for selectedVoice assignment
                    for line in content.split('\n'):
                        if 'selectedVoice' in line and '=' in line and 'let' in line:
                            voice_part = line.split('=', 1)[1].strip().strip(';').strip('"\'')
                            component_voices['ui_server_realtime.py:JS_selectedVoice'] = voice_part
                            if voice_part != self.expected_default_voice:
                                conflicts.append(f"JavaScript selectedVoice is '{voice_part}', expected '{self.expected_default_voice}'")
                            break
                    else:
                        missing_configs.append("JavaScript selectedVoice initialization not found")
                
                # Check WebSocket handler voice usage
                websocket_voice_count = content.count(f'voice="{self.expected_default_voice}"')
                if websocket_voice_count > 0:
                    component_voices['ui_server_realtime.py:WebSocket_voice_usage'] = f"{self.expected_default_voice} ({websocket_voice_count} occurrences)"
                else:
                    missing_configs.append(f"WebSocket handler voice usage of '{self.expected_default_voice}' not found")
                    
            else:
                missing_configs.append("src/api/ui_server_realtime.py not found")
                
        except Exception as e:
            validator_logger.error(f"❌ Error validating frontend configuration: {e}")
            conflicts.append(f"Error validating frontend configuration: {str(e)}")
    
    def _generate_recommendations(self, conflicts: List[str], missing_configs: List[str], 
                                component_voices: Dict[str, str]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if conflicts:
            recommendations.append(f"Fix {len(conflicts)} voice configuration conflicts to ensure consistency")
            recommendations.append("Update all conflicting components to use 'hf_alpha' as default voice")
        
        if missing_configs:
            recommendations.append(f"Add {len(missing_configs)} missing voice configurations")
            recommendations.append("Ensure all components have explicit voice configuration")
        
        # Check for specific patterns
        unique_voices = set(component_voices.values())
        if len(unique_voices) > 1:
            recommendations.append(f"Standardize voice configuration - found {len(unique_voices)} different voices: {', '.join(unique_voices)}")
        
        if not conflicts and not missing_configs:
            recommendations.append("Voice configuration is consistent across all components")
            recommendations.append("Consider adding automated validation to CI/CD pipeline")
        
        return recommendations
    
    def validate_startup_configuration(self) -> bool:
        """
        Validate voice configuration at startup
        
        Returns:
            True if configuration is valid, False otherwise
        """
        validator_logger.info("🚀 Performing startup voice configuration validation...")
        
        try:
            result = self.validate_voice_consistency()
            
            if result.is_valid:
                validator_logger.info("✅ Startup voice configuration validation passed")
                return True
            else:
                validator_logger.error("❌ Startup voice configuration validation failed")
                validator_logger.error(f"   Conflicts: {len(result.voice_conflicts)}")
                for conflict in result.voice_conflicts:
                    validator_logger.error(f"     - {conflict}")
                
                validator_logger.error(f"   Missing configs: {len(result.missing_configurations)}")
                for missing in result.missing_configurations:
                    validator_logger.error(f"     - {missing}")
                
                return False
                
        except Exception as e:
            validator_logger.error(f"❌ Startup validation error: {e}")
            return False
    
    def get_configuration_report(self) -> Dict[str, Any]:
        """
        Get comprehensive configuration validation report
        
        Returns:
            Dictionary with detailed validation results
        """
        try:
            result = self.validate_voice_consistency()
            
            return {
                "validation_summary": {
                    "is_valid": result.is_valid,
                    "total_conflicts": len(result.voice_conflicts),
                    "total_missing_configs": len(result.missing_configurations),
                    "total_components_checked": len(result.component_voices)
                },
                "component_voices": result.component_voices,
                "conflicts": result.voice_conflicts,
                "missing_configurations": result.missing_configurations,
                "recommendations": result.recommendations,
                "expected_voice": self.expected_default_voice,
                "available_voices": self.available_voices
            }
            
        except Exception as e:
            validator_logger.error(f"❌ Error generating configuration report: {e}")
            return {
                "validation_summary": {
                    "is_valid": False,
                    "error": str(e)
                }
            }

# Global validator instance
voice_config_validator = VoiceConfigurationValidator()