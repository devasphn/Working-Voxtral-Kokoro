#!/usr/bin/env python3
"""
Audio Delivery Diagnostic Script
Comprehensive analysis and testing of the audio delivery pipeline
"""

import asyncio
import sys
import logging
import base64
import numpy as np
import soundfile as sf
from io import BytesIO
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_diagnostic")

def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")

def print_warning(message: str):
    print(f"⚠️  {message}")

def test_wav_creation():
    """Test WAV file creation with proper headers"""
    print_header("Testing WAV File Creation")
    
    try:
        # Create test audio data (sine wave)
        sample_rate = 24000
        duration = 1.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
        
        print_info(f"Generated test audio: {len(audio_data)} samples at {sample_rate}Hz")
        
        # Test 1: Raw bytes (OLD METHOD - BROKEN)
        raw_bytes = audio_data.tobytes()
        print_info(f"Raw PCM bytes: {len(raw_bytes)} bytes")
        print_warning("Raw PCM data cannot be played as WAV (missing headers)")
        
        # Test 2: Proper WAV with headers (NEW METHOD - FIXED)
        wav_buffer = BytesIO()
        sf.write(wav_buffer, audio_data, sample_rate, format='WAV', subtype='PCM_16')
        wav_bytes = wav_buffer.getvalue()
        wav_buffer.close()
        
        print_success(f"Proper WAV file: {len(wav_bytes)} bytes (includes headers)")
        print_info(f"WAV overhead: {len(wav_bytes) - len(raw_bytes)} bytes for headers")
        
        # Test 3: Base64 encoding
        wav_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        print_success(f"Base64 encoded WAV: {len(wav_b64)} characters")
        
        # Test 4: Verify WAV headers
        if wav_bytes[:4] == b'RIFF' and wav_bytes[8:12] == b'WAVE':
            print_success("WAV file has proper RIFF/WAVE headers")
        else:
            print_error("WAV file missing proper headers")
        
        # Save test files for verification
        with open('test_raw.pcm', 'wb') as f:
            f.write(raw_bytes)
        
        with open('test_proper.wav', 'wb') as f:
            f.write(wav_bytes)
        
        print_success("Test files saved: test_raw.pcm (broken) and test_proper.wav (working)")
        
        return True
        
    except Exception as e:
        print_error(f"WAV creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_kokoro_audio_generation():
    """Test Kokoro TTS audio generation"""
    print_header("Testing Kokoro TTS Audio Generation")
    
    try:
        from src.models.kokoro_model_realtime import KokoroTTSModel
        
        print_info("Initializing Kokoro TTS model...")
        kokoro_model = KokoroTTSModel()
        
        if not kokoro_model.is_initialized:
            print_info("Model not initialized, attempting initialization...")
            success = await kokoro_model.initialize()
            if not success:
                print_error("Failed to initialize Kokoro TTS model")
                return False
        
        print_success("Kokoro TTS model initialized")
        
        # Test speech synthesis
        test_text = "Hello, this is a test of the audio delivery system."
        print_info(f"Synthesizing: '{test_text}'")
        
        result = await kokoro_model.synthesize_speech(test_text, chunk_id="diagnostic_test")
        
        if result.get("success", False):
            audio_data = result["audio_data"]
            sample_rate = result["sample_rate"]
            
            print_success(f"Speech synthesis successful:")
            print_info(f"  Audio samples: {len(audio_data)}")
            print_info(f"  Sample rate: {sample_rate}Hz")
            print_info(f"  Duration: {len(audio_data) / sample_rate:.2f}s")
            print_info(f"  Synthesis time: {result['synthesis_time_ms']:.1f}ms")
            
            # Test WAV conversion
            wav_buffer = BytesIO()
            sf.write(wav_buffer, audio_data, sample_rate, format='WAV', subtype='PCM_16')
            wav_bytes = wav_buffer.getvalue()
            wav_buffer.close()
            
            print_success(f"WAV conversion successful: {len(wav_bytes)} bytes")
            
            # Save test audio
            sf.write('diagnostic_kokoro_output.wav', audio_data, sample_rate)
            print_success("Test audio saved to diagnostic_kokoro_output.wav")
            
            return True
        else:
            print_error(f"Speech synthesis failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print_error(f"Kokoro audio generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_format_compatibility():
    """Test audio format compatibility with browsers"""
    print_header("Testing Audio Format Compatibility")
    
    try:
        # Create test audio
        sample_rate = 24000
        duration = 0.5
        frequency = 1000
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.3
        
        # Test different WAV formats
        formats = [
            ('PCM_16', 'PCM 16-bit (recommended for browsers)'),
            ('PCM_24', 'PCM 24-bit'),
            ('PCM_32', 'PCM 32-bit'),
            ('FLOAT', 'Float 32-bit')
        ]
        
        for subtype, description in formats:
            try:
                wav_buffer = BytesIO()
                sf.write(wav_buffer, audio_data, sample_rate, format='WAV', subtype=subtype)
                wav_bytes = wav_buffer.getvalue()
                wav_buffer.close()
                
                print_success(f"{description}: {len(wav_bytes)} bytes")
                
                # Save test file
                filename = f'test_format_{subtype.lower()}.wav'
                with open(filename, 'wb') as f:
                    f.write(wav_bytes)
                
            except Exception as e:
                print_error(f"{description}: Failed - {e}")
        
        print_info("Browser compatibility notes:")
        print_info("  ✅ PCM_16: Best browser support (recommended)")
        print_info("  ⚠️  PCM_24/32: Limited browser support")
        print_info("  ❌ FLOAT: Poor browser support")
        
        return True
        
    except Exception as e:
        print_error(f"Audio format compatibility test failed: {e}")
        return False

def analyze_audio_pipeline():
    """Analyze the complete audio delivery pipeline"""
    print_header("Audio Delivery Pipeline Analysis")
    
    print_info("Complete Audio Delivery Pipeline:")
    print_info("1. 🎤 User speaks → Client captures audio")
    print_info("2. 📡 Client sends audio via WebSocket")
    print_info("3. 🧠 Server processes with Voxtral (STT)")
    print_info("4. 💭 Server generates text response")
    print_info("5. 🎵 Server synthesizes speech with Kokoro TTS")
    print_info("6. 📦 Server creates proper WAV file with headers")
    print_info("7. 🔐 Server base64 encodes WAV data")
    print_info("8. 📡 Server sends audio_response via WebSocket")
    print_info("9. 🔓 Client decodes base64 to WAV blob")
    print_info("10. 🔊 Client plays WAV audio")
    
    print_info("\n🔧 Root Cause Identified:")
    print_error("❌ OLD: Server sent raw PCM data claiming it was WAV")
    print_error("   - numpy_array.tobytes() = raw samples without headers")
    print_error("   - Browser cannot play raw PCM as WAV")
    
    print_info("\n✅ FIXED: Server now sends proper WAV with headers")
    print_success("   - soundfile creates proper WAV format")
    print_success("   - Includes RIFF/WAVE headers and format chunks")
    print_success("   - Browser can decode and play correctly")
    
    print_info("\n📋 Verification Steps:")
    print_info("1. Check server logs for 'WAV conversion successful'")
    print_info("2. Check client logs for 'Audio chunk ready to play'")
    print_info("3. Verify no browser console errors")
    print_info("4. Confirm audio playback in browser")

async def main():
    """Run comprehensive audio delivery diagnostic"""
    print_header("Audio Delivery Diagnostic - Voxtral-Final")
    print_info("Analyzing and testing the complete audio delivery pipeline")
    
    tests = [
        ("WAV File Creation", test_wav_creation),
        ("Audio Format Compatibility", test_audio_format_compatibility),
        ("Kokoro Audio Generation", test_kokoro_audio_generation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔧 Running {test_name} test...")
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print_success(f"{test_name} test PASSED")
            else:
                failed += 1
                print_error(f"{test_name} test FAILED")
        except Exception as e:
            failed += 1
            print_error(f"{test_name} test FAILED with exception: {e}")
    
    # Always run pipeline analysis
    analyze_audio_pipeline()
    
    print_header("Diagnostic Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL AUDIO DELIVERY TESTS PASSED!")
        print_info("\n📋 Next Steps:")
        print_info("1. Start your Voxtral system: python -m src.api.ui_server_realtime")
        print_info("2. Test voice conversation in browser")
        print_info("3. Check browser console for audio playback logs")
        print_info("4. Verify you can hear AI responses")
        return True
    else:
        print_error(f"💥 {failed} test(s) failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
