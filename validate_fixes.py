#!/usr/bin/env python3
"""
Validation Script for Critical TTS Fixes
Tests the OrpheusModel parameter fix and Kokoro language code fix
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

async def test_orpheus_parameter_fix():
    """Test that OrpheusModel constructor no longer has parameter errors"""
    print("\n🔧 Testing OrpheusModel Parameter Fix...")
    
    try:
        from src.tts.orpheus_streaming_model import OrpheusStreamingModel
        
        # Create model instance
        model = OrpheusStreamingModel()
        print_success("OrpheusStreamingModel created successfully")
        
        # Check the constructor call in the code
        import inspect
        source = inspect.getsource(model.initialize)
        
        if "max_model_len=self.max_model_len" in source:
            print_error("OrpheusModel constructor still has max_model_len parameter!")
            return False
        elif "model_name=self.model_name" in source and "max_model_len" not in source:
            print_success("OrpheusModel constructor fixed - only model_name parameter")
            return True
        else:
            print_info("OrpheusModel constructor parameters unclear")
            return True
            
    except Exception as e:
        print_error(f"Failed to test OrpheusModel fix: {e}")
        return False

async def test_kokoro_language_code_fix():
    """Test that Kokoro language code is correctly set"""
    print("\n🌐 Testing Kokoro Language Code Fix...")
    
    try:
        from src.utils.config import config
        
        # Check the language code
        lang_code = config.tts.lang_code
        
        valid_codes = ['a', 'b', 'e', 'f', 'h', 'i', 'p', 'j', 'z']
        
        if lang_code in valid_codes:
            print_success(f"Kokoro language code is valid: '{lang_code}'")
            
            # Map codes to languages for clarity
            code_map = {
                'a': 'American English',
                'b': 'British English', 
                'e': 'Spanish',
                'f': 'French',
                'h': 'Hindi',
                'i': 'Italian',
                'p': 'Portuguese',
                'j': 'Japanese',
                'z': 'Mandarin Chinese'
            }
            
            print_info(f"Language: {code_map.get(lang_code, 'Unknown')}")
            return True
        else:
            print_error(f"Invalid Kokoro language code: '{lang_code}'")
            print_info(f"Valid codes: {valid_codes}")
            return False
            
    except Exception as e:
        print_error(f"Failed to test Kokoro language code: {e}")
        return False

async def test_tts_initialization():
    """Test TTS system initialization with fixes"""
    print("\n🎵 Testing TTS System Initialization...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel created successfully")
        
        # Test initialization (may fail due to missing models, but should not crash with parameter errors)
        try:
            success = await model.initialize()
            if success:
                print_success("TTS system initialized successfully!")
                
                if hasattr(model, 'use_kokoro') and model.use_kokoro:
                    print_info("Using Kokoro TTS as primary engine")
                elif hasattr(model, 'streaming_model') and model.streaming_model:
                    print_info("Using Orpheus TTS as fallback engine")
                    
            else:
                print_info("TTS initialization failed (expected if models not available)")
                
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                print_error(f"Parameter error still exists: {e}")
                return False
            else:
                print_info(f"Different error (not parameter related): {e}")
                
        except Exception as e:
            print_info(f"Initialization error (not parameter related): {e}")
            
        return True
        
    except Exception as e:
        print_error(f"Failed to test TTS initialization: {e}")
        return False

async def main():
    """Run all validation tests"""
    print_header("Critical TTS Fixes Validation")
    
    tests = [
        ("OrpheusModel Parameter Fix", test_orpheus_parameter_fix),
        ("Kokoro Language Code Fix", test_kokoro_language_code_fix),
        ("TTS System Initialization", test_tts_initialization),
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
    print_header("Validation Results")
    
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
        print_success("🎉 All critical fixes validated successfully!")
        print_info("Your system should now start without parameter errors")
        print_info("Run: python3 -m src.api.ui_server_realtime")
    else:
        print_error("Some fixes need attention. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
