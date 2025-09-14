#!/usr/bin/env python3
"""
Test Orpheus-only TTS (no fallback)
"""

import asyncio
import sys
import os
import requests

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_orpheus_server():
    """Test if Orpheus server is responding correctly"""
    print("🧪 Testing Orpheus-FastAPI server...")
    
    try:
        # Test with the exact prompt format we're using
        prompt = "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nGenerate speech for the voice 'ऋतिका' saying: \"Hello world\"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nऋतिका: <|audio|>"
        
        response = requests.post(
            "http://localhost:1234/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": 1024,
                "temperature": 0.3,
                "stream": False,
                "stop": ["<|eot_id|>"],
                "top_p": 0.9,
                "repeat_penalty": 1.1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("choices", [{}])[0].get("text", "")
            
            print(f"✅ Orpheus server responded")
            print(f"📝 Generated text: {generated_text}")
            
            # Check for audio tokens
            import re
            patterns = [
                r'<custom_token_(\d+)>',
                r'<audio_token_(\d+)>',
                r'<token_(\d+)>',
                r'<(\d+)>',
                r'\[(\d+)\]',
                r'token_(\d+)',
            ]
            
            tokens_found = []
            for pattern in patterns:
                matches = re.findall(pattern, generated_text)
                tokens_found.extend(matches)
            
            if tokens_found:
                print(f"🎵 Found {len(tokens_found)} potential audio tokens: {tokens_found[:10]}")
                return True
            else:
                print("⚠️ No audio tokens found in response")
                print(f"🔍 Full response for analysis: {generated_text}")
                return False
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

async def test_orpheus_engine():
    """Test the Orpheus engine directly"""
    print("🧪 Testing Orpheus TTS Engine (no fallback)...")
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Initialize engine
        engine = OrpheusTTSEngine()
        await engine.initialize()
        
        if not engine.is_initialized:
            print("❌ Engine failed to initialize")
            return False
        
        print("✅ Engine initialized successfully")
        
        # Test audio generation
        test_text = "Hello! This is a test of Orpheus TTS."
        print(f"🎵 Testing with: '{test_text}'")
        
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated successfully ({len(audio_data)} bytes)")
            
            # Save test audio
            with open("test_orpheus_only.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Audio saved as 'test_orpheus_only.wav'")
            
            await engine.close()
            return True
        else:
            print("❌ No audio generated")
            await engine.close()
            return False
            
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run Orpheus-only tests"""
    print("🔧 Orpheus-Only TTS Test (No Fallback)")
    print("=" * 40)
    
    # Test server first
    server_ok = test_orpheus_server()
    print()
    
    if not server_ok:
        print("💥 Orpheus server test failed - check if server is running")
        return False
    
    # Test engine
    engine_ok = await test_orpheus_engine()
    
    if engine_ok:
        print("\n🎉 Orpheus-only TTS is working!")
        print("🎯 Real Orpheus audio generation successful")
        return True
    else:
        print("\n💥 Orpheus-only TTS failed")
        print("🔧 Check the Orpheus model and prompting")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)