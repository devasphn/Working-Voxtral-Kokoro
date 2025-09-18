#!/usr/bin/env python3
"""
Test script for Speech-to-Speech functionality
Tests the complete pipeline: Audio Input → Voxtral → LLM → Kokoro TTS → Audio Output
"""
import asyncio
import numpy as np
import soundfile as sf
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.models.speech_to_speech_pipeline import speech_to_speech_pipeline
from src.utils.config import config

async def test_speech_to_speech_pipeline():
    """Test the complete speech-to-speech pipeline"""
    print("🧪 Testing Speech-to-Speech Pipeline")
    print("=" * 50)
    
    try:
        # Initialize the pipeline
        print("🚀 Initializing Speech-to-Speech pipeline...")
        await speech_to_speech_pipeline.initialize()
        print("✅ Pipeline initialized successfully")
        
        # Create test audio (simple sine wave representing speech)
        print("\n🎵 Generating test audio...")
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a more speech-like signal with amplitude modulation
        carrier = np.sin(2 * np.pi * frequency * t)
        modulation = 0.5 * (1 + np.sin(2 * np.pi * 5 * t))  # 5 Hz modulation
        test_audio = (carrier * modulation * 0.1).astype(np.float32)
        
        # Save test input audio
        sf.write('test_input_audio.wav', test_audio, sample_rate)
        print(f"   📁 Test input saved as test_input_audio.wav ({duration}s, {sample_rate}Hz)")
        
        # Process through the pipeline
        print("\n🔄 Processing through Speech-to-Speech pipeline...")
        start_time = time.time()
        
        result = await speech_to_speech_pipeline.process_conversation_turn(
            test_audio,
            conversation_id="test_pipeline_001",
            voice_preference="af_heart",
            speed_preference=1.0
        )
        
        total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        print(f"\n📊 Pipeline Results:")
        print(f"   ⏱️  Total processing time: {total_time:.1f}ms")
        print(f"   🎯 Target latency: {config.speech_to_speech.latency_target_ms}ms")
        print(f"   {'✅' if total_time <= config.speech_to_speech.latency_target_ms else '⚠️'} Latency target {'met' if total_time <= config.speech_to_speech.latency_target_ms else 'exceeded'}")
        print(f"   🔄 Success: {result['success']}")
        
        if result['success']:
            print(f"\n📝 Transcription: '{result['transcription']}'")
            print(f"💭 AI Response: '{result['response_text']}'")
            
            if len(result['response_audio']) > 0:
                # Save response audio
                sf.write('test_output_audio.wav', result['response_audio'], result['sample_rate'])
                audio_duration = len(result['response_audio']) / result['sample_rate']
                print(f"🔊 Response audio: {len(result['response_audio'])} samples ({audio_duration:.2f}s)")
                print(f"   📁 Response audio saved as test_output_audio.wav")
                print(f"   🎤 Voice used: {result.get('voice_used', 'unknown')}")
                print(f"   ⚡ Speed used: {result.get('speed_used', 'unknown')}")
            else:
                print("⚠️  No response audio generated")
            
            # Stage timing breakdown
            if 'stage_timings' in result:
                timings = result['stage_timings']
                print(f"\n⏱️  Stage Timings:")
                print(f"   🎤 Speech-to-Text: {timings.get('stt_ms', 0):.1f}ms")
                print(f"   🧠 LLM Processing: {timings.get('llm_ms', 0):.1f}ms")
                print(f"   🗣️  Text-to-Speech: {timings.get('tts_ms', 0):.1f}ms")
            
            # Performance stats
            if 'performance_stats' in result:
                stats = result['performance_stats']
                print(f"\n📈 Performance Stats:")
                print(f"   🎯 Meets target: {stats.get('meets_target', False)}")
                if 'real_time_factor' in stats:
                    print(f"   ⚡ Real-time factor: {stats['real_time_factor']:.2f}")
        else:
            print(f"❌ Pipeline failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test pipeline info
        print(f"\n📋 Pipeline Information:")
        pipeline_info = speech_to_speech_pipeline.get_pipeline_info()
        print(f"   🔄 Initialized: {pipeline_info['is_initialized']}")
        print(f"   💬 Total conversations: {pipeline_info['total_conversations']}")
        print(f"   🎭 Emotional TTS: {pipeline_info['emotional_tts_enabled']}")
        
        if 'performance_stats' in pipeline_info:
            perf = pipeline_info['performance_stats']
            print(f"   📊 Avg latency: {perf['avg_total_latency_ms']:.1f}ms")
            print(f"   🎯 Target met rate: {perf['target_met_rate_percent']:.1f}%")
        
        print(f"\n🎉 Speech-to-Speech pipeline test completed successfully!")
        print(f"🔊 Play test_output_audio.wav to hear the AI response")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return False

async def test_individual_components():
    """Test individual components separately"""
    print("\n🔧 Testing Individual Components")
    print("=" * 50)
    
    try:
        # Test Kokoro TTS directly
        print("🎵 Testing Kokoro TTS...")
        from src.models.kokoro_model_realtime import kokoro_model
        
        await kokoro_model.initialize()
        
        test_text = "Hello, this is a test of the Kokoro text-to-speech system."
        tts_result = await kokoro_model.synthesize_speech(test_text, chunk_id="component_test")
        
        if tts_result['success']:
            print(f"   ✅ TTS test successful: {tts_result['synthesis_time_ms']:.1f}ms")
            if len(tts_result['audio_data']) > 0:
                sf.write('test_tts_only.wav', tts_result['audio_data'], tts_result['sample_rate'])
                print(f"   📁 TTS-only audio saved as test_tts_only.wav")
        else:
            print(f"   ❌ TTS test failed: {tts_result.get('error', 'Unknown error')}")
            return False
        
        # Test Voxtral STT
        print("\n🎤 Testing Voxtral STT...")
        from src.models.voxtral_model_realtime import voxtral_model
        from src.models.audio_processor_realtime import AudioProcessor
        
        if not voxtral_model.is_initialized:
            await voxtral_model.initialize()
        
        audio_processor = AudioProcessor()
        
        # Create test audio
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.1
        
        audio_tensor = audio_processor.preprocess_realtime_chunk(test_audio, chunk_id="stt_test")
        stt_result = await voxtral_model.process_realtime_chunk(
            audio_tensor,
            chunk_id="stt_test",
            mode="conversation"
        )
        
        if stt_result['success']:
            print(f"   ✅ STT test successful: {stt_result['processing_time_ms']:.1f}ms")
            print(f"   📝 Transcription: '{stt_result['response']}'")
        else:
            print(f"   ❌ STT test failed: {stt_result.get('error', 'Unknown error')}")
            return False
        
        print(f"\n✅ All individual components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return False

async def main():
    """Main test function"""
    print("🧪 Voxtral Speech-to-Speech System Test")
    print("=" * 60)
    
    # Test individual components first
    components_ok = await test_individual_components()
    
    if components_ok:
        # Test complete pipeline
        pipeline_ok = await test_speech_to_speech_pipeline()
        
        if pipeline_ok:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"🗣️ Speech-to-Speech conversational AI is working correctly!")
            print(f"\n📁 Generated files:")
            print(f"   - test_input_audio.wav (test input)")
            print(f"   - test_output_audio.wav (AI response)")
            print(f"   - test_tts_only.wav (TTS component test)")
        else:
            print(f"\n❌ Pipeline test failed")
            return 1
    else:
        print(f"\n❌ Component tests failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
