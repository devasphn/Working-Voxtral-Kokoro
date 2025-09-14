#!/usr/bin/env python3
"""
Fix TTS issues by installing dependencies and testing functionality
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required TTS dependencies"""
    print("📦 Installing TTS dependencies...")
    
    try:
        # Install system dependencies
        print("🔧 Installing system packages...")
        subprocess.run([
            "apt-get", "update", "-qq"
        ], check=True)
        
        subprocess.run([
            "apt-get", "install", "-y", "-qq",
            "espeak-ng", "espeak-ng-data", "alsa-utils"
        ], check=True)
        
        print("✅ System packages installed")
        
        # Install Python dependencies
        print("🐍 Installing Python packages...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyttsx3"
        ], check=True)
        
        print("✅ Python packages installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    
    return True

def test_espeak():
    """Test espeak-ng functionality"""
    print("🧪 Testing espeak-ng...")
    
    try:
        result = subprocess.run([
            "espeak-ng", "--version"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ espeak-ng is working")
            return True
        else:
            print(f"❌ espeak-ng test failed: {result.stderr}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ espeak-ng not available: {e}")
        return False

def test_pyttsx3():
    """Test pyttsx3 functionality"""
    print("🧪 Testing pyttsx3...")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✅ pyttsx3 is working ({len(voices) if voices else 0} voices available)")
        return True
    except ImportError:
        print("❌ pyttsx3 not available")
        return False
    except Exception as e:
        print(f"❌ pyttsx3 test failed: {e}")
        return False

async def test_tts_service():
    """Test the actual TTS service"""
    print("🧪 Testing TTS Service...")
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from src.tts.tts_service import TTSService
        
        # Initialize TTS service
        tts_service = TTSService()
        await tts_service.initialize()
        
        # Test generation
        result = await tts_service.generate_speech_async(
            text="Hello, this is a TTS test.",
            voice="tara",
            return_format="wav"
        )
        
        if result["success"]:
            print("✅ TTS Service is working!")
            print(f"   📊 Generated {len(result['audio_data']) if result['audio_data'] else 0} chars of audio data")
            return True
        else:
            print(f"❌ TTS Service failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ TTS Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to fix and test TTS"""
    print("🔧 TTS Fix and Test Script")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        print("💥 Failed to install dependencies")
        return False
    
    # Test individual components
    espeak_ok = test_espeak()
    pyttsx3_ok = test_pyttsx3()
    
    if not (espeak_ok or pyttsx3_ok):
        print("💥 No working TTS engines available")
        return False
    
    # Test TTS service
    import asyncio
    tts_ok = asyncio.run(test_tts_service())
    
    if tts_ok:
        print("\n🎉 TTS is now working!")
        print("You can restart your Voxtral application to use TTS.")
        return True
    else:
        print("\n💥 TTS is still not working")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)