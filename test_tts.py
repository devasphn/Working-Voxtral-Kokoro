#!/usr/bin/env python3
"""
Simple TTS test script to verify audio generation is working
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.tts.tts_service import TTSService

async def test_tts():
    """Test TTS functionality"""
    print("🧪 Testing TTS Service...")
    
    try:
        # Initialize TTS service
        tts_service = TTSService()
        print("✅ TTS Service created")
        
        # Initialize the service
        await tts_service.initialize()
        print("✅ TTS Service initialized")
        
        # Test text
        test_text = "Hello! This is a test of the text-to-speech system."
        print(f"🎵 Generating speech for: '{test_text}'")
        
        # Generate speech
        result = await tts_service.generate_speech_async(
            text=test_text,
            voice="tara",
            return_format="wav"
        )
        
        if result["success"]:
            audio_data = result["audio_data"]
            metadata = result["metadata"]
            
            print("✅ TTS Generation successful!")
            print(f"   📊 Audio duration: {metadata.get('audio_duration', 'unknown')}s")
            print(f"   ⏱️  Processing time: {metadata.get('processing_time', 'unknown')}s")
            print(f"   🔢 Audio data length: {len(audio_data) if audio_data else 0} chars (base64)")
            
            # Save test audio file
            if audio_data:
                import base64
                with open("test_tts_output.wav", "wb") as f:
                    f.write(base64.b64decode(audio_data))
                print("💾 Test audio saved as 'test_tts_output.wav'")
                
            return True
        else:
            print(f"❌ TTS Generation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ TTS Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tts())
    if success:
        print("\n🎉 TTS Test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 TTS Test FAILED!")
        sys.exit(1)