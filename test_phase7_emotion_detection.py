#!/usr/bin/env python3
"""
PHASE 7: Emotion Detection Test Suite
Tests emotion detection from text with confidence scores
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.emotion_detector import EmotionDetector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase7EmotionDetection:
    """Test suite for Phase 7: Emotion Detection"""
    
    def __init__(self):
        self.emotion_detector = EmotionDetector()
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def test_supported_emotions(self):
        """Test 1: Verify supported emotions"""
        logger.info("📋 Test 1: Supported emotions")
        try:
            emotions = self.emotion_detector.get_supported_emotions()
            assert len(emotions) >= 5, f"Expected at least 5 emotions, got {len(emotions)}"
            assert "neutral" in emotions, "Should support neutral emotion"
            assert "happy" in emotions, "Should support happy emotion"
            assert "sad" in emotions, "Should support sad emotion"
            assert "angry" in emotions, "Should support angry emotion"
            assert "excited" in emotions, "Should support excited emotion"
            
            logger.info(f"✅ Test 1 PASSED: {len(emotions)} emotions supported: {emotions}")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_happy_emotion_detection(self):
        """Test 2: Detect happy emotion"""
        logger.info("📋 Test 2: Happy emotion detection")
        try:
            test_texts = [
                "I'm so happy and excited!",
                "This is wonderful and fantastic!",
                "I love this, it's fantastic!",
                "Great job, excellent work!"
            ]

            for text in test_texts:
                emotion, confidence = self.emotion_detector.detect_emotion(text)
                assert emotion == "happy", f"Expected 'happy' for '{text}', got '{emotion}'"
                assert confidence >= 0.5, f"Expected confidence >= 0.5, got {confidence}"
            
            logger.info(f"✅ Test 2 PASSED: Happy emotion detected correctly")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 2 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_sad_emotion_detection(self):
        """Test 3: Detect sad emotion"""
        logger.info("📋 Test 3: Sad emotion detection")
        try:
            test_texts = [
                "I'm so sad and depressed",
                "This is terrible and awful",
                "I feel miserable and down",
                "This is bad and disappointing"
            ]

            for text in test_texts:
                emotion, confidence = self.emotion_detector.detect_emotion(text)
                assert emotion == "sad", f"Expected 'sad' for '{text}', got '{emotion}'"
                assert confidence >= 0.5, f"Expected confidence >= 0.5, got {confidence}"
            
            logger.info(f"✅ Test 3 PASSED: Sad emotion detected correctly")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 3 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_angry_emotion_detection(self):
        """Test 4: Detect angry emotion"""
        logger.info("📋 Test 4: Angry emotion detection")
        try:
            test_texts = [
                "I'm so angry and furious!",
                "This makes me mad and irritated",
                "I hate this, it's disgusting!",
                "This is outrageous and infuriating!"
            ]

            for text in test_texts:
                emotion, confidence = self.emotion_detector.detect_emotion(text)
                assert emotion == "angry", f"Expected 'angry' for '{text}', got '{emotion}'"
                assert confidence >= 0.5, f"Expected confidence >= 0.5, got {confidence}"
            
            logger.info(f"✅ Test 4 PASSED: Angry emotion detected correctly")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_excited_emotion_detection(self):
        """Test 5: Detect excited emotion"""
        logger.info("📋 Test 5: Excited emotion detection")
        try:
            test_texts = [
                "I'm so excited and thrilled!",
                "This is amazing and energetic!",
                "I'm pumped and enthusiastic!",
                "This is incredible and dynamic!"
            ]

            for text in test_texts:
                emotion, confidence = self.emotion_detector.detect_emotion(text)
                assert emotion == "excited", f"Expected 'excited' for '{text}', got '{emotion}'"
                assert confidence >= 0.5, f"Expected confidence >= 0.5, got {confidence}"
            
            logger.info(f"✅ Test 5 PASSED: Excited emotion detected correctly")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_neutral_emotion_detection(self):
        """Test 6: Detect neutral emotion"""
        logger.info("📋 Test 6: Neutral emotion detection")
        try:
            test_texts = [
                "The weather is fine today",
                "I'm okay with this",
                "This is normal and regular",
                "Everything is fine"
            ]
            
            for text in test_texts:
                emotion, confidence = self.emotion_detector.detect_emotion(text)
                assert emotion == "neutral", f"Expected 'neutral' for '{text}', got '{emotion}'"
            
            logger.info(f"✅ Test 6 PASSED: Neutral emotion detected correctly")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 6 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_confidence_scores(self):
        """Test 7: Verify confidence scores"""
        logger.info("📋 Test 7: Confidence scores")
        try:
            emotion, confidence = self.emotion_detector.detect_emotion("I'm very happy!")
            assert 0.0 <= confidence <= 1.0, f"Confidence should be 0.0-1.0, got {confidence}"
            assert confidence > 0.5, f"Expected high confidence for clear emotion, got {confidence}"
            
            logger.info(f"✅ Test 7 PASSED: Confidence scores valid (0.0-1.0)")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 7 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_intensity_calculation(self):
        """Test 8: Verify intensity calculation"""
        logger.info("📋 Test 8: Intensity calculation")
        try:
            # Test normal intensity
            intensity1 = self.emotion_detector.get_intensity("I'm happy")
            assert 0.5 <= intensity1 <= 2.0, f"Intensity should be 0.5-2.0, got {intensity1}"
            
            # Test intensified emotion
            intensity2 = self.emotion_detector.get_intensity("I'm VERY happy!")
            assert intensity2 > intensity1, f"Intensified text should have higher intensity"
            
            logger.info(f"✅ Test 8 PASSED: Intensity calculation working (normal={intensity1:.2f}, intensified={intensity2:.2f})")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 8 FAILED: {e}")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🎭 [PHASE 7] Starting Emotion Detection Test Suite")
        logger.info("=" * 60)
        
        # Run all tests
        self.test_supported_emotions()
        self.test_happy_emotion_detection()
        self.test_sad_emotion_detection()
        self.test_angry_emotion_detection()
        self.test_excited_emotion_detection()
        self.test_neutral_emotion_detection()
        self.test_confidence_scores()
        self.test_intensity_calculation()
        
        # Print summary
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)
        
        return self.failed == 0

async def main():
    """Main test runner"""
    test_suite = TestPhase7EmotionDetection()
    success = await test_suite.run_all_tests()
    
    if success:
        logger.info("✅ All Phase 7 tests PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Some Phase 7 tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

