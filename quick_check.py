#!/usr/bin/env python3
"""
Quick check of Orpheus TTS setup
Just validates imports and basic setup without running full tests
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def main():
    print("🔍 Quick Orpheus TTS Setup Check")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check imports
    print("\n📦 Checking imports:")
    
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch not available")
        return False
    
    try:
        from snac import SNAC
        print("✅ SNAC available")
    except ImportError:
        print("❌ SNAC not available - install with: pip install snac")
        return False
    
    try:
        from src.utils.config import config
        print("✅ Config system")
        print(f"   TTS enabled: {config.tts.enabled}")
        print(f"   Default voice: {config.tts.default_voice}")
    except Exception as e:
        print(f"❌ Config system failed: {e}")
        return False
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        print("✅ Orpheus TTS Engine")
        
        # Test basic instantiation
        engine = OrpheusTTSEngine()
        voices = engine.get_available_voices()
        print(f"   Available voices: {len(voices)}")
        print(f"   Default voice: {engine.default_voice}")
        
    except Exception as e:
        print(f"❌ Orpheus TTS Engine failed: {e}")
        return False
    
    try:
        from src.tts.tts_service import TTSService
        print("✅ TTS Service")
        
        # Test basic instantiation
        service = TTSService()
        print(f"   Service created successfully")
        
    except Exception as e:
        print(f"❌ TTS Service failed: {e}")
        return False
    
    # Check file structure
    print("\n📁 Checking file structure:")
    required_files = [
        "src/tts/orpheus_tts_engine.py",
        "src/tts/tts_service.py",
        "src/utils/config.py",
        "config.yaml"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            all_files_exist = False
    
    if all_files_exist:
        print("\n🎉 Quick check passed!")
        print("🎯 Basic setup looks good")
        print("💡 Run comprehensive_test.py for full testing")
        return True
    else:
        print("\n💥 Quick check failed")
        print("🔧 Fix the issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)