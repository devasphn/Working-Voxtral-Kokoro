"""
Perfect Orpheus TTS Integration - Based on Official Example
Uses the exact API pattern from canopyai/Orpheus-TTS repository
"""

import torch
import asyncio
import time
import logging
import wave
import io
from typing import Dict, Any, Optional, List
from threading import Lock
import gc

# Import official Orpheus TTS - exactly as in the example
try:
    from orpheus_tts import OrpheusModel
    ORPHEUS_AVAILABLE = True
except ImportError:
    ORPHEUS_AVAILABLE = False
    OrpheusModel = None

# Setup logging
orpheus_logger = logging.getLogger("orpheus_perfect")
orpheus_logger.setLevel(logging.INFO)

class ModelInitializationError(Exception):
    """Raised when Orpheus model initialization fails"""
    pass

class AudioGenerationError(Exception):
    """Raised when TTS generation fails"""
    pass

class OrpheusPerfectModel:
    """
    Perfect Orpheus TTS Integration - Based on Official Example
    Uses the exact API pattern from the official repository
    """
    
    def __init__(self):
        self.model = None
        self.model_lock = Lock()
        self.is_initialized = False
        
        # EXACT configuration from official example
        self.model_name = "canopylabs/orpheus-tts-0.1-finetune-prod"
        self.max_model_len = 2048
        self.sample_rate = 24000  # As per official example
        
        # Available voices from official documentation
        self.available_voices = [
            # English voices
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",
            # Multi-language voices (if supported)
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",      # German
            "유나", "준서",                # Korean
            "长乐", "白芷",                # Mandarin
            "javi", "sergio", "maria",    # Spanish
            "pietro", "giulia", "carlo"   # Italian
        ]
        self.default_voice = "tara"  # Using English as default for reliability
        
        orpheus_logger.info(f"OrpheusPerfectModel initialized with model: {self.model_name}")
    
    async def initialize(self, device: str = None) -> bool:
        """
        Initialize Orpheus model using the EXACT official API
        """
        try:
            orpheus_logger.info("🚀 Initializing Perfect Orpheus Model...")
            start_time = time.time()
            
            # Check if orpheus_tts is available
            if not ORPHEUS_AVAILABLE:
                raise ModelInitializationError(
                    "orpheus_tts package not installed. Install with: pip install orpheus-tts"
                )
            
            # Initialize using EXACT official API pattern
            orpheus_logger.info(f"📥 Loading Orpheus model: {self.model_name}")
            
            # EXACT initialization from official example
            self.model = OrpheusModel(
                model_name=self.model_name,
                max_model_len=self.max_model_len
            )
            
            orpheus_logger.info("✅ Orpheus model loaded successfully with official API")
            
            # Test the model with a simple generation
            await self._test_model()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            orpheus_logger.info(f"🎉 Perfect Orpheus Model initialized in {init_time:.2f}s")
            
            return True
            
        except Exception as e:
            orpheus_logger.error(f"❌ Orpheus model initialization failed: {e}")
            import traceback
            orpheus_logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise ModelInitializationError(f"Failed to initialize Orpheus model: {e}")
    
    async def _test_model(self):
        """Test the model with a simple generation to ensure it works"""
        try:
            orpheus_logger.info("🧪 Testing model with simple generation...")
            
            # Simple test generation
            test_prompt = "Hello, this is a test."
            syn_tokens = self.model.generate_speech(
                prompt=test_prompt,
                voice=self.default_voice
            )
            
            # Count chunks to verify streaming works
            chunk_count = 0
            for _ in syn_tokens:
                chunk_count += 1
                if chunk_count >= 3:  # Just test first few chunks
                    break
            
            if chunk_count > 0:
                orpheus_logger.info(f"✅ Model test successful - generated {chunk_count} audio chunks")
            else:
                raise Exception("No audio chunks generated in test")
                
        except Exception as e:
            orpheus_logger.error(f"❌ Model test failed: {e}")
            raise
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """
        Generate speech using EXACT official API pattern
        Based on the exact example from canopyai/Orpheus-TTS
        """
        if not self.is_initialized:
            raise AudioGenerationError("Model not initialized")
        
        voice = voice or self.default_voice
        
        try:
            orpheus_logger.info(f"🎵 Generating speech: '{text[:50]}...' with voice '{voice}'")
            generation_start = time.monotonic()  # Using monotonic as in official example
            
            with self.model_lock:
                # EXACT API call from official example
                syn_tokens = self.model.generate_speech(
                    prompt=text,
                    voice=voice
                )
                
                # EXACT WAV file creation from official example
                audio_buffer = io.BytesIO()
                
                with wave.open(audio_buffer, "wb") as wf:
                    wf.setnchannels(1)      # Mono - as in official example
                    wf.setsampwidth(2)      # 16-bit - as in official example
                    wf.setframerate(24000)  # 24kHz - as in official example
                    
                    total_frames = 0
                    chunk_counter = 0
                    
                    # EXACT streaming processing from official example
                    for audio_chunk in syn_tokens:  # output streaming
                        chunk_counter += 1
                        frame_count = len(audio_chunk) // (wf.getsampwidth() * wf.getnchannels())
                        total_frames += frame_count
                        wf.writeframes(audio_chunk)
                
                # Calculate metrics exactly as in official example
                duration = total_frames / wf.getframerate()
                end_time = time.monotonic()
                generation_time = end_time - generation_start
                
                # Get the complete WAV file
                audio_buffer.seek(0)
                audio_data = audio_buffer.read()
                
                orpheus_logger.info(
                    f"✅ Generated {duration:.2f}s of audio in {generation_time:.2f}s "
                    f"({chunk_counter} chunks, {len(audio_data)} bytes)"
                )
                
                return audio_data
            
        except Exception as e:
            orpheus_logger.error(f"❌ Speech generation failed: {e}")
            raise AudioGenerationError(f"Speech generation failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        return {
            "model_name": self.model_name,
            "max_model_len": self.max_model_len,
            "is_initialized": self.is_initialized,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "sample_rate": self.sample_rate,
            "api_version": "official_orpheus_tts",
            "integration_type": "direct_streaming"
        }
    
    async def cleanup(self):
        """Cleanup model resources"""
        try:
            orpheus_logger.info("🧹 Cleaning up Perfect Orpheus Model resources...")
            
            if self.model:
                del self.model
                self.model = None
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Force garbage collection
            gc.collect()
            
            self.is_initialized = False
            orpheus_logger.info("✅ Cleanup completed")
            
        except Exception as e:
            orpheus_logger.error(f"❌ Cleanup failed: {e}")

# Global instance for easy access
orpheus_perfect_model = OrpheusPerfectModel()

# Test function to verify the integration
async def test_perfect_integration():
    """Test the perfect integration"""
    print("🧪 Testing Perfect Orpheus TTS Integration")
    print("=" * 50)
    
    try:
        # Initialize
        await orpheus_perfect_model.initialize()
        
        # Test generation with the exact example from the repository
        test_prompt = '''Man, the way social media has, um, completely changed how we interact is just wild, right? Like, we're all connected 24/7 but somehow people feel more alone than ever. And don't even get me started on how it's messing with kids' self-esteem and mental health and whatnot.'''
        
        audio_data = await orpheus_perfect_model.generate_speech(test_prompt, "tara")
        
        print(f"✅ Generated {len(audio_data)} bytes of audio")
        print(f"📊 Model info: {orpheus_perfect_model.get_model_info()}")
        
        # Cleanup
        await orpheus_perfect_model.cleanup()
        
        print("🎉 Perfect integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_perfect_integration())