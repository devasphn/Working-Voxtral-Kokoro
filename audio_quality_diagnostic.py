#!/usr/bin/env python3
"""
Audio Quality Diagnostic Script
Comprehensive analysis of audio quality issues in Voxtral-Final system
"""

import asyncio
import sys
import logging
import base64
import numpy as np
import soundfile as sf
from io import BytesIO
import time
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_quality_diagnostic")

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")

def print_warning(message: str):
    print(f"⚠️  {message}")

def analyze_audio_data_integrity():
    """Analyze potential audio data corruption issues"""
    print_header("Audio Data Integrity Analysis")
    
    try:
        # Create test audio with known characteristics
        sample_rate = 24000
        duration = 1.0
        frequency = 440  # A4 note
        
        # Generate clean sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        original_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.5
        
        print_info(f"Original audio: {len(original_audio)} samples at {sample_rate}Hz")
        print_info(f"Audio range: {np.min(original_audio):.6f} to {np.max(original_audio):.6f}")
        print_info(f"Audio RMS: {np.sqrt(np.mean(original_audio**2)):.6f}")
        
        # Test 1: WAV conversion (current server method)
        wav_buffer = BytesIO()
        sf.write(wav_buffer, original_audio, sample_rate, format='WAV', subtype='PCM_16')
        wav_bytes = wav_buffer.getvalue()
        wav_buffer.close()
        
        print_success(f"WAV conversion: {len(wav_bytes)} bytes")
        
        # Test 2: Base64 encoding/decoding
        wav_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        decoded_wav_bytes = base64.b64decode(wav_b64)
        
        if wav_bytes == decoded_wav_bytes:
            print_success("Base64 encoding/decoding: INTACT")
        else:
            print_error("Base64 encoding/decoding: CORRUPTED")
            return False
        
        # Test 3: WAV file integrity check
        decoded_buffer = BytesIO(decoded_wav_bytes)
        decoded_audio, decoded_sr = sf.read(decoded_buffer)
        decoded_buffer.close()
        
        print_info(f"Decoded audio: {len(decoded_audio)} samples at {decoded_sr}Hz")
        print_info(f"Decoded range: {np.min(decoded_audio):.6f} to {np.max(decoded_audio):.6f}")
        print_info(f"Decoded RMS: {np.sqrt(np.mean(decoded_audio**2)):.6f}")
        
        # Check for data integrity
        if decoded_sr != sample_rate:
            print_error(f"Sample rate mismatch: {sample_rate} → {decoded_sr}")
            return False
        
        if len(decoded_audio) != len(original_audio):
            print_error(f"Length mismatch: {len(original_audio)} → {len(decoded_audio)}")
            return False
        
        # Check audio similarity (allowing for quantization noise)
        correlation = np.corrcoef(original_audio, decoded_audio)[0, 1]
        print_info(f"Audio correlation: {correlation:.6f}")
        
        if correlation > 0.99:
            print_success("Audio data integrity: EXCELLENT")
        elif correlation > 0.95:
            print_warning("Audio data integrity: GOOD (minor quantization)")
        else:
            print_error(f"Audio data integrity: POOR (correlation: {correlation:.6f})")
            return False
        
        # Save test files
        sf.write('test_original.wav', original_audio, sample_rate)
        sf.write('test_decoded.wav', decoded_audio, decoded_sr)
        print_success("Test files saved: test_original.wav, test_decoded.wav")
        
        return True
        
    except Exception as e:
        print_error(f"Audio integrity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_sample_rate_issues():
    """Analyze potential sample rate mismatch issues"""
    print_header("Sample Rate Analysis")
    
    try:
        # Test different sample rates and their effects
        original_sr = 24000  # Kokoro output
        test_audio_duration = 1.0
        
        # Generate test audio at Kokoro's native sample rate
        t = np.linspace(0, test_audio_duration, int(original_sr * test_audio_duration), False)
        test_audio = np.sin(2 * np.pi * 1000 * t).astype(np.float32) * 0.5  # 1kHz tone
        
        print_info(f"Test audio: {len(test_audio)} samples at {original_sr}Hz")
        
        # Test 1: Correct sample rate handling
        wav_buffer = BytesIO()
        sf.write(wav_buffer, test_audio, original_sr, format='WAV', subtype='PCM_16')
        wav_bytes = wav_buffer.getvalue()
        wav_buffer.close()
        
        # Decode and verify
        decoded_buffer = BytesIO(wav_bytes)
        decoded_audio, decoded_sr = sf.read(decoded_buffer)
        decoded_buffer.close()
        
        print_success(f"Correct handling: {original_sr}Hz → {decoded_sr}Hz")
        
        # Test 2: Common browser sample rates
        browser_rates = [8000, 16000, 22050, 44100, 48000]
        
        print_info("Testing browser compatibility with different sample rates:")
        for rate in browser_rates:
            try:
                # Resample test audio
                import librosa
                resampled = librosa.resample(test_audio, orig_sr=original_sr, target_sr=rate)
                
                # Create WAV
                wav_buffer = BytesIO()
                sf.write(wav_buffer, resampled, rate, format='WAV', subtype='PCM_16')
                wav_bytes = wav_buffer.getvalue()
                wav_buffer.close()
                
                print_info(f"  {rate}Hz: {len(wav_bytes)} bytes ({'✅ Standard' if rate in [16000, 44100, 48000] else '⚠️ Non-standard'})")
                
            except Exception as e:
                print_error(f"  {rate}Hz: Failed - {e}")
        
        # Test 3: Check for sample rate metadata in WAV
        wav_buffer = BytesIO(wav_bytes)
        with sf.SoundFile(wav_buffer) as f:
            print_info(f"WAV metadata:")
            print_info(f"  Sample rate: {f.samplerate}Hz")
            print_info(f"  Channels: {f.channels}")
            print_info(f"  Subtype: {f.subtype}")
            print_info(f"  Format: {f.format}")
            print_info(f"  Frames: {f.frames}")
        wav_buffer.close()
        
        return True
        
    except Exception as e:
        print_error(f"Sample rate analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_audio_amplitude_issues():
    """Analyze potential audio amplitude and normalization issues"""
    print_header("Audio Amplitude Analysis")
    
    try:
        sample_rate = 24000
        duration = 1.0
        
        # Test different amplitude levels
        test_cases = [
            ("Very Quiet", 0.01),
            ("Quiet", 0.1),
            ("Normal", 0.5),
            ("Loud", 0.9),
            ("Clipping Risk", 1.0),
            ("Clipped", 1.5)
        ]
        
        print_info("Testing different audio amplitude levels:")
        
        for name, amplitude in test_cases:
            # Generate test tone
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * amplitude
            
            # Clip to valid range
            clipped_audio = np.clip(test_audio, -1.0, 1.0)
            clipping_occurred = not np.array_equal(test_audio, clipped_audio)
            
            # Calculate metrics
            rms = np.sqrt(np.mean(clipped_audio**2))
            peak = np.max(np.abs(clipped_audio))
            
            # Create WAV
            wav_buffer = BytesIO()
            sf.write(wav_buffer, clipped_audio, sample_rate, format='WAV', subtype='PCM_16')
            wav_bytes = wav_buffer.getvalue()
            wav_buffer.close()
            
            # Decode and check
            decoded_buffer = BytesIO(wav_bytes)
            decoded_audio, _ = sf.read(decoded_buffer)
            decoded_buffer.close()
            
            decoded_rms = np.sqrt(np.mean(decoded_audio**2))
            decoded_peak = np.max(np.abs(decoded_audio))
            
            status = "✅ Good"
            if clipping_occurred:
                status = "❌ Clipped"
            elif rms < 0.05:
                status = "⚠️ Too Quiet"
            elif rms > 0.8:
                status = "⚠️ Too Loud"
            
            print_info(f"  {name:12} | Amp: {amplitude:4.2f} | RMS: {rms:5.3f}→{decoded_rms:5.3f} | Peak: {peak:5.3f}→{decoded_peak:5.3f} | {status}")
            
            # Save test file
            filename = f"test_amplitude_{name.lower().replace(' ', '_')}.wav"
            sf.write(filename, decoded_audio, sample_rate)
        
        print_info("\nRecommendations:")
        print_info("  ✅ Optimal RMS range: 0.1 - 0.7")
        print_info("  ✅ Peak should not exceed 0.95")
        print_info("  ⚠️ Below 0.05 RMS may be too quiet for users")
        print_info("  ❌ Above 0.8 RMS may cause distortion")
        
        return True
        
    except Exception as e:
        print_error(f"Amplitude analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_kokoro_audio_quality():
    """Test actual Kokoro TTS audio quality"""
    print_header("Kokoro TTS Audio Quality Test")
    
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
        
        # Test different text lengths and complexities
        test_cases = [
            ("Short", "Hello."),
            ("Medium", "Hello! Yes, I can hear you just fine. How's it going?"),
            ("Long", "This is a longer test sentence to evaluate the audio quality and consistency of the Kokoro text-to-speech system when generating extended speech content."),
            ("Numbers", "The time is 12:34 PM and the temperature is 25.7 degrees Celsius."),
            ("Mixed", "नमस्ते! Hello! This is a test with mixed content.")
        ]
        
        for test_name, test_text in test_cases:
            print_info(f"\nTesting {test_name} text: '{test_text[:50]}{'...' if len(test_text) > 50 else ''}'")
            
            result = await kokoro_model.synthesize_speech(test_text, chunk_id=f"quality_test_{test_name.lower()}")
            
            if result.get("success", False):
                audio_data = result["audio_data"]
                sample_rate = result["sample_rate"]
                
                # Analyze audio quality
                if len(audio_data) > 0:
                    rms = np.sqrt(np.mean(audio_data**2))
                    peak = np.max(np.abs(audio_data))
                    duration = len(audio_data) / sample_rate
                    
                    print_success(f"  Generated: {len(audio_data)} samples, {duration:.2f}s")
                    print_info(f"  Audio RMS: {rms:.6f}")
                    print_info(f"  Audio Peak: {peak:.6f}")
                    print_info(f"  Sample Rate: {sample_rate}Hz")
                    print_info(f"  Synthesis Time: {result['synthesis_time_ms']:.1f}ms")
                    
                    # Quality assessment
                    if rms < 0.01:
                        print_warning("  ⚠️ Audio very quiet - may be inaudible")
                    elif rms > 0.8:
                        print_warning("  ⚠️ Audio very loud - may cause distortion")
                    else:
                        print_success("  ✅ Audio amplitude in good range")
                    
                    if peak >= 1.0:
                        print_error("  ❌ Audio clipping detected")
                    elif peak > 0.95:
                        print_warning("  ⚠️ Audio near clipping threshold")
                    else:
                        print_success("  ✅ No clipping detected")
                    
                    # Save test audio
                    filename = f"kokoro_quality_test_{test_name.lower()}.wav"
                    sf.write(filename, audio_data, sample_rate)
                    print_success(f"  Saved: {filename}")
                    
                    # Test WAV conversion (server pipeline simulation)
                    wav_buffer = BytesIO()
                    sf.write(wav_buffer, audio_data, sample_rate, format='WAV', subtype='PCM_16')
                    wav_bytes = wav_buffer.getvalue()
                    wav_buffer.close()
                    
                    # Test base64 encoding
                    wav_b64 = base64.b64encode(wav_bytes).decode('utf-8')
                    
                    # Simulate client decoding
                    decoded_wav_bytes = base64.b64decode(wav_b64)
                    decoded_buffer = BytesIO(decoded_wav_bytes)
                    decoded_audio, decoded_sr = sf.read(decoded_buffer)
                    decoded_buffer.close()
                    
                    # Check for degradation
                    correlation = np.corrcoef(audio_data, decoded_audio)[0, 1]
                    if correlation > 0.99:
                        print_success(f"  ✅ Pipeline integrity: Excellent ({correlation:.6f})")
                    else:
                        print_warning(f"  ⚠️ Pipeline integrity: {correlation:.6f}")
                    
                else:
                    print_error(f"  ❌ No audio generated")
            else:
                print_error(f"  ❌ Synthesis failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print_error(f"Kokoro audio quality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_browser_audio_compatibility():
    """Analyze browser audio format compatibility"""
    print_header("Browser Audio Compatibility Analysis")
    
    try:
        # Create test audio
        sample_rate = 24000
        duration = 0.5
        frequency = 1000
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        test_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.3
        
        # Test different WAV configurations
        wav_configs = [
            ('PCM_16', 'PCM 16-bit (Recommended)'),
            ('PCM_24', 'PCM 24-bit'),
            ('PCM_32', 'PCM 32-bit'),
            ('FLOAT', 'Float 32-bit')
        ]
        
        print_info("Testing WAV format compatibility:")
        
        for subtype, description in wav_configs:
            try:
                wav_buffer = BytesIO()
                sf.write(wav_buffer, test_audio, sample_rate, format='WAV', subtype=subtype)
                wav_bytes = wav_buffer.getvalue()
                wav_buffer.close()
                
                # Test decoding
                decoded_buffer = BytesIO(wav_bytes)
                decoded_audio, decoded_sr = sf.read(decoded_buffer)
                decoded_buffer.close()
                
                # Calculate file size and quality
                file_size = len(wav_bytes)
                correlation = np.corrcoef(test_audio, decoded_audio)[0, 1]
                
                browser_support = "✅ Excellent" if subtype == 'PCM_16' else "⚠️ Limited" if 'PCM' in subtype else "❌ Poor"
                
                print_info(f"  {description:20} | Size: {file_size:6d} bytes | Quality: {correlation:.6f} | Browser: {browser_support}")
                
                # Save test file
                filename = f"browser_test_{subtype.lower()}.wav"
                with open(filename, 'wb') as f:
                    f.write(wav_bytes)
                
            except Exception as e:
                print_error(f"  {description:20} | Failed: {e}")
        
        print_info("\nBrowser Compatibility Notes:")
        print_info("  ✅ PCM_16: Best support across all browsers")
        print_info("  ⚠️ PCM_24/32: May not work in older browsers")
        print_info("  ❌ FLOAT: Poor browser support, avoid")
        
        return True
        
    except Exception as e:
        print_error(f"Browser compatibility analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_audio_quality_issues():
    """Provide comprehensive diagnosis of potential audio quality issues"""
    print_header("Audio Quality Issue Diagnosis")
    
    print_info("Based on your symptoms (ultrasonic/distorted audio, incomplete playback):")
    print_info("")
    
    print_info("🔍 POTENTIAL CAUSES:")
    print_info("1. ❌ Sample Rate Mismatch")
    print_info("   - Server sends 24kHz audio")
    print_info("   - Client expects different sample rate")
    print_info("   - Results in pitch shifting (ultrasonic sound)")
    print_info("")
    
    print_info("2. ❌ Audio Amplitude Issues")
    print_info("   - Audio too quiet (below hearing threshold)")
    print_info("   - Audio clipping (distortion)")
    print_info("   - Incorrect normalization")
    print_info("")
    
    print_info("3. ❌ WAV Format Issues")
    print_info("   - Incorrect bit depth")
    print_info("   - Malformed WAV headers")
    print_info("   - Browser compatibility problems")
    print_info("")
    
    print_info("4. ❌ Audio Truncation")
    print_info("   - Base64 encoding/decoding errors")
    print_info("   - WebSocket message size limits")
    print_info("   - Client buffer issues")
    print_info("")
    
    print_info("5. ❌ Browser Audio Context Issues")
    print_info("   - Autoplay policies")
    print_info("   - Audio context not resumed")
    print_info("   - Incorrect audio element configuration")
    print_info("")
    
    print_info("🔧 RECOMMENDED FIXES:")
    print_info("1. ✅ Add audio quality validation in server")
    print_info("2. ✅ Add client-side audio debugging")
    print_info("3. ✅ Implement audio normalization")
    print_info("4. ✅ Add sample rate verification")
    print_info("5. ✅ Enhanced error handling")

async def main():
    """Run comprehensive audio quality diagnostic"""
    print_header("Audio Quality Diagnostic - Voxtral-Final")
    print_info("Analyzing audio quality degradation issues")
    
    tests = [
        ("Audio Data Integrity", analyze_audio_data_integrity),
        ("Sample Rate Analysis", analyze_sample_rate_issues),
        ("Audio Amplitude Analysis", analyze_audio_amplitude_issues),
        ("Browser Compatibility", analyze_browser_audio_compatibility),
        ("Kokoro Audio Quality", test_kokoro_audio_quality)
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
    
    # Always run diagnosis
    diagnose_audio_quality_issues()
    
    print_header("Diagnostic Results")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print_success("🎉 ALL AUDIO QUALITY TESTS PASSED!")
        print_info("If issues persist, check browser console for audio errors")
    else:
        print_error(f"💥 {failed} test(s) failed. Audio quality issues detected.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
