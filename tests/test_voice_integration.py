"""
Integration Tests for Voice Configuration System
Tests voice consistency across components and environment variable overrides
"""
import unittest
import tempfile
import os
import yaml
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.voice_config_validator import voice_config_validator
from src.utils.startup_validator import startup_validator, validate_startup_configuration

class TestVoiceConfigurationIntegration(unittest.TestCase):
    """Integration tests for voice configuration validation across components"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create basic directory structure
        self.create_directory_structure()
    
    def tearDown(self):
        """Clean up integration test environment"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_directory_structure(self):
        """Create the expected directory structure for tests"""
        directories = [
            'src/models',
            'src/api',
            'src/tts',
            'src/utils',
            'tests'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def create_config_files(self, voice="hf_alpha", create_conflicts=False):
        """Create configuration files with specified voice settings"""
        
        # Create config.yaml
        config_data = {
            'tts': {
                'default_voice': voice if not create_conflicts else 'af_bella',
                'voice': voice,
                'engine': 'kokoro',
                'sample_rate': 24000
            },
            'server': {
                'http_port': 8000
            },
            'model': {
                'device': 'cuda',
                'cache_dir': './model_cache'
            }
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config_data, f)
        
        # Create .env.example
        env_content = f"""# TTS Configuration
TTS_DEFAULT_VOICE={voice if not create_conflicts else 'af_bella'}
KOKORO_VOICE={voice}

# Other settings
DEBUG=false
"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        # Create Python configuration files
        self.create_python_files(voice, create_conflicts)
    
    def create_python_files(self, voice="hf_alpha", create_conflicts=False):
        """Create Python files with voice configuration"""
        
        # Create src/utils/config.py
        config_py_content = f'''"""Configuration module for testing"""
from pydantic import BaseModel
from typing import List

class TTSConfig(BaseModel):
    voice: str = "{voice}"
    default_voice: str = "{voice if not create_conflicts else 'af_nicole'}"
    engine: str = "kokoro"
    sample_rate: int = 24000

class ServerConfig(BaseModel):
    http_port: int = 8000

class ModelConfig(BaseModel):
    device: str = "cuda"
    cache_dir: str = "./model_cache"

class Config(BaseModel):
    tts: TTSConfig = TTSConfig()
    server: ServerConfig = ServerConfig()
    model: ModelConfig = ModelConfig()

config = Config()
'''
        
        with open('src/utils/config.py', 'w') as f:
            f.write(config_py_content)
        
        # Create src/models/kokoro_model_realtime.py
        kokoro_content = f'''"""Kokoro TTS Model for testing"""
import logging

class KokoroTTSModel:
    DEFAULT_VOICE = "{voice if not create_conflicts else 'hm_psi'}"
    
    def __init__(self, voice=None):
        self.voice = voice or self.DEFAULT_VOICE
        self.is_initialized = False
    
    async def initialize(self):
        self.is_initialized = True
        return True
    
    def get_model_info(self):
        return {{"is_initialized": self.is_initialized}}

kokoro_model = KokoroTTSModel()
'''
        
        with open('src/models/kokoro_model_realtime.py', 'w') as f:
            f.write(kokoro_content)
        
        # Create src/models/speech_to_speech_pipeline.py
        pipeline_content = f'''"""Speech-to-Speech Pipeline for testing"""

DEFAULT_TTS_CONFIG = {{
    'voice': '{voice if not create_conflicts else 'am_adam'}',
    'speed': 1.0,
    'lang': 'h',
    'sample_rate': 24000
}}

class SpeechToSpeechPipeline:
    def __init__(self):
        self.config = DEFAULT_TTS_CONFIG
'''
        
        with open('src/models/speech_to_speech_pipeline.py', 'w') as f:
            f.write(pipeline_content)
        
        # Create src/tts/tts_service.py
        tts_service_content = f'''"""TTS Service for testing"""

class TTSService:
    def __init__(self):
        self.default_voice = "{voice if not create_conflicts else 'af_sky'}"
        self.enabled = True
    
    def get_available_voices(self):
        return ["hf_alpha", "af_bella", "af_nicole", "af_sarah"]
'''
        
        with open('src/tts/tts_service.py', 'w') as f:
            f.write(tts_service_content)
        
        # Create src/api/ui_server_realtime.py
        ui_server_content = f'''"""UI Server for testing"""

HTML_CONTENT = """
<select id="voiceSelect">
    <option value="hf_alpha"{'selected' if voice == 'hf_alpha' and not create_conflicts else ''}>Heart (Calm & Friendly)</option>
    <option value="af_bella"{'selected' if create_conflicts else ''}>Bella (Energetic)</option>
    <option value="af_nicole">Nicole (Professional)</option>
</select>

<script>
let selectedVoice = '{voice if not create_conflicts else 'af_bella'}';

async function synthesizeSpeech(text) {{
    return await kokoro_model.synthesize_speech(
        text=text,
        voice="{voice if not create_conflicts else 'am_michael'}"
    );
}}
</script>
"""
'''
        
        with open('src/api/ui_server_realtime.py', 'w') as f:
            f.write(ui_server_content)
    
    def test_consistent_voice_configuration(self):
        """Test that all components use consistent voice configuration"""
        # Create files with consistent hf_alpha configuration
        self.create_config_files(voice="hf_alpha", create_conflicts=False)
        
        # Run voice configuration validation
        result = voice_config_validator.validate_voice_consistency()
        
        # Should pass validation
        self.assertTrue(result.is_valid, f"Validation failed: {result.voice_conflicts}")
        self.assertEqual(len(result.voice_conflicts), 0)
        self.assertEqual(len(result.missing_configurations), 0)
        
        # Check that all components report hf_alpha
        for component, voice in result.component_voices.items():
            self.assertEqual(voice, "hf_alpha", f"Component {component} has wrong voice: {voice}")
    
    def test_voice_configuration_conflicts(self):
        """Test detection of voice configuration conflicts"""
        # Create files with conflicting voice configurations
        self.create_config_files(voice="hf_alpha", create_conflicts=True)
        
        # Run voice configuration validation
        result = voice_config_validator.validate_voice_consistency()
        
        # Should fail validation due to conflicts
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.voice_conflicts), 0)
        
        # Check that conflicts are properly detected
        conflict_text = ' '.join(result.voice_conflicts)
        self.assertIn("af_bella", conflict_text)  # config.yaml conflict
        self.assertIn("af_bella", conflict_text)  # .env.example conflict
    
    def test_environment_variable_override(self):
        """Test environment variable override functionality"""
        # Create base configuration
        self.create_config_files(voice="hf_alpha", create_conflicts=False)
        
        # Test with environment variable overrides
        with patch.dict(os.environ, {
            'TTS_DEFAULT_VOICE': 'af_nicole',
            'KOKORO_VOICE': 'af_sarah'
        }):
            result = voice_config_validator.validate_voice_consistency()
            
            # Should detect conflicts from environment variables
            self.assertFalse(result.is_valid)
            self.assertGreater(len(result.voice_conflicts), 0)
            
            # Check that runtime environment variables are detected
            self.assertIn('runtime:TTS_DEFAULT_VOICE', result.component_voices)
            self.assertIn('runtime:KOKORO_VOICE', result.component_voices)
            self.assertEqual(result.component_voices['runtime:TTS_DEFAULT_VOICE'], 'af_nicole')
            self.assertEqual(result.component_voices['runtime:KOKORO_VOICE'], 'af_sarah')
    
    def test_missing_configuration_files(self):
        """Test handling of missing configuration files"""
        # Don't create any files - test missing file handling
        
        result = voice_config_validator.validate_voice_consistency()
        
        # Should detect missing configurations
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.missing_configurations), 0)
        
        # Check that missing files are properly reported
        missing_text = ' '.join(result.missing_configurations)
        self.assertIn("config.yaml", missing_text)
        self.assertIn(".env.example", missing_text)
    
    def test_startup_validation_integration(self):
        """Test startup validation integration"""
        # Create consistent configuration
        self.create_config_files(voice="hf_alpha", create_conflicts=False)
        
        # Mock the config module to avoid import issues
        with patch('src.utils.config.config') as mock_config:
            mock_tts = MagicMock()
            mock_tts.voice = "hf_alpha"
            mock_tts.default_voice = "hf_alpha"
            mock_tts.engine = "kokoro"
            
            mock_server = MagicMock()
            mock_server.http_port = 8000
            
            mock_model = MagicMock()
            mock_model.device = "cuda"
            mock_model.cache_dir = "./model_cache"
            
            mock_config.tts = mock_tts
            mock_config.server = mock_server
            mock_config.model = mock_model
            
            # Run startup validation
            result = startup_validator.validate_all_configurations(strict_mode=False)
            
            # Should pass validation
            self.assertTrue(result)
            
            # Check validation results
            validation_report = startup_validator.get_validation_report()
            self.assertGreater(validation_report['summary']['total_checks'], 0)
            self.assertGreater(validation_report['summary']['passed_checks'], 0)
    
    def test_configuration_report_generation(self):
        """Test comprehensive configuration report generation"""
        # Create configuration with some conflicts
        self.create_config_files(voice="hf_alpha", create_conflicts=True)
        
        # Generate configuration report
        report = voice_config_validator.get_configuration_report()
        
        # Validate report structure
        self.assertIn('validation_summary', report)
        self.assertIn('component_voices', report)
        self.assertIn('conflicts', report)
        self.assertIn('missing_configurations', report)
        self.assertIn('recommendations', report)
        self.assertIn('expected_voice', report)
        self.assertIn('available_voices', report)
        
        # Check report content
        self.assertEqual(report['expected_voice'], 'hf_alpha')
        self.assertIn('hf_alpha', report['available_voices'])
        self.assertFalse(report['validation_summary']['is_valid'])
        self.assertGreater(report['validation_summary']['total_conflicts'], 0)
    
    def test_voice_consistency_across_components(self):
        """Test voice consistency validation across all system components"""
        # Create configuration files
        self.create_config_files(voice="hf_alpha", create_conflicts=False)
        
        # Run validation
        result = voice_config_validator.validate_voice_consistency()
        
        # Check that all expected components are validated
        expected_components = [
            'config.yaml:tts.default_voice',
            'config.yaml:tts.voice',
            '.env.example:TTS_DEFAULT_VOICE',
            '.env.example:KOKORO_VOICE',
            'kokoro_model_realtime.py:DEFAULT_VOICE',
            'speech_to_speech_pipeline.py:DEFAULT_TTS_CONFIG.voice',
            'tts_service.py:default_voice',
            'ui_server_realtime.py:JS_selectedVoice'
        ]
        
        for component in expected_components:
            self.assertIn(component, result.component_voices, 
                         f"Component {component} not found in validation results")
    
    def test_recommendation_generation(self):
        """Test that appropriate recommendations are generated"""
        # Create configuration with conflicts
        self.create_config_files(voice="hf_alpha", create_conflicts=True)
        
        result = voice_config_validator.validate_voice_consistency()
        
        # Should generate recommendations
        self.assertGreater(len(result.recommendations), 0)
        
        # Check recommendation content
        rec_text = ' '.join(result.recommendations)
        self.assertIn("Fix", rec_text)
        self.assertIn("voice configuration", rec_text.lower())
    
    def test_validate_startup_configuration_function(self):
        """Test the standalone validate_startup_configuration function"""
        # Create consistent configuration
        self.create_config_files(voice="hf_alpha", create_conflicts=False)
        
        # Mock config to avoid import issues
        with patch('src.utils.config.config') as mock_config:
            mock_tts = MagicMock()
            mock_tts.voice = "hf_alpha"
            mock_tts.default_voice = "hf_alpha"
            
            mock_config.tts = mock_tts
            
            # Test non-strict mode
            result = validate_startup_configuration(strict_mode=False)
            self.assertTrue(result)
            
            # Test strict mode with valid config
            result = validate_startup_configuration(strict_mode=True)
            self.assertTrue(result)
    
    def test_validate_startup_configuration_strict_mode_failure(self):
        """Test startup validation failure in strict mode"""
        # Create configuration with conflicts
        self.create_config_files(voice="hf_alpha", create_conflicts=True)
        
        # Mock config
        with patch('src.utils.config.config') as mock_config:
            mock_tts = MagicMock()
            mock_tts.voice = None  # Missing voice config
            mock_config.tts = mock_tts
            
            # Should raise exception in strict mode
            from src.utils.startup_validator import StartupValidationError
            with self.assertRaises(StartupValidationError):
                validate_startup_configuration(strict_mode=True)
            
            # Should not raise exception in non-strict mode
            result = validate_startup_configuration(strict_mode=False)
            self.assertFalse(result)

class TestEnvironmentVariableOverrides(unittest.TestCase):
    """Test environment variable override functionality"""
    
    def setUp(self):
        """Set up environment variable tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create minimal directory structure
        os.makedirs('src/utils', exist_ok=True)
        
        # Create minimal config.py
        config_content = '''
from pydantic import BaseModel

class TTSConfig(BaseModel):
    voice: str = "hf_alpha"
    default_voice: str = "hf_alpha"

class Config(BaseModel):
    tts: TTSConfig = TTSConfig()

config = Config()
'''
        with open('src/utils/config.py', 'w') as f:
            f.write(config_content)
    
    def tearDown(self):
        """Clean up environment variable tests"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_environment_variables(self):
        """Test validation with no environment variables set"""
        # Create .env.example with correct values
        env_content = """TTS_DEFAULT_VOICE=hf_alpha
KOKORO_VOICE=hf_alpha"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            component_voices = {}
            conflicts = []
            missing_configs = []
            
            validator = voice_config_validator
            validator._validate_environment_variables(component_voices, conflicts, missing_configs)
            
            # Should have no conflicts from runtime variables
            runtime_conflicts = [c for c in conflicts if 'Runtime' in c]
            self.assertEqual(len(runtime_conflicts), 0)
    
    def test_correct_environment_variables(self):
        """Test validation with correct environment variables"""
        # Create .env.example
        env_content = """TTS_DEFAULT_VOICE=hf_alpha
KOKORO_VOICE=hf_alpha"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        # Set correct environment variables
        with patch.dict(os.environ, {
            'TTS_DEFAULT_VOICE': 'hf_alpha',
            'KOKORO_VOICE': 'hf_alpha'
        }):
            component_voices = {}
            conflicts = []
            missing_configs = []
            
            validator = voice_config_validator
            validator._validate_environment_variables(component_voices, conflicts, missing_configs)
            
            # Should have no conflicts
            self.assertEqual(len(conflicts), 0)
            
            # Should detect runtime variables
            self.assertIn('runtime:TTS_DEFAULT_VOICE', component_voices)
            self.assertIn('runtime:KOKORO_VOICE', component_voices)
            self.assertEqual(component_voices['runtime:TTS_DEFAULT_VOICE'], 'hf_alpha')
            self.assertEqual(component_voices['runtime:KOKORO_VOICE'], 'hf_alpha')
    
    def test_conflicting_environment_variables(self):
        """Test validation with conflicting environment variables"""
        # Create .env.example with correct values
        env_content = """TTS_DEFAULT_VOICE=hf_alpha
KOKORO_VOICE=hf_alpha"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        # Set conflicting environment variables
        with patch.dict(os.environ, {
            'TTS_DEFAULT_VOICE': 'af_bella',
            'KOKORO_VOICE': 'af_sarah'
        }):
            component_voices = {}
            conflicts = []
            missing_configs = []
            
            validator = voice_config_validator
            validator._validate_environment_variables(component_voices, conflicts, missing_configs)
            
            # Should detect conflicts
            self.assertGreater(len(conflicts), 0)
            
            # Check specific conflicts
            conflict_text = ' '.join(conflicts)
            self.assertIn("Runtime TTS_DEFAULT_VOICE is 'af_bella'", conflict_text)
            self.assertIn("Runtime KOKORO_VOICE is 'af_sarah'", conflict_text)

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run tests with high verbosity
    unittest.main(verbosity=2)