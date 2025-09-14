#!/usr/bin/env python3
"""
Test the clean Orpheus TTS implementation
"""

import asyncio
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_clean_implementation():
    """Test the clean implementation"""
    print("🧪 Testing Clean Orpheus TTS Implementation")
    print("=" * 50)
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Initialize engine
        print("🚀 Initializing engine...")
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        if engine.is_initialized:
            print("✅ Engine initialized successfully")
        else:
            print("❌ Engine initialization failed")
            return False
        
        # Test audio generation
        print("\n🎵 Testing audio generation...")
        test_text = "Hello! This is a test of the clean Orpheus implementation."
        
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated: {len(audio_data)} bytes")
            
            # Save audio
            with open("test_clean_output.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Audio saved as 'test_clean_output.wav'")
        else:
            print("❌ Audio generation failed")
        
        # Test model info
        print("\n📊 Model info:")
        info = engine.get_model_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        await engine.close()
        
        print("\n🎉 Clean implementation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_clean_implementation())
    sys.exit(0 if success else 1)