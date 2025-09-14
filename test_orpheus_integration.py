#!/usr/bin/env python3
"""
Test script for complete Orpheus TTS integration
Tests both LLM server and SNAC model integration
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

async def test_llm_server():
    """Test LLM server connectivity"""
    print("🧪 Testing LLM server...")
    
    try:
        response = requests.get("http://localhost:8010/health", timeout=5)
        if response.status_code == 200:
            print("✅ LLM server is running")
            return True
        else:
            print(f"⚠️ LLM server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ LLM server not running on port 8010")
        print("💡 Start with: ./start_llm_server.sh")
        return False
    except Exception as e:
        print(f"❌ LLM server test failed: {e}")
        return False

async def test_orpheus_tts():
    """Test complete Orpheus TTS system"""
    print("🧪 Testing Orpheus TTS integration...")
    
    try:
        from src.tts.tts_service import TTSService
        
        # Initialize TTS service
        tts_service = TTSService()
        await tts_service.initialize()
        
        if not tts_service.is_initialized:
            print("❌ TTS service failed to initialize")
            return False
        
        print("✅ TTS service initialized")
        
        # Test with ऋतिका voice
        test_text = "नमस्ते! यह ऋतिका की आवाज़ का परीक्षण है।"  # Hindi text for ऋतिका voice
        print(f"🎵 Testing with text: '{test_text}'")
        
        result = await tts_service.generate_speech_async(
            text=test_text,
            voice="ऋतिका",
            return_format="wav"
        )
        
        if result["success"]:
            audio_data = result["audio_data"]
            metadata = result["metadata"]
            
            print("✅ Orpheus TTS generation successful!")
            print(f"   🎯 Voice: ऋतिका")
            print(f"   📊 Audio duration: {metadata.get('audio_duration', 'unknown')}s")
            print(f"   ⏱️  Processing time: {metadata.get('processing_time', 'unknown')}s")
            print(f"   🔢 Audio data length: {len(audio_data) if audio_data else 0} chars (base64)")
            
            # Save test audio
            if audio_data:
                import base64
                with open("test_orpheus_output.wav", "wb") as f:
                    f.write(base64.b64decode(audio_data))
                print("💾 Test audio saved as 'test_orpheus_output.wav'")
            
            return True
        else:
            print(f"❌ Orpheus TTS generation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Orpheus TTS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_extraction():
    """Test token extraction from LLM output"""
    print("🧪 Testing token extraction...")
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        engine = OrpheusTTSEngine()
        
        # Test token extraction
        test_output = "ऋतिका: <custom_token_1234> Hello <custom_token_5678> world <custom_token_9012>"
        tokens = engine._extract_tokens_from_text(test_output)
        
        print(f"📝 Test output: {test_output}")
        print(f"🔢 Extracted tokens: {tokens}")
        
        if tokens:
            print("✅ Token extraction working")
            return True
        else:
            print("⚠️ No tokens extracted")
            return False
            
    except Exception as e:
        print(f"❌ Token extraction test failed: {e}")
        return False

async def main():
    """Run all Orpheus TTS tests"""
    print("🔧 Orpheus TTS Integration Test")
    print("=" * 40)
    
    # Test individual components
    llm_ok = await test_llm_server()
    print()
    
    token_ok = await test_token_extraction()
    print()
    
    tts_ok = await test_orpheus_tts()
    print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   LLM Server:     {'✅ Working' if llm_ok else '❌ Failed'}")
    print(f"   Token Extract:  {'✅ Working' if token_ok else '❌ Failed'}")
    print(f"   Orpheus TTS:    {'✅ Working' if tts_ok else '❌ Failed'}")
    
    if llm_ok and tts_ok:
        print("\n🎉 Orpheus TTS integration is working!")
        print("🎯 The system will use:")
        print("   1. LLM server for token generation")
        print("   2. SNAC model for audio conversion")
        print("   3. ऋतिका voice as default")
        return True
    elif tts_ok:
        print("\n⚠️ TTS is working but using fallback (espeak-ng)")
        print("💡 Start LLM server for full Orpheus TTS: ./start_llm_server.sh")
        return True
    else:
        print("\n💥 Orpheus TTS integration failed")
        print("🔧 Check the setup and try again")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)