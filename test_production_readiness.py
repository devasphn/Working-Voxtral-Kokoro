#!/usr/bin/env python3
"""
Production Readiness Test Suite for Speech-to-Speech Conversational AI
Comprehensive testing framework for audio quality validation and system reliability
"""
import asyncio
import numpy as np
import soundfile as sf
import time
import sys
import os
import json
import aiohttp
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from src.models.speech_to_speech_pipeline import speech_to_speech_pipeline
from src.models.kokoro_model_realtime import kokoro_model
from src.models.voxtral_model_realtime import voxtral_model
from src.models.audio_processor_realtime import AudioProcessor
from src.utils.config import config

class ProductionReadinessTestSuite:
    """Comprehensive test suite for production readiness validation"""
    
    def __init__(self):
        self.test_results = {}
        self.audio_processor = AudioProcessor()
        self.performance_metrics = []
        self.error_log = []
        
    async def test_component_initialization(self) -> Dict[str, Any]:
        """Test all components can be initialized properly"""
        print("🔧 Testing Component Initialization")
        print("-" * 50)
        
        results = {
            "voxtral_stt": {"status": "unknown", "time_ms": 0, "error": None},
            "kokoro_tts": {"status": "unknown", "time_ms": 0, "error": None},
            "speech_to_speech_pipeline": {"status": "unknown", "time_ms": 0, "error": None}
        }
        
        # Test Voxtral STT initialization
        try:
            start_time = time.time()
            if not voxtral_model.is_initialized:
                await voxtral_model.initialize()
            init_time = (time.time() - start_time) * 1000
            
            results["voxtral_stt"] = {
                "status": "success" if voxtral_model.is_initialized else "failed",
                "time_ms": init_time,
                "error": None
            }
            print(f"   ✅ Voxtral STT: {init_time:.1f}ms")
        except Exception as e:
            results["voxtral_stt"]["status"] = "failed"
            results["voxtral_stt"]["error"] = str(e)
            print(f"   ❌ Voxtral STT: {e}")
        
        # Test Kokoro TTS initialization
        try:
            start_time = time.time()
            if not kokoro_model.is_initialized:
                await kokoro_model.initialize()
            init_time = (time.time() - start_time) * 1000
            
            results["kokoro_tts"] = {
                "status": "success" if kokoro_model.is_initialized else "failed",
                "time_ms": init_time,
                "error": None
            }
            print(f"   ✅ Kokoro TTS: {init_time:.1f}ms")
        except Exception as e:
            results["kokoro_tts"]["status"] = "failed"
            results["kokoro_tts"]["error"] = str(e)
            print(f"   ❌ Kokoro TTS: {e}")
        
        # Test Speech-to-Speech Pipeline initialization
        try:
            start_time = time.time()
            if not speech_to_speech_pipeline.is_initialized:
                await speech_to_speech_pipeline.initialize()
            init_time = (time.time() - start_time) * 1000
            
            results["speech_to_speech_pipeline"] = {
                "status": "success" if speech_to_speech_pipeline.is_initialized else "failed",
                "time_ms": init_time,
                "error": None
            }
            print(f"   ✅ Speech-to-Speech Pipeline: {init_time:.1f}ms")
        except Exception as e:
            results["speech_to_speech_pipeline"]["status"] = "failed"
            results["speech_to_speech_pipeline"]["error"] = str(e)
            print(f"   ❌ Speech-to-Speech Pipeline: {e}")
        
        # Overall assessment
        all_success = all(r["status"] == "success" for r in results.values())
        print(f"\n📊 Component Initialization: {'✅ PASSED' if all_success else '❌ FAILED'}")
        
        return results
    
    async def test_latency_performance(self, num_tests: int = 10) -> Dict[str, Any]:
        """Test end-to-end latency performance"""
        print(f"\n⚡ Testing Latency Performance ({num_tests} tests)")
        print("-" * 50)
        
        latencies = []
        stage_timings = {"stt": [], "llm": [], "tts": []}
        
        for i in range(num_tests):
            try:
                # Generate test audio
                test_audio = self._generate_test_audio(duration=2.0, frequency=440)
                
                # Process through pipeline
                start_time = time.time()
                result = await speech_to_speech_pipeline.process_conversation_turn(
                    test_audio,
                    conversation_id=f"latency_test_{i+1}"
                )
                total_time = (time.time() - start_time) * 1000
                
                if result['success']:
                    latencies.append(total_time)
                    if 'stage_timings' in result:
                        stage_timings["stt"].append(result['stage_timings'].get('stt_ms', 0))
                        stage_timings["llm"].append(result['stage_timings'].get('llm_ms', 0))
                        stage_timings["tts"].append(result['stage_timings'].get('tts_ms', 0))
                    
                    print(f"   Test {i+1}: {total_time:.1f}ms {'✅' if total_time <= config.speech_to_speech.latency_target_ms else '⚠️'}")
                else:
                    print(f"   Test {i+1}: ❌ Failed - {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   Test {i+1}: ❌ Exception - {e}")
        
        # Calculate statistics
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            target_met_count = sum(1 for l in latencies if l <= config.speech_to_speech.latency_target_ms)
            target_met_rate = (target_met_count / len(latencies)) * 100
            
            results = {
                "total_tests": num_tests,
                "successful_tests": len(latencies),
                "avg_latency_ms": avg_latency,
                "min_latency_ms": min_latency,
                "max_latency_ms": max_latency,
                "target_latency_ms": config.speech_to_speech.latency_target_ms,
                "target_met_rate_percent": target_met_rate,
                "stage_averages": {
                    "stt_ms": sum(stage_timings["stt"]) / len(stage_timings["stt"]) if stage_timings["stt"] else 0,
                    "llm_ms": sum(stage_timings["llm"]) / len(stage_timings["llm"]) if stage_timings["llm"] else 0,
                    "tts_ms": sum(stage_timings["tts"]) / len(stage_timings["tts"]) if stage_timings["tts"] else 0
                }
            }
            
            print(f"\n📊 Latency Results:")
            print(f"   Average: {avg_latency:.1f}ms (target: {config.speech_to_speech.latency_target_ms}ms)")
            print(f"   Range: {min_latency:.1f}ms - {max_latency:.1f}ms")
            print(f"   Target met: {target_met_rate:.1f}% ({target_met_count}/{len(latencies)} tests)")
            print(f"   Stage breakdown: STT={results['stage_averages']['stt_ms']:.1f}ms, "
                  f"LLM={results['stage_averages']['llm_ms']:.1f}ms, "
                  f"TTS={results['stage_averages']['tts_ms']:.1f}ms")
            
            # Assessment
            if target_met_rate >= 90:
                print(f"   ✅ EXCELLENT performance")
            elif target_met_rate >= 75:
                print(f"   ⚠️ GOOD performance")
            else:
                print(f"   ❌ POOR performance")
        else:
            results = {"error": "No successful tests completed"}
            print(f"   ❌ All tests failed")
        
        return results
    
    async def test_audio_quality(self) -> Dict[str, Any]:
        """Test audio quality and synthesis capabilities"""
        print(f"\n🔊 Testing Audio Quality")
        print("-" * 50)
        
        test_phrases = [
            "Hello, this is a test of audio quality.",
            "The quick brown fox jumps over the lazy dog.",
            "Testing emotional expression with excitement and joy!",
            "This is a longer sentence to test the consistency of speech synthesis across extended utterances."
        ]
        
        quality_results = []
        
        for i, phrase in enumerate(test_phrases):
            try:
                result = await kokoro_model.synthesize_speech(
                    phrase,
                    voice="af_heart",
                    speed=1.0,
                    chunk_id=f"quality_test_{i+1}"
                )
                
                if result['success'] and len(result['audio_data']) > 0:
                    # Basic quality checks
                    audio_data = result['audio_data']
                    sample_rate = result['sample_rate']
                    
                    # Check for clipping
                    max_amplitude = np.max(np.abs(audio_data))
                    clipping_detected = max_amplitude >= 0.99
                    
                    # Check for silence
                    rms = np.sqrt(np.mean(audio_data ** 2))
                    too_quiet = rms < 0.001
                    
                    # Check duration reasonableness (rough estimate: ~150 words per minute)
                    word_count = len(phrase.split())
                    expected_duration = (word_count / 150) * 60  # seconds
                    actual_duration = len(audio_data) / sample_rate
                    duration_ratio = actual_duration / expected_duration if expected_duration > 0 else 0
                    
                    quality_score = 100
                    issues = []
                    
                    if clipping_detected:
                        quality_score -= 30
                        issues.append("clipping detected")
                    
                    if too_quiet:
                        quality_score -= 40
                        issues.append("audio too quiet")
                    
                    if duration_ratio < 0.5 or duration_ratio > 3.0:
                        quality_score -= 20
                        issues.append(f"unusual duration ratio: {duration_ratio:.1f}")
                    
                    quality_results.append({
                        "phrase": phrase,
                        "success": True,
                        "quality_score": max(0, quality_score),
                        "issues": issues,
                        "metrics": {
                            "max_amplitude": max_amplitude,
                            "rms": rms,
                            "duration_s": actual_duration,
                            "sample_rate": sample_rate
                        }
                    })
                    
                    # Save audio file for manual inspection
                    filename = f"quality_test_{i+1}.wav"
                    sf.write(filename, audio_data, sample_rate)
                    
                    status = "✅" if quality_score >= 80 else "⚠️" if quality_score >= 60 else "❌"
                    print(f"   Test {i+1}: {status} Quality score: {quality_score}/100")
                    if issues:
                        print(f"           Issues: {', '.join(issues)}")
                
                else:
                    quality_results.append({
                        "phrase": phrase,
                        "success": False,
                        "error": result.get('error', 'Unknown error')
                    })
                    print(f"   Test {i+1}: ❌ Synthesis failed")
                    
            except Exception as e:
                quality_results.append({
                    "phrase": phrase,
                    "success": False,
                    "error": str(e)
                })
                print(f"   Test {i+1}: ❌ Exception - {e}")
        
        # Overall quality assessment
        successful_tests = [r for r in quality_results if r.get('success', False)]
        if successful_tests:
            avg_quality = sum(r['quality_score'] for r in successful_tests) / len(successful_tests)
            print(f"\n📊 Audio Quality Results:")
            print(f"   Successful tests: {len(successful_tests)}/{len(test_phrases)}")
            print(f"   Average quality score: {avg_quality:.1f}/100")
            
            if avg_quality >= 85:
                print(f"   ✅ EXCELLENT audio quality")
            elif avg_quality >= 70:
                print(f"   ⚠️ GOOD audio quality")
            else:
                print(f"   ❌ POOR audio quality")
        
        return {
            "test_results": quality_results,
            "summary": {
                "total_tests": len(test_phrases),
                "successful_tests": len(successful_tests),
                "avg_quality_score": sum(r['quality_score'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
            }
        }
    
    async def test_stress_load(self, concurrent_requests: int = 5, duration_seconds: int = 30) -> Dict[str, Any]:
        """Test system under concurrent load"""
        print(f"\n🔥 Testing Stress Load ({concurrent_requests} concurrent requests for {duration_seconds}s)")
        print("-" * 50)
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0,
            "max_latency_ms": 0,
            "errors": []
        }
        
        async def single_request(request_id: int) -> Dict[str, Any]:
            """Single request for stress testing"""
            try:
                test_audio = self._generate_test_audio(duration=1.5)
                start_time = time.time()
                
                result = await speech_to_speech_pipeline.process_conversation_turn(
                    test_audio,
                    conversation_id=f"stress_test_{request_id}"
                )
                
                latency = (time.time() - start_time) * 1000
                
                return {
                    "success": result['success'],
                    "latency_ms": latency,
                    "error": result.get('error') if not result['success'] else None
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "latency_ms": 0,
                    "error": str(e)
                }
        
        # Run stress test
        start_time = time.time()
        request_id = 0
        latencies = []
        
        while time.time() - start_time < duration_seconds:
            # Launch concurrent requests
            tasks = []
            for _ in range(concurrent_requests):
                request_id += 1
                tasks.append(single_request(request_id))
            
            # Wait for completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed_requests"] += 1
                    results["errors"].append(str(result))
                elif result["success"]:
                    results["successful_requests"] += 1
                    latencies.append(result["latency_ms"])
                else:
                    results["failed_requests"] += 1
                    if result["error"]:
                        results["errors"].append(result["error"])
            
            results["total_requests"] = request_id
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        # Calculate final statistics
        if latencies:
            results["avg_latency_ms"] = sum(latencies) / len(latencies)
            results["max_latency_ms"] = max(latencies)
        
        success_rate = (results["successful_requests"] / results["total_requests"]) * 100 if results["total_requests"] > 0 else 0
        
        print(f"\n📊 Stress Test Results:")
        print(f"   Total requests: {results['total_requests']}")
        print(f"   Success rate: {success_rate:.1f}% ({results['successful_requests']}/{results['total_requests']})")
        print(f"   Average latency: {results['avg_latency_ms']:.1f}ms")
        print(f"   Max latency: {results['max_latency_ms']:.1f}ms")
        print(f"   Failed requests: {results['failed_requests']}")
        
        if success_rate >= 95:
            print(f"   ✅ EXCELLENT reliability under load")
        elif success_rate >= 85:
            print(f"   ⚠️ GOOD reliability under load")
        else:
            print(f"   ❌ POOR reliability under load")
        
        return results
    
    def _generate_test_audio(self, duration: float = 2.0, frequency: float = 440, sample_rate: int = 16000) -> np.ndarray:
        """Generate test audio signal"""
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Create a more speech-like signal with amplitude modulation
        carrier = np.sin(2 * np.pi * frequency * t)
        modulation = 0.5 * (1 + np.sin(2 * np.pi * 5 * t))  # 5 Hz modulation
        audio = (carrier * modulation * 0.1).astype(np.float32)
        return audio
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete production readiness test suite"""
        print("🧪 Production Readiness Test Suite for Speech-to-Speech AI")
        print("=" * 80)
        
        all_results = {}
        
        # Component initialization test
        all_results["component_initialization"] = await self.test_component_initialization()
        
        # Only proceed if components initialized successfully
        if all(r["status"] == "success" for r in all_results["component_initialization"].values()):
            # Latency performance test
            all_results["latency_performance"] = await self.test_latency_performance()
            
            # Audio quality test
            all_results["audio_quality"] = await self.test_audio_quality()
            
            # Stress load test
            all_results["stress_load"] = await self.test_stress_load()
        else:
            print("\n❌ Skipping remaining tests due to component initialization failures")
        
        # Generate final assessment
        assessment = self._generate_final_assessment(all_results)
        all_results["final_assessment"] = assessment
        
        return all_results
    
    def _generate_final_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final production readiness assessment"""
        print(f"\n🎯 Final Production Readiness Assessment")
        print("=" * 80)
        
        scores = {}
        
        # Component initialization score
        init_results = results.get("component_initialization", {})
        init_success = all(r.get("status") == "success" for r in init_results.values())
        scores["initialization"] = 100 if init_success else 0
        
        # Latency performance score
        latency_results = results.get("latency_performance", {})
        if "target_met_rate_percent" in latency_results:
            scores["latency"] = min(100, latency_results["target_met_rate_percent"] * 1.2)  # Bonus for exceeding
        else:
            scores["latency"] = 0
        
        # Audio quality score
        quality_results = results.get("audio_quality", {})
        if "summary" in quality_results:
            scores["audio_quality"] = quality_results["summary"]["avg_quality_score"]
        else:
            scores["audio_quality"] = 0
        
        # Reliability score (from stress test)
        stress_results = results.get("stress_load", {})
        if stress_results.get("total_requests", 0) > 0:
            success_rate = (stress_results["successful_requests"] / stress_results["total_requests"]) * 100
            scores["reliability"] = success_rate
        else:
            scores["reliability"] = 0
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores) if scores else 0
        
        # Determine readiness level
        if overall_score >= 90:
            readiness_level = "PRODUCTION READY"
            readiness_emoji = "🚀"
        elif overall_score >= 75:
            readiness_level = "STAGING READY"
            readiness_emoji = "⚠️"
        elif overall_score >= 50:
            readiness_level = "DEVELOPMENT READY"
            readiness_emoji = "🔧"
        else:
            readiness_level = "NOT READY"
            readiness_emoji = "❌"
        
        print(f"\n{readiness_emoji} OVERALL ASSESSMENT: {readiness_level}")
        print(f"📊 Overall Score: {overall_score:.1f}/100")
        print(f"\n📋 Component Scores:")
        for component, score in scores.items():
            emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"   {emoji} {component.replace('_', ' ').title()}: {score:.1f}/100")
        
        return {
            "overall_score": overall_score,
            "readiness_level": readiness_level,
            "component_scores": scores,
            "production_ready": overall_score >= 90
        }

async def main():
    """Main test execution"""
    test_suite = ProductionReadinessTestSuite()
    
    try:
        results = await test_suite.run_full_test_suite()
        
        # Save results to file
        with open('production_readiness_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results saved to: production_readiness_results.json")
        
        # Return appropriate exit code
        final_assessment = results.get("final_assessment", {})
        if final_assessment.get("production_ready", False):
            print(f"\n🎉 System is PRODUCTION READY!")
            return 0
        else:
            print(f"\n⚠️ System needs improvement before production deployment")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
