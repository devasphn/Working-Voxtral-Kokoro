#!/usr/bin/env python3
"""
Voxtral + TTS Setup Validation Script
Validates that all components are properly installed and configured
"""

import sys
import importlib
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SetupValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def check_python_version(self):
        """Check Python version compatibility"""
        logger.info("🐍 Checking Python version...")
        
        version = sys.version_info
        if version.major == 3 and 8 <= version.minor <= 11:
            logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
            return True
        else:
            error_msg = f"❌ Python {version.major}.{version.minor}.{version.micro} is not supported. Use Python 3.8-3.11"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def check_required_packages(self):
        """Check if required packages are installed"""
        logger.info("📦 Checking required packages...")
        
        required_packages = [
            'torch',
            'transformers',
            'librosa',
            'numpy',
            'scipy',
            'fastapi',
            'uvicorn',
            'websockets',
            'pydantic',
            'pydantic_settings',
            'soundfile',
            'torchaudio',
            'pyyaml',
            'requests',
            'snac'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                logger.info(f"✅ {package}")
            except ImportError:
                logger.error(f"❌ {package} - NOT INSTALLED")
                missing_packages.append(package)
        
        if missing_packages:
            error_msg = f"Missing packages: {', '.join(missing_packages)}"
            self.errors.append(error_msg)
            return False
        
        logger.info("✅ All required packages are installed")
        return True
    
    def check_cuda_availability(self):
        """Check CUDA availability"""
        logger.info("🚀 Checking CUDA availability...")
        
        try:
            import torch
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                current_device = torch.cuda.current_device()
                device_name = torch.cuda.get_device_name(current_device)
                
                logger.info(f"✅ CUDA available with {device_count} device(s)")
                logger.info(f"✅ Current device: {device_name}")
                
                # Check VRAM
                memory_allocated = torch.cuda.memory_allocated(current_device) / 1024**3
                memory_reserved = torch.cuda.memory_reserved(current_device) / 1024**3
                memory_total = torch.cuda.get_device_properties(current_device).total_memory / 1024**3
                
                logger.info(f"📊 GPU Memory: {memory_total:.1f}GB total, {memory_reserved:.1f}GB reserved")
                
                if memory_total < 8:
                    warning_msg = f"⚠️ GPU has only {memory_total:.1f}GB VRAM. 8GB+ recommended"
                    logger.warning(warning_msg)
                    self.warnings.append(warning_msg)
                
                return True
            else:
                error_msg = "❌ CUDA not available. GPU acceleration disabled"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ Error checking CUDA: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def check_file_structure(self):
        """Check if all required files are present"""
        logger.info("📁 Checking file structure...")
        
        required_files = [
            'config.yaml',
            'requirements.txt',
            'src/api/ui_server_realtime.py',
            'src/api/health_check.py',
            'src/streaming/tcp_server.py',
            'src/models/voxtral_model_realtime.py',
            'src/tts/__init__.py',
            'src/tts/orpheus_tts_engine.py',
            'src/tts/tts_service.py',
            'src/utils/config.py',
            'deploy_voxtral_tts.sh',
            'README_DEPLOYMENT.md'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            if Path(file_path).exists():
                logger.info(f"✅ {file_path}")
            else:
                logger.error(f"❌ {file_path} - MISSING")
                missing_files.append(file_path)
        
        if missing_files:
            error_msg = f"Missing files: {', '.join(missing_files)}"
            self.errors.append(error_msg)
            return False
        
        logger.info("✅ All required files are present")
        return True
    
    def check_configuration(self):
        """Check configuration validity"""
        logger.info("⚙️ Checking configuration...")
        
        try:
            from src.utils.config import load_config
            config = load_config()
            
            # Check TTS configuration
            if hasattr(config, 'tts'):
                logger.info("✅ TTS configuration found")
                logger.info(f"   • Engine: {config.tts.engine}")
                logger.info(f"   • Default voice: {config.tts.default_voice}")
                logger.info(f"   • Sample rate: {config.tts.sample_rate}")
                logger.info(f"   • Enabled: {config.tts.enabled}")
            else:
                error_msg = "❌ TTS configuration missing"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
            
            # Check model configuration
            if hasattr(config, 'model'):
                logger.info("✅ Model configuration found")
                logger.info(f"   • Model: {config.model.name}")
                logger.info(f"   • Device: {config.model.device}")
            else:
                error_msg = "❌ Model configuration missing"
                logger.error(error_msg)
                self.errors.append(error_msg)
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Configuration error: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def check_model_accessibility(self):
        """Check if models can be loaded"""
        logger.info("🤖 Checking model accessibility...")
        
        try:
            # Test Voxtral model loading
            logger.info("📥 Testing Voxtral model access...")
            from transformers import VoxtralForConditionalGeneration, AutoProcessor
            
            model_name = "mistralai/Voxtral-Mini-3B-2507"
            
            # Just check if we can create the processor (lightweight test)
            processor = AutoProcessor.from_pretrained(model_name, cache_dir="/workspace/model_cache")
            logger.info("✅ Voxtral model accessible")
            
            # Test SNAC model loading
            logger.info("📥 Testing SNAC model access...")
            from snac import SNAC
            snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
            logger.info("✅ SNAC model accessible")
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Model accessibility error: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def check_tts_integration(self):
        """Check TTS integration"""
        logger.info("🔊 Checking TTS integration...")
        
        try:
            from src.tts.tts_service import TTSService
            from src.tts.orpheus_tts_engine import OrpheusTTSEngine
            
            logger.info("✅ TTS modules importable")
            
            # Test TTS service initialization
            tts_service = TTSService()
            logger.info("✅ TTS service can be initialized")
            
            return True
            
        except Exception as e:
            error_msg = f"❌ TTS integration error: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def run_validation(self):
        """Run complete validation"""
        logger.info("🚀 Starting Voxtral + TTS Setup Validation")
        logger.info("=" * 60)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Required Packages", self.check_required_packages),
            ("CUDA Availability", self.check_cuda_availability),
            ("File Structure", self.check_file_structure),
            ("Configuration", self.check_configuration),
            ("Model Accessibility", self.check_model_accessibility),
            ("TTS Integration", self.check_tts_integration)
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_func in checks:
            logger.info(f"\n🔍 {check_name}...")
            try:
                if check_func():
                    passed_checks += 1
            except Exception as e:
                error_msg = f"❌ {check_name} failed with exception: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Checks passed: {passed_checks}/{total_checks}")
        
        if self.warnings:
            logger.info(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")
        
        if self.errors:
            logger.info(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        if passed_checks == total_checks and not self.errors:
            logger.info("\n🎉 VALIDATION PASSED! System is ready for deployment.")
            return True
        else:
            logger.error(f"\n❌ VALIDATION FAILED! Please fix the errors above.")
            return False

def main():
    """Main validation function"""
    validator = SetupValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
