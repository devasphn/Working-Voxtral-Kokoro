#!/usr/bin/env python3
"""
Test script to verify VAD thresholds are properly calibrated for normal speech
"""
import sys
import os
sys.path.append('.')

from src.models.audio_processor_realtime import AudioProcessor
from src.models.voxtral_model_realtime import VoxtralModel
import numpy as np

def test_vad_calibration():
    """Test VAD with speech levels matching user's actual audio (RMS ~0.032-0.033)"""
    print("🧪 Testing VAD Calibration for Normal Speech Levels")
    print("=" * 60)
    
    # Initialize processors
    audio_processor = AudioProcessor()
    
    print(f"📊 AudioProcessor VAD Settings:")
    print(f"   RMS Threshold: {audio_processor.vad_threshold}")
    print(f"   Energy Threshold: {audio_processor.energy_threshold}")
    print(f"   Spectral Centroid Threshold: {audio_processor.spectral_centroid_threshold}")
    print()
    
    # Test with user's actual speech levels
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create speech-like signal with user's RMS level (0.032-0.033)
    speech_signal = np.sin(2 * np.pi * 200 * t) * (1 + 0.3 * np.sin(2 * np.pi * 8 * t))
    speech_signal = speech_signal * 0.033  # Scale to user's RMS level
    
    actual_rms = np.sqrt(np.mean(speech_signal ** 2))
    max_amplitude = np.max(np.abs(speech_signal))
    
    print(f"🎙️ Test Speech Signal:")
    print(f"   RMS Energy: {actual_rms:.6f}")
    print(f"   Max Amplitude: {max_amplitude:.6f}")
    print(f"   Duration: {duration}s")
    print()
    
    # Test AudioProcessor VAD
    print("🔍 AudioProcessor VAD Test:")
    vad_result = audio_processor.detect_voice_activity(speech_signal, chunk_id="test_speech")
    
    print(f"   RMS Check: {actual_rms:.6f} > {audio_processor.vad_threshold} = {actual_rms > audio_processor.vad_threshold}")
    print(f"   Max Amplitude Check: {max_amplitude:.6f} > 0.005 = {max_amplitude > 0.005}")
    print(f"   VAD Result: {'✅ VOICE DETECTED' if vad_result['has_voice'] else '❌ SILENCE DETECTED'}")
    print(f"   Confidence: {vad_result['confidence']:.3f}")
    print()
    
    # Test validation (which includes VAD)
    print("🔍 AudioProcessor Validation Test:")
    is_valid = audio_processor.validate_realtime_chunk(speech_signal, chunk_id="test_validation")
    print(f"   Validation Result: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print()
    
    # Test with Voxtral model thresholds
    print("🔍 Voxtral Model VAD Test:")
    voxtral_model = VoxtralModel()
    print(f"   Voxtral Silence Threshold: {voxtral_model.silence_threshold}")
    print(f"   RMS Check: {actual_rms:.6f} > {voxtral_model.silence_threshold} = {actual_rms > voxtral_model.silence_threshold}")
    
    # Test Voxtral's speech detection
    speech_detected = voxtral_model._is_speech_detected(speech_signal, duration)
    print(f"   Voxtral Speech Detection: {'✅ SPEECH DETECTED' if speech_detected else '❌ SILENCE DETECTED'}")
    print()
    
    # Summary
    print("📋 SUMMARY:")
    print(f"   AudioProcessor VAD: {'✅ PASS' if vad_result['has_voice'] else '❌ FAIL'}")
    print(f"   AudioProcessor Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"   Voxtral Speech Detection: {'✅ PASS' if speech_detected else '❌ FAIL'}")
    print()
    
    if vad_result['has_voice'] and is_valid and speech_detected:
        print("🎉 ALL TESTS PASSED! Normal speech will be detected correctly.")
        return True
    else:
        print("❌ TESTS FAILED! VAD thresholds need further adjustment.")
        return False

if __name__ == "__main__":
    test_vad_calibration()
