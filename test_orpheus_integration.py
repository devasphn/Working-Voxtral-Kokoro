#!/usr/bin/env python3
"""
Simple test for Orpheus-FastAPI integration
Tests the HTTP server connection and TTS generation
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_orpheus_integration():
    """Test Orpheus-FastAPI integration"""
    print("🧪 Testing Orpheus-FastAPI Integration")
    print("=" * 50)
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        from src.tts.tts_service import TTSService
        
        # Test 1: Engine initialization
        print("🚀 Step 1: Testing engine initialization...")
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        if engine.is_initialized:
            print("✅ Engine initialized successfully")
        else:
            print("❌ Engine initialization failed")
            return False
        
        # Test 2: TTS Service
        print("\n🎵 Step 2: Testing TTS service...")
        service = TTSService()
        await service.initialize()
        
        if service.is_initialized:
            print("✅ TTS Service initialized successfully")
        else:
            print("❌ TTS Service initialization failed")
            return False
        
        # Test 3: Audio generation
        print("\n🎯 Step 3: Testing audio generation...")
        test_text = "Hello! This is a test of the Orpheus TTS system."
        
        result = await service.generate_speech_async(
            text=test_text,
            voice="ऋतिका",
            return_format="wav"
        )
        
        if result["success"]:
            print("✅ Audio generation successful!")
            print(f"   Processing time: {result['metadata'].get('processing_time', 'unknown')}s")
            print(f"   Audio duration: {result['metadata'].get('audio_duration', 'unknown')}s")
            
            # Save audio file
            if result["audio_data"]:
                import base64
                audio_bytes = base64.b64decode(result["audio_data"])
                with open("test_orpheus_output.wav", "wb") as f:
                    f.write(audio_bytes)
                print("💾 Audio saved as 'test_orpheus_output.wav'")
        else:
            print(f"❌ Audio generation failed: {result.get('error', 'Unknown error')}")
            return False
        
        print("\n🎉 All tests passed! Orpheus-FastAPI integration is working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_orpheus_integration())
    sys.exit(0 if success else 1)