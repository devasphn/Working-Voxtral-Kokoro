"""
TTS Service - High-level interface for text-to-speech functionality
Integrates with Voxtral system for seamless audio generation
"""

import asyncio
import base64
import time
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from io import BytesIO
import wave

from .tts_service_perfect import tts_service_perfect
from src.utils.config import config

# Setup logging
tts_service_logger = logging.getLogger("tts_service")
tts_service_logger.setLevel(logging.INFO)

class TTSService:
    """
    High-level TTS service for Voxtral integration
    Handles text-to-speech conversion with voice selection and audio streaming
    """
    
    def __init__(self):
        self.engine = tts_service_perfect
        self.is_initialized = False
        
        # Configuration from config file
        self.default_voice = "ऋतिका"  # Override to use ऋतिका voice as requested
        self.sample_rate = config.tts.sample_rate
        self.enabled = config.tts.enabled
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "total_audio_duration": 0.0,
            "total_processing_time": 0.0,
            "average_realtime_factor": 0.0
        }
        
        tts_service_logger.info("TTSService initialized")
    
    async def initialize(self):
        """Initialize the TTS service and engine"""
        try:
            tts_service_logger.info("🚀 Initializing TTS Service...")
            await self.engine.initialize()
            self.is_initialized = True
            tts_service_logger.info("✅ TTS Service initialized successfully")
        except Exception as e:
            tts_service_logger.error(f"❌ Failed to initialize TTS Service: {e}")
            # Don't raise the exception - allow the service to continue with degraded functionality
            tts_service_logger.warning("⚠️ TTS Service will continue with limited functionality")
            self.is_initialized = False
    
    async def generate_speech_async(self, text: str, voice: str = None, 
                                  return_format: str = "wav") -> Dict[str, Any]:
        """
        Generate speech from text asynchronously
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to service default)
            return_format: Format for audio data ("wav", "raw", "base64")
            
        Returns:
            Dictionary with audio data and metadata
        """
        start_time = time.time()
        voice = voice or self.default_voice
        
        tts_service_logger.info(f"🎵 Generating speech: '{text[:50]}...' with voice '{voice}'")
        
        # Try to initialize if not already done
        if not self.is_initialized:
            tts_service_logger.warning("⚠️ TTS Service not initialized, attempting initialization...")
            try:
                await self.initialize()
            except Exception as e:
                tts_service_logger.error(f"❌ Failed to initialize TTS during generation: {e}")
                return {
                    "success": False,
                    "error": "TTS Service initialization failed",
                    "audio_data": None,
                    "metadata": {}
                }
        
        try:
            # For now, we'll implement a basic version that would integrate with
            # an external LLM inference server (like the original Orpheus-FastAPI design)
            # This is a placeholder that would be connected to the actual token generation
            
            # Generate audio segments (this would be replaced with actual token processing)
            audio_segments = await self._generate_audio_segments(text, voice)
            
            if not audio_segments:
                return {
                    "success": False,
                    "error": "No audio generated",
                    "audio_data": None,
                    "metadata": {}
                }
            
            # Combine audio segments
            combined_audio = self._combine_audio_segments(audio_segments)
            
            # Format audio data based on requested format
            audio_data = self._format_audio_data(combined_audio, return_format)
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            audio_duration = len(combined_audio) / (2 * self.sample_rate)  # 2 bytes per sample
            realtime_factor = audio_duration / processing_time if processing_time > 0 else 0
            
            # Update statistics
            self._update_stats(processing_time, audio_duration, realtime_factor)
            
            tts_service_logger.info(f"✅ Speech generated in {processing_time:.2f}s "
                                  f"({realtime_factor:.2f}x realtime)")
            
            return {
                "success": True,
                "audio_data": audio_data,
                "metadata": {
                    "voice": voice,
                    "text_length": len(text),
                    "audio_duration": audio_duration,
                    "processing_time": processing_time,
                    "realtime_factor": realtime_factor,
                    "sample_rate": self.sample_rate,
                    "format": return_format
                }
            }
            
        except Exception as e:
            tts_service_logger.error(f"❌ Error generating speech: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": None,
                "metadata": {}
            }
    
    async def _generate_audio_segments(self, text: str, voice: str) -> List[bytes]:
        """
        Generate audio segments from text using the TTS engine
        """
        try:
            # Use the engine to generate audio
            audio_data = await self.engine.generate_speech(text, voice)
            if audio_data:
                return [audio_data]
            else:
                tts_service_logger.warning("⚠️ No audio data generated from engine")
                return []
        except Exception as e:
            tts_service_logger.error(f"❌ Error in audio generation: {e}")
            return []
    
    def _combine_audio_segments(self, segments: List[bytes]) -> bytes:
        """Combine multiple audio segments into a single audio stream"""
        if not segments:
            return b""
        
        # Simple concatenation for now
        # In production, this would include crossfading for smooth transitions
        combined = b"".join(segments)
        return combined
    
    def _format_audio_data(self, audio_bytes: bytes, format_type: str) -> Any:
        """Format audio data according to requested format"""
        if format_type == "raw":
            return audio_bytes
        elif format_type == "base64":
            return base64.b64encode(audio_bytes).decode('utf-8')
        elif format_type == "wav":
            # Create WAV format
            wav_buffer = BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_bytes)
            
            wav_data = wav_buffer.getvalue()
            return base64.b64encode(wav_data).decode('utf-8')
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _update_stats(self, processing_time: float, audio_duration: float, realtime_factor: float):
        """Update performance statistics"""
        self.generation_stats["total_requests"] += 1
        self.generation_stats["total_audio_duration"] += audio_duration
        self.generation_stats["total_processing_time"] += processing_time
        
        # Calculate running average of realtime factor
        total_requests = self.generation_stats["total_requests"]
        current_avg = self.generation_stats["average_realtime_factor"]
        self.generation_stats["average_realtime_factor"] = (
            (current_avg * (total_requests - 1) + realtime_factor) / total_requests
        )
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.engine.get_available_voices()
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get TTS service information and statistics"""
        engine_info = self.engine.get_model_info()
        
        return {
            "service": "TTSService",
            "initialized": self.is_initialized,
            "engine_info": engine_info,
            "statistics": self.generation_stats.copy(),
            "configuration": {
                "default_voice": self.default_voice,
                "sample_rate": self.sample_rate
            }
        }
    
    async def stream_speech(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Stream speech generation for real-time applications
        This would be used for streaming audio back to the client
        """
        if not self.is_initialized:
            raise RuntimeError("TTS Service not initialized")
        
        voice = voice or self.default_voice
        tts_service_logger.info(f"🎵 Streaming speech generation for voice '{voice}'")
        
        # This would implement streaming token processing
        # For now, yield empty as placeholder
        tts_service_logger.warning("⚠️ Speech streaming not yet implemented - placeholder")
        yield b""  # Placeholder
    
    def validate_voice(self, voice: str) -> bool:
        """Validate if a voice is available"""
        return voice in self.engine.get_available_voices()
    
    def get_default_voice(self) -> str:
        """Get the default voice"""
        return self.default_voice
    
    def set_default_voice(self, voice: str) -> bool:
        """Set the default voice"""
        if self.validate_voice(voice):
            self.default_voice = voice
            tts_service_logger.info(f"Default voice changed to: {voice}")
            return True
        else:
            tts_service_logger.warning(f"Invalid voice: {voice}")
            return False
