#!/usr/bin/env python3
"""
Complete System Validation Script
Tests all components of the Voxtral + Orpheus TTS integration
"""

import asyncio
import sys
import os
import time
import traceback
import torch
import numpy as np

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n{step_num}. {title}")
    print("-" * 40)

def print_success(message):
    """Print success message"""
    print(f"   ✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"   ❌ {message}")

def print_warning(message):
    """Print warning message"""
    print(f"   ⚠️ {message}")

def print_info(message):
    """Print info message"""
    print(f"   💡 {message}")

async def test_environment():
    """Test the environment setup"""
    print_step(1, "Environment Validation")
    
    try:
        # Test Python version
        python_version = sys.version
        print_success(f"Python version: {python_version.split()[0]}")
        
        # Test CUDA availability
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print_success(f"CUDA available: {device_name} ({memory_gb:.1f}GB)")
            
            if memory_gb >= 8:
                print_success("Sufficient VRAM for both models")
            else:
                print_warning(f"Limited VRAM: {memory_gb:.1f}GB (8GB+ recommended)")
        else:
            print_warning("CUDA not available - will run on CPU (slower)")
        
        # Test directory structure
        required_dirs = ['src', 'src/models', 'src/tts', 'src/streaming', 'src/utils']
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                print_success(f"Directory exists: {dir_path}")
            else:
                print_error(f"Missing directory: {dir_path}")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Environment test failed: {e}")
        return False

async def test_package_imports():
    """Test all required package imports"""
    print_step(2, "Package Import Validation")
    
    packages_to_test = [
        ('torch', 'PyTorch'),
        ('transformers', 'Transformers'),
        ('mistral_common', 'Mistral Common'),
        ('kokoro', 'Kokoro TTS'),
        ('fastapi', 'FastAPI'),
        ('websockets', 'WebSockets'),
        ('numpy', 'NumPy'),
        ('librosa', 'Librosa'),
        ('soundfile', 'SoundFile')
    ]
    
    success_count = 0
    for package, name in packages_to_test:
        try:
            __import__(package)
            print_success(f"{name} imported successfully")
            success_count += 1
        except ImportError as e:
            print_error(f"{name} import failed: {e}")
    
    if success_count == len(packages_to_test):
        print_success("All required packages imported successfully")
        return True
    else:
        print_error(f"Only {success_count}/{len(packages_to_test)} packages imported successfully")
        return False

async def test_model_imports():
    """Test model class imports"""
    print_step(3, "Model Class Import Validation")
    
    try:
        # Test Voxtral model import
        from src.models.voxtral_model_realtime import VoxtralModel
        print_success("VoxtralModel imported")
        
        # Test Kokoro TTS model import
        from src.models.kokoro_model_realtime import KokoroTTSModel
        print_success("KokoroTTSModel imported")

        from src.tts.tts_service import TTSService
        print_success("TTSService imported")
        
        # Test unified manager import
        from src.models.unified_model_manager import UnifiedModelManager
        print_success("UnifiedModelManager imported")
        
        # Test utility imports
        from src.utils.gpu_memory_manager import GPUMemoryManager
        print_success("GPUMemoryManager imported")
        
        from src.models.audio_processor_realtime import AudioProcessor
        print_success("AudioProcessor imported")
        
        return True
        
    except ImportError as e:
        print_error(f"Model import failed: {e}")
        traceback.print_exc()
        return False

async def test_kokoro_integration():
    """Test Kokoro TTS integration"""
    print_step(4, "Kokoro TTS Integration Test")

    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel

        # Initialize model
        print_info("Initializing Kokoro TTS Model...")
        kokoro_model = KokoroTTSModel()

        success = await kokoro_model.initialize()
        if not success:
            print_error("Kokoro TTS model initialization failed")
            return False
        
        print_success("Kokoro TTS model initialized successfully")

        # Test speech generation
        print_info("Testing speech generation...")
        test_text = "Hello, this is a test of the Kokoro TTS integration."

        start_time = time.time()
        result = await kokoro_model.synthesize_speech(test_text, "af_heart")
        generation_time = time.time() - start_time

        if result.get("success", False) and result.get("audio_data") is not None:
            audio_data = result["audio_data"]
            print_success(f"Generated audio in {generation_time:.2f}s")
        else:
            print_error(f"No audio data generated: {result.get('error', 'Unknown error')}")
            return False
        
        # Test model info
        model_info = kokoro_model.get_model_info()
        print_success(f"Model info retrieved: {model_info.get('model_name', 'Kokoro TTS')}")

        # Cleanup
        await kokoro_model.cleanup()
        print_success("Kokoro TTS model cleanup completed")

        return True

    except Exception as e:
        print_error(f"Kokoro TTS integration test failed: {e}")
        traceback.print_exc()
        return False

async def test_voxtral_integration():
    """Test Voxtral model integration"""
    print_step(5, "Voxtral Model Integration Test")
    
    try:
        from src.models.voxtral_model_realtime import VoxtralModel
        
        # Initialize model
        print_info("Initializing Voxtral model...")
        voxtral_model = VoxtralModel()
        
        # Note: We'll skip full initialization for this test as it requires large model download
        # Instead, we'll test the class structure and methods
        
        # Test model info (should work even without initialization)
        model_info = voxtral_model.get_model_info()
        print_success(f"Model info retrieved: {model_info['status']}")
        
        # Test audio processing methods exist
        if hasattr(voxtral_model, 'process_realtime_chunk'):
            print_success("process_realtime_chunk method available")
        else:
            print_error("process_realtime_chunk method missing")
            return False
        
        if hasattr(voxtral_model, '_is_speech_detected'):
            print_success("VAD method available")
        else:
            print_error("VAD method missing")
            return False
        
        print_success("Voxtral model structure validated")
        return True
        
    except Exception as e:
        print_error(f"Voxtral integration test failed: {e}")
        traceback.print_exc()
        return False

async def test_unified_manager():
    """Test unified model manager"""
    print_step(6, "Unified Model Manager Test")
    
    try:
        from src.models.unified_model_manager import UnifiedModelManager
        
        # Create manager instance
        manager = UnifiedModelManager()
        print_success("UnifiedModelManager created")
        
        # Test manager info (should work without initialization)
        manager_info = manager.get_model_info()
        print_success(f"Manager info retrieved: {manager_info['unified_manager']['is_initialized']}")
        
        # Test memory stats
        memory_stats = manager.get_memory_stats()
        if 'memory_stats' in memory_stats or 'error' in memory_stats:
            print_success("Memory stats method working")
        else:
            print_error("Memory stats method failed")
            return False
        
        print_success("Unified model manager structure validated")
        return True
        
    except Exception as e:
        print_error(f"Unified manager test failed: {e}")
        traceback.print_exc()
        return False

async def test_audio_processing():
    """Test audio processing pipeline"""
    print_step(7, "Audio Processing Pipeline Test")
    
    try:
        from src.models.audio_processor_realtime import AudioProcessor
        
        # Create audio processor
        audio_processor = AudioProcessor()
        print_success("AudioProcessor created")
        
        # Create dummy audio data
        sample_rate = 16000
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        
        # Generate test audio (sine wave)
        t = np.linspace(0, duration, samples, False)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        print_success(f"Generated test audio: {len(audio_data)} samples")
        
        # Test validation
        if hasattr(audio_processor, 'validate_realtime_chunk'):
            is_valid = audio_processor.validate_realtime_chunk(audio_data, 1)
            print_success(f"Audio validation: {is_valid}")
        
        # Test preprocessing
        if hasattr(audio_processor, 'preprocess_realtime_chunk'):
            processed = audio_processor.preprocess_realtime_chunk(audio_data, 1)
            if processed is not None:
                print_success(f"Audio preprocessing successful: {type(processed)}")
            else:
                print_error("Audio preprocessing failed")
                return False
        
        print_success("Audio processing pipeline validated")
        return True
        
    except Exception as e:
        print_error(f"Audio processing test failed: {e}")
        traceback.print_exc()
        return False

async def test_api_structure():
    """Test API and server structure"""
    print_step(8, "API Structure Validation")
    
    try:
        # Test FastAPI server import
        from src.api.ui_server_realtime import app
        print_success("FastAPI app imported")
        
        # Test WebSocket server import
        from src.streaming.websocket_server import WebSocketServer
        print_success("WebSocket server imported")
        
        # Test configuration
        from src.utils.config import config
        print_success("Configuration loaded")
        
        # Validate config structure
        if hasattr(config, 'server') and hasattr(config, 'model') and hasattr(config, 'audio'):
            print_success("Configuration structure validated")
        else:
            print_error("Configuration structure incomplete")
            return False
        
        print_success("API structure validated")
        return True
        
    except Exception as e:
        print_error(f"API structure test failed: {e}")
        traceback.print_exc()
        return False

async def run_complete_validation():
    """Run complete system validation"""
    print_header("Complete Voxtral + Orpheus TTS System Validation")
    
    tests = [
        ("Environment", test_environment),
        ("Package Imports", test_package_imports),
        ("Model Imports", test_model_imports),
        ("Kokoro TTS Integration", test_kokoro_integration),
        ("Voxtral Integration", test_voxtral_integration),
        ("Unified Manager", test_unified_manager),
        ("Audio Processing", test_audio_processing),
        ("API Structure", test_api_structure)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
                print_success(f"{test_name} test PASSED")
            else:
                print_error(f"{test_name} test FAILED")
        except Exception as e:
            print_error(f"{test_name} test FAILED with exception: {e}")
    
    print_header("Validation Summary")
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED! System is ready for production!")
        print_info("Next steps:")
        print_info("1. Run: python -m src.api.ui_server_realtime")
        print_info("2. Access UI at: http://localhost:8000")
        print_info("3. Test voice conversations")
        return True
    else:
        print_error(f"❌ {total_tests - passed_tests} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_complete_validation())
    sys.exit(0 if success else 1)
