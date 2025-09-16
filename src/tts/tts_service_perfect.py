"""
Perfect TTS Service - Production-Ready Service Layer
Provides high-level TTS operations with performance monitoring and error handling
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from threading import Lock
import gc

# Import the perfect model
from .orpheus_perfect_model import OrpheusPerfectModel, ModelInitializationError, AudioGenerationError

# Setup logging
service_logger = logging.getLogger("tts_service_perfect")
service_logger.setLevel(logging.INFO)

class TTSServicePerfect:
    """
    Production-ready TTS service that provides high-level operations
    with performance monitoring, caching, and error handling
    """
    
    def __init__(self):
        self.model = OrpheusPerfectModel()
        self.is_initialized = False
        self.service_lock = Lock()
        
        # Service statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0
        self.total_audio_generated = 0  # bytes
        
        # Performance tracking
        self.request_history = []  # Last 100 requests
        self.max_history = 100
        
        service_logger.info("TTSServicePerfect initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the TTS service
        """
        try:
            with self.service_lock:
                if self.is_initialized:
                    service_logger.info("✅ TTSServicePerfect already initialized")
                    return True
                
                service_logger.info("🚀 Initializing TTSServicePerfect...")
                start_time = time.time()
                
                # Initialize the underlying model
                success = await self.model.initialize()
                
                if success:
                    self.is_initialized = True
                    init_time = time.time() - start_time
                    service_logger.info(f"🎉 TTSServicePerfect initialized successfully in {init_time:.2f}s")
                    return True
                else:
                    service_logger.error("❌ TTSServicePerfect initialization failed")
                    return False
                    
        except Exception as e:
            service_logger.error(f"❌ TTSServicePerfect initialization error: {e}")
            raise ModelInitializationError(f"Failed to initialize TTSServicePerfect: {e}")
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """
        Generate speech audio from text with performance tracking
        """
        if not self.is_initialized:
            raise AudioGenerationError("TTSServicePerfect not initialized")
        
        request_start = time.time()
        request_id = self.total_requests + 1
        
        try:
            service_logger.info(f"🎵 [Request {request_id}] Generating speech: '{text[:50]}...' with voice '{voice or 'default'}'")
            
            # Validate input
            if not text or not text.strip():
                raise AudioGenerationError("Empty text provided")
            
            if len(text) > 5000:  # Reasonable limit
                service_logger.warning(f"[Request {request_id}] Long text detected: {len(text)} characters")
            
            # Generate speech using the model
            audio_data = await self.model.generate_speech(text, voice)
            
            # Track success
            processing_time = time.time() - request_start
            self._record_successful_request(request_id, text, voice, processing_time, len(audio_data))
            
            service_logger.info(f"✅ [Request {request_id}] Speech generated successfully in {processing_time:.2f}s ({len(audio_data)} bytes)")
            
            return audio_data
            
        except Exception as e:
            # Track failure
            processing_time = time.time() - request_start
            self._record_failed_request(request_id, text, voice, processing_time, str(e))
            
            service_logger.error(f"❌ [Request {request_id}] Speech generation failed: {e}")
            raise AudioGenerationError(f"Speech generation failed: {e}")
    
    async def generate_speech_batch(self, texts: List[str], voice: str = None) -> List[bytes]:
        """
        Generate speech for multiple texts (batch processing)
        """
        if not self.is_initialized:
            raise AudioGenerationError("TTSServicePerfect not initialized")
        
        service_logger.info(f"🎵 Batch generating speech for {len(texts)} texts")
        
        results = []
        for i, text in enumerate(texts):
            try:
                audio_data = await self.generate_speech(text, voice)
                results.append(audio_data)
                service_logger.debug(f"✅ Batch item {i+1}/{len(texts)} completed")
            except Exception as e:
                service_logger.error(f"❌ Batch item {i+1}/{len(texts)} failed: {e}")
                results.append(b'')  # Empty audio for failed items
        
        successful_count = len([r for r in results if r])
        service_logger.info(f"✅ Batch completed: {successful_count}/{len(texts)} successful")
        
        return results
    
    def _record_successful_request(self, request_id: int, text: str, voice: str, processing_time: float, audio_size: int):
        """Record a successful request for statistics"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_processing_time += processing_time
        self.total_audio_generated += audio_size
        
        # Add to history
        request_record = {
            "request_id": request_id,
            "timestamp": time.time(),
            "text_length": len(text),
            "voice": voice,
            "processing_time": processing_time,
            "audio_size": audio_size,
            "success": True
        }
        
        self.request_history.append(request_record)
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    def _record_failed_request(self, request_id: int, text: str, voice: str, processing_time: float, error: str):
        """Record a failed request for statistics"""
        self.total_requests += 1
        self.failed_requests += 1
        
        # Add to history
        request_record = {
            "request_id": request_id,
            "timestamp": time.time(),
            "text_length": len(text),
            "voice": voice,
            "processing_time": processing_time,
            "error": error,
            "success": False
        }
        
        self.request_history.append(request_record)
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        if not self.is_initialized:
            return []
        return self.model.get_available_voices()
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get comprehensive service information and statistics"""
        base_info = {
            "service_name": "TTSServicePerfect",
            "is_initialized": self.is_initialized,
            "statistics": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": (
                    self.successful_requests / self.total_requests * 100 
                    if self.total_requests > 0 else 0.0
                ),
                "total_processing_time_s": self.total_processing_time,
                "average_processing_time_s": (
                    self.total_processing_time / self.successful_requests 
                    if self.successful_requests > 0 else 0.0
                ),
                "total_audio_generated_bytes": self.total_audio_generated,
                "average_audio_size_bytes": (
                    self.total_audio_generated / self.successful_requests 
                    if self.successful_requests > 0 else 0.0
                )
            }
        }
        
        # Add recent performance metrics
        if self.request_history:
            recent_requests = self.request_history[-10:]  # Last 10 requests
            successful_recent = [r for r in recent_requests if r["success"]]
            
            if successful_recent:
                avg_recent_time = sum(r["processing_time"] for r in successful_recent) / len(successful_recent)
                base_info["recent_performance"] = {
                    "last_10_requests_avg_time_s": avg_recent_time,
                    "last_10_requests_success_rate": len(successful_recent) / len(recent_requests) * 100
                }
        
        # Add model info if available
        if self.is_initialized:
            base_info["model_info"] = self.model.get_model_info()
        
        return base_info
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics"""
        if not self.request_history:
            return {"status": "no_data", "message": "No requests processed yet"}
        
        successful_requests = [r for r in self.request_history if r["success"]]
        
        if not successful_requests:
            return {"status": "no_successful_requests", "message": "No successful requests in history"}
        
        processing_times = [r["processing_time"] for r in successful_requests]
        audio_sizes = [r["audio_size"] for r in successful_requests]
        
        return {
            "status": "healthy",
            "total_requests_in_history": len(self.request_history),
            "successful_requests_in_history": len(successful_requests),
            "performance_metrics": {
                "min_processing_time_s": min(processing_times),
                "max_processing_time_s": max(processing_times),
                "avg_processing_time_s": sum(processing_times) / len(processing_times),
                "min_audio_size_bytes": min(audio_sizes),
                "max_audio_size_bytes": max(audio_sizes),
                "avg_audio_size_bytes": sum(audio_sizes) / len(audio_sizes)
            }
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        try:
            service_logger.info("🧹 Cleaning up TTSServicePerfect...")
            
            # Cleanup the underlying model
            await self.model.cleanup()
            
            # Reset state
            self.is_initialized = False
            
            service_logger.info("✅ TTSServicePerfect cleanup completed")
            
        except Exception as e:
            service_logger.error(f"❌ TTSServicePerfect cleanup failed: {e}")

# Global instance for easy access
tts_service_perfect = TTSServicePerfect()

# Test function for validation
async def test_tts_service():
    """Test the TTS service"""
    print("🧪 Testing TTSServicePerfect")
    print("=" * 50)
    
    try:
        # Initialize
        await tts_service_perfect.initialize()
        
        # Test single generation
        test_text = "Hello, this is a test of the perfect TTS service."
        audio_data = await tts_service_perfect.generate_speech(test_text, "tara")
        
        print(f"✅ Generated {len(audio_data)} bytes of audio")
        
        # Test batch generation
        batch_texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        batch_results = await tts_service_perfect.generate_speech_batch(batch_texts, "tara")
        successful_batch = len([r for r in batch_results if r])
        
        print(f"✅ Batch generation: {successful_batch}/{len(batch_texts)} successful")
        
        # Show service info
        info = tts_service_perfect.get_service_info()
        print(f"📊 Service info: {info['statistics']['total_requests']} requests, "
              f"{info['statistics']['success_rate']:.1f}% success rate")
        
        # Show performance summary
        perf = tts_service_perfect.get_performance_summary()
        if perf["status"] == "healthy":
            print(f"⚡ Performance: avg {perf['performance_metrics']['avg_processing_time_s']:.2f}s per request")
        
        # Cleanup
        await tts_service_perfect.cleanup()
        
        print("🎉 TTS service test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tts_service())
