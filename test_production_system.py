#!/usr/bin/env python3
"""
Production System Testing and Validation
Comprehensive test suite for Voxtral + Orpheus TTS system
"""

import asyncio
import aiohttp
import websockets
import json
import time
import sys
import logging
from typing import Dict, Any, List
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionSystemTester:
    """Comprehensive production system tester"""
    
    def __init__(self, base_url: str = "http://localhost:8000", ws_url: str = "ws://localhost:8765"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.test_results = []
        
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test system health endpoint"""
        logger.info("Testing health endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "test": "health_endpoint",
                            "status": "PASS",
                            "response_time_ms": 0,  # Will be measured
                            "data": data
                        }
                    else:
                        return {
                            "test": "health_endpoint",
                            "status": "FAIL",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "test": "health_endpoint",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def test_model_status(self) -> Dict[str, Any]:
        """Test model status endpoint"""
        logger.info("Testing model status...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/system/status", timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "test": "model_status",
                            "status": "PASS",
                            "data": data
                        }
                    else:
                        return {
                            "test": "model_status",
                            "status": "FAIL",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "test": "model_status",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test WebSocket connection"""
        logger.info("Testing WebSocket connection...")
        
        try:
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                # Send ping
                ping_message = {"type": "ping", "timestamp": time.time()}
                await websocket.send(json.dumps(ping_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                
                return {
                    "test": "websocket_connection",
                    "status": "PASS",
                    "response": response_data
                }
        except Exception as e:
            return {
                "test": "websocket_connection",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def test_latency_performance(self) -> Dict[str, Any]:
        """Test system latency performance"""
        logger.info("Testing latency performance...")
        
        try:
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "test_type": "latency",
                    "iterations": 5
                }
                
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/performance/test",
                    json=test_payload,
                    timeout=60
                ) as response:
                    end_time = time.time()
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "test": "latency_performance",
                            "status": "PASS",
                            "response_time_ms": (end_time - start_time) * 1000,
                            "data": data
                        }
                    else:
                        return {
                            "test": "latency_performance",
                            "status": "FAIL",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "test": "latency_performance",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def test_audio_processing(self) -> Dict[str, Any]:
        """Test audio processing pipeline"""
        logger.info("Testing audio processing...")
        
        try:
            # Generate test audio data
            sample_rate = 16000
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32)
            
            # Convert to base64
            import base64
            audio_bytes = audio_data.tobytes()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            async with websockets.connect(self.ws_url, timeout=10) as websocket:
                # Send audio data
                message = {
                    "type": "audio_chunk",
                    "audio_data": audio_b64,
                    "sample_rate": sample_rate,
                    "chunk_id": "test_chunk_1"
                }
                
                start_time = time.time()
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                end_time = time.time()
                
                response_data = json.loads(response)
                processing_time = (end_time - start_time) * 1000
                
                return {
                    "test": "audio_processing",
                    "status": "PASS",
                    "processing_time_ms": processing_time,
                    "response": response_data
                }
        except Exception as e:
            return {
                "test": "audio_processing",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def test_stress_load(self, concurrent_requests: int = 5) -> Dict[str, Any]:
        """Test system under load"""
        logger.info(f"Testing stress load with {concurrent_requests} concurrent requests...")
        
        async def single_request():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/health", timeout=10) as response:
                        return response.status == 200
            except:
                return False
        
        try:
            start_time = time.time()
            tasks = [single_request() for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            success_count = sum(results)
            success_rate = success_count / len(results)
            total_time = (end_time - start_time) * 1000
            
            return {
                "test": "stress_load",
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "concurrent_requests": concurrent_requests,
                "success_rate": success_rate,
                "total_time_ms": total_time,
                "avg_time_per_request_ms": total_time / concurrent_requests
            }
        except Exception as e:
            return {
                "test": "stress_load",
                "status": "FAIL",
                "error": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all production tests"""
        logger.info("🧪 Starting comprehensive production system tests...")
        
        tests = [
            self.test_health_endpoint(),
            self.test_model_status(),
            self.test_websocket_connection(),
            self.test_latency_performance(),
            self.test_audio_processing(),
            self.test_stress_load()
        ]
        
        results = []
        for test in tests:
            try:
                result = await test
                results.append(result)
                
                if result["status"] == "PASS":
                    logger.info(f"✅ {result['test']}: PASSED")
                else:
                    logger.error(f"❌ {result['test']}: FAILED - {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"❌ Test failed with exception: {e}")
                results.append({
                    "test": "unknown",
                    "status": "FAIL",
                    "error": str(e)
                })
        
        # Calculate summary
        passed_tests = sum(1 for r in results if r["status"] == "PASS")
        total_tests = len(results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate >= 0.8 else "FAIL",
            "test_results": results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 PRODUCTION SYSTEM TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Overall Status: {summary['overall_status']}")
        print("="*60)
        
        for result in summary['test_results']:
            status_icon = "✅" if result['status'] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result['status'] == "FAIL" and 'error' in result:
                print(f"   Error: {result['error']}")
        
        print("="*60)
        
        if summary['overall_status'] == "PASS":
            print("🎉 PRODUCTION SYSTEM IS READY!")
        else:
            print("⚠️ PRODUCTION SYSTEM HAS ISSUES - CHECK FAILED TESTS")

async def main():
    """Main test function"""
    tester = ProductionSystemTester()
    summary = await tester.run_all_tests()
    tester.print_summary(summary)
    
    # Exit with appropriate code
    sys.exit(0 if summary['overall_status'] == "PASS" else 1)

if __name__ == "__main__":
    asyncio.run(main())
