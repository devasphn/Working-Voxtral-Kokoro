#!/usr/bin/env python3
"""
Simple Kokoro TTS Fix Script
Focuses on core issues: memory statistics and basic functionality
"""

import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_kokoro_fix")

def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")

async def test_memory_statistics():
    """Test that memory statistics work correctly"""
    print_header("Testing Memory Statistics")
    
    try:
        from src.utils.gpu_memory_manager import GPUMemoryManager
        
        print_info("Creating GPU Memory Manager...")
        gpu_manager = GPUMemoryManager()
        
        print_info("Testing memory stats retrieval...")
        stats = gpu_manager.get_memory_stats()
        
        # Check that kokoro_memory_gb attribute exists
        if hasattr(stats, 'kokoro_memory_gb'):
            print_success(f"kokoro_memory_gb attribute exists: {stats.kokoro_memory_gb:.2f} GB")
        else:
            print_error("kokoro_memory_gb attribute missing!")
            return False
        
        # Test memory tracking
        print_info("Testing Kokoro memory tracking...")
        gpu_manager.track_model_memory("kokoro", 1.5)
        updated_stats = gpu_manager.get_memory_stats()
        
        if updated_stats.kokoro_memory_gb == 1.5:
            print_success("Kokoro memory tracking works correctly")
        else:
            print_error(f"Memory tracking failed: expected 1.5, got {updated_stats.kokoro_memory_gb}")
            return False
        
        # Test memory monitoring
        print_info("Testing memory monitoring...")
        monitoring_data = gpu_manager.monitor_memory_usage()
        
        if monitoring_data.get("status") != "error":
            print_success("Memory monitoring works correctly")
        else:
            print_error(f"Memory monitoring failed: {monitoring_data.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Memory statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_kokoro_imports():
    """Test that Kokoro components can be imported"""
    print_header("Testing Kokoro Imports")
    
    try:
        print_info("Testing TTS service import...")
        from src.tts.tts_service import TTSService
        print_success("TTSService imported successfully")
        
        print_info("Testing voice mapping import...")
        from src.tts.tts_service import map_voice_to_kokoro
        print_success("Voice mapping function imported successfully")
        
        print_info("Testing Kokoro model import...")
        from src.models.kokoro_model_realtime import KokoroTTSModel
        print_success("KokoroTTSModel imported successfully")
        
        return True
        
    except Exception as e:
        print_error(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voice_mapping():
    """Test voice mapping functionality"""
    print_header("Testing Voice Mapping")
    
    try:
        from src.tts.tts_service import map_voice_to_kokoro
        
        test_cases = [
            ("ऋतिका", "hm_omega"),
            ("ritika", "hm_omega"),
            ("hindi", "hm_omega"),
            ("af_heart", "af_heart"),
            ("unknown_voice", "af_heart")
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
        import traceback
        traceback.print_exc()
        return False

async def test_basic_kokoro_setup():
    """Test basic Kokoro TTS setup without full initialization"""
    print_header("Testing Basic Kokoro Setup")
    
    try:
        print_info("Testing Kokoro model creation...")
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        model = KokoroTTSModel()
        print_success("Kokoro model created successfully")
        
        print_info("Testing model info...")
        model_info = model.get_model_info()
        print_success(f"Model info retrieved: {model_info.get('model_name', 'Kokoro TTS')}")
        
        return True
        
    except Exception as e:
        print_error(f"Basic Kokoro setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tts_service_basic():
    """Test basic TTS service functionality"""
    print_header("Testing TTS Service Basic")
    
    try:
        from src.tts.tts_service import TTSService
        
        print_info("Creating TTS service...")
        tts_service = TTSService()
        print_success("TTS service created successfully")
        
        print_info("Testing service info...")
        service_info = tts_service.get_service_info()
        print_success(f"Service info: {service_info.get('engine', 'Unknown')}")
        
        print_info("Testing available voices...")
        voices = tts_service.get_available_voices()
        print_success(f"Available voices: {voices}")
        
        return True
        
    except Exception as e:
        print_error(f"TTS service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run simple fix tests"""
    print_header("Simple Kokoro TTS Fix Script")
    print_info("Testing core functionality without full model initialization")
    
    tests = [
        ("Memory Statistics", test_memory_statistics),
        ("Kokoro Imports", test_kokoro_imports),
        ("Voice Mapping", test_voice_mapping),
        ("Basic Kokoro Setup", test_basic_kokoro_setup),
        ("TTS Service Basic", test_tts_service_basic)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔧 Running {test_name} test...")
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
    
    print_header("Simple Fix Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL CORE FIXES SUCCESSFUL!")
        print_info("\n📋 Next Steps:")
        print_info("1. Install missing dependencies: pip install kokoro>=0.7.4")
        print_info("2. Install mistral-common: pip install mistral-common[audio]>=1.8.1")
        print_info("3. Install pydantic-settings: pip install pydantic-settings>=2.1.0")
        print_info("4. Run the full system: python -m src.api.ui_server_realtime")
        return True
    else:
        print_error(f"💥 {failed} core fix(es) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
