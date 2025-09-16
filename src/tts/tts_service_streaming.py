"""
Streaming TTS Service - Uses Orpheus Streaming Model
Clean, efficient streaming TTS service based on official Flask example
"""

import asyncio
import time
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from threading import Lock

from src.tts.orpheus_streaming_model import orpheus_streaming_model
from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("tts_service_streaming")
tts_logger.setLevel(logging.INFO)

class TTSServiceStreaming:
    """
    Streaming TTS Service using Orpheus Streaming Model
    Based on official Flask example pattern
    """
    
    def __init__(self):
        self.is_initialized = False
        self.service_lock = Lock()
        
        # Performance tracking
        self.generation_count = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        self.total_bytes_generated = 0
        
        tts_logger.info("TTSServiceStreaming initialized")
    
    async def initialize(self) -> bool:
        """Initialize the streaming TTS service"""
        try:
            tts_logger.info("🚀 Initializing Streaming TTS Service...")
            start_time = time.time()
            
            # Initialize the streaming Orpheus model
            success = await orpheus_streaming_model.initialize()
            
            if success:
                self.is_initialized = True
                init_time = time.time() - start_time
                tts_logger.info(f"🎉 Streaming TTS Service initialized in {init_time:.2f}s")
                return True
            else:
                tts_logger.error("❌ Failed to initialize Orpheus streaming model")
                return False
                
        except Exception as e:
            tts_logger.error(f"❌ Streaming TTS Service initialization failed: {e}")
            return False
    
    async def generate_speech_stream(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming speech from text
        """
        if not self.is_initialized:
            tts_logger.error("❌ Streaming TTS Service not initialized")
            return
        
        try:
            generation_start = time.time()
            chunk_count = 0
            total_bytes = 0
            
            # Use the streaming Orpheus model
            async for chunk in orpheus_streaming_model.generate_speech_stream(text, voice):
                chunk_count += 1
                total_bytes += len(chunk)
                yield chunk
            
            # Track performance
            generation_time = time.time() - generation_start
            self.last_generation_time = generation_time
            self.generation_count += 1
            self.total_generation_time += generation_time
            self.total_bytes_generated += total_bytes
            
            tts_logger.info(
                f"✅ Streamed {chunk_count} chunks ({total_bytes} bytes) in {generation_time*1000:.1f}ms"
            )
                
        except Exception as e:
            tts_logger.error(f"❌ Streaming speech generation failed: {e}")
            return
    
    async def generate_speech(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Generate complete speech from text (non-streaming version)
        """
        if not self.is_initialized:
            tts_logger.error("❌ Streaming TTS Service not initialized")
            return None
        
        try:
            generation_start = time.time()
            
            # Use the streaming Orpheus model
            audio_data = await orpheus_streaming_model.generate_speech(text, voice)
            
            # Track performance
            generation_time = time.time() - generation_start
            self.last_generation_time = generation_time
            self.generation_count += 1
            self.total_generation_time += generation_time
            
            if audio_data:
                self.total_bytes_generated += len(audio_data)
                tts_logger.info(
                    f"✅ Generated {len(audio_data)} bytes in {generation_time*1000:.1f}ms "
                    f"(avg: {(self.total_generation_time/self.generation_count)*1000:.1f}ms)"
                )
                return audio_data
            else:
                tts_logger.error("❌ No audio data generated")
                return None
                
        except Exception as e:
            tts_logger.error(f"❌ Speech generation failed: {e}")
            return None
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return orpheus_streaming_model.get_available_voices()
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and statistics"""
        model_info = orpheus_streaming_model.get_model_info()
        
        service_info = {
            "service_name": "TTSServiceStreaming",
            "is_initialized": self.is_initialized,
            "generation_count": self.generation_count,
            "total_bytes_generated": self.total_bytes_generated,
            "last_generation_time_ms": self.last_generation_time * 1000,
            "average_generation_time_ms": (
                (self.total_generation_time / self.generation_count) * 1000 
                if self.generation_count > 0 else 0
            ),
            "model_info": model_info
        }
        
        return service_info
    
    async def cleanup(self):
        """Cleanup service resources"""
        try:
            tts_logger.info("🧹 Cleaning up Streaming TTS Service...")
            
            await orpheus_streaming_model.cleanup()
            
            self.is_initialized = False
            tts_logger.info("✅ Streaming TTS Service cleanup completed")
            
        except Exception as e:
            tts_logger.error(f"❌ Streaming TTS Service cleanup failed: {e}")

# Global service instance
tts_service_streaming = TTSServiceStreaming()

# Test function
async def test_streaming_tts_service():
    """Test the streaming TTS service"""
    print("🧪 Testing Streaming TTS Service")
    print("=" * 40)
    
    try:
        # Initialize
        success = await tts_service_streaming.initialize()
        if not success:
            print("❌ Initialization failed")
            return
        
        # Test streaming generation
        test_text = "Hello, this is a test of the streaming TTS service."
        
        print("Testing streaming generation...")
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in tts_service_streaming.generate_speech_stream(test_text, "tara"):
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count <= 3:
                print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
        
        print(f"✅ Streamed {chunk_count} chunks, {total_bytes} total bytes")
        
        # Test complete generation
        print("Testing complete generation...")
        audio_data = await tts_service_streaming.generate_speech(test_text, "tara")
        
        if audio_data:
            print(f"✅ Generated {len(audio_data)} bytes of complete audio")
        else:
            print("❌ No complete audio generated")
        
        # Show service info
        info = tts_service_streaming.get_service_info()
        print(f"📊 Service info: {info}")
        
        # Cleanup
        await tts_service_streaming.cleanup()
        
        print("🎉 Streaming TTS Service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_tts_service())