"""
Mock TTS Service for Testing and Fallback
Provides a simple TTS interface that generates silence or beeps for testing
"""

import asyncio
import time
import logging
import struct
import io
from typing import Dict, Any, Optional, List, AsyncGenerator
import numpy as np

# Setup logging
mock_logger = logging.getLogger("mock_tts")
mock_logger.setLevel(logging.INFO)

class MockTTSService:
    """
    Mock TTS service for testing and fallback scenarios
    Generates simple audio responses without requiring heavy models
    """
    
    def __init__(self):
        self.is_initialized = False
        self.sample_rate = 24000
        self.bits_per_sample = 16
        self.channels = 1
        
        # Available mock voices
        self.available_voices = [
            "mock_tara", "mock_leah", "mock_jess", "mock_leo", 
            "mock_dan", "mock_mia", "mock_zac", "mock_zoe",
            "mock_ऋतिका"  # Mock Hindi voice
        ]
        self.default_voice = "mock_ऋतिका"
        
        mock_logger.info("MockTTSService initialized")
    
    def create_wav_header(self, data_size: int = 0) -> bytes:
        """Create WAV header for audio data"""
        byte_rate = self.sample_rate * self.channels * self.bits_per_sample // 8
        block_align = self.channels * self.bits_per_sample // 8
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',
            36 + data_size,
            b'WAVE',
            b'fmt ',
            16,
            1,
            self.channels,
            self.sample_rate,
            byte_rate,
            block_align,
            self.bits_per_sample,
            b'data',
            data_size
        )
        return header
    
    def generate_mock_audio(self, text: str, voice: str = None) -> bytes:
        """
        Generate mock audio data based on text length
        Creates a simple tone or silence pattern
        """
        voice = voice or self.default_voice
        
        # Calculate duration based on text length (roughly 150 words per minute)
        words = len(text.split())
        duration_seconds = max(0.5, words * 0.4)  # Minimum 0.5s, ~0.4s per word
        
        # Generate audio samples
        num_samples = int(duration_seconds * self.sample_rate)
        
        # Create a simple tone pattern to simulate speech
        t = np.linspace(0, duration_seconds, num_samples)
        
        # Generate a simple pattern that varies with text content
        text_hash = hash(text) % 1000
        base_freq = 200 + (text_hash % 300)  # Frequency between 200-500 Hz
        
        # Create a modulated tone that sounds more speech-like
        audio = np.sin(2 * np.pi * base_freq * t) * 0.1
        audio += np.sin(2 * np.pi * (base_freq * 1.5) * t) * 0.05
        audio *= np.exp(-t * 0.5)  # Fade out
        
        # Add some variation to make it less monotonous
        modulation = np.sin(2 * np.pi * 5 * t) * 0.3 + 0.7
        audio *= modulation
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        
        # Create complete WAV file
        wav_header = self.create_wav_header(len(audio_bytes))
        return wav_header + audio_bytes
    
    async def initialize(self) -> bool:
        """Initialize the mock TTS service"""
        try:
            mock_logger.info("🚀 Initializing Mock TTS Service...")
            start_time = time.time()
            
            # Simulate initialization delay
            await asyncio.sleep(0.1)
            
            self.is_initialized = True
            init_time = time.time() - start_time
            mock_logger.info(f"🎉 Mock TTS Service initialized in {init_time:.2f}s")
            
            return True
            
        except Exception as e:
            mock_logger.error(f"❌ Mock TTS initialization failed: {e}")
            return False
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """Generate complete speech audio (non-streaming version)"""
        if not self.is_initialized:
            raise RuntimeError("Mock TTS service not initialized")
        
        voice = voice or self.default_voice
        
        try:
            mock_logger.info(f"🎵 Generating mock speech: '{text[:50]}...' with voice '{voice}'")
            generation_start = time.time()
            
            # Simulate generation time
            await asyncio.sleep(0.05)  # 50ms simulation
            
            audio_data = self.generate_mock_audio(text, voice)
            
            generation_time = time.time() - generation_start
            mock_logger.info(f"✅ Generated mock audio: {len(audio_data)} bytes in {generation_time:.2f}s")
            
            return audio_data
            
        except Exception as e:
            mock_logger.error(f"❌ Mock speech generation failed: {e}")
            raise RuntimeError(f"Mock speech generation failed: {e}")
    
    async def generate_speech_stream(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """Generate streaming speech audio"""
        if not self.is_initialized:
            raise RuntimeError("Mock TTS service not initialized")
        
        voice = voice or self.default_voice
        
        try:
            mock_logger.info(f"🎵 Streaming mock speech: '{text[:50]}...' with voice '{voice}'")
            
            # Generate complete audio first
            audio_data = self.generate_mock_audio(text, voice)
            
            # Yield WAV header first
            header_size = 44  # Standard WAV header size
            yield audio_data[:header_size]
            
            # Stream audio data in chunks
            audio_content = audio_data[header_size:]
            chunk_size = 1024  # 1KB chunks
            
            for i in range(0, len(audio_content), chunk_size):
                chunk = audio_content[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
            
            mock_logger.info(f"✅ Streamed mock audio: {len(audio_data)} bytes")
            
        except Exception as e:
            mock_logger.error(f"❌ Mock streaming generation failed: {e}")
            raise RuntimeError(f"Mock streaming generation failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available mock voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information"""
        return {
            "model_name": "MockTTSService",
            "is_initialized": self.is_initialized,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "sample_rate": self.sample_rate,
            "bits_per_sample": self.bits_per_sample,
            "channels": self.channels,
            "api_version": "mock_tts_v1.0",
            "integration_type": "mock_fallback"
        }
    
    async def cleanup(self):
        """Cleanup mock TTS resources"""
        try:
            mock_logger.info("🧹 Cleaning up Mock TTS Service...")
            self.is_initialized = False
            mock_logger.info("✅ Mock TTS cleanup completed")
        except Exception as e:
            mock_logger.error(f"❌ Mock TTS cleanup failed: {e}")

# Global instance for easy access
mock_tts_service = MockTTSService()

# Test function
async def test_mock_tts():
    """Test the mock TTS service"""
    print("🧪 Testing Mock TTS Service")
    print("=" * 50)
    
    try:
        # Initialize
        await mock_tts_service.initialize()
        
        # Test generation
        test_text = "Hello, this is a test of the mock TTS service."
        audio_data = await mock_tts_service.generate_speech(test_text, "mock_ऋतिका")
        
        print(f"✅ Generated {len(audio_data)} bytes of mock audio")
        
        # Test streaming
        print("Testing streaming generation...")
        chunk_count = 0
        total_bytes = 0
        
        async for chunk in mock_tts_service.generate_speech_stream(test_text, "mock_ऋतिका"):
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count <= 3:  # Show first few chunks
                print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
        
        print(f"✅ Streamed {chunk_count} chunks, {total_bytes} total bytes")
        
        # Show model info
        info = mock_tts_service.get_model_info()
        print(f"📊 Model info: {info['model_name']}, voices: {info['available_voices']}")
        
        # Cleanup
        await mock_tts_service.cleanup()
        
        print("🎉 Mock TTS service test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock_tts())
