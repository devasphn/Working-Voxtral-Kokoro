"""
Startup Configuration Validation
Validates system configuration at startup and provides early error detection
"""
import logging
import sys
from typing import Dict, Any, List
from pathlib import Path

from src.utils.voice_config_validator import voice_config_validator
from src.utils.config import config

# Setup logging
startup_logger = logging.getLogger("startup_validator")

class StartupValidationError(Exception):
    """Raised when critical startup validation fails"""
    pass

class StartupValidator:
    """
    Validates system configuration at startup
    """
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_all_configurations(self, strict_mode: bool = False) -> bool:
        """
        Validate all system configurations at startup
        
        Args:
            strict_mode: If True, fail on any validation errors. If False, only fail on critical errors.
            
        Returns:
            True if validation passes, False otherwise
            
        Raises:
            StartupValidationError: If critical validation fails in strict mode
        """
        startup_logger.info("🔍 Starting comprehensive startup validation...")
        
        validation_passed = True
        critical_errors = []
        warnings = []
        
        try:
            # 1. Validate voice configuration
            voice_validation_passed = self._validate_voice_configuration(critical_errors, warnings)
            validation_passed = validation_passed and voice_validation_passed
            
            # 2. Validate file structure
            file_validation_passed = self._validate_file_structure(critical_errors, warnings)
            validation_passed = validation_passed and file_validation_passed
            
            # 3. Validate configuration loading
            config_validation_passed = self._validate_configuration_loading(critical_errors, warnings)
            validation_passed = validation_passed and config_validation_passed
            
            # 4. Validate model requirements
            model_validation_passed = self._validate_model_requirements(critical_errors, warnings)
            validation_passed = validation_passed and model_validation_passed
            
            # Log results
            self._log_validation_results(validation_passed, critical_errors, warnings)
            
            # Handle strict mode
            if strict_mode and not validation_passed:
                error_msg = f"Startup validation failed with {len(critical_errors)} critical errors"
                startup_logger.error(f"❌ {error_msg}")
                raise StartupValidationError(error_msg)
            
            return validation_passed
            
        except Exception as e:
            startup_logger.error(f"❌ Startup validation error: {e}")
            if strict_mode:
                raise StartupValidationError(f"Startup validation failed: {e}")
            return False
    
    def _validate_voice_configuration(self, critical_errors: List[str], warnings: List[str]) -> bool:
        """Validate voice configuration consistency"""
        try:
            startup_logger.info("🎤 Validating voice configuration...")
            
            # Use the voice configuration validator
            validation_passed = voice_config_validator.validate_startup_configuration()
            
            if not validation_passed:
                # Get detailed results
                result = voice_config_validator.validate_voice_consistency()
                
                # Categorize issues
                for conflict in result.voice_conflicts:
                    if "config.yaml" in conflict or "DEFAULT_VOICE" in conflict:
                        critical_errors.append(f"Voice config: {conflict}")
                    else:
                        warnings.append(f"Voice config: {conflict}")
                
                for missing in result.missing_configurations:
                    if "config.yaml" in missing or "DEFAULT_VOICE" in missing:
                        critical_errors.append(f"Voice config missing: {missing}")
                    else:
                        warnings.append(f"Voice config missing: {missing}")
            
            self.validation_results['voice_configuration'] = {
                'passed': validation_passed,
                'validator_result': voice_config_validator.validate_voice_consistency()
            }
            
            return validation_passed
            
        except Exception as e:
            critical_errors.append(f"Voice configuration validation failed: {e}")
            return False
    
    def _validate_file_structure(self, critical_errors: List[str], warnings: List[str]) -> bool:
        """Validate required file structure"""
        try:
            startup_logger.info("📁 Validating file structure...")
            
            required_files = [
                "config.yaml",
                "src/utils/config.py",
                "src/api/ui_server_realtime.py"
            ]

            optional_files = [
                ".env.example"
            ]
            
            missing_required = []
            missing_optional = []
            
            for file_path in required_files:
                if not Path(file_path).exists():
                    missing_required.append(file_path)
            
            for file_path in optional_files:
                if not Path(file_path).exists():
                    missing_optional.append(file_path)
            
            # Add to errors/warnings
            for missing in missing_required:
                critical_errors.append(f"Required file missing: {missing}")
            
            for missing in missing_optional:
                warnings.append(f"Optional file missing: {missing}")
            
            validation_passed = len(missing_required) == 0
            
            self.validation_results['file_structure'] = {
                'passed': validation_passed,
                'missing_required': missing_required,
                'missing_optional': missing_optional
            }
            
            return validation_passed
            
        except Exception as e:
            critical_errors.append(f"File structure validation failed: {e}")
            return False
    
    def _validate_configuration_loading(self, critical_errors: List[str], warnings: List[str]) -> bool:
        """Validate configuration can be loaded properly"""
        try:
            startup_logger.info("⚙️ Validating configuration loading...")
            
            # Test configuration loading
            try:
                tts_config = config.tts
                voice = getattr(tts_config, 'voice', None)
                default_voice = getattr(tts_config, 'default_voice', None)
                
                if not voice:
                    critical_errors.append("TTS voice configuration not loaded")
                
                if not default_voice:
                    critical_errors.append("TTS default_voice configuration not loaded")
                
                if voice and voice not in ["hf_alpha", "af_bella", "af_nicole", "af_sarah", "hf_beta", "hm_psi"]:
                    warnings.append(f"Unusual TTS voice configured: {voice}")
                
            except Exception as e:
                critical_errors.append(f"Failed to load TTS configuration: {e}")
            
            # Test other critical configurations
            try:
                server_config = config.server
                model_config = config.model
                
                if not hasattr(server_config, 'http_port'):
                    critical_errors.append("Server HTTP port not configured")
                
                if not hasattr(model_config, 'device'):
                    critical_errors.append("Model device not configured")
                    
            except Exception as e:
                critical_errors.append(f"Failed to load server/model configuration: {e}")
            
            validation_passed = len([e for e in critical_errors if "configuration" in e.lower()]) == 0
            
            self.validation_results['configuration_loading'] = {
                'passed': validation_passed,
                'tts_voice': getattr(config.tts, 'voice', None),
                'tts_default_voice': getattr(config.tts, 'default_voice', None)
            }
            
            return validation_passed
            
        except Exception as e:
            critical_errors.append(f"Configuration loading validation failed: {e}")
            return False
    
    def _validate_model_requirements(self, critical_errors: List[str], warnings: List[str]) -> bool:
        """Validate model requirements and dependencies"""
        try:
            startup_logger.info("🤖 Validating model requirements...")
            
            # Check if required directories exist
            model_cache_dir = Path(getattr(config.model, 'cache_dir', './model_cache'))
            if not model_cache_dir.exists():
                warnings.append(f"Model cache directory does not exist: {model_cache_dir}")
            
            # Check device configuration
            device = getattr(config.model, 'device', 'cpu')
            if device == 'cuda':
                try:
                    import torch
                    if not torch.cuda.is_available():
                        warnings.append("CUDA device configured but not available")
                except ImportError:
                    critical_errors.append("PyTorch not available but required for model operations")
            
            # Voxtral is ASR only - no TTS engine needed
            
            validation_passed = len([e for e in critical_errors if "model" in e.lower() or "torch" in e.lower()]) == 0
            
            self.validation_results['model_requirements'] = {
                'passed': validation_passed,
                'device': device,
                'tts_engine': tts_engine,
                'model_cache_dir': str(model_cache_dir)
            }
            
            return validation_passed
            
        except Exception as e:
            critical_errors.append(f"Model requirements validation failed: {e}")
            return False
    
    def _log_validation_results(self, validation_passed: bool, critical_errors: List[str], warnings: List[str]):
        """Log comprehensive validation results"""
        if validation_passed:
            startup_logger.info("✅ All startup validations passed successfully")
        else:
            startup_logger.error(f"❌ Startup validation failed with {len(critical_errors)} critical errors")
        
        if critical_errors:
            startup_logger.error("🚨 Critical Errors:")
            for error in critical_errors:
                startup_logger.error(f"   - {error}")
        
        if warnings:
            startup_logger.warning(f"⚠️ Warnings ({len(warnings)}):")
            for warning in warnings:
                startup_logger.warning(f"   - {warning}")
        
        # Log summary statistics
        total_validations = len(self.validation_results)
        passed_validations = sum(1 for result in self.validation_results.values() if result['passed'])
        
        startup_logger.info(f"📊 Validation Summary: {passed_validations}/{total_validations} checks passed")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report"""
        return {
            "validation_results": self.validation_results,
            "summary": {
                "total_checks": len(self.validation_results),
                "passed_checks": sum(1 for result in self.validation_results.values() if result['passed']),
                "failed_checks": sum(1 for result in self.validation_results.values() if not result['passed'])
            }
        }
    
    def validate_voice_configuration_only(self) -> bool:
        """
        Validate only voice configuration (for focused testing)
        
        Returns:
            True if voice configuration is valid, False otherwise
        """
        startup_logger.info("🎤 Validating voice configuration only...")
        
        try:
            return voice_config_validator.validate_startup_configuration()
        except Exception as e:
            startup_logger.error(f"❌ Voice configuration validation failed: {e}")
            return False

# Global startup validator instance
startup_validator = StartupValidator()

def validate_startup_configuration(strict_mode: bool = False) -> bool:
    """
    Convenience function to validate startup configuration
    
    Args:
        strict_mode: If True, raise exception on validation failure
        
    Returns:
        True if validation passes, False otherwise
    """
    return startup_validator.validate_all_configurations(strict_mode=strict_mode)