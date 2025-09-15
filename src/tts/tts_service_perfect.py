"""
Perfect TTS Service - Uses Orpheus Perfect Model
Clean, simple, and efficient TTS service
"""

import asyncio
import time
import logging
from typing import Optional, List, Dict, Any
from threading import Lock

from src.tts.orpheus_perfect_model import orpheus_perfect_model
from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("tts_service_perfect")
tts_logger.setLevel(logging.INFO)

class TTSServicePerfect:
    """
    Perfect TTS Service using Orpheus Perfect Model
    Simple, clean, and efficient
    """
    
    def __init__(self):
        self.is_initialized = False
        self.service_lock = Lock()
        
        # Performance tracking
        self.generation_count = 0
        self.total_generation_time = 0.0
        self.last_generation_time = 0.0
        
        tts_logger.info("TTSServicePerfect initialized")
    
    async def initialize(self) -> bool:
        """Initialize the TTS service"""
        try:
            tts_logger.info("🚀 Initializing Perfect TTS Service...")
            start_time = time.time()
            
            # Initialize the perfect Orpheus model
            success = await orpheus_perfect_model.initialize()
            
            if success:
                self.is_initialized = True
                init_time = time.time() - start_time
                tts_logger.info(f"🎉 Perfect TTS Service initialized in {init_time:.2f}s")
                return True
            else:
                tts_logger.error("❌ Failed to initialize Orpheus model")
                return False
                
        except Exception as e:
            tts_logger.error(f"❌ TTS Service initialization failed: {e}")
            return False
    
    async def generate_speech(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Generate speech from text using perfect Orpheus integration
        """
        if not self.is_initialized:
            tts_logger.error("❌ TTS Service not initialized")
            return None
        
        try:
            generation_start = time.time()
            
            # Use the perfect Orpheus model
            audio_data = await orpheus_perfect_model.generate_speech(text, voice)
            
            # Track performance
            generation_time = time.time() - generation_start
            self.last_generation_time = generation_time
            self.generation_count += 1
            self.total_generation_time += generation_time
            
            if audio_data:
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
        return orpheus_perfect_model.get_available_voices()
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and statistics"""
        model_info = orpheus_perfect_model.get_model_info()
        
        service_info = {
            "service_name": "TTSServicePerfect",
            "is_initialized": self.is_initialized,
            "generation_count": self.generation_count,
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
            tts_logger.info("🧹 Cleaning up Perfect TTS Service...")
            
            await orpheus_perfect_model.cleanup()
            
            self.is_initialized = False
            tts_logger.info("✅ TTS Service cleanup completed")
            
        except Exception as e:
            tts_logger.error(f"❌ TTS Service cleanup failed: {e}")

# Global service instance
tts_service_perfect = TTSServicePerfect()

# Test function
async def test_perfect_tts_service():
    """Test the perfect TTS service"""
    print("🧪 Testing Perfect TTS Service")
    print("=" * 40)
    
    try:
        # Initialize
        success = await tts_service_perfect.initialize()
        if not success:
            print("❌ Initialization failed")
            return
        
        # Test generation
        test_text = "Hello, this is a test of the perfect TTS service."
        audio_data = await tts_service_perfect.generate_speech(test_text, "tara")
        
        if audio_data:
            print(f"✅ Generated {len(audio_data)} bytes of audio")
        else:
            print("❌ No audio generated")
        
        # Show service info
        info = tts_service_perfect.get_service_info()
        print(f"📊 Service info: {info}")
        
        # Cleanup
        await tts_service_perfect.cleanup()
        
        print("🎉 Perfect TTS Service test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_perfect_tts_service())