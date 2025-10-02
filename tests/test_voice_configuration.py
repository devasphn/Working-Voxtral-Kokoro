"""
Unit Tests for Voice Configuration Validation System
Tests voice configuration loading, validation, and consistency checking
"""
import unittest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Import the modules to test
from src.utils.voice_config_validator import VoiceConfigurationValidator, VoiceConfigValidationResult
from src.utils.startup_validator import StartupValidator, StartupValidationError

class TestVoiceConfigurationValidator(unittest.TestCase):
    """Test cases for VoiceConfigurationValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = VoiceConfigurationValidator()
        self.expected_voice = "hf_alpha"
    
    def test_validator_initialization(self):
        """Test validator initializes with correct default values"""
        self.assertEqual(self.validator.expected_default_voice, "hf_alpha")
        self.assertIn("hf_alpha", self.validator.available_voices)
        self.assertNotIn("hm_omega", self.validator.available_voices)
        self.assertIn("af_bella", self.validator.available_voices)
    
    def test_validation_result_dataclass(self):
        """Test VoiceConfigValidationResult dataclass functionality"""
        result = VoiceConfigValidationResult(
            is_valid=False,
            voice_conflicts=["conflict1", "conflict2"],
            missing_configurations=["missing1"],
            recommendations=["rec1"],
            component_voices={"comp1": "voice1"}
        )
        
        self.assertFalse(result.is_valid)
        self.assertTrue(result.has_conflicts())
        self.assertTrue(result.has_missing_configs())
        self.assertEqual(len(result.voice_conflicts), 2)
        self.assertEqual(len(result.missing_configurations), 1)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_config_yaml_success(self, mock_file, mock_exists):
        """Test successful config.yaml validation"""
        mock_exists.return_value = True
        
        # Mock config.yaml content with correct voice configuration
        config_content = """
tts:
  default_voice: "hf_alpha"
  voice: "hf_alpha"
  engine: "kokoro"
"""
        mock_file.return_value.read.return_value = config_content
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        result = self.validator._validate_config_yaml(component_voices, conflicts, missing_configs)
        
        self.assertEqual(result, "hf_alpha")
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(missing_configs), 0)
        self.assertIn('config.yaml:tts.default_voice', component_voices)
        self.assertIn('config.yaml:tts.voice', component_voices)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_config_yaml_conflicts(self, mock_file, mock_exists):
        """Test config.yaml validation with voice conflicts"""
        mock_exists.return_value = True
        
        # Mock config.yaml content with incorrect voice configuration
        config_content = """
tts:
  default_voice: "af_bella"
  voice: "af_nicole"
  engine: "kokoro"
"""
        mock_file.return_value.read.return_value = config_content
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        result = self.validator._validate_config_yaml(component_voices, conflicts, missing_configs)
        
        self.assertEqual(result, "af_bella")
        self.assertEqual(len(conflicts), 2)  # Both default_voice and voice are wrong
        self.assertEqual(len(missing_configs), 0)
        self.assertIn("config.yaml:tts.default_voice is 'af_bella'", conflicts[0])
        self.assertIn("config.yaml:tts.voice is 'af_nicole'", conflicts[1])
    
    @patch('pathlib.Path.exists')
    def test_validate_config_yaml_missing_file(self, mock_exists):
        """Test config.yaml validation when file is missing"""
        mock_exists.return_value = False
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        result = self.validator._validate_config_yaml(component_voices, conflicts, missing_configs)
        
        self.assertIsNone(result)
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(missing_configs), 1)
        self.assertIn("config.yaml file not found", missing_configs[0])
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_environment_variables_success(self, mock_file, mock_exists):
        """Test successful environment variables validation"""
        mock_exists.return_value = True
        
        # Mock .env.example content with correct configuration
        env_content = """
