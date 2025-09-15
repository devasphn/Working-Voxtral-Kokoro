#!/usr/bin/env python3
"""
Test Perfect System Integration
Verifies that all components work together correctly
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_perfect_system():
    """Test the complete perfect system"""
    print("🧪 Testing Perfect Voxtral + Orpheus TTS System")
    print("=" * 60)
    
    try:
        # Test 1: Import all components
        print("1. Testing imports...")
        
        try:
            from src.tts.orpheus_perfect_model import OrpheusPerfectModel
            print("   ✅ OrpheusPerfectModel imported")
        except ImportError as e:
            print(f"   ❌ OrpheusPerfectModel import failed: {e}")
            return False
        
        try:
            from src.tts.tts_service_perfect import TTSServicePerfect
            print("   ✅ TTSServicePerfect imported")
        except ImportError as e:
            print(f"   ❌ TTSServicePerfect import failed: {e}")
            return False
        
        try:
            from src.models.voxtral_model_realtime import VoxtralModel
            print("   ✅ VoxtralModel imported")
        except ImportError as e:
            print(f"   ❌ VoxtralModel import failed: {e}")
            return False
        
        # Test 2: Check Orpheus TTS package
        print("\n2. Testing Orpheus TTS package...")
        try:
            from orpheus_tts import OrpheusModel
            print("   ✅ Orpheus TTS package available")
        except ImportError as e:
            print(f"   ❌ Orpheus TTS package not installed: {e}")
            print("   💡 Run: pip install orpheus-tts")
            return False
        
        # Test 3: Initialize Orpheus Perfect Model
        print("\n3. Testing Orpheus Perfect Model initialization...")
        try:
            orpheus_model = OrpheusPerfectModel()
            success = await orpheus_model.initialize()
            
            if success:
                print("   ✅ Orpheus Perfect Model initialized successfully")
                
                # Test generation
                print("   🎵 Testing speech generation...")
                audio_data = await orpheus_model.generate_speech(
                    "Hello, this is a test of the perfect integration.", 
                    "tara"
                )
                
                if audio_data and len(audio_data) > 0:
                    print(f"   ✅ Generated {len(audio_data)} bytes of audio")
                else:
                    print("   ❌ No audio data generated")
                    return False
                
                # Cleanup
                await orpheus_model.cleanup()
                print("   ✅ Orpheus model cleanup completed")
                
            else:
                print("   ❌ Orpheus Perfect Model initialization failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Orpheus Perfect Model test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Test TTS Service
        print("\n4. Testing Perfect TTS Service...")
        try:
            tts_service = TTSServicePerfect()
            success = await tts_service.initialize()
            
            if success:
                print("   ✅ TTS Service initialized successfully")
                
                # Test generation through service
                audio_data = await tts_service.generate_speech(
                    "Testing the TTS service integration.", 
                    "tara"
                )
                
                if audio_data and len(audio_data) > 0:
                    print(f"   ✅ Service generated {len(audio_data)} bytes of audio")
                else:
                    print("   ❌ Service generated no audio data")
                    return False
                
                # Show service info
                info = tts_service.get_service_info()
                print(f"   📊 Service info: {info['service_name']}, "
                      f"avg time: {info['average_generation_time_ms']:.1f}ms")
                
                # Cleanup
                await tts_service.cleanup()
                print("   ✅ TTS Service cleanup completed")
                
            else:
                print("   ❌ TTS Service initialization failed")
                return False
                
        except Exception as e:
            print(f"   ❌ TTS Service test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Perfect system is ready!")
        print("\nNext steps:")
        print("1. Start the server: ./start_perfect.sh")
        print("2. Access UI: http://localhost:8000")
        print("3. Test voice conversations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_perfect_system())
    sys.exit(0 if success else 1)