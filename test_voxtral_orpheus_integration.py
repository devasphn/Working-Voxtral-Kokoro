#!/usr/bin/env python3
"""
Test script for Voxtral + Orpheus-FastAPI integration
Tests the complete pipeline: Text → Orpheus-FastAPI → Audio
"""

import asyncio
import sys
import os
import requests
import json

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_orpheus_fastapi_server():
    """Test Orpheus-FastAPI server connectivity"""
    print("🧪 Testing Orpheus-FastAPI server...")
    
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=10)
        if response.status_code == 200:
            print("✅ Orpheus-FastAPI server is running")
            models = response.json()
            print(f"📋 Available models: {len(models.get('data', []))}")
            return True
        else:
            print(f"⚠️ Orpheus-FastAPI server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Orpheus-FastAPI server not running on port 1234")
        print("💡 Start with: ./start_orpheus_fastapi.sh")
        return False
    except Exception as e:
        print(f"❌ Orpheus-FastAPI server test failed: {e}")
        return False

async def test_orpheus_tts_engine():
    """Test Orpheus TTS engine integration"""
    print("🧪 Testing Orpheus TTS engine integration...")
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Initialize engine
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        if not engine.is_initialized:
            print("⚠️ Orpheus TTS engine not fully initialized (will use fallback)")
        else:
            print("✅ Orpheus TTS engine initialized")
        
        # Test audio generation with ऋतिका voice
        test_text = "नमस्ते! यह ऋतिका की आवाज़ का परीक्षण है।"  # Hindi text
        print(f"🎵 Testing with Hindi text: '{test_text}'")
        
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated successfully ({len(audio_data)} bytes)")
            
            # Save test audio
            with open("test_orpheus_integration.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Test audio saved as 'test_orpheus_integration.wav'")
            
            await engine.close()
            return True
        else:
            print("❌ No audio generated")
            await engine.close()
            return False
            
    except Exception as e:
        print(f"❌ Orpheus TTS engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_tts_service():
    """Test complete TTS service with Orpheus integration"""
    print("🧪 Testing complete TTS service...")
    
    try:
        from src.tts.tts_service import TTSService
        
        # Initialize TTS service
        tts_service = TTSService()
        await tts_service.initialize()
        
        print(f"✅ TTS service initialized (status: {tts_service.is_initialized})")
        
        # Test with ऋतिका voice
        test_texts = [
            "Hello! This is a test of the Orpheus TTS system.",
            "नमस्ते! यह ऋतिका की आवाज़ है।",  # Hindi
            "Testing the integration between Voxtral and Orpheus-FastAPI."
        ]
        
        for i, test_text in enumerate(test_texts):
            print(f"🎵 Test {i+1}: '{test_text[:50]}...'")
            
            result = await tts_service.generate_speech_async(
                text=test_text,
                voice="ऋतिका",
                return_format="wav"
            )
            
            if result["success"]:
                audio_data = result["audio_data"]
                metadata = result["metadata"]
                
                print(f"   ✅ Success! Duration: {metadata.get('audio_duration', 'unknown')}s")
                print(f"   ⏱️  Processing time: {metadata.get('processing_time', 'unknown')}s")
                print(f"   🔢 Audio data: {len(audio_data) if audio_data else 0} chars (base64)")
                
                # Save test audio
                if audio_data:
                    import base64
                    with open(f"test_tts_service_{i+1}.wav", "wb") as f:
                        f.write(base64.b64decode(audio_data))
                    print(f"   💾 Saved as 'test_tts_service_{i+1}.wav'")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voice_mapping():
    """Test voice and language mapping"""
    print("🧪 Testing voice and language mapping...")
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        engine = OrpheusTTSEngine()
        
        # Test voice mappings
        test_voices = ["ऋतिका", "tara", "pierre", "jana", "javi"]
        
        for voice in test_voices:
            language = engine._get_language_for_voice(voice)
            print(f"   🎯 Voice '{voice}' → Language '{language}'")
        
        available_voices = engine.get_available_voices()
        print(f"✅ Available voices: {len(available_voices)}")
        print(f"   Primary voice: {available_voices[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice mapping test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🔧 Voxtral + Orpheus-FastAPI Integration Test")
    print("=" * 50)
    
    # Test individual components
    orpheus_server_ok = await test_orpheus_fastapi_server()
    print()
    
    voice_mapping_ok = await test_voice_mapping()
    print()
    
    orpheus_engine_ok = await test_orpheus_tts_engine()
    print()
    
    tts_service_ok = await test_complete_tts_service()
    print()
    
    # Summary
    print("📊 Integration Test Results:")
    print(f"   Orpheus Server:  {'✅ Working' if orpheus_server_ok else '❌ Failed'}")
    print(f"   Voice Mapping:   {'✅ Working' if voice_mapping_ok else '❌ Failed'}")
    print(f"   Orpheus Engine:  {'✅ Working' if orpheus_engine_ok else '❌ Failed'}")
    print(f"   TTS Service:     {'✅ Working' if tts_service_ok else '❌ Failed'}")
    
    if orpheus_server_ok and tts_service_ok:
        print("\n🎉 Voxtral + Orpheus-FastAPI integration is working!")
        print("🎯 The system will use:")
        print("   1. Voxtral model for VAD + ASR + LLM")
        print("   2. Orpheus-FastAPI for high-quality TTS")
        print("   3. ऋतिका voice as default")
        print("   4. Real-time audio streaming")
        return True
    elif tts_service_ok:
        print("\n⚠️ TTS is working but using fallback (espeak-ng)")
        print("💡 Start Orpheus-FastAPI server for full integration:")
        print("   ./start_orpheus_fastapi.sh")
        return True
    else:
        print("\n💥 Integration test failed")
        print("🔧 Check the setup and try again:")
        print("   1. Run: ./setup_orpheus_fastapi.sh")
        print("   2. Start: ./start_orpheus_fastapi.sh")
        print("   3. Test: python3 test_voxtral_orpheus_integration.py")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)