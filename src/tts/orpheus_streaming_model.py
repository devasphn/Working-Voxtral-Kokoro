"""
Orpheus Streaming TTS Model - Based on Official Flask Example
Uses the exact streaming API pattern from canopyai/Orpheus-TTS repository
"""

import asyncio
import time
import logging
import struct
import io
from typing import Dict, Any, Optional, List, AsyncGenerator
from threading import Lock
import gc

# Defer Orpheus TTS import to avoid immediate CUDA initialization
ORPHEUS_AVAILABLE = False
OrpheusModel = None

def _import_orpheus():
    """Lazy import of OrpheusModel to avoid immediate CUDA initialization"""
    global ORPHEUS_AVAILABLE, OrpheusModel
    if OrpheusModel is None:
        try:
            from orpheus_tts import OrpheusModel as _OrpheusModel
            OrpheusModel = _OrpheusModel
            ORPHEUS_AVAILABLE = True
            orpheus_logger.info("✅ OrpheusModel imported successfully")
        except ImportError as e:
            ORPHEUS_AVAILABLE = False
            OrpheusModel = None
            orpheus_logger.error(f"❌ Failed to import OrpheusModel: {e}")
        except Exception as e:
            ORPHEUS_AVAILABLE = False
            OrpheusModel = None
            orpheus_logger.error(f"❌ Error during OrpheusModel import: {e}")
    return ORPHEUS_AVAILABLE

# Setup logging
orpheus_logger = logging.getLogger("orpheus_streaming")
orpheus_logger.setLevel(logging.INFO)

class ModelInitializationError(Exception):
    """Raised when Orpheus model initialization fails"""
    pass

class AudioGenerationError(Exception):
    """Raised when TTS generation fails"""
    pass

