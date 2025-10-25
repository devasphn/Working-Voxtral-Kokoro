#!/usr/bin/env python3
"""
PHASE 7: Code Verification Script
Verifies that all Phase 7 implementation requirements are met
"""

import sys
from pathlib import Path

class Phase7CodeVerification:
    """Verify Phase 7 implementation"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
    
    def check(self, name, condition, details=""):
        """Record a check result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results.append(f"{status}: {name}")
        if details:
            self.results.append(f"   Details: {details}")
        
        if condition:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
        
        return condition
    
    def verify_emotion_detector(self):
        """Verify emotion_detector.py creation"""
        print("\n📋 Checking emotion_detector.py...")
        
        emotion_file = Path("src/utils/emotion_detector.py")
        if not emotion_file.exists():
            self.check("emotion_detector.py exists", False, "File not found")
            return
        
        content = emotion_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: EmotionDetector class
        self.check(
            "EmotionDetector class",
            "class EmotionDetector:" in content,
            "Should define EmotionDetector class"
        )
        
        # Check 2: EMOTION_KEYWORDS dictionary
        self.check(
            "EMOTION_KEYWORDS dictionary",
            "EMOTION_KEYWORDS = {" in content,
            "Should define emotion keywords"
        )
        
        # Check 3: detect_emotion method
        self.check(
            "detect_emotion method",
            "def detect_emotion(self, text: str)" in content,
            "Should implement emotion detection"
        )
        
        # Check 4: Supported emotions
        self.check(
            "At least 5 emotions supported",
            '"happy"' in content and '"sad"' in content and '"angry"' in content and '"excited"' in content and '"neutral"' in content,
            "Should support happy, sad, angry, excited, neutral"
        )
        
        # Check 5: Confidence score
        self.check(
            "Confidence score returned",
            "Tuple[str, float]" in content or "confidence" in content.lower(),
            "Should return emotion and confidence"
        )
        
        # Check 6: Intensifiers
        self.check(
            "Intensifiers support",
            "INTENSIFIERS" in content,
            "Should support emotion intensifiers"
        )
        
        # Check 7: Negators
        self.check(
            "Negators support",
            "NEGATORS" in content,
            "Should support emotion negators"
        )
        
        # Check 8: get_intensity method
        self.check(
            "get_intensity method",
            "def get_intensity(self, text: str)" in content,
            "Should calculate emotion intensity"
        )
    
    def verify_voxtral_model_integration(self):
        """Verify voxtral_model_realtime.py integration"""
        print("\n📋 Checking voxtral_model_realtime.py integration...")
        
        model_file = Path("src/models/voxtral_model_realtime.py")
        content = model_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: EmotionDetector import
        self.check(
            "EmotionDetector import",
            "from src.utils.emotion_detector import EmotionDetector" in content,
            "Should import EmotionDetector"
        )
        
        # Check 2: EMOTION_DETECTION_AVAILABLE flag
        self.check(
            "EMOTION_DETECTION_AVAILABLE flag",
            "EMOTION_DETECTION_AVAILABLE" in content,
            "Should have availability flag"
        )
        
        # Check 3: emotion_detector attribute
        self.check(
            "emotion_detector attribute",
            "self.emotion_detector = None" in content,
            "Should initialize emotion_detector"
        )
        
        # Check 4: get_emotion_detector method
        self.check(
            "get_emotion_detector method",
            "def get_emotion_detector(self)" in content,
            "Should have getter method"
        )
        
        # Check 5: Emotion detection in streaming
        self.check(
            "Emotion detection in streaming",
            "detect_emotion" in content and "emotion" in content,
            "Should detect emotion in streaming"
        )
        
        # Check 6: Emotion passed to TTS
        self.check(
            "Emotion passed to TTS",
            "emotion=emotion" in content,
            "Should pass emotion to TTS synthesis"
        )
        
        # Check 7: PHASE 7 comments
        self.check(
            "PHASE 7 comments",
            "PHASE 7" in content,
            "Should have PHASE 7 markers"
        )
    
    def verify_tts_manager_integration(self):
        """Verify tts_manager.py integration"""
        print("\n📋 Checking tts_manager.py integration...")
        
        tts_file = Path("src/models/tts_manager.py")
        content = tts_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: Emotion parameter in synthesize
        self.check(
            "Emotion parameter in synthesize",
            "emotion: str = \"neutral\"" in content,
            "Should accept emotion parameter"
        )
        
        # Check 2: Emotion logging
        self.check(
            "Emotion logging",
            "emotion=" in content,
            "Should log emotion being used"
        )
        
        # Check 3: PHASE 7 comments
        self.check(
            "PHASE 7 comments in TTS",
            "PHASE 7" in content,
            "Should have PHASE 7 markers"
        )
    
    def verify_utils_package(self):
        """Verify utils package structure"""
        print("\n📋 Checking utils package...")
        
        utils_init = Path("src/utils/__init__.py")
        if not utils_init.exists():
            self.check("utils/__init__.py exists", False, "File not found")
            return
        
        content = utils_init.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: EmotionDetector export
        self.check(
            "EmotionDetector exported",
            "EmotionDetector" in content,
            "Should export EmotionDetector"
        )
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("🎭 [PHASE 7] Code Verification")
        print("=" * 60)
        
        self.verify_emotion_detector()
        self.verify_voxtral_model_integration()
        self.verify_tts_manager_integration()
        self.verify_utils_package()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 Verification Results:")
        print("=" * 60)
        for result in self.results:
            print(result)
        
        print("\n" + "=" * 60)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"📊 Total: {self.checks_passed + self.checks_failed}")
        print("=" * 60)
        
        return self.checks_failed == 0

def main():
    """Main verification runner"""
    verifier = Phase7CodeVerification()
    success = verifier.run_all_checks()
    
    if success:
        print("\n✅ All Phase 7 code verification checks PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 7 code verification checks FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()

