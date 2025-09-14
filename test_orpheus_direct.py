#!/usr/bin/env python3
"""
Direct test of Orpheus-FastAPI server to understand the API format
"""

import requests
import json
import sys

def test_orpheus_direct():
    """Test Orpheus server directly to understand the API"""
    server_url = "http://localhost:1234"
    
    print("🧪 Testing Orpheus-FastAPI Server Direct API")
    print("=" * 50)
    
    # Test 1: Check models endpoint
    print("📋 Step 1: Testing models endpoint...")
    try:
        response = requests.get(f"{server_url}/v1/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print("✅ Models endpoint working")
            print(f"   Available models: {len(models.get('data', []))}")
            if models.get('data'):
                print(f"   First model: {models['data'][0].get('id', 'unknown')}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False
    
    # Test 2: Simple completion
    print("\n🎯 Step 2: Testing simple completion...")
    try:
        payload = {
            "prompt": "ऋतिका: Hello, this is a test.",
            "max_tokens": 100,
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(
            f"{server_url}/v1/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Simple completion working")
            if "choices" in result and result["choices"]:
                generated_text = result["choices"][0].get("text", "")
                print(f"   Generated: {generated_text[:100]}...")
                
                # Check if it contains TTS-like tokens
                if any(token in generated_text.lower() for token in ["<custom_token_", "audio", "token"]):
                    print("🎵 Response contains TTS-like tokens!")
                else:
                    print("ℹ️ Response doesn't contain obvious TTS tokens")
            else:
                print("⚠️ No choices in response")
        else:
            print(f"❌ Simple completion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple completion error: {e}")
        return False
    
    # Test 3: Test with different voices
    print("\n🎵 Step 3: Testing different voices...")
    voices = ["ऋतिका", "tara", "pierre"]
    
    for voice in voices:
        try:
            payload = {
                "prompt": f"{voice}: Hello, this is a test with {voice} voice.",
                "max_tokens": 50,
                "temperature": 0.7,
                "stream": False,
                "stop": ["\n", f"{voice}:"]
            }
            
            response = requests.post(
                f"{server_url}/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    generated_text = result["choices"][0].get("text", "").strip()
                    print(f"   ✅ {voice}: {generated_text[:50]}...")
                else:
                    print(f"   ⚠️ {voice}: No response")
            else:
                print(f"   ❌ {voice}: Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   ❌ {voice}: Error - {e}")
    
    print("\n🎉 Direct API test completed!")
    return True

if __name__ == "__main__":
    success = test_orpheus_direct()
    sys.exit(0 if success else 1)