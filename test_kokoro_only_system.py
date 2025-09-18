#!/usr/bin/env python3
"""
Comprehensive Test Suite for Kokoro-Only TTS System
Tests the complete removal of Orpheus dependencies and validates Kokoro TTS functionality
"""

import asyncio
import sys
import time
import traceback
import logging
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step: int, description: str):
    """Print a test step"""
    print(f"\n[STEP {step}] {description}")
    print("-" * 50)

def print_success(message: str):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print an error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")

async def test_orpheus_removal():
    """Test that all Orpheus dependencies have been removed"""
    print_step(1, "Orpheus Dependency Removal Test")
    
    # Test that Orpheus modules cannot be imported
    orpheus_modules = [
        "src.tts.orpheus_streaming_model",
        "src.tts.orpheus_perfect_model", 
        "src.tts.tts_service_perfect"
    ]
    
    for module in orpheus_modules:
        try:
            __import__(module)
            print_error(f"Orpheus module still exists: {module}")
            return False
        except ImportError:
            print_success(f"Orpheus module properly removed: {module}")
    
    # Test that orpheus_tts package is not available
    try:
        import orpheus_tts
        print_error("orpheus_tts package is still available")
        return False
    except ImportError:
        print_success("orpheus_tts package properly removed")
    
    return True

async def test_kokoro_imports():
    """Test that Kokoro TTS components can be imported"""
    print_step(2, "Kokoro TTS Import Test")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        print_success("KokoroTTSModel imported successfully")
        
        from src.tts.tts_service import TTSService, map_voice_to_kokoro
        print_success("TTSService and voice mapping imported successfully")
        
        from src.models.unified_model_manager import UnifiedModelManager
        print_success("UnifiedModelManager imported successfully")
        
        return True
        
    except ImportError as e:
        print_error(f"Failed to import Kokoro components: {e}")
        traceback.print_exc()
        return False

async def test_voice_mapping():
    """Test voice mapping from Orpheus voices to Kokoro voices"""
    print_step(3, "Voice Mapping Test")
    
    try:
        from src.tts.tts_service import map_voice_to_kokoro
        
        # Test Hindi voice mapping
        test_cases = [
            ("ऋतिका", "hm_omega"),
            ("ritika", "hm_omega"),
            ("hindi", "hm_omega"),
            ("हिंदी", "hm_omega"),
            ("unknown_voice", "af_heart")  # Default fallback
        ]
        
        for input_voice, expected_output in test_cases:
            result = map_voice_to_kokoro(input_voice)
            if result == expected_output:
                print_success(f"Voice mapping: '{input_voice}' → '{result}'")
            else:
                print_error(f"Voice mapping failed: '{input_voice}' → '{result}' (expected '{expected_output}')")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Voice mapping test failed: {e}")
        traceback.print_exc()
        return False

async def test_kokoro_initialization():
    """Test Kokoro TTS model initialization"""
    print_step(4, "Kokoro TTS Initialization Test")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        print_info("Initializing Kokoro TTS model...")
        kokoro_model = KokoroTTSModel()
        
        start_time = time.time()
        success = await kokoro_model.initialize()
        init_time = time.time() - start_time
        
        if success:
            print_success(f"Kokoro TTS initialized successfully in {init_time:.2f}s")
            
            # Test model info
            model_info = kokoro_model.get_model_info()
            print_success(f"Model info retrieved: {model_info.get('model_name', 'Kokoro TTS')}")
            
            # Cleanup
            await kokoro_model.cleanup()
            print_success("Kokoro TTS cleanup completed")
            
            return True
        else:
            print_error("Kokoro TTS initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Kokoro TTS initialization test failed: {e}")
        traceback.print_exc()
        return False

