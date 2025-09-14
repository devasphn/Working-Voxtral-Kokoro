#!/usr/bin/env python3
"""
Check the Orpheus model details and capabilities
"""

import requests
import json
import sys
import os

def check_orpheus_model():
    """Check Orpheus model details"""
    server_url = "http://localhost:1234"
    model_path = "/workspace/models/Orpheus-3b-FT-Q8_0.gguf"
    
    print("🔍 Checking Orpheus Model Details")
    print("=" * 50)
    
    # Check if model file exists
    print("📁 Model file check:")
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        print(f"✅ Model file exists: {model_path}")
        print(f"📊 File size: {file_size / (1024**3):.2f} GB")
    else:
        print(f"❌ Model file not found: {model_path}")
        return False
    
    # Check server model info
    print("\n🌐 Server model info:")
    try:
        response = requests.get(f"{server_url}/v1/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print("✅ Server responding")
            
            if "data" in models and models["data"]:
                for model in models["data"]:
                    print(f"   Model ID: {model.get('id', 'unknown')}")
                    print(f"   Object: {model.get('object', 'unknown')}")
                    print(f"   Created: {model.get('created', 'unknown')}")
                    print(f"   Owned by: {model.get('owned_by', 'unknown')}")
            else:
                print("⚠️ No model data in response")
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connection error: {e}")
        return False
    
    # Test model capabilities
    print("\n🧪 Testing model capabilities:")
    
    # Test 1: Basic completion
    print("\n1. Basic text completion:")
    try:
        payload = {
            "prompt": "The weather today is",
            "max_tokens": 20,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{server_url}/v1/completions",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                text = result["choices"][0].get("text", "")
                print(f"   ✅ Basic completion works: '{text.strip()}'")
            else:
                print("   ❌ No completion generated")
        else:
            print(f"   ❌ Completion failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: TTS-style prompt
    print("\n2. TTS-style prompt:")
    try:
        payload = {
            "prompt": "ऋतिका: नमस्ते, मैं ऋतिका हूँ।",
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{server_url}/v1/completions",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                text = result["choices"][0].get("text", "")
                print(f"   ✅ TTS prompt works: '{text.strip()}'")
                
                # Check if it looks like TTS output
                if any(indicator in text.lower() for indicator in ["<", ">", "token", "audio"]):
                    print("   🎵 Response contains TTS-like markers")
                else:
                    print("   ℹ️ Response looks like regular text")
            else:
                print("   ❌ No TTS completion generated")
        else:
            print(f"   ❌ TTS prompt failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check tokenizer
    print("\n3. Tokenizer test:")
    try:
        # Try to get tokenizer info if available
        response = requests.post(
            f"{server_url}/v1/completions",
            json={
                "prompt": "Test",
                "max_tokens": 0,  # Just tokenize, don't generate
                "echo": True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "usage" in result:
                usage = result["usage"]
                print(f"   ✅ Tokenizer working - Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            else:
                print("   ℹ️ No usage info available")
        else:
            print(f"   ⚠️ Tokenizer test inconclusive: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Tokenizer error: {e}")
    
    print("\n📋 Summary:")
    print("   - Model file is loaded and server is responding")
    print("   - Test different prompt formats to find TTS generation")
    print("   - The model might need specific prompting to generate TTS tokens")
    print("   - Consider checking the original Orpheus-FastAPI repository for correct usage")
    
    return True

if __name__ == "__main__":
    success = check_orpheus_model()
    sys.exit(0 if success else 1)