# TTS Configuration
TTS_DEFAULT_VOICE=hf_alpha
KOKORO_VOICE=hf_alpha
# Other settings
DEBUG=false
"""
        mock_file.return_value.read.return_value = env_content
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        with patch.dict(os.environ, {}, clear=True):
            self.validator._validate_environment_variables(component_voices, conflicts, missing_configs)
        
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(missing_configs), 0)
        self.assertEqual(component_voices['.env.example:TTS_DEFAULT_VOICE'], 'hf_alpha')
        self.assertEqual(component_voices['.env.example:KOKORO_VOICE'], 'hf_alpha')
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_environment_variables_conflicts(self, mock_file, mock_exists):
        """Test environment variables validation with conflicts"""
        mock_exists.return_value = True
        
        # Mock .env.example content with incorrect configuration
        env_content = """
TTS_DEFAULT_VOICE=af_bella
KOKORO_VOICE=af_nicole
"""
        mock_file.return_value.read.return_value = env_content
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        # Also test runtime environment variables
        with patch.dict(os.environ, {'TTS_DEFAULT_VOICE': 'af_nicole', 'KOKORO_VOICE': 'af_sarah'}):
            self.validator._validate_environment_variables(component_voices, conflicts, missing_configs)
        
        self.assertEqual(len(conflicts), 4)  # 2 from .env.example + 2 from runtime
        self.assertEqual(len(missing_configs), 0)
        
        # Check that conflicts are properly detected
        conflict_messages = ' '.join(conflicts)
        self.assertIn("TTS_DEFAULT_VOICE is 'af_bella'", conflict_messages)
        self.assertIn("KOKORO_VOICE is 'af_nicole'", conflict_messages)
        self.assertIn("Runtime TTS_DEFAULT_VOICE is 'af_nicole'", conflict_messages)
        self.assertIn("Runtime KOKORO_VOICE is 'af_sarah'", conflict_messages)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_python_code_defaults_success(self, mock_file, mock_exists):
        """Test successful Python code defaults validation"""
        mock_exists.return_value = True
        
        # Mock file contents with correct voice configuration
        kokoro_model_content = '''
class KokoroTTSModel:
    DEFAULT_VOICE = "hf_alpha"
    
    def __init__(self):
        pass
'''
        
        pipeline_content = '''
DEFAULT_TTS_CONFIG = {
    'voice': 'hf_alpha',
    'speed': 1.0,
    'lang': 'h'
}
'''
        
        tts_service_content = '''
class TTSService:
    def __init__(self):
        self.default_voice = "hf_alpha"
'''
        
        # Mock different files being read
        def mock_open_side_effect(*args, **kwargs):
            filename = str(args[0])
            if 'kokoro_model_realtime.py' in filename:
                return mock_open(read_data=kokoro_model_content).return_value
            elif 'speech_to_speech_pipeline.py' in filename:
                return mock_open(read_data=pipeline_content).return_value
            elif 'tts_service.py' in filename:
                return mock_open(read_data=tts_service_content).return_value
            return mock_open().return_value
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        with patch('builtins.open', side_effect=mock_open_side_effect):
            self.validator._validate_python_code_defaults(component_voices, conflicts, missing_configs)
        
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(missing_configs), 0)
        self.assertEqual(component_voices['kokoro_model_realtime.py:DEFAULT_VOICE'], 'hf_alpha')
        self.assertEqual(component_voices['speech_to_speech_pipeline.py:DEFAULT_TTS_CONFIG.voice'], 'hf_alpha')
        self.assertEqual(component_voices['tts_service.py:default_voice'], 'hf_alpha')
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_frontend_configuration_success(self, mock_file, mock_exists):
        """Test successful frontend configuration validation"""
        mock_exists.return_value = True
        
        # Mock ui_server_realtime.py content with correct configuration
        ui_server_content = '''
<select id="voiceSelect">
    <option value="hf_alpha" selected>Heart (Calm & Friendly)</option>
    <option value="af_bella">Bella (Energetic)</option>
</select>

<script>
let selectedVoice = 'hf_alpha';

// WebSocket handler
result = await kokoro_model.synthesize_speech(
    text=response,
    voice="hf_alpha"
)
</script>
'''
        
        mock_file.return_value.read.return_value = ui_server_content
        
        component_voices = {}
        conflicts = []
        missing_configs = []
        
        self.validator._validate_frontend_configuration(component_voices, conflicts, missing_configs)
        
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(len(missing_configs), 0)
        self.assertEqual(component_voices['ui_server_realtime.py:HTML_option_selected'], 'hf_alpha')
        self.assertEqual(component_voices['ui_server_realtime.py:JS_selectedVoice'], 'hf_alpha')
        self.assertIn('hf_alpha', component_voices['ui_server_realtime.py:WebSocket_voice_usage'])
    
    def test_generate_recommendations(self):
        """Test recommendation generation based on validation results"""
        conflicts = ["config.yaml voice mismatch", "frontend voice mismatch"]
        missing_configs = ["missing env variable"]
        component_voices = {"comp1": "hf_alpha", "comp2": "af_bella", "comp3": "af_nicole"}
        
        recommendations = self.validator._generate_recommendations(conflicts, missing_configs, component_voices)
        
        self.assertGreater(len(recommendations), 0)
        
        # Check that recommendations address the issues
        rec_text = ' '.join(recommendations)
        self.assertIn("Fix 2 voice configuration conflicts", rec_text)
        self.assertIn("Add 1 missing voice configurations", rec_text)
        self.assertIn("3 different voices", rec_text)  # Should detect multiple voices
    
    @patch.object(VoiceConfigurationValidator, '_validate_config_yaml')
    @patch.object(VoiceConfigurationValidator, '_validate_environment_variables')
    @patch.object(VoiceConfigurationValidator, '_validate_python_code_defaults')
    @patch.object(VoiceConfigurationValidator, '_validate_frontend_configuration')
    def test_validate_voice_consistency_success(self, mock_frontend, mock_python, mock_env, mock_config):
        """Test successful voice consistency validation"""
        # Mock all validation methods to return no conflicts
        mock_config.return_value = "hf_alpha"
        
        # Mock that all methods add no conflicts or missing configs
        def mock_validation_method(component_voices, conflicts, missing_configs):
            component_voices['test_component'] = 'hf_alpha'
        
        mock_frontend.side_effect = mock_validation_method
        mock_python.side_effect = mock_validation_method
        mock_env.side_effect = mock_validation_method
        
        result = self.validator.validate_voice_consistency()
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.voice_conflicts), 0)
        self.assertEqual(len(result.missing_configurations), 0)
        self.assertGreater(len(result.component_voices), 0)
    
    def test_validate_startup_configuration(self):
        """Test startup configuration validation"""
        # Mock the validate_voice_consistency method
        with patch.object(self.validator, 'validate_voice_consistency') as mock_validate:
            # Test successful validation
            mock_validate.return_value = VoiceConfigValidationResult(
                is_valid=True,
                voice_conflicts=[],
                missing_configurations=[],
                recommendations=["All good"],
                component_voices={"test": "hf_alpha"}
            )
            
            result = self.validator.validate_startup_configuration()
            self.assertTrue(result)
            
            # Test failed validation
            mock_validate.return_value = VoiceConfigValidationResult(
                is_valid=False,
                voice_conflicts=["conflict"],
                missing_configurations=["missing"],
                recommendations=["fix issues"],
                component_voices={"test": "wrong_voice"}
            )
            
            result = self.validator.validate_startup_configuration()
            self.assertFalse(result)

class TestStartupValidator(unittest.TestCase):
    """Test cases for StartupValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = StartupValidator()
    
    def test_startup_validator_initialization(self):
        """Test startup validator initializes correctly"""
        self.assertEqual(len(self.validator.validation_results), 0)
    
    @patch('src.utils.voice_config_validator.voice_config_validator.validate_startup_configuration')
    def test_validate_voice_configuration_success(self, mock_voice_validator):
        """Test successful voice configuration validation"""
        mock_voice_validator.return_value = True
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_voice_configuration(critical_errors, warnings)
        
        self.assertTrue(result)
        self.assertEqual(len(critical_errors), 0)
        self.assertEqual(len(warnings), 0)
        self.assertIn('voice_configuration', self.validator.validation_results)
    
    @patch('src.utils.voice_config_validator.voice_config_validator.validate_startup_configuration')
    @patch('src.utils.voice_config_validator.voice_config_validator.validate_voice_consistency')
    def test_validate_voice_configuration_failure(self, mock_consistency, mock_voice_validator):
        """Test voice configuration validation failure"""
        mock_voice_validator.return_value = False
        mock_consistency.return_value = VoiceConfigValidationResult(
            is_valid=False,
            voice_conflicts=["config.yaml conflict", "frontend conflict"],
            missing_configurations=["missing config.yaml setting"],
            recommendations=["fix conflicts"],
            component_voices={"test": "wrong_voice"}
        )
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_voice_configuration(critical_errors, warnings)
        
        self.assertFalse(result)
        self.assertGreater(len(critical_errors), 0)
        
        # Check that config.yaml issues are treated as critical
        critical_error_text = ' '.join(critical_errors)
        self.assertIn("config.yaml", critical_error_text)
    
    @patch('pathlib.Path.exists')
    def test_validate_file_structure_success(self, mock_exists):
        """Test successful file structure validation"""
        # Mock that all required files exist
        mock_exists.return_value = True
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_file_structure(critical_errors, warnings)
        
        self.assertTrue(result)
        self.assertEqual(len(critical_errors), 0)
        self.assertIn('file_structure', self.validator.validation_results)
    
    @patch('pathlib.Path.exists')
    def test_validate_file_structure_missing_files(self, mock_exists):
        """Test file structure validation with missing files"""
        # Mock that some files are missing
        def exists_side_effect(path_obj):
            path_str = str(path_obj)
            if 'config.yaml' in path_str:
                return False  # Required file missing
            elif '.env.example' in path_str:
                return False  # Optional file missing
            return True
        
        mock_exists.side_effect = exists_side_effect
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_file_structure(critical_errors, warnings)
        
        self.assertFalse(result)  # Should fail due to missing required file
        self.assertGreater(len(critical_errors), 0)
        self.assertGreater(len(warnings), 0)
        
        # Check that config.yaml is treated as critical
        critical_error_text = ' '.join(critical_errors)
        self.assertIn("config.yaml", critical_error_text)
    
    @patch('src.utils.config.config')
    def test_validate_configuration_loading_success(self, mock_config):
        """Test successful configuration loading validation"""
        # Mock configuration objects
        mock_tts = MagicMock()
        mock_tts.voice = "hf_alpha"
        mock_tts.default_voice = "hf_alpha"
        
        mock_server = MagicMock()
        mock_server.http_port = 8000
        
        mock_model = MagicMock()
        mock_model.device = "cuda"
        
        mock_config.tts = mock_tts
        mock_config.server = mock_server
        mock_config.model = mock_model
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_configuration_loading(critical_errors, warnings)
        
        self.assertTrue(result)
        self.assertEqual(len(critical_errors), 0)
        self.assertIn('configuration_loading', self.validator.validation_results)
    
    @patch('src.utils.config.config')
    def test_validate_configuration_loading_missing_config(self, mock_config):
        """Test configuration loading validation with missing configuration"""
        # Mock configuration with missing attributes
        mock_tts = MagicMock()
        mock_tts.voice = None  # Missing voice
        mock_tts.default_voice = "hf_alpha"
        
        mock_config.tts = mock_tts
        
        critical_errors = []
        warnings = []
        
        result = self.validator._validate_configuration_loading(critical_errors, warnings)
        
        self.assertFalse(result)
        self.assertGreater(len(critical_errors), 0)
        
        critical_error_text = ' '.join(critical_errors)
        self.assertIn("TTS voice configuration not loaded", critical_error_text)
    
    @patch('src.utils.voice_config_validator.voice_config_validator.validate_startup_configuration')
    @patch('pathlib.Path.exists')
    @patch('src.utils.config.config')
    def test_validate_all_configurations_success(self, mock_config, mock_exists, mock_voice_validator):
        """Test successful validation of all configurations"""
        # Mock successful voice validation
        mock_voice_validator.return_value = True
        
        # Mock all files exist
        mock_exists.return_value = True
        
        # Mock valid configuration
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
        
        result = self.validator.validate_all_configurations(strict_mode=False)
        
        self.assertTrue(result)
        self.assertGreater(len(self.validator.validation_results), 0)
    
    @patch('src.utils.voice_config_validator.voice_config_validator.validate_startup_configuration')
    def test_validate_all_configurations_strict_mode_failure(self, mock_voice_validator):
        """Test validation failure in strict mode raises exception"""
        mock_voice_validator.return_value = False
        
        with self.assertRaises(StartupValidationError):
            self.validator.validate_all_configurations(strict_mode=True)
    
    def test_get_validation_report(self):
        """Test validation report generation"""
        # Add some mock validation results
        self.validator.validation_results = {
            'test1': {'passed': True},
            'test2': {'passed': False},
            'test3': {'passed': True}
        }
        
        report = self.validator.get_validation_report()
        
        self.assertIn('validation_results', report)
        self.assertIn('summary', report)
        self.assertEqual(report['summary']['total_checks'], 3)
        self.assertEqual(report['summary']['passed_checks'], 2)
        self.assertEqual(report['summary']['failed_checks'], 1)