async def test_unified_manager():
    """Test unified model manager with Kokoro-only configuration"""
    print_step(5, "Unified Model Manager Test")
    
    try:
        from src.models.unified_model_manager import UnifiedModelManager
        
        print_info("Initializing unified model manager...")
        manager = UnifiedModelManager()
        
        start_time = time.time()
        success = await manager.initialize()
        init_time = time.time() - start_time
        
        if success:
            print_success(f"Unified model manager initialized in {init_time:.2f}s")
            
            # Test model info
            model_info = manager.get_model_info()
            unified_info = model_info.get("unified_manager", {})
            
            print_success(f"Voxtral initialized: {unified_info.get('voxtral_initialized', False)}")
            print_success(f"Kokoro initialized: {unified_info.get('kokoro_initialized', False)}")
            
            # Verify no Orpheus references
            if "orpheus_initialized" in unified_info:
                print_error("Orpheus references still exist in unified manager")
                return False
            else:
                print_success("No Orpheus references found in unified manager")
            
            # Test getting Kokoro model
            try:
                kokoro_model = await manager.get_kokoro_model()
                print_success("Kokoro model retrieved from unified manager")
            except Exception as e:
                print_error(f"Failed to get Kokoro model: {e}")
                return False
            
            # Cleanup
            await manager.shutdown()
            print_success("Unified model manager shutdown completed")
            
            return True
        else:
            print_error("Unified model manager initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Unified model manager test failed: {e}")
        traceback.print_exc()
        return False

async def test_tts_service():
    """Test TTS service with Kokoro-only configuration"""
    print_step(6, "TTS Service Test")
    
    try:
        from src.tts.tts_service import TTSService
        
        print_info("Initializing TTS service...")
        tts_service = TTSService()
        
        # Check default voice is Kokoro voice
        if tts_service.default_voice == "hm_omega":
            print_success(f"Default voice correctly set to Kokoro: {tts_service.default_voice}")
        else:
            print_error(f"Default voice not set to Kokoro: {tts_service.default_voice}")
            return False
        
        # Test available voices
        available_voices = tts_service.get_available_voices()
        kokoro_voices = ["af_heart", "af_bella", "af_nicole", "af_sarah", "hm_omega", "hf_alpha", "hf_beta", "hm_psi"]
        
        if all(voice in kokoro_voices for voice in available_voices):
            print_success(f"Available voices are all Kokoro voices: {available_voices}")
        else:
            print_error(f"Non-Kokoro voices found: {available_voices}")
            return False
        
        # Test service info
        service_info = tts_service.get_service_info()
        if service_info.get("engine") == "Kokoro TTS":
            print_success("TTS service engine correctly set to Kokoro TTS")
        else:
            print_error(f"TTS service engine not set correctly: {service_info.get('engine')}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"TTS service test failed: {e}")
        traceback.print_exc()
        return False

async def test_configuration():
    """Test configuration files for Kokoro-only setup"""
    print_step(7, "Configuration Test")
    
    try:
        from src.utils.config import config
        
        # Test TTS engine configuration
        if config.tts.engine == "kokoro":
            print_success(f"TTS engine correctly set to: {config.tts.engine}")
        else:
            print_error(f"TTS engine not set to kokoro: {config.tts.engine}")
            return False
        
        # Test default voice
        if config.tts.default_voice == "hm_omega":
            print_success(f"Default voice correctly set to: {config.tts.default_voice}")
        else:
            print_error(f"Default voice not set to hm_omega: {config.tts.default_voice}")
            return False
        
        # Test language code
        if config.tts.lang_code == "h":
            print_success(f"Language code correctly set to Hindi: {config.tts.lang_code}")
        else:
            print_error(f"Language code not set to Hindi: {config.tts.lang_code}")
            return False
        
        # Test that Orpheus config is removed
        if hasattr(config.tts, 'orpheus_direct'):
            print_error("Orpheus configuration still exists")
            return False
        else:
            print_success("Orpheus configuration properly removed")
        
        return True
        
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print_header("Kokoro-Only TTS System Validation")
    print_info("Testing complete removal of Orpheus dependencies and Kokoro TTS functionality")
    
    tests = [
        ("Orpheus Removal", test_orpheus_removal),
        ("Kokoro Imports", test_kokoro_imports),
        ("Voice Mapping", test_voice_mapping),
        ("Kokoro Initialization", test_kokoro_initialization),
        ("Unified Manager", test_unified_manager),
        ("TTS Service", test_tts_service),
        ("Configuration", test_configuration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print_success(f"{test_name} test PASSED")
            else:
                failed += 1
                print_error(f"{test_name} test FAILED")
        except Exception as e:
            failed += 1
            print_error(f"{test_name} test FAILED with exception: {e}")
            traceback.print_exc()
    
    print_header("Test Results Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL TESTS PASSED! Kokoro-only system is working correctly!")
        return True
    else:
        print_error(f"💥 {failed} test(s) failed. Please review and fix the issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
