#!/usr/bin/env python3
"""
PHASE 5: Language Support Test Suite
Tests multi-language support with language routing and fallback mechanisms
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.tts_manager import TTSManager, LANGUAGE_MODELS, CHATTERBOX_LANGUAGES, DIA_TTS_LANGUAGES, INDIC_TTS_LANGUAGES

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase5LanguageSupport:
    """Test suite for Phase 5: Language Support"""
    
    def __init__(self):
        self.tts_manager = None
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    async def setup(self):
        """Setup test environment"""
        logger.info("🌍 [PHASE 5] Setting up language support tests...")
        try:
            self.tts_manager = TTSManager(model_name="chatterbox", device="cpu")
            self.tts_manager.initialize()
            logger.info("✅ TTS Manager initialized")
        except Exception as e:
            logger.warning(f"⚠️ TTS Manager initialization failed (expected in test env): {e}")
    
    def test_language_models_dictionary(self):
        """Test 1: Verify LANGUAGE_MODELS dictionary"""
        logger.info("📋 Test 1: LANGUAGE_MODELS dictionary")
        try:
            assert isinstance(LANGUAGE_MODELS, dict), "LANGUAGE_MODELS should be a dictionary"
            assert len(LANGUAGE_MODELS) == 17, f"Expected 17 languages, got {len(LANGUAGE_MODELS)}"
            
            # Check all required languages
            required_langs = ['en', 'hi', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ms', 'ta', 'te', 'mr', 'kn', 'ml', 'bn']
            for lang in required_langs:
                assert lang in LANGUAGE_MODELS, f"Missing language: {lang}"
            
            logger.info(f"✅ Test 1 PASSED: LANGUAGE_MODELS has {len(LANGUAGE_MODELS)} languages")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_language_constants(self):
        """Test 2: Verify language support constants"""
        logger.info("📋 Test 2: Language support constants")
        try:
            assert len(CHATTERBOX_LANGUAGES) == 10, f"Expected 10 Chatterbox languages, got {len(CHATTERBOX_LANGUAGES)}"
            assert len(DIA_TTS_LANGUAGES) == 1, f"Expected 1 Dia-TTS language, got {len(DIA_TTS_LANGUAGES)}"
            assert len(INDIC_TTS_LANGUAGES) == 6, f"Expected 6 Indic-TTS languages, got {len(INDIC_TTS_LANGUAGES)}"
            
            logger.info(f"✅ Test 2 PASSED: Language constants verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 2 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_language_routing(self):
        """Test 3: Verify language routing"""
        logger.info("📋 Test 3: Language routing")
        try:
            # Test Chatterbox routing
            assert LANGUAGE_MODELS['en'] == 'chatterbox', "English should use Chatterbox"
            assert LANGUAGE_MODELS['hi'] == 'chatterbox', "Hindi should use Chatterbox"
            
            # Test Dia-TTS routing
            assert LANGUAGE_MODELS['ms'] == 'dia-tts', "Malaysian should use Dia-TTS"
            
            # Test Indic-TTS routing
            assert LANGUAGE_MODELS['ta'] == 'indic-tts', "Tamil should use Indic-TTS"
            assert LANGUAGE_MODELS['te'] == 'indic-tts', "Telugu should use Indic-TTS"
            
            logger.info(f"✅ Test 3 PASSED: Language routing verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 3 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_tts_manager_methods(self):
        """Test 4: Verify TTSManager methods"""
        logger.info("📋 Test 4: TTSManager methods")
        try:
            # Test get_supported_languages
            supported = self.tts_manager.get_supported_languages()
            assert isinstance(supported, dict), "get_supported_languages should return dict"
            assert 'chatterbox' in supported, "Should have Chatterbox in supported languages"
            
            # Test get_all_supported_languages
            all_langs = self.tts_manager.get_all_supported_languages()
            assert isinstance(all_langs, list), "get_all_supported_languages should return list"
            assert len(all_langs) == 17, f"Expected 17 languages, got {len(all_langs)}"
            
            # Test get_language_model
            model = self.tts_manager.get_language_model('en')
            assert model == 'chatterbox', f"Expected 'chatterbox' for 'en', got '{model}'"
            
            model = self.tts_manager.get_language_model('ms')
            assert model == 'dia-tts', f"Expected 'dia-tts' for 'ms', got '{model}'"
            
            logger.info(f"✅ Test 4 PASSED: TTSManager methods verified")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            self.failed += 1
            return False
    
    async def test_synthesize_with_fallback(self):
        """Test 5: Verify synthesize_with_fallback method"""
        logger.info("📋 Test 5: synthesize_with_fallback method")
        try:
            # Check method exists
            assert hasattr(self.tts_manager, 'synthesize_with_fallback'), "Missing synthesize_with_fallback method"
            
            # Check model-specific methods exist
            assert hasattr(self.tts_manager, '_synthesize_chatterbox'), "Missing _synthesize_chatterbox method"
            assert hasattr(self.tts_manager, '_synthesize_dia'), "Missing _synthesize_dia method"
            assert hasattr(self.tts_manager, '_synthesize_indic'), "Missing _synthesize_indic method"
            
            logger.info(f"✅ Test 5 PASSED: synthesize_with_fallback methods verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_fallback_mechanism(self):
        """Test 6: Verify fallback mechanism for unsupported languages"""
        logger.info("📋 Test 6: Fallback mechanism")
        try:
            # Test fallback for unknown language
            model = self.tts_manager.get_language_model('unknown')
            assert model == 'chatterbox', f"Unknown language should fallback to Chatterbox, got '{model}'"
            
            logger.info(f"✅ Test 6 PASSED: Fallback mechanism verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 6 FAILED: {e}")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🌍 [PHASE 5] Starting Language Support Test Suite")
        logger.info("=" * 60)
        
        await self.setup()
        
        # Run synchronous tests
        self.test_language_models_dictionary()
        self.test_language_constants()
        self.test_language_routing()
        self.test_tts_manager_methods()
        await self.test_synthesize_with_fallback()
        self.test_fallback_mechanism()
        
        # Print summary
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)
        
        return self.failed == 0

async def main():
    """Main test runner"""
    test_suite = TestPhase5LanguageSupport()
    success = await test_suite.run_all_tests()
    
    if success:
        logger.info("✅ All Phase 5 tests PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Some Phase 5 tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

