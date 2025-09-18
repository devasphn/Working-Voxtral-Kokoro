#!/usr/bin/env python3
"""
Comprehensive Fix Script for Kokoro TTS Issues
Addresses memory statistics errors and model download issues
"""

import asyncio
import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("kokoro_fixes")

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

async def fix_memory_statistics():
    """Fix memory statistics issues"""
    print_step(1, "Fixing Memory Statistics Issues")
    
    try:
        # Test memory statistics
        from src.utils.gpu_memory_manager import GPUMemoryManager
        
        print_info("Testing GPU Memory Manager...")
        gpu_manager = GPUMemoryManager()
        
        # Test memory stats
        stats = gpu_manager.get_memory_stats()
        print_success(f"Memory stats retrieved successfully")
        print_info(f"   Total VRAM: {stats.total_vram_gb:.2f} GB")
        print_info(f"   Used VRAM: {stats.used_vram_gb:.2f} GB")
        print_info(f"   Voxtral Memory: {stats.voxtral_memory_gb:.2f} GB")
        print_info(f"   Kokoro Memory: {stats.kokoro_memory_gb:.2f} GB")
        print_info(f"   Available VRAM: {stats.available_vram_gb:.2f} GB")
        
        # Test memory tracking
        gpu_manager.track_model_memory("kokoro", 1.5)
        updated_stats = gpu_manager.get_memory_stats()
        
        if updated_stats.kokoro_memory_gb == 1.5:
            print_success("Kokoro memory tracking working correctly")
        else:
            print_error(f"Kokoro memory tracking failed: {updated_stats.kokoro_memory_gb}")
            return False
        
        # Test memory monitoring
        monitoring_data = gpu_manager.monitor_memory_usage()
        if monitoring_data.get("status") != "error":
            print_success("Memory monitoring working correctly")
        else:
            print_error(f"Memory monitoring failed: {monitoring_data.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Memory statistics fix failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def fix_model_download():
    """Fix model download issues"""
    print_step(2, "Fixing Model Download Issues")
    
    try:
        from src.utils.kokoro_model_manager import kokoro_model_manager
        
        print_info("Checking model status...")
        status = kokoro_model_manager.get_model_status()
        
        print_info(f"Model availability: {status['availability_percentage']:.1f}%")
        print_info(f"Model integrity: {status['integrity_percentage']:.1f}%")
        
        if status['integrity_percentage'] < 100:
            print_info("Downloading missing or corrupted model files...")
            download_success = kokoro_model_manager.download_model_files()
            
            if download_success:
                print_success("Model files downloaded successfully")
                
                # Verify download
                updated_status = kokoro_model_manager.get_model_status()
                if updated_status['integrity_percentage'] == 100:
                    print_success("All model files verified after download")
                else:
                    print_error(f"Model verification failed after download: {updated_status['integrity_percentage']:.1f}%")
                    return False
            else:
                print_error("Model download failed")
                return False
        else:
            print_success("All model files already available and verified")
        
        return True
        
    except Exception as e:
        print_error(f"Model download fix failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_unified_model_manager():
    """Test unified model manager with fixes"""
    print_step(3, "Testing Unified Model Manager")
    
    try:
        from src.models.unified_model_manager import UnifiedModelManager
        
        print_info("Initializing unified model manager...")
        manager = UnifiedModelManager()
        
        start_time = time.time()
        success = await manager.initialize()
        init_time = time.time() - start_time
        
        if success:
            print_success(f"Unified model manager initialized in {init_time:.2f}s")
            
            # Test memory statistics logging
            try:
                await manager._log_memory_statistics()
                print_success("Memory statistics logging working correctly")
            except Exception as e:
                print_error(f"Memory statistics logging failed: {e}")
                return False
            
            # Test model info
            model_info = manager.get_model_info()
            unified_info = model_info.get("unified_manager", {})
            
            print_info(f"Voxtral initialized: {unified_info.get('voxtral_initialized', False)}")
            print_info(f"Kokoro initialized: {unified_info.get('kokoro_initialized', False)}")
            
            # Verify no Orpheus references
            if "orpheus_initialized" in unified_info:
                print_error("Orpheus references still exist in unified manager")
                return False
            else:
                print_success("No Orpheus references found")
            
            # Cleanup
            await manager.shutdown()
            print_success("Unified model manager shutdown completed")
            
            return True
        else:
            print_error("Unified model manager initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Unified model manager test failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_kokoro_model():
    """Test Kokoro TTS model functionality"""
    print_step(4, "Testing Kokoro TTS Model")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        print_info("Creating Kokoro TTS model...")
        model = KokoroTTSModel()
        
        print_info("Initializing model...")
        start_time = time.time()
        success = await model.initialize()
        init_time = time.time() - start_time
        
        if success:
            print_success(f"Kokoro TTS model initialized in {init_time:.2f}s")
            
            # Test synthesis
            print_info("Testing speech synthesis...")
            result = await model.synthesize_speech("Hello, this is a test.", "af_heart")
            
            if result.get("success", False):
                print_success("Speech synthesis successful")
            else:
                print_error(f"Speech synthesis failed: {result.get('error')}")
                return False
            
            # Cleanup
            await model.cleanup()
            print_success("Model cleanup completed")
            
            return True
        else:
            print_error("Kokoro TTS model initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Kokoro TTS model test failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_tts_service():
    """Test TTS service functionality"""
    print_step(5, "Testing TTS Service")
    
    try:
        from src.tts.tts_service import TTSService, map_voice_to_kokoro
        
        # Test voice mapping
        print_info("Testing voice mapping...")
        test_cases = [
            ("ऋतिका", "hm_omega"),
            ("ritika", "hm_omega"),
            ("af_heart", "af_heart")
        ]
        
        for input_voice, expected in test_cases:
            result = map_voice_to_kokoro(input_voice)
            if result == expected:
                print_success(f"Voice mapping: '{input_voice}' → '{result}'")
            else:
                print_error(f"Voice mapping failed: '{input_voice}' → '{result}' (expected '{expected}')")
                return False
        
        # Test TTS service
        print_info("Testing TTS service...")
        tts_service = TTSService()
        
        service_info = tts_service.get_service_info()
        if service_info.get("engine") == "Kokoro TTS":
            print_success("TTS service configured correctly")
        else:
            print_error(f"TTS service misconfigured: {service_info.get('engine')}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"TTS service test failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main fix function"""
    print_header("Kokoro TTS Issues Fix Script")
    print_info("Fixing memory statistics errors and model download issues")
    
    fixes = [
        ("Memory Statistics", fix_memory_statistics),
        ("Model Download", fix_model_download),
        ("Unified Model Manager", test_unified_model_manager),
        ("Kokoro TTS Model", test_kokoro_model),
        ("TTS Service", test_tts_service)
    ]
    
    passed = 0
    failed = 0
    
    for fix_name, fix_func in fixes:
        try:
            result = await fix_func()
            if result:
                passed += 1
                print_success(f"{fix_name} fix PASSED")
            else:
                failed += 1
                print_error(f"{fix_name} fix FAILED")
        except Exception as e:
            failed += 1
            print_error(f"{fix_name} fix FAILED with exception: {e}")
    
    print_header("Fix Results Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL FIXES SUCCESSFUL! Kokoro TTS system is working correctly!")
        print_info("\n🚀 You can now start your system with:")
        print_info("   python -m src.api.ui_server_realtime")
        return True
    else:
        print_error(f"💥 {failed} fix(es) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
