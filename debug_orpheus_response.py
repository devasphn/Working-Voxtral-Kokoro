#!/usr/bin/env python3
"""
Debug script to see exactly what the Orpheus model is returning
"""

import requests
import json
import sys

def debug_orpheus_response():
    """Debug what Orpheus model actually returns"""
    server_url = "http://localhost:1234"
    
    print("🔍 Debugging Orpheus Model Response")
    print("=" * 50)
    
    # Test different prompt formats to see what works
    test_prompts = [
        # Format 1: Simple voice prompt
        "ऋतिका: Hello, this is a test.",
        
        # Format 2: Instruction format
        "Generate speech for the following text using voice 'ऋतिका': Hello, this is a test.",
        
        # Format 3: Chat format
        "<|start_header_id|>user<|end_header_id|>\n\nGenerate speech for the following text using voice 'ऋतिका': Hello, this is a test.<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        
        # Format 4: TTS specific format
        "[TTS] Voice: ऋतिका, Text: Hello, this is a test.",
        
        # Format 5: Direct instruction
        "Convert to speech with ऋतिका voice: Hello, this is a test."
    ]
    
    for i, prompt in enumerate(test_prompts):
        print(f"\n🧪 Test {i+1}: Testing prompt format...")
        print(f"📝 Prompt: {prompt[:100]}...")
        
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": 200,
                "temperature": 0.3,
                "stream": False,
                "stop": ["<|eot_id|>", "\n\n"]
            }
            
            response = requests.post(
                f"{server_url}/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    generated_text = result["choices"][0].get("text", "")
                    print(f"✅ Response length: {len(generated_text)} chars")
                    print(f"📄 Full response: '{generated_text}'")
                    
                    # Check for TTS indicators
                    tts_indicators = ["<custom_token_", "audio", "speech", "[AUDIO]", "<audio>", "token"]
                    found_indicators = [ind for ind in tts_indicators if ind.lower() in generated_text.lower()]
                    
                    if found_indicators:
                        print(f"🎵 TTS indicators found: {found_indicators}")
                    else:
                        print("ℹ️ No obvious TTS indicators found")
                    
                    # Check response metadata
                    if "usage" in result:
                        usage = result["usage"]
                        print(f"📊 Tokens - Prompt: {usage.get('prompt_tokens', 'N/A')}, Completion: {usage.get('completion_tokens', 'N/A')}")
                else:
                    print("❌ No choices in response")
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test with different parameters
    print(f"\n🔧 Testing with different parameters...")
    
    test_params = [
        {"temperature": 0.1, "top_p": 0.9, "max_tokens": 500},
        {"temperature": 0.7, "top_p": 0.95, "max_tokens": 1000},
        {"temperature": 1.0, "top_p": 1.0, "max_tokens": 100},
    ]
    
    base_prompt = "ऋतिका: Hello, this is a test of the TTS system."
    
    for i, params in enumerate(test_params):
        print(f"\n🎛️ Parameter test {i+1}: {params}")
        
        try:
            payload = {
                "prompt": base_prompt,
                "stream": False,
                "stop": ["<|eot_id|>"],
                **params
            }
            
            response = requests.post(
                f"{server_url}/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and result["choices"]:
                    generated_text = result["choices"][0].get("text", "")
                    print(f"   ✅ Length: {len(generated_text)}, Content: '{generated_text[:100]}...'")
                else:
                    print("   ❌ No response")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 Debug completed!")
    print("\n💡 Analysis:")
    print("   - Check which prompt format generates the longest/most useful response")
    print("   - Look for any TTS-specific tokens or patterns")
    print("   - Note if the model is generating text vs. special tokens")

if __name__ == "__main__":
    debug_orpheus_response()