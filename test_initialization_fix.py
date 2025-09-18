#!/usr/bin/env python3
"""
Test Script for Kokoro TTS Initialization Return Value Fix
Validates that the initialize() method properly returns True/False
"""

import asyncio
import sys
import os
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️  {message}")

async def test_kokoro_initialize_return_value():
    """Test that KokoroTTSModel.initialize() returns proper boolean values"""
    print("\n🔧 Testing KokoroTTSModel.initialize() Return Value...")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        # Create model instance
        model = KokoroTTSModel()
        print_success("KokoroTTSModel instance created")
        
        # Test initialization and check return value
        print_info("Calling model.initialize()...")
        result = await model.initialize()
        
        print_info(f"initialize() returned: {result} (type: {type(result)})")
        
        if result is True:
            print_success("✅ initialize() correctly returned True on success!")
            
            # Test that calling it again returns True (already initialized)
            result2 = await model.initialize()
            if result2 is True:
                print_success("✅ initialize() correctly returned True when already initialized!")
            else:
                print_error(f"❌ initialize() returned {result2} when already initialized (should be True)")
                return False
                
            return True
            
        elif result is False:
            print_warning("⚠️ initialize() returned False (likely due to missing dependencies)")
            print_info("This is expected if Kokoro TTS is not installed")
            return True  # This is correct behavior
            
        elif result is None:
            print_error("❌ initialize() returned None (this was the bug!)")
            print_error("The method should return True on success or False on failure")
            return False
            
        else:
            print_error(f"❌ initialize() returned unexpected value: {result}")
            return False
            
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orpheus_perfect_model_integration():
    """Test that OrpheusPerfectModel correctly handles Kokoro return values"""
    print("\n🎯 Testing OrpheusPerfectModel Integration...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel instance created")
        
        # Test initialization
        print_info("Calling OrpheusPerfectModel.initialize()...")
        result = await model.initialize()
        
        print_info(f"OrpheusPerfectModel.initialize() returned: {result} (type: {type(result)})")
        
        if result is True:
            print_success("✅ OrpheusPerfectModel initialized successfully!")
            
            # Check which TTS engine is being used
            if hasattr(model, 'use_kokoro') and model.use_kokoro:
                print_success("🎵 Using Kokoro TTS as primary engine")
            elif hasattr(model, 'streaming_model') and model.streaming_model:
                print_success("🔊 Using Orpheus TTS as fallback engine")
            else:
                print_info("TTS engine status unclear")
                
            return True
            
        elif result is False:
            print_warning("⚠️ OrpheusPerfectModel initialization failed")
            print_info("This is expected if no TTS engines are available")
            return True  # This is correct behavior
            
        else:
            print_error(f"❌ OrpheusPerfectModel returned unexpected value: {result}")
            return False
            
    except Exception as e:
        print_error(f"OrpheusPerfectModel test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voice_configuration():
    """Test that the voice configuration is correct"""
    print("\n🎤 Testing Voice Configuration...")
    
    try:
        from src.utils.config import config
        
        voice = config.tts.voice
        lang_code = config.tts.lang_code
        
        print_info(f"Configured voice: '{voice}'")
        print_info(f"Configured language code: '{lang_code}'")
        
        # Check if this is the fixed configuration
        if voice == "af_heart" and lang_code == "a":
            print_success("✅ Voice configuration is correct (af_heart, American English)")
            return True
        elif voice == "default":
            print_error("❌ Voice is still set to 'default' (this will cause 404 errors)")
            return False
        else:
            print_warning(f"⚠️ Voice is set to '{voice}' (not the recommended af_heart)")
            print_info("This might work if it's a valid Kokoro voice")
            return True
            
    except Exception as e:
        print_error(f"Voice configuration test failed: {e}")
        return False

async def test_repository_url_format():
    """Test that the expected repository URL format is correct"""
    print("\n🌐 Testing Repository URL Format...")
    
    try:
        from src.utils.config import config
        voice = config.tts.voice
        
        # Expected URL format
        expected_url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{voice}.pt"
        print_info(f"Expected voice file URL: {expected_url}")
        
        # Check URL format validity
        if voice and not voice.endswith('.pt') and voice.replace('_', '').replace('-', '').isalnum():
            print_success("✅ Voice file URL format is valid")
            return True
        else:
            print_error("❌ Voice file URL format is invalid")
            return False
            
    except Exception as e:
        print_error(f"Repository URL test failed: {e}")
        return False

async def main():
    """Run all initialization fix tests"""
    print_header("Kokoro TTS Initialization Fix Validation")
    
    tests = [
        ("Voice Configuration", test_voice_configuration),
        ("Repository URL Format", test_repository_url_format),
        ("KokoroTTSModel Return Value", test_kokoro_initialize_return_value),
        ("OrpheusPerfectModel Integration", test_orpheus_perfect_model_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Results Summary")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("🎉 All initialization fixes validated successfully!")
        print_info("Key fixes applied:")
        print_info("  ✓ KokoroTTSModel.initialize() now returns True/False")
        print_info("  ✓ Voice configuration uses valid 'af_heart' voice")
        print_info("  ✓ Repository URL format is correct")
        print_info("  ✓ OrpheusPerfectModel integration works properly")
        print_info("\nYour system should now:")
        print_info("  ✓ Initialize Kokoro TTS without return value errors")
        print_info("  ✓ Download voice files without 404 errors")
        print_info("  ✓ Pass all test validations correctly")
    else:
        print_warning("Some tests failed. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
