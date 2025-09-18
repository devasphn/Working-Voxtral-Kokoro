#!/usr/bin/env python3
"""
Kokoro TTS Model Verification Script
Standalone script to check, download, and verify Kokoro TTS model files
"""

import asyncio
import argparse
import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("kokoro_verification")

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

def print_warning(message: str):
    """Print a warning message"""
    print(f"⚠️  {message}")

async def check_kokoro_installation():
    """Check if Kokoro TTS is properly installed"""
    print_step(1, "Checking Kokoro TTS Installation")
    
    try:
        import kokoro
        print_success(f"Kokoro TTS package found: version {getattr(kokoro, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print_error(f"Kokoro TTS package not found: {e}")
        print_info("Install with: pip install kokoro>=0.7.4")
        return False

async def check_model_files():
    """Check if model files are available"""
    print_step(2, "Checking Model Files")
    
    try:
        from src.utils.kokoro_model_manager import kokoro_model_manager
        
        status = kokoro_model_manager.get_model_status()
        
        print_info(f"Cache directory: {status['cache_directory']}")
        print_info(f"Repository: {status['repository']}")
        print_info(f"Total files: {status['total_files']}")
        print_info(f"Available files: {status['available_files']}")
        print_info(f"Valid files: {status['valid_files']}")
        print_info(f"Availability: {status['availability_percentage']:.1f}%")
        print_info(f"Integrity: {status['integrity_percentage']:.1f}%")
        
        # Show detailed file status
        print("\n📋 File Details:")
        for file_key, details in status['file_details'].items():
            status_icon = "✅" if details['valid'] else ("📁" if details['available'] else "❌")
            print(f"   {status_icon} {file_key}")
        
        if status['integrity_percentage'] == 100:
            print_success("All model files are available and verified")
            return True
        else:
            print_warning(f"Model files incomplete: {status['integrity_percentage']:.1f}% valid")
            return False
            
    except Exception as e:
        print_error(f"Error checking model files: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def download_model_files(force_download: bool = False):
    """Download model files if needed"""
    print_step(3, "Downloading Model Files" if not force_download else "Force Downloading Model Files")
    
    try:
        from src.utils.kokoro_model_manager import kokoro_model_manager
        
        start_time = time.time()
        success = kokoro_model_manager.download_model_files(force_download=force_download)
        download_time = time.time() - start_time
        
        if success:
            print_success(f"Model files downloaded successfully in {download_time:.2f}s")
            return True
        else:
            print_error("Model file download failed")
            return False
            
    except Exception as e:
        print_error(f"Error downloading model files: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_kokoro_initialization():
    """Test Kokoro TTS model initialization"""
    print_step(4, "Testing Kokoro TTS Initialization")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        print_info("Creating Kokoro TTS model instance...")
        model = KokoroTTSModel()
        
        print_info("Initializing model...")
        start_time = time.time()
        success = await model.initialize()
        init_time = time.time() - start_time
        
        if success:
            print_success(f"Kokoro TTS model initialized successfully in {init_time:.2f}s")
            
            # Test model info
            model_info = model.get_model_info()
            print_info(f"Model info: {model_info}")
            
            # Cleanup
            await model.cleanup()
            print_success("Model cleanup completed")
            
            return True
        else:
            print_error("Kokoro TTS model initialization failed")
            return False
            
    except Exception as e:
        print_error(f"Error testing Kokoro initialization: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_speech_synthesis():
    """Test speech synthesis functionality"""
    print_step(5, "Testing Speech Synthesis")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        model = KokoroTTSModel()
        
        if not await model.initialize():
            print_error("Failed to initialize model for synthesis test")
            return False
        
        # Test English synthesis
        print_info("Testing English synthesis...")
        result = await model.synthesize_speech("Hello, this is a test of Kokoro TTS.", "af_heart")
        
        if result.get("success", False):
            audio_data = result.get("audio_data")
            if audio_data is not None and len(audio_data) > 0:
                print_success(f"English synthesis successful: {len(audio_data)} samples generated")
            else:
                print_error("English synthesis returned empty audio")
                return False
        else:
            print_error(f"English synthesis failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test Hindi synthesis
        print_info("Testing Hindi synthesis...")
        result = await model.synthesize_speech("यह कोकोरो टीटीएस का परीक्षण है।", "hm_omega")
        
        if result.get("success", False):
            audio_data = result.get("audio_data")
            if audio_data is not None and len(audio_data) > 0:
                print_success(f"Hindi synthesis successful: {len(audio_data)} samples generated")
            else:
                print_error("Hindi synthesis returned empty audio")
                return False
        else:
            print_error(f"Hindi synthesis failed: {result.get('error', 'Unknown error')}")
            return False
        
        await model.cleanup()
        print_success("Speech synthesis tests completed successfully")
        return True
        
    except Exception as e:
        print_error(f"Error testing speech synthesis: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_voice_mapping():
    """Test voice mapping functionality"""
    print_step(6, "Testing Voice Mapping")
    
    try:
        from src.tts.tts_service import map_voice_to_kokoro
        
        test_cases = [
            ("ऋतिका", "hm_omega"),
            ("ritika", "hm_omega"),
            ("hindi", "hm_omega"),
            ("हिंदी", "hm_omega"),
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
        print_error(f"Error testing voice mapping: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main verification function"""
    parser = argparse.ArgumentParser(description="Verify Kokoro TTS model installation and functionality")
    parser.add_argument("--force-download", action="store_true", help="Force re-download of model files")
    parser.add_argument("--skip-synthesis", action="store_true", help="Skip speech synthesis tests")
    parser.add_argument("--cleanup", action="store_true", help="Clean up model cache before verification")
    
    args = parser.parse_args()
    
    print_header("Kokoro TTS Model Verification")
    print_info("Verifying Kokoro TTS installation, model files, and functionality")
    
    # Cleanup if requested
    if args.cleanup:
        print_step(0, "Cleaning Up Model Cache")
        try:
            from src.utils.kokoro_model_manager import kokoro_model_manager
            kokoro_model_manager.cleanup_cache()
            print_success("Model cache cleaned up")
        except Exception as e:
            print_error(f"Error cleaning up cache: {e}")
    
    tests = [
        ("Kokoro Installation", check_kokoro_installation),
        ("Model Files", check_model_files),
        ("Download Models", lambda: download_model_files(args.force_download)),
        ("Model Initialization", test_kokoro_initialization),
        ("Voice Mapping", test_voice_mapping)
    ]
    
    if not args.skip_synthesis:
        tests.append(("Speech Synthesis", test_speech_synthesis))
    
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
    
    print_header("Verification Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL TESTS PASSED! Kokoro TTS is ready for use!")
        return True
    else:
        print_error(f"💥 {failed} test(s) failed. Please review and fix the issues.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
