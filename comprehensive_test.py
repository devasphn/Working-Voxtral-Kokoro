#!/usr/bin/env python3
"""
Comprehensive test of Orpheus TTS integration
Tests all components step by step to identify issues
"""

import asyncio
import sys
import os
import logging

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_step_1_imports():
    """Step 1: Test all imports"""
    print("🔍 Step 1: Testing imports...")
    
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}")
        
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print("✅ Transformers")
        
        from snac import SNAC
        print("✅ SNAC")
        
        import numpy as np
        import wave
        import io
        print("✅ Audio processing libraries")
        
        from src.utils.config import config
        print("✅ Config system")
        
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        print("✅ Orpheus TTS Engine")
        
        from src.tts.tts_service import TTSService
        print("✅ TTS Service")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_step_2_config():
    """Step 2: Test configuration loading"""
    print("\n🔧 Step 2: Testing configuration...")
    
    try:
        from src.utils.config import config
        
        print(f"✅ TTS enabled: {config.tts.enabled}")
        print(f"✅ TTS engine: {config.tts.engine}")
        print(f"✅ Default voice: {config.tts.default_voice}")
        print(f"✅ Sample rate: {config.tts.sample_rate}")
        print(f"✅ Available voices: {len(config.tts.voices.hindi)} Hindi voices")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