class TestIntegrationVoiceConfiguration(unittest.TestCase):
    """Integration tests for voice configuration validation"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_voice_validation_success(self):
        """Test end-to-end voice validation with correct configuration"""
        # Create test files with correct configuration
        config_content = {
            'tts': {
                'default_voice': 'hf_alpha',
                'voice': 'hf_alpha',
                'engine': 'kokoro'
            }
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(config_content, f)
        
        env_content = """TTS_DEFAULT_VOICE=hf_alpha
KOKORO_VOICE=hf_alpha"""
        
        with open('.env.example', 'w') as f:
            f.write(env_content)
        
        # Create source directory structure
        os.makedirs('src/models', exist_ok=True)
        os.makedirs('src/api', exist_ok=True)
        os.makedirs('src/tts', exist_ok=True)
        
        # Create Python files with correct configuration
        kokoro_content = '''class KokoroTTSModel:
    DEFAULT_VOICE = "hf_alpha"'''
        
        with open('src/models/kokoro_model_realtime.py', 'w') as f:
            f.write(kokoro_content)
        
        pipeline_content = '''DEFAULT_TTS_CONFIG = {
    'voice': 'hf_alpha'
}'''
        
        with open('src/models/speech_to_speech_pipeline.py', 'w') as f:
            f.write(pipeline_content)
        
        tts_service_content = '''class TTSService:
    def __init__(self):
        self.default_voice = "hf_alpha"'''
        
        with open('src/tts/tts_service.py', 'w') as f:
            f.write(tts_service_content)
        
        ui_server_content = '''<option value="hf_alpha" selected>Heart</option>
let selectedVoice = 'hf_alpha';
voice="hf_alpha"'''
        
        with open('src/api/ui_server_realtime.py', 'w') as f:
            f.write(ui_server_content)
        
        # Create config.py file
        config_py_content = '''from pydantic import BaseModel
class TTSConfig(BaseModel):
    voice: str = "hf_alpha"
    default_voice: str = "hf_alpha"
class Config(BaseModel):
    tts: TTSConfig = TTSConfig()
config = Config()'''
        
        os.makedirs('src/utils', exist_ok=True)
        with open('src/utils/config.py', 'w') as f:
            f.write(config_py_content)
        
        # Run validation
        validator = VoiceConfigurationValidator()
        result = validator.validate_voice_consistency()
        
        # Should pass with all correct configurations
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.voice_conflicts), 0)
        self.assertGreater(len(result.component_voices), 0)

if __name__ == '__main__':
    # Set up logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)