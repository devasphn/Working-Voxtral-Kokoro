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

# Import the actual streaming model
from .orpheus_streaming_model import OrpheusStreamingModel, ModelInitializationError, AudioGenerationError

# Setup logging
perfect_logger = logging.getLogger("orpheus_perfect")
perfect_logger.setLevel(logging.INFO)

class OrpheusPerfectModel:
    """
    Production-ready Orpheus model wrapper that provides the interface
    expected by the unified model manager while using the streaming implementation
    """
    
    def __init__(self):
        self.streaming_model = OrpheusStreamingModel()
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
                
                # Initialize the underlying streaming model
                success = await self.streaming_model.initialize()
                
                if success:
                    self.is_initialized = True
                    init_time = time.time() - start_time
                    perfect_logger.info(f"🎉 OrpheusPerfectModel initialized successfully in {init_time:.2f}s")
                    
                    # Log device and memory pool info if provided
                    if device:
                        perfect_logger.info(f"🎯 Target device: {device}")
                    if shared_memory_pool:
                        perfect_logger.info("🏊 Using shared memory pool for optimization")
                    
                    return True
                else:
                    perfect_logger.error("❌ OrpheusPerfectModel initialization failed")
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
            
            # Use the streaming model's generate_speech method
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
            
            # Use the streaming model's generate_speech_stream method
            async for chunk in self.streaming_model.generate_speech_stream(text, voice):
                yield chunk
                
        except Exception as e:
            perfect_logger.error(f"❌ Streaming speech generation failed: {e}")
            raise AudioGenerationError(f"Streaming speech generation failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.streaming_model.get_available_voices()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        base_info = self.streaming_model.get_model_info()
        
        # Add perfect model wrapper info
        perfect_info = {
            "wrapper_type": "OrpheusPerfectModel",
            "is_initialized": self.is_initialized,
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
            
            # Cleanup the underlying streaming model
            await self.streaming_model.cleanup()
            
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
