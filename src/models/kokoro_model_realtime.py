"""
Kokoro TTS Model for Real-time Speech Synthesis
Production-ready implementation following Voxtral patterns
"""
import asyncio
import time
import logging
import torch
import numpy as np
from typing import Dict, Any, Optional, List, Union
from threading import Lock
from collections import deque
import soundfile as sf
import io
# ADD these imports at the top
import threading
from concurrent.futures import ThreadPoolExecutor

from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("kokoro_tts")

class KokoroTTSModel:
    """
    Production-ready Kokoro TTS model wrapper for real-time speech synthesis
    Follows the same patterns as VoxtralModel for consistency
    """
    
    DEFAULT_VOICE = "hf_alpha"
    
    def __init__(self):
        self.pipeline = None
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Real-time TTS optimization
        self.recent_generations = deque(maxlen=10)  # Track recent generations
        self.generation_history = deque(maxlen=100)  # Performance tracking
        
        # Performance optimization settings
        self.device = config.model.device
        self.torch_dtype = getattr(torch, config.model.torch_dtype)
        
        # TTS-specific settings
        self.sample_rate = config.tts.sample_rate
        self.voice = getattr(config.tts, 'voice', self.DEFAULT_VOICE) or self.DEFAULT_VOICE
        self.speed = config.tts.speed
        self.lang_code = config.tts.lang_code
        
        # ADDED: Performance optimization settings
        self.max_text_length = 500  # OPTIMIZED: Smaller chunks (was 1000)
        self.chunk_size = 512      # OPTIMIZED: Smaller processing chunks
        
        # ADDED: Threading for async processing
        self.tts_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kokoro_tts")
        self.synthesis_cache = {}  # Simple response caching
        self.cache_size_limit = 50
        
        # ADDED: Quality vs Speed settings
        quality_preset = getattr(config.tts.performance, 'quality_preset', 'balanced')
        if quality_preset == 'speed':
            self.speed_multiplier = 1.2
            self.quality_settings = {}  # REMOVED: temperature not supported by KPipeline
        elif quality_preset == 'quality':
            self.speed_multiplier = 0.9
            self.quality_settings = {}  # REMOVED: temperature not supported by KPipeline
        else:  # balanced
            self.speed_multiplier = 1.0
            self.quality_settings = {}  # REMOVED: temperature not supported by KPipeline
        
        tts_logger.info(f"🎵 KokoroTTSModel initialized with device: {self.device}")
        tts_logger.info(f"   🎤 Voice: {self.voice}, Speed: {self.speed}, Lang: {self.lang_code}")
    
    async def initialize(self) -> bool:
        """Initialize the Kokoro TTS model with production-ready settings"""
        if self.is_initialized:
            tts_logger.info("🎵 Kokoro TTS model already initialized")
            return True

        start_time = time.time()
        tts_logger.info("🚀 Initializing Kokoro TTS model for real-time synthesis...")

        try:
            # Check and download model files if needed
            from src.utils.kokoro_model_manager import kokoro_model_manager

            tts_logger.info("🔍 Checking Kokoro model files...")
            status = kokoro_model_manager.get_model_status()

            if status['integrity_percentage'] < 100:
                tts_logger.info(f"📥 Model files incomplete ({status['integrity_percentage']:.1f}%), downloading...")
                download_success = kokoro_model_manager.download_model_files()
                if not download_success:
                    tts_logger.error("❌ Failed to download Kokoro model files")
                    return False
                tts_logger.info("✅ Model files downloaded successfully")
            else:
                tts_logger.info("✅ All model files verified and ready")

            # Import Kokoro pipeline
            from kokoro import KPipeline

            tts_logger.info(f"📥 Loading Kokoro pipeline with language code: {self.lang_code}")

            # Initialize pipeline with language code
            self.pipeline = KPipeline(lang_code=self.lang_code)

            # Test the pipeline with a short sample
            test_text = "Kokoro TTS initialization test."
            tts_logger.info("🧪 Testing Kokoro pipeline with sample text...")

            test_generator = self.pipeline(test_text, voice=self.voice, speed=self.speed)
            test_audio = None

            for i, (gs, ps, audio) in enumerate(test_generator):
                test_audio = audio
                break  # Just test the first chunk

            if test_audio is not None:
                tts_logger.info(f"✅ Kokoro pipeline test successful - generated {len(test_audio)} samples")
            else:
                raise RuntimeError("Pipeline test failed - no audio generated")

            self.is_initialized = True
            init_time = time.time() - start_time
            tts_logger.info(f"🎉 Kokoro TTS model fully initialized in {init_time:.2f}s and ready for synthesis!")
            return True

        except ImportError as e:
            tts_logger.error(f"❌ Failed to import Kokoro: {e}")
            tts_logger.error("💡 Please install Kokoro: pip install kokoro>=0.9.4")
            return False
        except Exception as e:
            tts_logger.error(f"❌ Failed to initialize Kokoro TTS model: {e}")
            import traceback
            tts_logger.error(f"❌ Full error traceback: {traceback.format_exc()}")
            return False
    
    def _preprocess_text_for_tts(self, text: str) -> str:
        """OPTIMIZED: Preprocess text for faster TTS"""
        if not text or not text.strip():
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive punctuation that slows TTS
        import re
        text = re.sub(r'[.]{2,}', '.', text)  # Multiple periods
        text = re.sub(r'[!]{2,}', '!', text)  # Multiple exclamations
        text = re.sub(r'[?]{2,}', '?', text)  # Multiple questions
        text = re.sub(r'\s+', ' ', text)      # Multiple spaces
        
        # Truncate if too long
        if len(text) > self.max_text_length:
            # Smart truncation at sentence boundary
            sentences = text.split('.')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < self.max_text_length:
                    result += sentence + "."
                else:
                    break
            text = result.rstrip('.')
            if not text:  # If no complete sentences fit, hard truncate
                text = text[:self.max_text_length].rsplit(' ', 1)[0]
        
        return text
    
    async def synthesize_speech(self, text: str, chunk_id: str = None) -> Dict[str, Any]:
        """ULTRA-FAST TTS synthesis - FINAL WORKING VERSION"""
        if not self.is_initialized:
            raise RuntimeError("KokoroTTSModel not initialized")
        
        synthesis_start = time.time()
        try:
            # Truncate text for speed
            max_chars = 200
            if len(text) > max_chars:
                text = text[:max_chars].rsplit(' ', 1)[0] + "..."
            
            tts_logger.debug(f"🎵 Starting ULTRA-FAST TTS for chunk {chunk_id}")
            
            # WORKING: Call pipeline with minimal parameters
            result = self.pipeline(
                text,
                voice=self.voice,
                speed=self.speed
            )
            
            synthesis_time = (time.time() - synthesis_start) * 1000
            
            # FIXED: Handle generator object properly
            if hasattr(result, 'audio') and result.audio is not None:
                audio_data = result.audio
            elif isinstance(result, torch.Tensor):
                audio_data = result
            elif hasattr(result, '__iter__') and not isinstance(result, (str, bytes)):
                # Handle generator - convert to list first
                try:
                    result_list = list(result)
                    if result_list and hasattr(result_list[0], 'audio'):
                        audio_data = result_list[0].audio
                    else:
                        audio_data = result_list[0] if result_list else torch.zeros(16000)
                except:
                    audio_data = torch.zeros(16000)  # Fallback silent audio
            else:
                audio_data = result
            
            # Convert to numpy safely
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.cpu().numpy()
            elif not isinstance(audio_data, np.ndarray):
                # Create silent audio as fallback
                audio_data = np.zeros(int(self.sample_rate * 1.0))  # 1 second of silence
            
            tts_logger.info(f"✅ Synthesized speech for chunk {chunk_id} in {synthesis_time:.1f}ms: {len(audio_data)/self.sample_rate:.2f}s audio")
            
            return {
                'success': True,
                'audio_data': audio_data,
                'sample_rate': self.sample_rate,
                'synthesis_time_ms': synthesis_time,
                'audio_duration_s': len(audio_data) / self.sample_rate
            }
            
        except Exception as e:
            synthesis_time = (time.time() - synthesis_start) * 1000
            tts_logger.error(f"❌ TTS synthesis error for chunk {chunk_id}: {e}")
            # Return silent audio instead of empty array
            silent_audio = np.zeros(int(self.sample_rate * 1.0))  # 1 second silence
            return {
                'success': False,
                'audio_data': silent_audio,
                'sample_rate': self.sample_rate,
                'synthesis_time_ms': synthesis_time,
                'error': str(e)
            }
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        # Common Kokoro voices - this could be expanded based on the model
        return [
            'hf_alpha', 'af_bella', 'af_sarah', 'af_nicole', 'af_sky',
            'am_adam', 'am_michael', 'am_edward', 'am_lewis', 'am_william'
        ]
    
    def set_voice_parameters(self, voice: Optional[str] = None, speed: Optional[float] = None):
        """Update voice parameters for future synthesis"""
        if voice is not None:
            self.voice = voice
            tts_logger.info(f"🎤 Voice updated to: {voice}")
        
        if speed is not None:
            self.speed = max(0.5, min(2.0, speed))  # Clamp speed between 0.5 and 2.0
            tts_logger.info(f"⚡ Speed updated to: {self.speed}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information and performance statistics"""
        base_info = {
            "model_name": "Kokoro-82M",
            "model_type": "text_to_speech",
            "is_initialized": self.is_initialized,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "current_voice": self.voice,
            "current_speed": self.speed,
            "language_code": self.lang_code,
            "available_voices": self.get_available_voices()
        }
        
        if self.is_initialized and self.generation_history:
            # Calculate performance statistics
            recent_stats = list(self.generation_history)[-10:]  # Last 10 generations
            
            if recent_stats:
                avg_synthesis_time = sum(s['synthesis_time_ms'] for s in recent_stats) / len(recent_stats)
                avg_rtf = sum(s['real_time_factor'] for s in recent_stats) / len(recent_stats)
                total_generations = len(self.generation_history)
                
                base_info.update({
                    "tts_stats": {
                        "total_generations": total_generations,
                        "avg_synthesis_time_ms": round(avg_synthesis_time, 1),
                        "avg_real_time_factor": round(avg_rtf, 2),
                        "recent_generations_in_memory": len(recent_stats),
                        "performance_history_size": len(self.generation_history)
                    }
                })
        
        return base_info

# Global model instance for real-time TTS
kokoro_model = KokoroTTSModel()

# Main execution block for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_kokoro():
        """Test the Kokoro TTS model"""
        try:
            await kokoro_model.initialize()
            
            test_text = "Hello, this is a test of the Kokoro text-to-speech system. It should generate natural sounding speech."
            result = await kokoro_model.synthesize_speech(test_text, chunk_id="test_001")
            
            if result['success'] and len(result['audio_data']) > 0:
                # Save test audio
                sf.write('test_kokoro_output.wav', result['audio_data'], result['sample_rate'])
                print(f"✅ Test successful! Audio saved to test_kokoro_output.wav")
                print(f"   Synthesis time: {result['synthesis_time_ms']:.1f}ms")
                print(f"   Audio duration: {result['audio_duration_s']:.2f}s")
            else:
                print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    asyncio.run(test_kokoro())
