#!/usr/bin/env python3
"""
Simple test of current Orpheus TTS implementation
Tests the direct integration without external servers
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_orpheus_engine():
    """Test the Orpheus TTS engine directly"""
    print("🧪 Testing Orpheus TTS Engine (Direct Integration)")
    print("=" * 50)
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Initialize engine
        print("🚀 Initializing Orpheus TTS Engine...")
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        if engine.is_initialized:
            print("✅ Engine initialized successfully")
        else:
            print("⚠️ Engine initialization incomplete")
        
        # Test voice mapping
        print("\n🎯 Testing voice mapping:")
        test_voices = ["ऋतिका", "tara", "pierre"]
        for voice in test_voices:
            language = engine._get_language_for_voice(voice)
            print(f"   Voice '{voice}' → Language '{language}'")
        
        # Test audio generation
        print("\n🎵 Testing audio generation:")
        test_text = "नमस्ते! यह ऋतिका की आवाज़ का परीक्षण है।"
        print(f"   Text: '{test_text}'")
        print(f"   Voice: ऋतिका")
        
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated: {len(audio_data)} bytes")
            
            # Save test audio
            with open("test_orpheus_direct.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Audio saved as 'test_orpheus_direct.wav'")
            
            # Test with English text
            english_text = "Hello! This is a test of the Orpheus TTS system."
            print(f"\n🎵 Testing with English text: '{english_text}'")
            
            audio_data_en = await engine.generate_audio(english_text, "tara")
            if audio_data_en:
                print(f"✅ English audio generated: {len(audio_data_en)} bytes")
                with open("test_orpheus_english.wav", "wb") as f:
                    f.write(audio_data_en)
                print("💾 English audio saved as 'test_orpheus_english.wav'")
            else:
                print("❌ English audio generation failed")
        else:
            print("❌ Audio generation failed")
        
        # Get model info
        print("\n📊 Model Information:")
        model_info = engine.get_model_info()
        for key, value in model_info.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        await engine.close()
        print("\n🧹 Engine cleanup completed")
        
        return audio_data is not None
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tts_service():
    """Test the TTS service integration"""
    print("\n🧪 Testing TTS Service Integration")
    print("=" * 50)
    
    try:
        from src.tts.tts_service import TTSService
        
        # Initialize service
        print("🚀 Initializing TTS Service...")
        service = TTSService()
        await service.initialize()
        
        if service.is_initialized:
            print("✅ TTS Service initialized successfully")
        else:
            print("⚠️ TTS Service initialization incomplete")
        
        # Test speech generation
        print("\n🎵 Testing speech generation:")
        test_text = "Hello! This is a test of the TTS service integration."
        
        result = await service.generate_speech_async(
            text=test_text,
            voice="ऋतिका",
            return_format="wav"
        )
        
        if result["success"]:
            print("✅ Speech generation successful")
            print(f"   Processing time: {result['metadata'].get('processing_time', 'unknown')}s")
            print(f"   Audio duration: {result['metadata'].get('audio_duration', 'unknown')}s")
            print(f"   Realtime factor: {result['metadata'].get('realtime_factor', 'unknown')}x")
            
            # Save audio if available
            if result["audio_data"]:
                import base64
                audio_bytes = base64.b64decode(result["audio_data"])
                with open("test_tts_service.wav", "wb") as f:
                    f.write(audio_bytes)
                print("💾 Audio saved as 'test_tts_service.wav'")
        else:
            print(f"❌ Speech generation failed: {result.get('error', 'Unknown error')}")
        
        # Get service info
        print("\n📊 Service Information:")
        service_info = service.get_service_info()
        print(f"   Service initialized: {service_info['initialized']}")
        print(f"   Default voice: {service_info['configuration']['default_voice']}")
        print(f"   Available voices: {len(service.get_available_voices())}")
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ TTS Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🔧 Orpheus TTS Direct Integration Test")
    print("=" * 60)
    
    # Test engine directly
    engine_ok = await test_orpheus_engine()
    
    # Test service integration
    service_ok = await test_tts_service()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print(f"   Orpheus Engine:  {'✅ Working' if engine_ok else '❌ Failed'}")
    print(f"   TTS Service:     {'✅ Working' if service_ok else '❌ Failed'}")
    
    if engine_ok and service_ok:
        print("\n🎉 Orpheus TTS Direct Integration is working!")
        print("🎯 Ready for Voxtral integration")
        return True
    else:
        print("\n💥 Integration test failed")
        print("🔧 Check the implementation and try again")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)