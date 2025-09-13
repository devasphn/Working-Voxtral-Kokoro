#!/usr/bin/env python3
"""
Voxtral + TTS Integration Test Suite
Tests the complete pipeline: WebSocket → STT → LLM → TTS → Audio Response
"""

import asyncio
import websockets
import json
import base64
import numpy as np
import soundfile as sf
import time
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoxtralTTSIntegrationTest:
    def __init__(self, base_url="localhost", http_port=8000, health_port=8005):
        self.base_url = base_url
        self.http_port = http_port
        self.health_port = health_port
        self.websocket_url = f"ws://{base_url}:{http_port}/ws"
        self.health_url = f"http://{base_url}:{health_port}/health"
        self.web_url = f"http://{base_url}:{http_port}"
        
    async def test_health_check(self):
        """Test health check endpoint"""
        logger.info("🩺 Testing health check endpoint...")
        try:
            response = requests.get(self.health_url, timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Health check passed: {health_data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_web_interface(self):
        """Test web interface accessibility"""
        logger.info("🌐 Testing web interface...")
        try:
            response = requests.get(self.web_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Web interface accessible")
                return True
            else:
                logger.error(f"❌ Web interface failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Web interface error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        logger.info("🔌 Testing WebSocket connection...")
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                logger.info("✅ WebSocket connection established")
                
                # Wait for connection message
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                
                if data.get('type') == 'connection':
                    logger.info(f"✅ Connection message received: {data.get('message')}")
                    return True, websocket
                else:
                    logger.error(f"❌ Unexpected message type: {data.get('type')}")
                    return False, None
                    
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            return False, None
    
    def generate_test_audio(self, duration=2.0, sample_rate=16000, frequency=440):
        """Generate test audio signal"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        # Generate a simple sine wave
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        return audio.astype(np.float32)
    
    def audio_to_base64(self, audio_data, sample_rate=16000):
        """Convert audio array to base64 encoded WAV"""
        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Create temporary file
        temp_path = Path("temp_audio.wav")
        sf.write(temp_path, audio_int16, sample_rate)
        
        # Read as base64
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Clean up
        temp_path.unlink()
        
        return audio_base64
    
    async def test_audio_pipeline(self):
        """Test complete audio pipeline"""
        logger.info("🎵 Testing complete audio pipeline...")
        
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                # Wait for connection
                await websocket.recv()
                
                # Generate test audio
                logger.info("🎤 Generating test audio...")
                test_audio = self.generate_test_audio(duration=3.0)
                audio_base64 = self.audio_to_base64(test_audio)
                
                # Send audio chunk
                logger.info("📤 Sending audio chunk...")
                audio_message = {
                    "type": "conversational_audio_chunk",
                    "audio_data": audio_base64,
                    "chunk_id": "test_chunk_001",
                    "timestamp": time.time(),
                    "mode": "understanding"
                }
                
                await websocket.send(json.dumps(audio_message))
                logger.info("✅ Audio chunk sent")
                
                # Wait for responses
                logger.info("⏳ Waiting for responses...")
                responses_received = []
                
                try:
                    # Wait for multiple responses (text and audio)
                    for i in range(3):  # Expect up to 3 responses
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(response)
                        responses_received.append(data)
                        
                        logger.info(f"📥 Response {i+1}: {data.get('type')}")
                        
                        if data.get('type') == 'response':
                            logger.info(f"📝 Text response: {data.get('text', 'No text')[:100]}...")
                        elif data.get('type') == 'audio_response':
                            logger.info(f"🔊 Audio response received (voice: {data.get('voice')})")
                            
                            # Validate audio data
                            if data.get('audio_data'):
                                logger.info("✅ Audio data present in response")
                            else:
                                logger.warning("⚠️ No audio data in audio response")
                
                except asyncio.TimeoutError:
                    logger.warning("⏰ Timeout waiting for responses")
                
                # Analyze responses
                text_responses = [r for r in responses_received if r.get('type') == 'response']
                audio_responses = [r for r in responses_received if r.get('type') == 'audio_response']
                
                logger.info(f"📊 Pipeline Results:")
                logger.info(f"   • Text responses: {len(text_responses)}")
                logger.info(f"   • Audio responses: {len(audio_responses)}")
                
                if text_responses and audio_responses:
                    logger.info("🎉 Complete pipeline test PASSED!")
                    return True
                else:
                    logger.error("❌ Complete pipeline test FAILED - missing responses")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Audio pipeline test error: {e}")
            return False
    
    async def test_tts_voices(self):
        """Test different TTS voices"""
        logger.info("🎭 Testing TTS voice variety...")
        
        voices_to_test = ["tara", "leah", "leo", "dan"]
        
        try:
            async with websockets.connect(self.websocket_url, timeout=10) as websocket:
                await websocket.recv()  # Connection message
                
                for voice in voices_to_test:
                    logger.info(f"🗣️ Testing voice: {voice}")
                    
                    # Send a simple audio chunk
                    test_audio = self.generate_test_audio(duration=1.0)
                    audio_base64 = self.audio_to_base64(test_audio)
                    
                    message = {
                        "type": "conversational_audio_chunk",
                        "audio_data": audio_base64,
                        "chunk_id": f"voice_test_{voice}",
                        "timestamp": time.time(),
                        "mode": "understanding",
                        "preferred_voice": voice
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    # Wait for audio response
                    try:
                        for _ in range(3):
                            response = await asyncio.wait_for(websocket.recv(), timeout=15)
                            data = json.loads(response)
                            
                            if data.get('type') == 'audio_response':
                                received_voice = data.get('voice', 'unknown')
                                logger.info(f"✅ Voice {voice} test completed (received: {received_voice})")
                                break
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Voice {voice} test timeout")
                    
                    await asyncio.sleep(1)  # Brief pause between tests
                
                logger.info("🎭 Voice variety test completed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Voice test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Voxtral + TTS Integration Test Suite")
        logger.info("=" * 60)
        
        test_results = {}
        
        # Test 1: Health Check
        test_results['health_check'] = await self.test_health_check()
        
        # Test 2: Web Interface
        test_results['web_interface'] = await self.test_web_interface()
        
        # Test 3: WebSocket Connection
        ws_result, _ = await self.test_websocket_connection()
        test_results['websocket_connection'] = ws_result
        
        # Test 4: Complete Audio Pipeline
        test_results['audio_pipeline'] = await self.test_audio_pipeline()
        
        # Test 5: TTS Voice Variety
        test_results['tts_voices'] = await self.test_tts_voices()
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed_tests += 1
        
        logger.info("=" * 60)
        logger.info(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Integration is working correctly.")
            return True
        else:
            logger.error(f"❌ {total_tests - passed_tests} tests failed. Please check the logs.")
            return False

async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Voxtral + TTS Integration')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--http-port', type=int, default=8000, help='HTTP port')
    parser.add_argument('--health-port', type=int, default=8005, help='Health check port')
    
    args = parser.parse_args()
    
    tester = VoxtralTTSIntegrationTest(
        base_url=args.host,
        http_port=args.http_port,
        health_port=args.health_port
    )
    
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
