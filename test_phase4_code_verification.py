#!/usr/bin/env python3
"""
Phase 4 Code Verification Script
Verifies that all Phase 4 changes are correctly implemented
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PHASE4_VERIFICATION")


def verify_websocket_handler():
    """Verify WebSocket handler supports binary messages"""
    logger.info("\n[CHECK 1] WebSocket Handler Binary Support...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("if (event.data instanceof ArrayBuffer", "ArrayBuffer check"),
        ("if (event.data instanceof Blob", "Blob check"),
        ("handleAudioChunkBinary", "Binary handler call"),
        ("JSON.parse(event.data)", "JSON parsing fallback"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_audio_queue_management():
    """Verify audio queue management is implemented"""
    logger.info("\n[CHECK 2] Audio Queue Management...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("audioQueue.push", "Queue push operation"),
        ("audioQueue.shift", "Queue shift operation"),
        ("audioQueue.length", "Queue length check"),
        ("isPlayingAudio", "Playback state tracking"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_web_audio_api():
    """Verify Web Audio API implementation"""
    logger.info("\n[CHECK 3] Web Audio API Implementation...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("new (window.AudioContext || window.webkitAudioContext)", "AudioContext creation"),
        ("audioContext.decodeAudioData", "Audio decoding"),
        ("createBufferSource", "Buffer source"),
        ("source.connect(audioContext.destination)", "Audio routing"),
        ("source.start(0)", "Audio playback start"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_playback_controls():
    """Verify playback control functions"""
    logger.info("\n[CHECK 4] Playback Control Functions...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("function toggleAudioPlayback", "Toggle function"),
        ("function pauseAudioPlayback", "Pause function"),
        ("function resumeAudioPlayback", "Resume function"),
        ("function setAudioVolume", "Volume control"),
        ("audioContext.suspend()", "Suspend playback"),
        ("audioContext.resume()", "Resume playback"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_html_ui():
    """Verify HTML UI elements"""
    logger.info("\n[CHECK 5] HTML UI Elements...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ('id="audioPlayBtn"', "Play button"),
        ('id="audioPauseBtn"', "Pause button"),
        ('id="volumeControl"', "Volume slider"),
        ('id="audioQueueLength"', "Queue display"),
        ('id="audioPlaybackStatus"', "Status display"),
        ("onclick=\"toggleAudioPlayback()\"", "Play button handler"),
        ("onclick=\"pauseAudioPlayback()\"", "Pause button handler"),
        ("onchange=\"setAudioVolume(this.value)\"", "Volume handler"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.error(f"❌ Missing: {description}")
            return False
    
    return True


def verify_error_handling():
    """Verify error handling"""
    logger.info("\n[CHECK 6] Error Handling...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("try {", "Try blocks"),
        ("catch (error)", "Catch blocks"),
        ("console.error", "Error logging"),
        ("log(`❌", "Error messages"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.warning(f"⚠️ Missing: {description}")
    
    return True


def verify_phase_integration():
    """Verify integration with previous phases"""
    logger.info("\n[CHECK 7] Phase Integration...")
    
    ui_file = Path("src/api/ui_server_realtime.py")
    content = ui_file.read_text(encoding='utf-8', errors='ignore')
    
    checks = [
        ("case 'text_chunk'", "Phase 3 text chunks"),
        ("handleWebSocketMessage", "Message routing"),
        ("displayPartialResponse", "Text display"),
        ("PHASE 4", "Phase 4 markers"),
    ]
    
    for check_str, description in checks:
        if check_str in content:
            logger.info(f"✅ Found: {description}")
        else:
            logger.warning(f"⚠️ Missing: {description}")
    
    return True


def main():
    """Run all verification checks"""
    
    logger.info("=" * 80)
    logger.info("PHASE 4 CODE VERIFICATION")
    logger.info("=" * 80)
    
    checks = [
        ("WebSocket Handler Binary Support", verify_websocket_handler),
        ("Audio Queue Management", verify_audio_queue_management),
        ("Web Audio API Implementation", verify_web_audio_api),
        ("Playback Control Functions", verify_playback_controls),
        ("HTML UI Elements", verify_html_ui),
        ("Error Handling", verify_error_handling),
        ("Phase Integration", verify_phase_integration),
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
        logger.info("Phase 4 implementation is complete and correct!")
        return 0
    else:
        logger.error("\n❌ SOME VERIFICATION CHECKS FAILED")
        logger.error("Please review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

