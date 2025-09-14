#!/usr/bin/env python3
"""
Test the fixed Orpheus TTS integration
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_fixed_orpheus():
    """Test the fixed Orpheus TTS engine"""
    print("🧪 Testing Fixed Orpheus TTS Engine")
    print("=" * 40)
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Initialize engine
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        print(f"✅ Engine initialized: {engine.is_initialized}")
        print(f"🎯 Default voice: {engine.default_voice}")
        print(f"🔗 Server URL: {engine.orpheus_server_url}")
        
        # Test audio generation
        test_text = "Hello! This is a test of the fixed Orpheus TTS system."
        print(f"🎵 Testing with: '{test_text}'")
        
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated successfully ({len(audio_data)} bytes)")
            
            # Save test audio
            with open("test_fixed_orpheus.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Audio saved as 'test_fixed_orpheus.wav'")
            
            await engine.close()
            return True
        else:
            print("❌ No audio generated")
            await engine.close()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_orpheus())
    if success:
        print("\n🎉 Fixed Orpheus TTS is working!")
    else:
        print("\n💥 Test failed")
    sys.exit(0 if success else 1)