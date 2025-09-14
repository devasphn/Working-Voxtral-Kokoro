#!/usr/bin/env python3
"""
Simple test for Orpheus-FastAPI integration
"""

import requests
import json
import sys

def test_orpheus_connection():
    """Test basic connection to Orpheus-FastAPI"""
    print("🧪 Testing Orpheus-FastAPI connection...")
    
    try:
        # Test models endpoint
        response = requests.get("http://localhost:1234/v1/models", timeout=10)
        if response.status_code == 200:
            print("✅ Orpheus-FastAPI server is running")
            return True
        else:
            print(f"⚠️ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Orpheus-FastAPI on port 1234")
        print("💡 Start with: ./start_orpheus_fastapi.sh")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_orpheus_completion():
    """Test text completion with Orpheus"""
    print("🧪 Testing Orpheus-FastAPI completion...")
    
    try:
        # Test with ऋतिका voice
        prompt = "ऋतिका: Hello, this is a test of the Orpheus TTS system."
        
        response = requests.post(
            "http://localhost:1234/v1/completions",
            json={
                "prompt": prompt,
                "max_tokens": 50,
                "temperature": 0.7,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated = result.get("choices", [{}])[0].get("text", "")
            print(f"✅ Completion successful: {generated[:100]}...")
            return True
        else:
            print(f"❌ Completion failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Completion test failed: {e}")
        return False

def main():
    print("🔧 Simple Orpheus-FastAPI Test")
    print("=" * 30)
    
    connection_ok = test_orpheus_connection()
    if not connection_ok:
        print("\n💥 Connection failed - start Orpheus-FastAPI first")
        return False
    
    completion_ok = test_orpheus_completion()
    
    if connection_ok and completion_ok:
        print("\n🎉 Orpheus-FastAPI is working!")
        print("🔗 Ready for Voxtral integration")
        return True
    else:
        print("\n⚠️ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)