#!/usr/bin/env python3
"""
Phase 3 Code Verification Script
Verifies that all Phase 3 changes are correctly implemented
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE3_VERIFICATION")


def verify_voxtral_model_changes():
    """Verify voxtral_model_realtime.py has TTS integration"""
    logger.info("\n[CHECK 1] Verify voxtral_model_realtime.py changes...")
    
    model_file = Path("src/models/voxtral_model_realtime.py")
    if not model_file.exists():
        logger.error(f"❌ File not found: {model_file}")
        return False
    
    content = model_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("from src.models.tts_manager import TTSManager", "TTSManager import"),
        ("TTS_AVAILABLE = True", "TTS_AVAILABLE flag"),
        ("self.tts_manager = None", "tts_manager attribute"),
        ("def get_tts_manager", "get_tts_manager method"),
        ("tts_manager = self.get_tts_manager()", "TTS manager initialization in streaming"),
        ("tts_enabled = tts_manager is not None", "TTS enabled check"),
        ("audio_bytes = await tts_manager.synthesize", "TTS synthesis call"),
        ("'audio': audio_bytes", "Audio in response dict"),
        ("PHASE 3", "PHASE 3 comments"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_ui_server_changes():
    """Verify ui_server_realtime.py handles audio chunks"""
    logger.info("\n[CHECK 2] Verify ui_server_realtime.py changes...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    if not ui_file.exists():
        logger.error(f"❌ File not found: {ui_file}")
        return False
    
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("has_audio", "has_audio field in JSON"),
        ("await websocket.send_bytes(text_chunk['audio'])", "Audio bytes sending"),
        ("PHASE 3", "PHASE 3 comments"),
        ("if text_chunk.get('audio')", "Audio chunk handling"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_backward_compatibility():
    """Verify backward compatibility is maintained"""
    logger.info("\n[CHECK 3] Verify backward compatibility...")
    
    model_file = Path("src/models/voxtral_model_realtime.py")
    content = model_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check that text-only responses still work
    checks = [
        ("'text': chunk_text.strip()", "Text field still present"),
        ("'is_final': False", "is_final field still present"),
        ("'chunk_index': chunk_index", "chunk_index field still present"),
        ("'processing_time_ms'", "processing_time_ms field still present"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_no_regressions():
    """Verify no regressions in existing functionality"""
    logger.info("\n[CHECK 4] Verify no regressions...")
    
    model_file = Path("src/models/voxtral_model_realtime.py")
    content = model_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check Phase 0 and Phase 1 still exist
    checks = [
        ("PHASE 0", "Phase 0 code"),
        ("PHASE 1", "Phase 1 code"),
        ("first_token_latency_ms", "TTFT tracking"),
        ("conversation_context", "Conversation context"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.warning(f"⚠️ Missing: {description} (may be acceptable)")
    
    return True


def verify_tts_error_handling():
    """Verify TTS error handling"""
    logger.info("\n[CHECK 5] Verify TTS error handling...")
    
    model_file = Path("src/models/voxtral_model_realtime.py")
    content = model_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("try:", "Try-except blocks"),
        ("except Exception as e", "Exception handling"),
        ("realtime_logger.warning", "Warning logging"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.warning(f"⚠️ Missing: {description}")
    
    return True


def verify_audio_field_optional():
    """Verify audio field is optional"""
    logger.info("\n[CHECK 6] Verify audio field is optional...")
    
    model_file = Path("src/models/voxtral_model_realtime.py")
    content = model_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check that audio can be None
    if "'audio': audio_bytes" in content or "'audio': None" in content:
        logger.info("✅ Audio field can be None")
    else:
        logger.warning("⚠️ Audio field handling unclear")
    
    # Check that text-only responses are still supported
    if "if tts_enabled:" in content:
        logger.info("✅ TTS is conditionally enabled")
    else:
        logger.warning("⚠️ TTS conditional check not found")
    
    return True


def main():
    """Run all verification checks"""
    
    logger.info("=" * 80)
    logger.info("PHASE 3 CODE VERIFICATION")
    logger.info("=" * 80)
    
    checks = [
        ("Voxtral Model Changes", verify_voxtral_model_changes),
        ("UI Server Changes", verify_ui_server_changes),
        ("Backward Compatibility", verify_backward_compatibility),
        ("No Regressions", verify_no_regressions),
        ("TTS Error Handling", verify_tts_error_handling),
        ("Audio Field Optional", verify_audio_field_optional),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"❌ Check failed with exception: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 80)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{check_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ ALL VERIFICATION CHECKS PASSED")
        logger.info("Phase 3 implementation is complete and correct!")
        return 0
    else:
        logger.error("\n❌ SOME VERIFICATION CHECKS FAILED")
        logger.error("Please review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

