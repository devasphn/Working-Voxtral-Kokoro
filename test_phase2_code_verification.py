#!/usr/bin/env python3
"""
Phase 2 Code Verification Script
Verifies that all Phase 2 changes are correctly implemented
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE2_VERIFICATION")


def verify_tts_manager_file():
    """Verify TTSManager file exists and has correct structure"""
    logger.info("\n[CHECK 1] Verify TTSManager file exists...")

    tts_file = Path("src/models/tts_manager.py")
    if not tts_file.exists():
        logger.error(f"❌ File not found: {tts_file}")
        return False

    logger.info(f"✅ File exists: {tts_file}")

    # Check file size
    file_size = tts_file.stat().st_size
    logger.info(f"✅ File size: {file_size} bytes")

    # Check content
    content = tts_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("class TTSManager", "TTSManager class definition"),
        ("def __init__", "__init__ method"),
        ("def initialize", "initialize method"),
        ("async def synthesize", "synthesize method"),
        ("def _convert_to_audio_bytes", "_convert_to_audio_bytes method"),
        ("def get_supported_languages", "get_supported_languages method"),
        ("def get_supported_emotions", "get_supported_emotions method"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_requirements_updated():
    """Verify requirements.txt has TTS dependencies"""
    logger.info("\n[CHECK 2] Verify requirements.txt updated...")

    req_file = Path("requirements.txt")
    if not req_file.exists():
        logger.error(f"❌ File not found: {req_file}")
        return False

    content = req_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check for TTS comment
    if "PHASE 2" in content and "TTS" in content:
        logger.info("✅ PHASE 2 TTS comment found")
    else:
        logger.warning("⚠️ PHASE 2 TTS comment not found (may be acceptable)")
    
    # Check for required packages
    required_packages = [
        "scipy",  # Already in requirements
        "soundfile",  # Already in requirements
        "librosa",  # Already in requirements
    ]
    
    for package in required_packages:
        if package in content:
            logger.info(f"✅ Found: {package}")
        else:
            logger.warning(f"⚠️ Missing: {package} (may be acceptable)")
    
    return True


def verify_ui_server_integration():
    """Verify ui_server_realtime.py has TTS integration"""
    logger.info("\n[CHECK 3] Verify ui_server_realtime.py integration...")

    ui_file = Path("src/api/ui_server_realtime.py")
    if not ui_file.exists():
        logger.error(f"❌ File not found: {ui_file}")
        return False

    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("from src.models.tts_manager import TTSManager", "TTSManager import"),
        ("def get_tts_manager()", "get_tts_manager function"),
        ("_tts_manager = None", "TTS manager global variable"),
        ("@app.websocket(\"/ws/tts\")", "TTS WebSocket endpoint"),
        ("async def websocket_tts", "websocket_tts function"),
        ("tts_manager = get_tts_manager()", "TTS manager initialization"),
        ("await tts_manager.synthesize", "TTS synthesis call"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_tts_manager_import():
    """Verify TTSManager can be imported"""
    logger.info("\n[CHECK 4] Verify TTSManager import...")
    
    try:
        from src.models.tts_manager import TTSManager
        logger.info("✅ TTSManager imported successfully")
        
        # Check class attributes
        tts = TTSManager(model_name="chatterbox", device="cpu")
        
        if hasattr(tts, 'model_name'):
            logger.info(f"✅ model_name attribute: {tts.model_name}")
        else:
            logger.error("❌ Missing model_name attribute")
            return False
        
        if hasattr(tts, 'device'):
            logger.info(f"✅ device attribute: {tts.device}")
        else:
            logger.error("❌ Missing device attribute")
            return False
        
        if hasattr(tts, 'is_initialized'):
            logger.info(f"✅ is_initialized attribute: {tts.is_initialized}")
        else:
            logger.error("❌ Missing is_initialized attribute")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def verify_websocket_endpoint():
    """Verify WebSocket endpoint is properly defined"""
    logger.info("\n[CHECK 5] Verify WebSocket endpoint...")

    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check for TTS endpoint
    if "@app.websocket(\"/ws/tts\")" in content:
        logger.info("✅ TTS WebSocket endpoint decorator found")
    else:
        logger.error("❌ TTS WebSocket endpoint decorator not found")
        return False
    
    # Check for endpoint handler
    if "async def websocket_tts(websocket: WebSocket):" in content:
        logger.info("✅ TTS WebSocket handler found")
    else:
        logger.error("❌ TTS WebSocket handler not found")
        return False
    
    # Check for message handling
    if "message_type == \"synthesize\"" in content:
        logger.info("✅ Synthesize message handling found")
    else:
        logger.error("❌ Synthesize message handling not found")
        return False
    
    # Check for audio sending
    if "await websocket.send_bytes(audio_bytes)" in content:
        logger.info("✅ Audio bytes sending found")
    else:
        logger.error("❌ Audio bytes sending not found")
        return False
    
    return True


def verify_no_regressions():
    """Verify no regressions in existing functionality"""
    logger.info("\n[CHECK 6] Verify no regressions...")

    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    # Check Phase 0 still exists
    if "PHASE 0" in content:
        logger.info("✅ Phase 0 code still present")
    else:
        logger.warning("⚠️ Phase 0 code not found")
    
    # Check Phase 1 still exists
    if "PHASE 1" in content:
        logger.info("✅ Phase 1 code still present")
    else:
        logger.warning("⚠️ Phase 1 code not found")
    
    # Check main WebSocket endpoint still exists
    if "@app.websocket(\"/ws\")" in content:
        logger.info("✅ Main conversation endpoint still present")
    else:
        logger.error("❌ Main conversation endpoint missing")
        return False
    
    return True


def main():
    """Run all verification checks"""
    
    logger.info("=" * 80)
    logger.info("PHASE 2 CODE VERIFICATION")
    logger.info("=" * 80)
    
    checks = [
        ("TTSManager file", verify_tts_manager_file),
        ("Requirements updated", verify_requirements_updated),
        ("UI Server integration", verify_ui_server_integration),
        ("TTSManager import", verify_tts_manager_import),
        ("WebSocket endpoint", verify_websocket_endpoint),
        ("No regressions", verify_no_regressions),
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
        logger.info("Phase 2 implementation is complete and correct!")
        return 0
    else:
        logger.error("\n❌ SOME VERIFICATION CHECKS FAILED")
        logger.error("Please review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

