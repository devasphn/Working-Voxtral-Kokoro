#!/usr/bin/env python3
"""
PHASE 5: Code Verification Script
Verifies that all Phase 5 implementation requirements are met
"""

import sys
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class Phase5CodeVerification:
    """Verify Phase 5 implementation"""
    
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
    
    def verify_tts_manager(self):
        """Verify tts_manager.py modifications"""
        print("\n📋 Checking tts_manager.py...")

        tts_file = Path("src/models/tts_manager.py")
        if not tts_file.exists():
            self.check("tts_manager.py exists", False, "File not found")
            return

        content = tts_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: LANGUAGE_MODELS dictionary
        self.check(
            "LANGUAGE_MODELS dictionary defined",
            "LANGUAGE_MODELS = {" in content,
            "Dictionary should map languages to TTS models"
        )
        
        # Check 2: Language constants
        self.check(
            "CHATTERBOX_LANGUAGES constant",
            "CHATTERBOX_LANGUAGES = [" in content,
            "Should list Chatterbox-supported languages"
        )
        
        self.check(
            "DIA_TTS_LANGUAGES constant",
            "DIA_TTS_LANGUAGES = [" in content,
            "Should list Dia-TTS-supported languages"
        )
        
        self.check(
            "INDIC_TTS_LANGUAGES constant",
            "INDIC_TTS_LANGUAGES = [" in content,
            "Should list Indic-TTS-supported languages"
        )
        
        # Check 3: synthesize_with_fallback method
        self.check(
            "synthesize_with_fallback method",
            "async def synthesize_with_fallback" in content,
            "Should implement language-aware synthesis with fallback"
        )
        
        # Check 4: Model-specific synthesis methods
        self.check(
            "_synthesize_chatterbox method",
            "async def _synthesize_chatterbox" in content,
            "Should implement Chatterbox synthesis"
        )
        
        self.check(
            "_synthesize_dia method",
            "async def _synthesize_dia" in content,
            "Should implement Dia-TTS synthesis"
        )
        
        self.check(
            "_synthesize_indic method",
            "async def _synthesize_indic" in content,
            "Should implement Indic-TTS synthesis"
        )
        
        # Check 5: Updated get_supported_languages
        self.check(
            "Updated get_supported_languages method",
            "def get_supported_languages(self) -> Dict" in content,
            "Should return dict of languages by model"
        )
        
        # Check 6: New helper methods
        self.check(
            "get_all_supported_languages method",
            "def get_all_supported_languages" in content,
            "Should return list of all supported language codes"
        )
        
        self.check(
            "get_language_model method",
            "def get_language_model" in content,
            "Should return TTS model for a language"
        )
    
    def verify_voxtral_model(self):
        """Verify voxtral_model_realtime.py modifications"""
        print("\n📋 Checking voxtral_model_realtime.py...")

        model_file = Path("src/models/voxtral_model_realtime.py")
        if not model_file.exists():
            self.check("voxtral_model_realtime.py exists", False, "File not found")
            return

        content = model_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: Language parameter in method signature
        self.check(
            "Language parameter in process_realtime_chunk_streaming",
            'language: str = "en"' in content,
            "Should accept language parameter with default 'en'"
        )
        
        # Check 2: Language used in TTS synthesis
        self.check(
            "Language parameter passed to TTS synthesis",
            "language=language" in content,
            "Should pass language parameter to synthesize method"
        )
        
        # Check 3: PHASE 5 comments
        self.check(
            "PHASE 5 comments in code",
            "PHASE 5" in content,
            "Should have PHASE 5 markers for language support"
        )
    
    def verify_ui_server(self):
        """Verify ui_server_realtime.py modifications"""
        print("\n📋 Checking ui_server_realtime.py...")

        ui_file = Path("src/api/ui_server_realtime.py")
        if not ui_file.exists():
            self.check("ui_server_realtime.py exists", False, "File not found")
            return

        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: Language selection UI
        self.check(
            "Language selection dropdown in HTML",
            'id="languageSelect"' in content,
            "Should have language dropdown control"
        )
        
        # Check 2: Language names mapping
        self.check(
            "LANGUAGE_NAMES JavaScript object",
            "const LANGUAGE_NAMES = {" in content,
            "Should map language codes to names"
        )
        
        # Check 3: Language models mapping
        self.check(
            "LANGUAGE_MODELS JavaScript object",
            "const LANGUAGE_MODELS = {" in content,
            "Should map language codes to TTS models"
        )
        
        # Check 4: Language control functions
        self.check(
            "setLanguage function",
            "function setLanguage(languageCode)" in content,
            "Should implement language selection"
        )
        
        self.check(
            "getLanguage function",
            "function getLanguage()" in content,
            "Should return current language"
        )
        
        self.check(
            "getSupportedLanguages function",
            "function getSupportedLanguages()" in content,
            "Should return list of supported languages"
        )
        
        # Check 5: Language parameter in WebSocket message
        self.check(
            "Language parameter in audio_chunk message",
            "language: getLanguage()" in content,
            "Should include language in WebSocket messages"
        )
        
        # Check 6: Language parameter extraction in backend
        self.check(
            "Language extraction from message",
            'language = message.get("language"' in content,
            "Should extract language from WebSocket message"
        )
        
        # Check 7: Language parameter passed to streaming method
        self.check(
            "Language passed to process_realtime_chunk_streaming",
            "language=language" in content and "process_realtime_chunk_streaming" in content,
            "Should pass language to streaming method"
        )
        
        # Check 8: Current language display
        self.check(
            "Current language display in UI",
            'id="currentLanguage"' in content,
            "Should display current language in UI"
        )
        
        self.check(
            "Current model display in UI",
            'id="currentModel"' in content,
            "Should display current TTS model in UI"
        )
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("🌍 [PHASE 5] Code Verification")
        print("=" * 60)
        
        self.verify_tts_manager()
        self.verify_voxtral_model()
        self.verify_ui_server()
        
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
    verifier = Phase5CodeVerification()
    success = verifier.run_all_checks()
    
    if success:
        print("\n✅ All Phase 5 code verification checks PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 5 code verification checks FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()

