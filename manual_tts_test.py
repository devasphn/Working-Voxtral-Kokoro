#!/usr/bin/env python3
"""
Manual TTS test - simple standalone test
"""

import subprocess
import tempfile
import os
import base64

def test_espeak_directly():
    """Test espeak-ng directly"""
    print("🧪 Testing espeak-ng directly...")
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Generate audio with espeak-ng
        cmd = [
            "espeak-ng",
            "-v", "en+f3",  # Female voice
            "-s", "150",    # Speed
            "-w", temp_path,  # Output to WAV file
            "Hello! This is a test of the text to speech system. Can you hear me?"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            # Read the generated audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            if len(audio_data) > 44:  # WAV header is 44 bytes
                print(f"✅ espeak-ng generated {len(audio_data)} bytes of audio")
                
                # Save as test file
                with open("manual_test_output.wav", "wb") as f:
                    f.write(audio_data)
                print("💾 Audio saved as 'manual_test_output.wav'")
                
                # Convert to base64 for web use
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                print(f"📝 Base64 audio length: {len(audio_b64)} characters")
                
                return True
            else:
                print("❌ Generated audio file is too small")
                return False
        else:
            print(f"❌ espeak-ng failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ espeak-ng test failed: {e}")
        return False

def test_pyttsx3_directly():
    """Test pyttsx3 directly"""
    print("🧪 Testing pyttsx3 directly...")
    
    try:
        import pyttsx3
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Initialize pyttsx3
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', 180)
        engine.setProperty('volume', 0.9)
        
        # Generate audio
        engine.save_to_file("Hello! This is a test of pyttsx3 text to speech.", temp_path)
        engine.runAndWait()
        
        if os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(temp_path)
            
            if len(audio_data) > 44:
                print(f"✅ pyttsx3 generated {len(audio_data)} bytes of audio")
                
                # Save as test file
                with open("manual_pyttsx3_output.wav", "wb") as f:
                    f.write(audio_data)
                print("💾 Audio saved as 'manual_pyttsx3_output.wav'")
                
                return True
            else:
                print("❌ Generated audio file is too small")
                return False
        else:
            print("❌ pyttsx3 did not generate output file")
            return False
            
    except ImportError:
        print("❌ pyttsx3 not available")
        return False
    except Exception as e:
        print(f"❌ pyttsx3 test failed: {e}")
        return False

def main():
    """Run manual TTS tests"""
    print("🔧 Manual TTS Test")
    print("=" * 30)
    
    espeak_ok = test_espeak_directly()
    print()
    pyttsx3_ok = test_pyttsx3_directly()
    
    print("\n📊 Results:")
    print(f"   espeak-ng: {'✅ Working' if espeak_ok else '❌ Failed'}")
    print(f"   pyttsx3:   {'✅ Working' if pyttsx3_ok else '❌ Failed'}")
    
    if espeak_ok or pyttsx3_ok:
        print("\n🎉 At least one TTS engine is working!")
        print("Check the generated .wav files to verify audio quality.")
        return True
    else:
        print("\n💥 No TTS engines are working!")
        print("Try running: python fix_tts.py")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)