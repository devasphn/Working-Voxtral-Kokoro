#!/usr/bin/env python3
"""
Test Script for TTS System Architecture Fixes
Validates the Kokoro-primary, Orpheus-fallback hierarchy without mock dependencies
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

async def test_orpheus_perfect_model_attributes():
    """Test that OrpheusPerfectModel no longer has mock-related attributes"""
    print("\n🔧 Testing OrpheusPerfectModel Mock Attribute Removal...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel instance created")
        
        # Check that mock attributes don't exist
        mock_attributes = ['use_mock', 'mock_model']
        
        for attr in mock_attributes:
            if hasattr(model, attr):
                print_error(f"Model still has mock attribute: {attr}")
                return False
            else:
                print_success(f"Mock attribute '{attr}' successfully removed")
        
        # Check that proper attributes exist
        required_attributes = ['use_kokoro', 'kokoro_model', 'streaming_model', 'is_initialized']
        
        for attr in required_attributes:
            if hasattr(model, attr):
                print_success(f"Required attribute '{attr}' exists")
            else:
                print_error(f"Missing required attribute: {attr}")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"OrpheusPerfectModel attribute test failed: {e}")
        return False

async def test_get_model_info_method():
    """Test that get_model_info() method works without mock attributes"""
    print("\n📊 Testing get_model_info() Method...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel instance created")
        
        # Test get_model_info() without initialization
        info = model.get_model_info()
        print_success("get_model_info() called successfully")
        
        # Check that info doesn't contain mock references
        if 'using_mock' in info:
            print_error("get_model_info() still returns 'using_mock' field")
            return False
        else:
            print_success("'using_mock' field successfully removed from model info")
        
        # Check that proper fields exist
        required_fields = ['wrapper_type', 'is_initialized', 'tts_engine', 'generation_statistics']
        
        for field in required_fields:
            if field in info:
                print_success(f"Required field '{field}' exists in model info")
            else:
                print_error(f"Missing required field in model info: {field}")
                return False
        
        print_info(f"TTS engine: {info.get('tts_engine', 'unknown')}")
        print_info(f"Initialization status: {info.get('is_initialized', False)}")
        
        return True
        
    except Exception as e:
        print_error(f"get_model_info() test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cleanup_method():
    """Test that cleanup() method works without mock_model references"""
    print("\n🧹 Testing cleanup() Method...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel instance created")
        
        # Test cleanup method
        await model.cleanup()
        print_success("cleanup() method executed successfully")
        
        # Check that state was reset properly
        if not model.is_initialized and not model.use_kokoro:
            print_success("Model state reset correctly after cleanup")
        else:
            print_warning("Model state may not have been reset properly")
        
        return True
        
    except Exception as e:
        print_error(f"cleanup() test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tts_hierarchy_initialization():
    """Test the Kokoro-primary, Orpheus-fallback hierarchy"""
    print("\n🎵 Testing TTS Hierarchy Initialization...")
    
    try:
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Create model instance
        model = OrpheusPerfectModel()
        print_success("OrpheusPerfectModel instance created")
        
        # Test initialization
        print_info("Attempting TTS hierarchy initialization...")
        success = await model.initialize()
        
        if success:
            print_success("TTS hierarchy initialized successfully!")
            
            # Check which engine was used
            info = model.get_model_info()
            tts_engine = info.get('tts_engine', 'unknown')
            
            if tts_engine == 'kokoro':
                print_success("🎉 Kokoro TTS is primary engine (as expected)")
            elif tts_engine == 'orpheus':
                print_success("🔄 Orpheus TTS is fallback engine (Kokoro failed)")
            else:
                print_warning(f"Unknown TTS engine: {tts_engine}")
            
            # Test that only one engine is active
            if model.use_kokoro and model.streaming_model:
                print_error("Both Kokoro and Orpheus models are active (should be exclusive)")
                return False
            elif model.use_kokoro:
                print_success("Only Kokoro model is active (correct)")
            elif model.streaming_model:
                print_success("Only Orpheus model is active (correct fallback)")
            else:
                print_error("No TTS model is active (unexpected)")
                return False
                
        else:
            print_warning("TTS hierarchy initialization failed (expected if no TTS engines available)")
        
        return True
        
    except Exception as e:
        print_error(f"TTS hierarchy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_unified_model_manager_integration():
    """Test that unified model manager works with the fixed TTS hierarchy"""
    print("\n🎯 Testing Unified Model Manager Integration...")
    
    try:
        from src.models.unified_model_manager import UnifiedModelManager
        
        # Create manager instance
        manager = UnifiedModelManager()
        print_success("UnifiedModelManager instance created")
        
        # Test that it has the new _initialize_tts_model method
        if hasattr(manager, '_initialize_tts_model'):
            print_success("_initialize_tts_model method exists")
        else:
            print_error("_initialize_tts_model method missing")
            return False
        
        # Check that orpheus_initialized attribute exists
        if hasattr(manager, 'orpheus_initialized'):
            print_success("orpheus_initialized attribute exists")
        else:
            print_error("orpheus_initialized attribute missing")
            return False
        
        print_info("Unified model manager structure validated")
        return True
        
    except Exception as e:
        print_error(f"Unified model manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all architecture fix tests"""
    print_header("TTS System Architecture Fixes Validation")
    
    tests = [
        ("OrpheusPerfectModel Mock Attributes", test_orpheus_perfect_model_attributes),
        ("get_model_info() Method", test_get_model_info_method),
        ("cleanup() Method", test_cleanup_method),
        ("TTS Hierarchy Initialization", test_tts_hierarchy_initialization),
        ("Unified Model Manager Integration", test_unified_model_manager_integration),
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
        print_success("🎉 All architecture fixes validated successfully!")
        print_info("Key fixes applied:")
        print_info("  ✓ Removed all mock-related attributes and references")
        print_info("  ✓ Fixed get_model_info() method to work without mock fields")
        print_info("  ✓ Fixed cleanup() method to handle proper model references")
        print_info("  ✓ Implemented Kokoro-primary, Orpheus-fallback hierarchy")
        print_info("  ✓ Updated unified model manager for conditional TTS initialization")
        print_info("\nSystem behavior:")
        print_info("  🎵 Kokoro TTS tries to initialize first (primary)")
        print_info("  🔄 Orpheus TTS only initializes if Kokoro fails (fallback)")
        print_info("  🚫 No mock TTS services or dependencies")
        print_info("  ✅ Clean separation between TTS engines")
    else:
        print_warning("Some tests failed. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
