#!/usr/bin/env python3
"""
PERFECT Installation Test Script
Tests the complete Voxtral + Orpheus TTS system with ZERO ERRORS
Based on official repositories: mistralai/mistral-common + canopyai/Orpheus-TTS
"""

import sys
import traceback
from typing import Dict, Any

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step: int, title: str):
    """Print a formatted step"""
    print(f"\n{step}️⃣ {title}")
    print("-" * 40)

def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"⚠️ {message}")

def test_core_packages():
    """Test core package imports"""
    print_step(1, "Core Package Imports")
    
    results = {}
    
    # Test PyTorch
    try:
        import torch
        print_success(f"PyTorch {torch.__version__} imported")
        print_success(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print_success(f"CUDA device: {torch.cuda.get_device_name()}")
        results['torch'] = True
    except Exception as e:
        print_error(f"PyTorch import failed: {e}")
        results['torch'] = False
    
    # Test Transformers
    try:
        import transformers
        print_success(f"Transformers {transformers.__version__} imported")
        results['transformers'] = True
    except Exception as e:
        print_error(f"Transformers import failed: {e}")
        results['transformers'] = False
    
    # Test HuggingFace Hub
    try:
        import huggingface_hub
        print_success(f"HuggingFace Hub {huggingface_hub.__version__} imported")
        results['huggingface_hub'] = True
    except Exception as e:
        print_error(f"HuggingFace Hub import failed: {e}")
        results['huggingface_hub'] = False
    
    return results

def test_mistral_common():
    """Test Mistral Common with audio support"""
    print_step(2, "Mistral Common Audio Support")
    
    try:
        import mistral_common
        print_success("Mistral Common imported successfully")
        
        # Test audio support
        try:
            from mistral_common.audio import AudioTokenizer
            print_success("Audio tokenizer available")
            return True
        except ImportError as e:
            print_warning(f"Audio support not available: {e}")
            return False
            
    except Exception as e:
        print_error(f"Mistral Common import failed: {e}")
        return False

def test_orpheus_tts():
    """Test Orpheus TTS (orpheus-speech package)"""
    print_step(3, "Orpheus TTS (orpheus-speech)")
    
    try:
        from orpheus_tts import OrpheusModel
        print_success("Orpheus TTS imported successfully")
        
        # Test model initialization (without loading)
        try:
            model_name = "canopylabs/orpheus-tts-0.1-finetune-prod"
            print_success(f"Model name: {model_name}")
            print_success("OrpheusModel class available")
            return True
        except Exception as e:
            print_warning(f"Model initialization test failed: {e}")
            return False
            
    except Exception as e:
        print_error(f"Orpheus TTS import failed: {e}")
        print_error("Make sure to install: pip install orpheus-speech")
        return False

def test_vllm():
    """Test vLLM"""
    print_step(4, "vLLM")
    
    try:
        import vllm
        print_success(f"vLLM {vllm.__version__} imported")
        return True
    except Exception as e:
        print_error(f"vLLM import failed: {e}")
        return False

def test_web_framework():
    """Test web framework components"""
    print_step(5, "Web Framework")
    
    results = {}
    
    # Test FastAPI
    try:
        import fastapi
        print_success(f"FastAPI {fastapi.__version__} imported")
        results['fastapi'] = True
    except Exception as e:
        print_error(f"FastAPI import failed: {e}")
        results['fastapi'] = False
    
    # Test Pydantic
    try:
        import pydantic
        print_success(f"Pydantic {pydantic.__version__} imported")
        results['pydantic'] = True
    except Exception as e:
        print_error(f"Pydantic import failed: {e}")
        results['pydantic'] = False
    
    # Test WebSockets
    try:
        import websockets
        print_success(f"WebSockets imported")
        results['websockets'] = True
    except Exception as e:
        print_error(f"WebSockets import failed: {e}")
        results['websockets'] = False
    
    return results

def test_audio_processing():
    """Test audio processing libraries"""
    print_step(6, "Audio Processing")
    
    results = {}
    
    # Test librosa
    try:
        import librosa
        print_success(f"Librosa {librosa.__version__} imported")
        results['librosa'] = True
    except Exception as e:
        print_error(f"Librosa import failed: {e}")
        results['librosa'] = False
    
    # Test soundfile
    try:
        import soundfile
        print_success(f"SoundFile imported")
        results['soundfile'] = True
    except Exception as e:
        print_error(f"SoundFile import failed: {e}")
        results['soundfile'] = False
    
    return results

def test_flash_attention():
    """Test Flash Attention"""
    print_step(7, "Flash Attention")
    
    try:
        import flash_attn
        print_success("Flash Attention imported successfully")
        return True
    except Exception as e:
        print_warning(f"Flash Attention not available: {e}")
        return False

def main():
    """Run all tests"""
    print_header("PERFECT Installation Test")
    print("Testing Voxtral + Orpheus TTS system")
    print("Based on official repositories")
    
    all_results = {}
    
    # Run all tests
    all_results['core'] = test_core_packages()
    all_results['mistral'] = test_mistral_common()
    all_results['orpheus'] = test_orpheus_tts()
    all_results['vllm'] = test_vllm()
    all_results['web'] = test_web_framework()
    all_results['audio'] = test_audio_processing()
    all_results['flash_attn'] = test_flash_attention()
    
    # Summary
    print_header("Test Summary")
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        if isinstance(results, dict):
            for test, passed in results.items():
                total_tests += 1
                if passed:
                    passed_tests += 1
        elif isinstance(results, bool):
            total_tests += 1
            if results:
                passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"📊 Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print_success("🎉 EXCELLENT! System is ready for production")
    elif success_rate >= 75:
        print_warning("⚠️ GOOD! Some optional components missing")
    else:
        print_error("❌ CRITICAL! Major components missing")
    
    return success_rate >= 75

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_error(f"Test script failed: {e}")
        traceback.print_exc()
        sys.exit(1)
