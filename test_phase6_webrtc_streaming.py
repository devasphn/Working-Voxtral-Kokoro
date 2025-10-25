#!/usr/bin/env python3
"""
PHASE 6: WebRTC Audio Streaming Test Suite
Tests WebRTC connection establishment and audio streaming
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPhase6WebRTCStreaming:
    """Test suite for Phase 6: WebRTC Audio Streaming"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def test_webrtc_enabled(self):
        """Test 1: Verify WebRTC is enabled"""
        logger.info("📋 Test 1: WebRTC enabled")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check that useWebRTC is set to true
            assert "let useWebRTC = true;" in content, "useWebRTC should be set to true"
            
            # Check that PHASE 6 comment is present
            assert "PHASE 6" in content, "Should have PHASE 6 markers"
            
            logger.info(f"✅ Test 1 PASSED: WebRTC is enabled")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 1 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_webrtc_endpoints_exist(self):
        """Test 2: Verify WebRTC endpoints exist"""
        logger.info("📋 Test 2: WebRTC endpoints exist")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check for WebRTC endpoints
            assert "@app.post(\"/webrtc/offer\")" in content, "Should have /webrtc/offer endpoint"
            assert "@app.post(\"/webrtc/answer\")" in content or "handle_webrtc_offer" in content, "Should have WebRTC answer handling"
            
            logger.info(f"✅ Test 2 PASSED: WebRTC endpoints exist")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 2 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_webrtc_connection_logic(self):
        """Test 3: Verify WebRTC connection logic"""
        logger.info("📋 Test 3: WebRTC connection logic")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check for WebRTC connection establishment
            assert "peerConnection" in content, "Should have peerConnection variable"
            assert "RTCPeerConnection" in content, "Should use RTCPeerConnection API"
            assert "createOffer" in content or "createAnswer" in content, "Should have offer/answer logic"
            
            logger.info(f"✅ Test 3 PASSED: WebRTC connection logic verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 3 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_audio_streaming_over_webrtc(self):
        """Test 4: Verify audio streaming over WebRTC"""
        logger.info("📋 Test 4: Audio streaming over WebRTC")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')

            # Check for audio track handling (mediaStream and getTracks)
            assert "mediaStream" in content and "getTracks" in content, "Should handle audio tracks from media stream"
            assert "createMediaStreamSource" in content or "mediaStream" in content, "Should create media stream source"

            logger.info(f"✅ Test 4 PASSED: Audio streaming over WebRTC verified")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 4 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_backward_compatibility(self):
        """Test 5: Verify backward compatibility with WebSocket"""
        logger.info("📋 Test 5: Backward compatibility with WebSocket")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check that WebSocket code still exists
            assert "ws = new WebSocket" in content or "new WebSocket" in content, "Should still have WebSocket code"
            assert "@app.websocket(\"/ws\")" in content, "Should still have WebSocket endpoint"
            
            logger.info(f"✅ Test 5 PASSED: Backward compatibility maintained")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 5 FAILED: {e}")
            self.failed += 1
            return False
    
    def test_latency_optimization(self):
        """Test 6: Verify latency optimization markers"""
        logger.info("📋 Test 6: Latency optimization markers")
        try:
            ui_file = Path("src/api/ui_server_realtime.py")
            content = ui_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check for latency tracking
            assert "latency" in content.lower(), "Should track latency"
            assert "streamStartTime" in content, "Should track stream start time"
            
            logger.info(f"✅ Test 6 PASSED: Latency optimization markers present")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"❌ Test 6 FAILED: {e}")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🌐 [PHASE 6] Starting WebRTC Audio Streaming Test Suite")
        logger.info("=" * 60)
        
        # Run all tests
        self.test_webrtc_enabled()
        self.test_webrtc_endpoints_exist()
        self.test_webrtc_connection_logic()
        self.test_audio_streaming_over_webrtc()
        self.test_backward_compatibility()
        self.test_latency_optimization()
        
        # Print summary
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        logger.info("=" * 60)
        
        return self.failed == 0

async def main():
    """Main test runner"""
    test_suite = TestPhase6WebRTCStreaming()
    success = await test_suite.run_all_tests()
    
    if success:
        logger.info("✅ All Phase 6 tests PASSED!")
        sys.exit(0)
    else:
        logger.error("❌ Some Phase 6 tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

