#!/usr/bin/env python3
"""
Test Streaming System Integration
Verifies that the streaming Orpheus TTS integration works correctly
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_streaming_system():
    """Test the complete streaming system"""
    print("🧪 Testing Streaming Voxtral + Orpheus TTS System")
    print("=" * 60)
    
    try:
        # Test 1: Import streaming components
        print("1. Testing streaming imports...")
        
        try:
            from src.tts.orpheus_streaming_model import OrpheusStreamingModel
            print("   ✅ OrpheusStreamingModel imported")
        except ImportError as e:
            print(f"   ❌ OrpheusStreamingModel import failed: {e}")
            return False
        
        try:
            from src.tts.tts_service_streaming import TTSServiceStreaming
            print("   ✅ TTSServiceStreaming imported")
        except ImportError as e:
            print(f"   ❌ TTSServiceStreaming import failed: {e}")
            return False
        
        # Test 2: Check Orpheus TTS package
        print("\n2. Testing Orpheus TTS package...")
        try:
            from orpheus_tts import OrpheusModel
            print("   ✅ Orpheus TTS package available")
        except ImportError as e:
            print(f"   ❌ Orpheus TTS package not installed: {e}")
            print("   💡 Run: pip install orpheus-tts")
            return False
        
        # Test 3: Test CORRECT Orpheus initialization
        print("\n3. Testing CORRECT Orpheus model initialization...")
        try:
            print("   🧠 Using CORRECT initialization (exactly as in Flask example)")
            
            # Test the CORRECT initialization from your Flask example
            model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
            print("   ✅ CORRECT Orpheus model created successfully")
            
            # Clean up immediately to free memory
            del model
            
        except Exception as e:
            print(f"   ❌ CORRECT model initialization failed: {e}")
            print("   💡 Make sure you've set the environment variables:")
            print("      export VLLM_GPU_MEMORY_UTILIZATION=0.8")
            print("      export VLLM_MAX_MODEL_LEN=1024")
            print("      export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512")
            return False
        
        # Test 4: Test streaming model initialization
        print("\n4. Testing streaming model initialization...")
        try:
            streaming_model = OrpheusStreamingModel()
            success = await streaming_model.initialize()
            
            if success:
                print("   ✅ Streaming model initialized successfully")
                
                # Test streaming generation
                print("   🎵 Testing streaming generation...")
                chunk_count = 0
                total_bytes = 0
                
                async for chunk in streaming_model.generate_speech_stream(
                    "Hello, this is a streaming test.", 
                    "tara"
                ):
                    chunk_count += 1
                    total_bytes += len(chunk)
                    if chunk_count >= 5:  # Test first 5 chunks
                        break
                
                if chunk_count > 0:
                    print(f"   ✅ Generated {chunk_count} streaming chunks ({total_bytes} bytes)")
                else:
                    print("   ❌ No streaming chunks generated")
                    return False
                
                # Cleanup
                await streaming_model.cleanup()
                print("   ✅ Streaming model cleanup completed")
                
            else:
                print("   ❌ Streaming model initialization failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Streaming model test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Test streaming service
        print("\n5. Testing streaming TTS service...")
        try:
            from src.tts.tts_service_streaming import tts_service_streaming
            
            success = await tts_service_streaming.initialize()
            
            if success:
                print("   ✅ Streaming TTS service initialized successfully")
                
                # Test service generation
                audio_data = await tts_service_streaming.generate_speech(
                    "Testing the streaming service integration.", 
                    "tara"
                )
                
                if audio_data and len(audio_data) > 0:
                    print(f"   ✅ Service generated {len(audio_data)} bytes of audio")
                else:
                    print("   ❌ Service generated no audio data")
                    return False
                
                # Show service info
                info = tts_service_streaming.get_service_info()
                print(f"   📊 Service: {info['service_name']}, "
                      f"avg time: {info['average_generation_time_ms']:.1f}ms")
                
                # Cleanup
                await tts_service_streaming.cleanup()
                print("   ✅ Streaming service cleanup completed")
                
            else:
                print("   ❌ Streaming TTS service initialization failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Streaming service test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL STREAMING TESTS PASSED! System is ready!")
        print("\nNext steps:")
        print("1. Start the server: ./start_perfect.sh")
        print("2. Access UI: http://localhost:8000")
        print("3. Test streaming voice conversations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_streaming_system())
    sys.exit(0 if success else 1)