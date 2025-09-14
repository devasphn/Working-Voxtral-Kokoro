#!/usr/bin/env python3
"""
Test script for Orpheus-FastAPI server
"""

import requests
import json
import time
import sys

def test_orpheus_server():
    """Test if Orpheus-FastAPI server is responding"""
    server_url = "http://localhost:1234"
    
    print("🧪 Testing Orpheus-FastAPI server...")
    
    try:
        # Test health endpoint (if available)
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Orpheus-FastAPI server health check passed")
            else:
                print(f"⚠️ Health check returned: {response.status_code}")
        except requests.exceptions.RequestException:
            print("ℹ️ Health endpoint not available (normal for llama-cpp-python server)")
        
        # Test completion endpoint with TTS-style prompt
        test_text = "Hello, this is a test of the Orpheus TTS system."
        test_voice = "ऋतिका"
        
        # Format prompt for Orpheus TTS
        prompt = f"{test_voice}: {test_text}"
        
        print(f"🎯 Testing with prompt: '{prompt}'")
        
        response = requests.post(
            f"{server_url}/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": 100,
                "temperature": 0.7,
                "stream": False,
                "stop": ["<|eot_id|>", "\n\n"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("choices", [{}])[0].get("text", "")
            print("✅ Orpheus-FastAPI completion test successful")
            print(f"📝 Generated: {generated_text[:100]}...")
            
            # Check if it looks like TTS tokens
            if "<custom_token_" in generated_text or "audio" in generated_text.lower():
                print("🎵 Response contains TTS-like tokens - good!")
            else:
                print("ℹ️ Response doesn't contain obvious TTS tokens")
            
            return True
        else:
            print(f"❌ Orpheus-FastAPI completion test failed: {response.status_code}")
            try:
                error_text = response.text
                print(f"❌ Error details: {error_text}")
            except:
                pass
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Orpheus-FastAPI server on port 1234")
        print("💡 Make sure to start the server first: ./start_orpheus_fastapi.sh")
        return False
    except Exception as e:
        print(f"❌ Orpheus-FastAPI test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_orpheus_server()
    if success:
        print("\n🎉 Orpheus-FastAPI server is working!")
        print("🔗 Ready for integration with Voxtral system")
    else:
        print("\n💥 Orpheus-FastAPI server test failed")
        print("🔧 Check the server logs and try again")
    
    sys.exit(0 if success else 1)