class OrpheusStreamingModel:
    """
    Orpheus Streaming TTS Model - Based on Official Flask Example
    Uses the exact streaming API pattern from the official repository
    """
    
    def __init__(self):
        self.model = None
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Configuration from official Flask example
        self.model_name = "canopylabs/orpheus-tts-0.1-finetune-prod"
        self.sample_rate = 24000
        self.bits_per_sample = 16
        self.channels = 1
        
        # No memory parameters needed - OrpheusModel handles this internally
        
        # Available voices from official documentation
        self.available_voices = [
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",  # English
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",      # German
            "유나", "준서",                # Korean
            "长乐", "白芷",                # Mandarin
            "javi", "sergio", "maria",    # Spanish
            "pietro", "giulia", "carlo"   # Italian
        ]
        self.default_voice = "tara"
        
        orpheus_logger.info(f"OrpheusStreamingModel initialized with model: {self.model_name}")
    
    def create_wav_header(self, data_size: int = 0) -> bytes:
        """
        Create WAV header - EXACT implementation from Flask example
        """
        byte_rate = self.sample_rate * self.channels * self.bits_per_sample // 8
        block_align = self.channels * self.bits_per_sample // 8
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,        # File size
            b'WAVE',
            b'fmt ',
            16,                    # PCM format size
            1,                     # PCM format
            self.channels,
            self.sample_rate,
            byte_rate,
            block_align,
            self.bits_per_sample,
            b'data',
            data_size
        )
        return header
    
    async def initialize(self) -> bool:
        """
        Initialize Orpheus model with memory optimization
        """
        try:
            orpheus_logger.info("🚀 Initializing Orpheus Streaming Model...")
            start_time = time.time()

            # Import OrpheusModel with lazy loading
            if not _import_orpheus():
                raise ModelInitializationError(
                    "orpheus_tts package not available or failed to import. Install with: pip install orpheus-speech"
                )
            
            # EXACT initialization from your Flask example
            orpheus_logger.info(f"📥 Loading Orpheus model: {self.model_name}")
            
            # CORRECT initialization - exactly as in your Flask example
            self.model = OrpheusModel(model_name=self.model_name)
            
            orpheus_logger.info("✅ Orpheus model loaded successfully with streaming API")
            
            # Test the model with a simple generation
            await self._test_streaming()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            orpheus_logger.info(f"🎉 Orpheus Streaming Model initialized in {init_time:.2f}s")
            
            return True
            
        except Exception as e:
            orpheus_logger.error(f"❌ Orpheus model initialization failed: {e}")
            import traceback
            orpheus_logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise ModelInitializationError(f"Failed to initialize Orpheus model: {e}")
    
    async def _test_streaming(self):
        """Test the model with streaming generation"""
        try:
            orpheus_logger.info("🧪 Testing streaming generation...")
            
            # Simple test generation using EXACT Flask example parameters
            test_prompt = "Hello, this is a test."
            syn_tokens = self.model.generate_speech(
                prompt=test_prompt,
                voice=self.default_voice,
                repetition_penalty=1.1,
                stop_token_ids=[128258],
                max_tokens=100,  # Small test
                temperature=0.4,
                top_p=0.9
            )
            
            # Count chunks to verify streaming works
            chunk_count = 0
            for _ in syn_tokens:
                chunk_count += 1
                if chunk_count >= 3:  # Just test first few chunks
                    break
            
            if chunk_count > 0:
                orpheus_logger.info(f"✅ Streaming test successful - generated {chunk_count} audio chunks")
            else:
                raise Exception("No audio chunks generated in streaming test")
                
        except Exception as e:
            orpheus_logger.error(f"❌ Streaming test failed: {e}")
            raise
    
    async def generate_speech_stream(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Generate streaming speech - EXACT implementation from Flask example
        """
        if not self.is_initialized:
            raise AudioGenerationError("Model not initialized")
        
        voice = voice or self.default_voice
        
        try:
            orpheus_logger.info(f"🎵 Streaming speech: '{text[:50]}...' with voice '{voice}'")
            generation_start = time.time()
            
            with self.model_lock:
                # Yield WAV header first - EXACT from Flask example
                yield self.create_wav_header()
                
                # Generate speech using EXACT Flask example parameters
                syn_tokens = self.model.generate_speech(
                    prompt=text,
                    voice=voice,
                    repetition_penalty=1.1,
                    stop_token_ids=[128258],
                    max_tokens=2000,
                    temperature=0.4,
                    top_p=0.9
                )
                
                chunk_count = 0
                total_bytes = 0
                
                # Stream audio chunks - EXACT from Flask example
                for chunk in syn_tokens:
                    chunk_count += 1
                    total_bytes += len(chunk)
                    yield chunk
                
                generation_time = time.time() - generation_start
                orpheus_logger.info(
                    f"✅ Streamed {chunk_count} chunks ({total_bytes} bytes) in {generation_time:.2f}s"
                )
            
        except Exception as e:
            orpheus_logger.error(f"❌ Streaming generation failed: {e}")
            raise AudioGenerationError(f"Streaming generation failed: {e}")
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """
        Generate complete speech audio (non-streaming version)
        """
        if not self.is_initialized:
            raise AudioGenerationError("Model not initialized")
        
        voice = voice or self.default_voice
        
        try:
            orpheus_logger.info(f"🎵 Generating complete speech: '{text[:50]}...' with voice '{voice}'")
            
            # Collect all streaming chunks
            audio_buffer = io.BytesIO()
            
            async for chunk in self.generate_speech_stream(text, voice):
                audio_buffer.write(chunk)
            
            audio_data = audio_buffer.getvalue()
            orpheus_logger.info(f"✅ Generated complete audio: {len(audio_data)} bytes")
            
            return audio_data
            
        except Exception as e:
            orpheus_logger.error(f"❌ Complete speech generation failed: {e}")
            raise AudioGenerationError(f"Complete speech generation failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "sample_rate": self.sample_rate,
            "bits_per_sample": self.bits_per_sample,
            "channels": self.channels,
            "api_version": "streaming_orpheus_tts",
            "integration_type": "direct_streaming"
        }
    
    async def cleanup(self):
        """Cleanup model resources"""
        try:
            orpheus_logger.info("🧹 Cleaning up Orpheus Streaming Model resources...")
            
            if self.model:
                del self.model
                self.model = None
            
            # Force garbage collection
            gc.collect()
            
            self.is_initialized = False
            orpheus_logger.info("✅ Cleanup completed")
            
        except Exception as e:
            orpheus_logger.error(f"❌ Cleanup failed: {e}")

# Global instance for easy access
orpheus_streaming_model = OrpheusStreamingModel()

# Test function to verify the streaming integration
async def test_streaming_integration():
    """Test the streaming integration"""
    print("🧪 Testing Orpheus Streaming TTS Integration")
    print("=" * 50)
    
    try:
        # Initialize
        await orpheus_streaming_model.initialize()
        
        # Test streaming generation
        test_prompt = "Hello, this is a test of the streaming TTS integration."
        
        print("Testing streaming generation...")
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in orpheus_streaming_model.generate_speech_stream(test_prompt, "tara"):
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count <= 3:  # Show first few chunks
                print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
        
        print(f"✅ Streamed {chunk_count} chunks, {total_bytes} total bytes")
        
        # Test complete generation
        print("Testing complete generation...")
        audio_data = await orpheus_streaming_model.generate_speech(test_prompt, "tara")
        print(f"✅ Generated complete audio: {len(audio_data)} bytes")
        
        # Show model info
        print(f"📊 Model info: {orpheus_streaming_model.get_model_info()}")
        
        # Cleanup
        await orpheus_streaming_model.cleanup()
        
        print("🎉 Streaming integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming_integration())