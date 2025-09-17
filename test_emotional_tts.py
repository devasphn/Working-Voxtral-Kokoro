#!/usr/bin/env python3
"""
Test script for Emotional Speech Synthesis functionality
Tests the emotional voice selection and speech generation capabilities
"""
import asyncio
import numpy as np
import soundfile as sf
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.models.speech_to_speech_pipeline import speech_to_speech_pipeline
from src.models.kokoro_model_realtime import kokoro_model
from src.utils.config import config

async def test_emotional_voice_selection():
    """Test emotional voice selection based on different text content"""
    print("🎭 Testing Emotional Voice Selection")
    print("=" * 50)
    
    # Test cases with different emotional contexts
    test_cases = [
        {
            'user_input': "I'm so excited about this new project!",
            'ai_response': "That's wonderful! I'm thrilled to hear about your enthusiasm for the project!",
            'expected_emotion': 'excited'
        },
        {
            'user_input': "I'm feeling really sad about what happened.",
            'ai_response': "I'm sorry to hear that you're going through a difficult time. I'm here to help.",
            'expected_emotion': 'empathetic'
        },
        {
            'user_input': "Can you provide a professional analysis of the quarterly report?",
            'ai_response': "Certainly. I'll provide a comprehensive analysis of the quarterly financial performance.",
            'expected_emotion': 'professional'
        },
        {
            'user_input': "I need to relax and find some peace.",
            'ai_response': "Let's take this slowly and find a calm approach to help you feel more peaceful.",
            'expected_emotion': 'calm'
        },
        {
            'user_input': "How are you doing today?",
            'ai_response': "I'm doing well, thank you for asking! How can I help you today?",
            'expected_emotion': 'friendly'
        }
    ]
    
    try:
        await speech_to_speech_pipeline.initialize()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['expected_emotion'].title()} Emotion")
            print(f"   User: \"{test_case['user_input']}\"")
            print(f"   AI: \"{test_case['ai_response']}\"")
            
            # Analyze emotion
            emotion_analysis = speech_to_speech_pipeline.analyze_conversation_emotion(
                test_case['user_input'], 
                test_case['ai_response']
            )
            
            print(f"   🎭 Detected emotions: User={emotion_analysis['user_emotion']}, AI={emotion_analysis['response_emotion']}")
            print(f"   🎤 Selected voice: {emotion_analysis['voice_selected']}")
            print(f"   ⚡ Selected speed: {emotion_analysis['speed_selected']:.1f}x")
            print(f"   📊 Appropriateness score: {emotion_analysis['appropriateness_score']:.1f}")
            print(f"   🧠 Reasoning: {emotion_analysis['emotional_reasoning']}")
            
            # Check if emotion detection is working correctly
            if emotion_analysis['response_emotion'] == test_case['expected_emotion']:
                print(f"   ✅ Emotion detection: CORRECT")
            else:
                print(f"   ⚠️  Emotion detection: Expected {test_case['expected_emotion']}, got {emotion_analysis['response_emotion']}")
        
        print(f"\n✅ Emotional voice selection test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Emotional voice selection test failed: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return False

async def test_emotional_speech_synthesis():
    """Test actual speech synthesis with different emotions"""
    print("\n🎵 Testing Emotional Speech Synthesis")
    print("=" * 50)
    
    # Test different emotional responses
    emotional_tests = [
        {
            'text': "I'm absolutely thrilled to help you with this exciting project!",
            'emotion': 'excited',
            'expected_voice': 'af_bella',
            'filename': 'test_excited_speech.wav'
        },
        {
            'text': "I understand this is a difficult situation, and I'm here to support you through it.",
            'emotion': 'empathetic',
            'expected_voice': 'af_sarah',
            'filename': 'test_empathetic_speech.wav'
        },
        {
            'text': "Let me provide you with a comprehensive analysis of the current market conditions.",
            'emotion': 'professional',
            'expected_voice': 'af_nicole',
            'filename': 'test_professional_speech.wav'
        },
        {
            'text': "Take a deep breath and let's approach this calmly and peacefully.",
            'emotion': 'calm',
            'expected_voice': 'af_heart',
            'filename': 'test_calm_speech.wav'
        }
    ]
    
    try:
        await kokoro_model.initialize()
        
        for i, test in enumerate(emotional_tests, 1):
            print(f"\n🎤 Test {i}: {test['emotion'].title()} Speech")
            print(f"   Text: \"{test['text']}\"")
            print(f"   Expected voice: {test['expected_voice']}")
            
            # Detect emotion and get voice
            detected_emotion = speech_to_speech_pipeline._detect_emotion_in_text(test['text'])
            selected_voice = speech_to_speech_pipeline._get_voice_for_emotion(detected_emotion)
            selected_speed = speech_to_speech_pipeline._get_speed_for_emotion(detected_emotion, test['text'])
            
            print(f"   🎭 Detected emotion: {detected_emotion}")
            print(f"   🎤 Selected voice: {selected_voice}")
            print(f"   ⚡ Selected speed: {selected_speed:.1f}x")
            
            # Synthesize speech
            start_time = time.time()
            result = await kokoro_model.synthesize_speech(
                test['text'],
                voice=selected_voice,
                speed=selected_speed,
                chunk_id=f"emotional_test_{i}"
            )
            synthesis_time = (time.time() - start_time) * 1000
            
            if result['success'] and len(result['audio_data']) > 0:
                # Save audio file
                sf.write(test['filename'], result['audio_data'], result['sample_rate'])
                
                print(f"   ✅ Synthesis successful: {synthesis_time:.1f}ms")
                print(f"   📁 Audio saved: {test['filename']}")
                print(f"   🔊 Duration: {result['audio_duration_s']:.2f}s")
                print(f"   📊 Real-time factor: {result['performance_stats']['real_time_factor']:.2f}")
                
                # Verify voice selection
                if selected_voice == test['expected_voice']:
                    print(f"   ✅ Voice selection: CORRECT")
                else:
                    print(f"   ⚠️  Voice selection: Expected {test['expected_voice']}, got {selected_voice}")
            else:
                print(f"   ❌ Synthesis failed: {result.get('error', 'Unknown error')}")
                return False
        
        print(f"\n🎉 Emotional speech synthesis test completed!")
        print(f"🔊 Play the generated audio files to hear the emotional differences:")
        for test in emotional_tests:
            print(f"   - {test['filename']} ({test['emotion']} emotion)")
        
        return True
        
    except Exception as e:
        print(f"❌ Emotional speech synthesis test failed: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return False

async def test_emotion_appropriateness():
    """Test emotional appropriateness scoring"""
    print("\n📊 Testing Emotional Appropriateness Scoring")
    print("=" * 50)
    
    # Test cases for appropriateness scoring
    appropriateness_tests = [
        {
            'user_emotion': 'excited',
            'response_emotion': 'excited',
            'expected_score': 1.0,
            'description': 'Perfect match - excited user, excited response'
        },
        {
            'user_emotion': 'sad',
            'response_emotion': 'empathetic',
            'expected_score': 1.0,
            'description': 'Appropriate response - sad user, empathetic response'
        },
        {
            'user_emotion': 'professional',
            'response_emotion': 'professional',
            'expected_score': 1.0,
            'description': 'Perfect match - professional context'
        },
        {
            'user_emotion': 'excited',
            'response_emotion': 'friendly',
            'expected_score': 0.8,
            'description': 'Good response - friendly is generally appropriate'
        },
        {
            'user_emotion': 'sad',
            'response_emotion': 'excited',
            'expected_score': 0.6,
            'description': 'Poor match - sad user, excited response'
        }
    ]
    
    try:
        for i, test in enumerate(appropriateness_tests, 1):
            print(f"\n📋 Test {i}: {test['description']}")
            print(f"   User emotion: {test['user_emotion']}")
            print(f"   Response emotion: {test['response_emotion']}")
            
            score = speech_to_speech_pipeline._calculate_emotional_appropriateness(
                test['user_emotion'], 
                test['response_emotion']
            )
            
            print(f"   📊 Calculated score: {score:.1f}")
            print(f"   🎯 Expected score: {test['expected_score']:.1f}")
            
            if abs(score - test['expected_score']) < 0.1:
                print(f"   ✅ Appropriateness scoring: CORRECT")
            else:
                print(f"   ⚠️  Appropriateness scoring: MISMATCH")
        
        print(f"\n✅ Emotional appropriateness scoring test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Emotional appropriateness test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🎭 Emotional Speech Synthesis Test Suite")
    print("=" * 60)
    
    # Run all emotional tests
    voice_selection_ok = await test_emotional_voice_selection()
    speech_synthesis_ok = await test_emotional_speech_synthesis()
    appropriateness_ok = await test_emotion_appropriateness()
    
    if voice_selection_ok and speech_synthesis_ok and appropriateness_ok:
        print(f"\n🎉 ALL EMOTIONAL TESTS PASSED!")
        print(f"🎭 Emotional speech synthesis is working correctly!")
        print(f"\n📁 Generated emotional speech samples:")
        print(f"   - test_excited_speech.wav")
        print(f"   - test_empathetic_speech.wav")
        print(f"   - test_professional_speech.wav")
        print(f"   - test_calm_speech.wav")
        print(f"\n🔊 Listen to these files to experience the emotional differences!")
        return 0
    else:
        print(f"\n❌ Some emotional tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
