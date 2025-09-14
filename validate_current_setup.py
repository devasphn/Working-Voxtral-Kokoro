#!/usr/bin/env python3
"""
Validate current setup for Orpheus TTS integration
Checks dependencies and basic functionality
"""

import sys
import os

def check_imports():
    """Check if all required imports are available"""
    print("🔍 Checking imports...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA device: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print("✅ Transformers available")
    except ImportError as e:
        print(f"❌ Transformers import failed: {e}")
        return False
    
    try:
        from snac import SNAC
        print("✅ SNAC available")
    except ImportError as e:
        print(f"❌ SNAC import failed: {e}")
        print("💡 Install with: pip install snac")
        return False
    
    try:
        import numpy as np
        import wave
        import io
        print("✅ Audio processing libraries available")
    except ImportError as e:
        print(f"❌ Audio libraries import failed: {e}")
        return False
    
    return True

def test_snac_model():
    """Test SNAC model loading"""
    print("\n🧪 Testing SNAC model loading...")
    
    try:
        from snac import SNAC
        import torch
        
        print("📥 Loading SNAC model...")
        model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
        
        if torch.cuda.is_available():
            model = model.cuda()
            print("✅ SNAC model loaded on GPU")
        else:
            print("✅ SNAC model loaded on CPU")
        
        # Test basic functionality
        device = next(model.parameters()).device
        print(f"   Model device: {device}")
        
        return True
        
    except Exception as e:
        print(f"❌ SNAC model test failed: {e}")
        return False

def check_project_structure():
    """Check if project structure is correct"""
    print("\n📁 Checking project structure...")
    
    required_files = [
        "src/tts/orpheus_tts_engine.py",
        "src/tts/tts_service.py",
        "src/utils/config.py",
        "config.yaml"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def test_basic_functionality():
    """Test basic TTS functionality"""
    print("\n🧪 Testing basic TTS functionality...")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Create engine instance
        engine = OrpheusTTSEngine()
        print("✅ OrpheusTTSEngine created")
        
        # Check voice mapping
        test_voice = "ऋतिका"
        language = engine._get_language_for_voice(test_voice)
        print(f"✅ Voice mapping: '{test_voice}' → '{language}'")
        
        # Check available voices
        voices = engine.get_available_voices()
        print(f"✅ Available voices: {len(voices)} voices")
        print(f"   Default voice: {engine.default_voice}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation checks"""
    print("🔧 Orpheus TTS Setup Validation")
    print("=" * 40)
    
    # Run checks
    imports_ok = check_imports()
    structure_ok = check_project_structure()
    snac_ok = test_snac_model()
    basic_ok = test_basic_functionality()
    
    # Summary
    print("\n📊 Validation Results:")
    print(f"   Imports:         {'✅ OK' if imports_ok else '❌ Failed'}")
    print(f"   Project Structure: {'✅ OK' if structure_ok else '❌ Failed'}")
    print(f"   SNAC Model:      {'✅ OK' if snac_ok else '❌ Failed'}")
    print(f"   Basic Functions: {'✅ OK' if basic_ok else '❌ Failed'}")
    
    if all([imports_ok, structure_ok, snac_ok, basic_ok]):
        print("\n🎉 Setup validation successful!")
        print("🎯 Ready to test Orpheus TTS integration")
        return True
    else:
        print("\n💥 Setup validation failed")
        print("🔧 Fix the issues above and try again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)