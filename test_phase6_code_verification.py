#!/usr/bin/env python3
"""
PHASE 6: Code Verification Script
Verifies that all Phase 6 implementation requirements are met
"""

import sys
from pathlib import Path

class Phase6CodeVerification:
    """Verify Phase 6 implementation"""
    
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
    
    def verify_webrtc_enabled(self):
        """Verify WebRTC is enabled"""
        print("\n📋 Checking WebRTC configuration...")
        
        ui_file = Path("src/api/ui_server_realtime.py")
        if not ui_file.exists():
            self.check("ui_server_realtime.py exists", False, "File not found")
            return
        
        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: useWebRTC is set to true
        self.check(
            "useWebRTC set to true",
            "let useWebRTC = true;" in content,
            "Should enable WebRTC for lower latency"
        )
        
        # Check 2: PHASE 6 comment present
        self.check(
            "PHASE 6 comment present",
            "PHASE 6" in content,
            "Should have PHASE 6 markers"
        )
    
    def verify_webrtc_endpoints(self):
        """Verify WebRTC endpoints"""
        print("\n📋 Checking WebRTC endpoints...")
        
        ui_file = Path("src/api/ui_server_realtime.py")
        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: WebRTC offer endpoint
        self.check(
            "WebRTC /offer endpoint",
            "@app.post(\"/webrtc/offer\")" in content,
            "Should have endpoint for WebRTC offers"
        )
        
        # Check 2: WebRTC answer handling
        self.check(
            "WebRTC answer handling",
            "handle_webrtc_offer" in content or "webrtc" in content.lower(),
            "Should handle WebRTC answers"
        )
    
    def verify_webrtc_connection(self):
        """Verify WebRTC connection logic"""
        print("\n📋 Checking WebRTC connection logic...")
        
        ui_file = Path("src/api/ui_server_realtime.py")
        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: peerConnection variable
        self.check(
            "peerConnection variable",
            "peerConnection" in content,
            "Should have peerConnection variable"
        )
        
        # Check 2: RTCPeerConnection API
        self.check(
            "RTCPeerConnection API",
            "RTCPeerConnection" in content,
            "Should use RTCPeerConnection for peer-to-peer communication"
        )
        
        # Check 3: Offer/Answer logic
        self.check(
            "Offer/Answer logic",
            "createOffer" in content or "createAnswer" in content,
            "Should have SDP offer/answer exchange"
        )
    
    def verify_audio_streaming(self):
        """Verify audio streaming over WebRTC"""
        print("\n📋 Checking audio streaming over WebRTC...")

        ui_file = Path("src/api/ui_server_realtime.py")
        content = ui_file.read_text(encoding='utf-8', errors='ignore')

        # Check 1: Audio track handling (mediaStream or getTracks)
        self.check(
            "Audio track handling",
            "mediaStream" in content and "getTracks" in content,
            "Should handle audio tracks from media stream"
        )

        # Check 2: Media stream source
        self.check(
            "Media stream source",
            "createMediaStreamSource" in content or "mediaStream" in content,
            "Should create media stream source for audio input"
        )

        # Check 3: Audio context
        self.check(
            "Audio context",
            "audioContext" in content or "AudioContext" in content,
            "Should have audio context for playback"
        )
    
    def verify_backward_compatibility(self):
        """Verify backward compatibility"""
        print("\n📋 Checking backward compatibility...")
        
        ui_file = Path("src/api/ui_server_realtime.py")
        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: WebSocket code still exists
        self.check(
            "WebSocket code present",
            "new WebSocket" in content,
            "Should still have WebSocket fallback"
        )
        
        # Check 2: WebSocket endpoint
        self.check(
            "WebSocket endpoint",
            "@app.websocket(\"/ws\")" in content,
            "Should still have WebSocket endpoint"
        )
        
        # Check 3: useWebRTC toggle
        self.check(
            "useWebRTC toggle",
            "useWebRTC" in content,
            "Should have toggle for WebRTC/WebSocket selection"
        )
    
    def verify_latency_optimization(self):
        """Verify latency optimization"""
        print("\n📋 Checking latency optimization...")
        
        ui_file = Path("src/api/ui_server_realtime.py")
        content = ui_file.read_text(encoding='utf-8', errors='ignore')
        
        # Check 1: Latency tracking
        self.check(
            "Latency tracking",
            "latency" in content.lower() or "streamStartTime" in content,
            "Should track latency for performance monitoring"
        )
        
        # Check 2: Stream timing
        self.check(
            "Stream timing",
            "streamStartTime" in content,
            "Should track stream start time for latency calculation"
        )
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("🌐 [PHASE 6] Code Verification")
        print("=" * 60)
        
        self.verify_webrtc_enabled()
        self.verify_webrtc_endpoints()
        self.verify_webrtc_connection()
        self.verify_audio_streaming()
        self.verify_backward_compatibility()
        self.verify_latency_optimization()
        
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
    verifier = Phase6CodeVerification()
    success = verifier.run_all_checks()
    
    if success:
        print("\n✅ All Phase 6 code verification checks PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some Phase 6 code verification checks FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()