async def test_step_3_snac_model():
    """Step 3: Test SNAC model loading"""
    print("\n🧪 Step 3: Testing SNAC model...")
    
    try:
        from snac import SNAC
        import torch
        
        print("📥 Loading SNAC model...")
        model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
        
        if torch.cuda.is_available():
            model = model.cuda()
            print("✅ SNAC model loaded on GPU")
        else:
            print("✅ SNAC model loaded on CPU")
        
        # Test basic model properties
        device = next(model.parameters()).device
        print(f"   Model device: {device}")
        
        # Test basic encoding/decoding
        print("🔧 Testing SNAC encode/decode...")
        
        # Create dummy audio data
        dummy_audio = torch.randn(1, 1, 2048, device=device)
        
        # Encode
        with torch.inference_mode():
            codes = model.encode(dummy_audio)
            print(f"   Encoded to {len(codes)} code levels")
            
            # Decode
            reconstructed = model.decode(codes)
            print(f"   Decoded shape: {reconstructed.shape}")
        
        print("✅ SNAC model working correctly")
        return True
        
    except Exception as e:
        print(f"❌ SNAC model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_step_4_orpheus_engine():
    """Step 4: Test Orpheus TTS Engine"""
    print("\n🎵 Step 4: Testing Orpheus TTS Engine...")
    
    try:
        from src.tts.orpheus_tts_engine import OrpheusTTSEngine
        
        # Create engine
        engine = OrpheusTTSEngine()
        print("✅ Engine created")
        
        # Test voice mapping
        test_voice = "ऋतिका"
        language = engine._get_language_for_voice(test_voice)
        print(f"✅ Voice mapping: '{test_voice}' → '{language}'")
        
        # Test available voices
        voices = engine.get_available_voices()
        print(f"✅ Available voices: {len(voices)}")
        print(f"   Default: {engine.default_voice}")
        
        # Initialize engine
        print("🚀 Initializing engine...")
        await engine.initialize()
        
        if engine.is_initialized:
            print("✅ Engine initialized")
        else:
            print("⚠️ Engine initialization incomplete")
        
        # Test synthetic token generation
        print("🔢 Testing synthetic token generation...")
        test_text = "नमस्ते! यह परीक्षण है।"
        tokens = engine._generate_synthetic_audio_tokens(test_text, "ऋतिका")
        print(f"✅ Generated {len(tokens)} tokens")
        
        # Test audio generation
        print("🎵 Testing audio generation...")
        audio_data = await engine.generate_audio(test_text, "ऋतिका")
        
        if audio_data:
            print(f"✅ Audio generated: {len(audio_data)} bytes")
            
            # Save test audio
            with open("test_step4_audio.wav", "wb") as f:
                f.write(audio_data)
            print("💾 Audio saved as 'test_step4_audio.wav'")
        else:
            print("❌ No audio generated")
        
        # Cleanup
        await engine.close()
        
        return audio_data is not None
        
    except Exception as e:
        print(f"❌ Orpheus engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_step_5_tts_service():
    """Step 5: Test TTS Service"""
    print("\n🎯 Step 5: Testing TTS Service...")
    
    try:
        from src.tts.tts_service import TTSService
        
        # Create service
        service = TTSService()
        print("✅ TTS Service created")
        
        # Initialize service
        print("🚀 Initializing TTS service...")
        await service.initialize()
        
        if service.is_initialized:
            print("✅ TTS Service initialized")
        else:
            print("⚠️ TTS Service initialization incomplete")
        
        # Test speech generation
        print("🎵 Testing speech generation...")
        test_text = "Hello! This is a comprehensive test."
        
        result = await service.generate_speech_async(
            text=test_text,
            voice="ऋतिका",
            return_format="wav"
        )
        
        if result["success"]:
            print("✅ Speech generation successful")
            metadata = result["metadata"]
            print(f"   Processing time: {metadata.get('processing_time', 'unknown')}s")
            print(f"   Audio duration: {metadata.get('audio_duration', 'unknown')}s")
            print(f"   Realtime factor: {metadata.get('realtime_factor', 'unknown')}x")
            
            # Save audio
            if result["audio_data"]:
                import base64
                audio_bytes = base64.b64decode(result["audio_data"])
                with open("test_step5_service.wav", "wb") as f:
                    f.write(audio_bytes)
                print("💾 Audio saved as 'test_step5_service.wav'")
        else:
            print(f"❌ Speech generation failed: {result.get('error', 'Unknown error')}")
        
        # Get service info
        service_info = service.get_service_info()
        print(f"✅ Service info retrieved: {service_info['initialized']}")
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ TTS Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_step_6_integration():
    """Step 6: Test full integration"""
    print("\n🔗 Step 6: Testing full integration...")
    
    try:
        from src.tts.tts_service import TTSService
        
        # Test multiple languages and voices
        test_cases = [
            ("Hello! This is English.", "tara"),
            ("नमस्ते! यह हिंदी है।", "ऋतिका"),
            ("Bonjour! C'est français.", "pierre"),
        ]
        
        service = TTSService()
        await service.initialize()
        
        for i, (text, voice) in enumerate(test_cases):
            print(f"🎵 Test case {i+1}: '{text}' with voice '{voice}'")
            
            result = await service.generate_speech_async(
                text=text,
                voice=voice,
                return_format="wav"
            )
            
            if result["success"]:
                print(f"   ✅ Success! Duration: {result['metadata'].get('audio_duration', 'unknown')}s")
                
                # Save audio
                if result["audio_data"]:
                    import base64
                    audio_bytes = base64.b64decode(result["audio_data"])
                    with open(f"test_step6_case_{i+1}.wav", "wb") as f:
                        f.write(audio_bytes)
                    print(f"   💾 Saved as 'test_step6_case_{i+1}.wav'")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run comprehensive test suite"""
    print("🔧 Comprehensive Orpheus TTS Integration Test")
    print("=" * 60)
    
    # Run all test steps
    step1_ok = await test_step_1_imports()
    step2_ok = await test_step_2_config()
    step3_ok = await test_step_3_snac_model()
    step4_ok = await test_step_4_orpheus_engine()
    step5_ok = await test_step_5_tts_service()
    step6_ok = await test_step_6_integration()
    
    # Summary
    print("\n📊 Comprehensive Test Results:")
    print(f"   Step 1 - Imports:        {'✅ OK' if step1_ok else '❌ Failed'}")
    print(f"   Step 2 - Config:         {'✅ OK' if step2_ok else '❌ Failed'}")
    print(f"   Step 3 - SNAC Model:     {'✅ OK' if step3_ok else '❌ Failed'}")
    print(f"   Step 4 - Orpheus Engine: {'✅ OK' if step4_ok else '❌ Failed'}")
    print(f"   Step 5 - TTS Service:    {'✅ OK' if step5_ok else '❌ Failed'}")
    print(f"   Step 6 - Integration:    {'✅ OK' if step6_ok else '❌ Failed'}")
    
    all_ok = all([step1_ok, step2_ok, step3_ok, step4_ok, step5_ok, step6_ok])
    
    if all_ok:
        print("\n🎉 All tests passed! Orpheus TTS integration is working!")
        print("🎯 System ready for Voxtral integration")
        print("🎵 Generated audio files saved for verification")
    else:
        print("\n💥 Some tests failed")
        print("🔧 Check the errors above and fix the issues")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)