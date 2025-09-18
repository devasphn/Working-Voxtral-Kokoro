"""
Orpheus Perfect Model - Production-Ready Wrapper
Provides the interface expected by the unified model manager while using OrpheusStreamingModel
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from threading import Lock
import gc

# Import the actual streaming model and Kokoro fallback
try:
    from .orpheus_streaming_model import OrpheusStreamingModel, ModelInitializationError, AudioGenerationError
    ORPHEUS_STREAMING_AVAILABLE = True
except Exception as e:
    perfect_logger.warning(f"OrpheusStreamingModel not available: {e}")
    ORPHEUS_STREAMING_AVAILABLE = False

# Import Kokoro TTS as fallback
try:
    from src.models.kokoro_model_realtime import KokoroTTSModel
    KOKORO_AVAILABLE = True
except Exception as e:
    perfect_logger.warning(f"Kokoro TTS not available: {e}")
    KOKORO_AVAILABLE = False

class ModelInitializationError(Exception):
    """Raised when model initialization fails"""
    pass

class AudioGenerationError(Exception):
    """Raised when TTS generation fails"""
    pass

# Setup logging
perfect_logger = logging.getLogger("orpheus_perfect")
perfect_logger.setLevel(logging.INFO)

class OrpheusPerfectModel:
    """
    Production-ready Orpheus model wrapper that provides the interface
    expected by the unified model manager while using the streaming implementation
    """
    
    def __init__(self):
        self.streaming_model = None
        self.kokoro_model = None
        self.use_kokoro = False
        self.is_initialized = False
        self.initialization_lock = Lock()

        # Performance tracking
        self.generation_count = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0

        perfect_logger.info("OrpheusPerfectModel wrapper initialized")
    
    async def initialize(self, device: str = "cuda", shared_memory_pool: Optional[Any] = None) -> bool:
        """
        Initialize the Orpheus model with optional device and memory pool
        """
        try:
            with self.initialization_lock:
                if self.is_initialized:
                    perfect_logger.info("✅ OrpheusPerfectModel already initialized")
                    return True
                
                perfect_logger.info("🚀 Initializing OrpheusPerfectModel...")
                start_time = time.time()

                # Try to initialize Kokoro TTS first (primary due to storage constraints)
                if KOKORO_AVAILABLE:
                    try:
                        perfect_logger.info("🎵 Initializing Kokoro TTS (primary)...")
                        self.kokoro_model = KokoroTTSModel()
                        success = await self.kokoro_model.initialize()

                        if success:
                            self.use_kokoro = True
                            self.is_initialized = True
                            init_time = time.time() - start_time
                            perfect_logger.info(f"🎉 OrpheusPerfectModel (Kokoro primary) initialized successfully in {init_time:.2f}s")

                            # Log device and memory pool info if provided
                            if device:
                                perfect_logger.info(f"🎯 Target device: {device}")
                            if shared_memory_pool:
                                perfect_logger.info("🏊 Using shared memory pool for optimization")

                            return True
                        else:
                            perfect_logger.warning("⚠️ Kokoro TTS failed, falling back to Orpheus...")
                    except Exception as e:
                        perfect_logger.warning(f"⚠️ Kokoro TTS error: {e}, falling back to Orpheus...")

                # Fall back to Orpheus streaming model (if storage allows)
                if ORPHEUS_STREAMING_AVAILABLE:
                    perfect_logger.info("🔄 Initializing Orpheus TTS fallback...")
                    try:
                        self.streaming_model = OrpheusStreamingModel()
                        success = await self.streaming_model.initialize()

                        if success:
                            self.use_kokoro = False
                            self.is_initialized = True
                            init_time = time.time() - start_time
                            perfect_logger.info(f"🎉 OrpheusPerfectModel (Orpheus fallback) initialized successfully in {init_time:.2f}s")
                            return True
                        else:
                            perfect_logger.error("❌ Both Kokoro and Orpheus TTS initialization failed")
                    except Exception as e:
                        perfect_logger.error(f"❌ Orpheus fallback error: {e}")
                else:
                    perfect_logger.error("❌ Kokoro failed and Orpheus TTS not available")
                    return False
                    
        except Exception as e:
            perfect_logger.error(f"❌ OrpheusPerfectModel initialization error: {e}")
            raise ModelInitializationError(f"Failed to initialize OrpheusPerfectModel: {e}")
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """
        Generate speech audio from text
        """
        if not self.is_initialized:
            raise AudioGenerationError("OrpheusPerfectModel not initialized")
        
        try:
            generation_start = time.time()
            perfect_logger.info(f"🎵 Generating speech: '{text[:50]}...' with voice '{voice or 'default'}'")
            
            # Use the appropriate model's generate_speech method
            if self.use_kokoro:
                # Kokoro returns a different format, need to extract audio_data
                result = await self.kokoro_model.synthesize_speech(text, voice)
                if result.get('success', False):
                    audio_data = result['audio_data']
                    # Convert numpy array to bytes if needed
                    if hasattr(audio_data, 'tobytes'):
                        audio_data = audio_data.tobytes()
                else:
                    raise AudioGenerationError(f"Kokoro TTS generation failed: {result.get('error', 'Unknown error')}")
            else:
                audio_data = await self.streaming_model.generate_speech(text, voice)
            
            generation_time = time.time() - generation_start
            self.last_generation_time = generation_time
            self.total_generation_time += generation_time
            self.generation_count += 1
            
            perfect_logger.info(f"✅ Speech generated in {generation_time:.2f}s ({len(audio_data)} bytes)")
            
            return audio_data
            
        except Exception as e:
            perfect_logger.error(f"❌ Speech generation failed: {e}")
            raise AudioGenerationError(f"Speech generation failed: {e}")
    
    async def generate_speech_stream(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming speech audio from text
        """
        if not self.is_initialized:
            raise AudioGenerationError("OrpheusPerfectModel not initialized")
        
        try:
            perfect_logger.info(f"🎵 Streaming speech: '{text[:50]}...' with voice '{voice or 'default'}'")
            
            # Use the appropriate model's generate_speech_stream method
            if self.use_kokoro:
                # Kokoro doesn't have streaming, so generate full audio and chunk it
                result = await self.kokoro_model.synthesize_speech(text, voice)
                if result.get('success', False):
                    audio_data = result['audio_data']
                    if hasattr(audio_data, 'tobytes'):
                        audio_bytes = audio_data.tobytes()
                    else:
                        audio_bytes = audio_data

                    # Yield in chunks for streaming effect
                    chunk_size = 1024
                    for i in range(0, len(audio_bytes), chunk_size):
                        yield audio_bytes[i:i + chunk_size]
                else:
                    raise AudioGenerationError(f"Kokoro TTS streaming failed: {result.get('error', 'Unknown error')}")
            else:
                async for chunk in self.streaming_model.generate_speech_stream(text, voice):
                    yield chunk
                
        except Exception as e:
            perfect_logger.error(f"❌ Streaming speech generation failed: {e}")
            raise AudioGenerationError(f"Streaming speech generation failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        if self.use_kokoro:
            # Kokoro has different voice system, return basic voices
            return ["default", "ऋतिका"]
        elif self.streaming_model:
            return self.streaming_model.get_available_voices()
        else:
            return ["ऋतिका"]  # Default fallback
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        if self.use_kokoro:
            base_info = {
                "model_name": "Kokoro TTS (fallback)",
                "status": "kokoro_fallback",
                "integration_type": "kokoro_tts"
            }
        elif self.streaming_model:
            base_info = self.streaming_model.get_model_info()
        else:
            base_info = {"model_name": "not_initialized"}

        # Add perfect model wrapper info
        perfect_info = {
            "wrapper_type": "OrpheusPerfectModel",
            "is_initialized": self.is_initialized,
            "using_mock": self.use_mock,
            "generation_statistics": {
                "total_generations": self.generation_count,
                "average_generation_time_s": (
                    self.total_generation_time / self.generation_count
                    if self.generation_count > 0 else 0.0
                ),
                "last_generation_time_s": self.last_generation_time
            },
            "underlying_model": base_info
        }

        return perfect_info
    
    async def cleanup(self):
        """Cleanup model resources"""
        try:
            perfect_logger.info("🧹 Cleaning up OrpheusPerfectModel...")
            
            # Cleanup the underlying models
            if self.streaming_model:
                await self.streaming_model.cleanup()
            if self.mock_model:
                await self.mock_model.cleanup()
            
            # Reset state
            self.is_initialized = False
            self.generation_count = 0
            self.total_generation_time = 0.0
            self.last_generation_time = 0.0
            
            perfect_logger.info("✅ OrpheusPerfectModel cleanup completed")
            
        except Exception as e:
            perfect_logger.error(f"❌ OrpheusPerfectModel cleanup failed: {e}")

# Global instance for easy access
orpheus_perfect_model = OrpheusPerfectModel()

# Test function for validation
async def test_perfect_model():
    """Test the perfect model wrapper"""
    print("🧪 Testing OrpheusPerfectModel Wrapper")
    print("=" * 50)
    
    try:
        # Initialize
        await orpheus_perfect_model.initialize()
        
        # Test generation
        test_text = "Hello, this is a test of the perfect model wrapper."
        audio_data = await orpheus_perfect_model.generate_speech(test_text, "tara")
        
        print(f"✅ Generated {len(audio_data)} bytes of audio")
        
        # Test streaming
        print("Testing streaming generation...")
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in orpheus_perfect_model.generate_speech_stream(test_text, "tara"):
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count <= 3:  # Show first few chunks
                print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
        
        print(f"✅ Streamed {chunk_count} chunks, {total_bytes} total bytes")
        
        # Show model info
        info = orpheus_perfect_model.get_model_info()
        print(f"📊 Model info: {info['wrapper_type']}, generations: {info['generation_statistics']['total_generations']}")
        
        # Cleanup
        await orpheus_perfect_model.cleanup()
        
        print("🎉 Perfect model wrapper test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_perfect_model())
