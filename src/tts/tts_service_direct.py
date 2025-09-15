"""
Enhanced TTS Service with Direct Orpheus Integration
High-level TTS service using direct Orpheus model without FastAPI dependency
"""

import asyncio
import time
import logging
import base64
import io
import wave
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass

from src.models.unified_model_manager import unified_model_manager
from src.tts.orpheus_direct_model import OrpheusDirectModel, AudioGenerationError

# Setup logging
tts_service_logger = logging.getLogger("tts_service_direct")
tts_service_logger.setLevel(logging.INFO)

@dataclass
class TTSRequest:
    """TTS generation request data structure"""
    text: str
    voice: str = "ऋतिका"
    format: str = "wav"
    quality: str = "high"
    streaming: bool = False

@dataclass
class TTSResponse:
    """TTS generation response data structure"""
    audio_data: Optional[bytes]
    generation_time_ms: float
    audio_duration_ms: float
    success: bool
    metadata: Dict[str, Any]
    error: Optional[str] = None

class TTSServiceDirect:
    """
    Enhanced TTS Service using direct Orpheus integration
    Provides high-level async interface for TTS generation with performance monitoring
    """
    
    def __init__(self):
        self.is_initialized = False
        self.orpheus_model = None
        self.sample_rate = 24000
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_generation_time_ms": 0.0,
            "total_generation_time_ms": 0.0
        }
        
        # Voice validation
        self.available_voices = [
            "ऋतिका",  # Hindi - Primary voice
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",  # English
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",  # German
            "유나", "준서",  # Korean
            "长乐", "白芷",  # Mandarin
            "javi", "sergio", "maria",  # Spanish
            "pietro", "giulia", "carlo"  # Italian
        ]
        
        tts_service_logger.info("TTSServiceDirect created")
    
    async def initialize(self) -> bool:
        """
        Initialize TTS service with direct Orpheus model
        """
        try:
            tts_service_logger.info("🚀 Initializing TTS Service Direct...")
            start_time = time.time()
            
            # Get Orpheus model from unified manager
            self.orpheus_model = await unified_model_manager.get_orpheus_model()
            
            if not self.orpheus_model or not self.orpheus_model.is_initialized:
                raise AudioGenerationError("Orpheus model not available or not initialized")
            
            self.is_initialized = True
            init_time = (time.time() - start_time) * 1000
            
            tts_service_logger.info(f"✅ TTS Service Direct initialized in {init_time:.1f}ms")
            
            # Log available voices
            voices = self.get_available_voices()
            tts_service_logger.info(f"🎵 Available voices: {len(voices)} ({', '.join(voices[:5])}{'...' if len(voices) > 5 else ''})")
            
            return True
            
        except Exception as e:
            tts_service_logger.error(f"❌ TTS Service initialization failed: {e}")
            self.is_initialized = False
            return False
    
    async def generate_speech_async(self, text: str, voice: str = None, format: str = "wav") -> Dict[str, Any]:
        """
        Generate speech audio from text asynchronously
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (default: ऋतिका)
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Dictionary with audio data, metadata, and success status
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "TTS Service not initialized",
                "audio_data": None,
                "metadata": {}
            }
        
        # Create TTS request
        request = TTSRequest(
            text=text,
            voice=voice or "ऋतिका",
            format=format.lower(),
            quality="high",
            streaming=False
        )
        
        return await self._process_tts_request(request)
    
    async def _process_tts_request(self, request: TTSRequest) -> Dict[str, Any]:
        """
        Process TTS request with comprehensive error handling and performance tracking
        """
        generation_start = time.time()
        request_id = f"req_{int(generation_start * 1000)}"
        
        try:
            tts_service_logger.info(f"🎵 Processing TTS request {request_id}: '{request.text[:50]}...' with voice '{request.voice}'")
            
            # Update stats
            self.generation_stats["total_requests"] += 1
            
            # Validate request
            validation_result = self._validate_request(request)
            if not validation_result["valid"]:
                self.generation_stats["failed_requests"] += 1
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "audio_data": None,
                    "metadata": {
                        "request_id": request_id,
                        "processing_time_ms": (time.time() - generation_start) * 1000,
                        "validation_error": True
                    }
                }
            
            # Generate audio using Orpheus Direct Model
            audio_generation_start = time.time()
            audio_data = await self.orpheus_model.generate_speech(request.text, request.voice)
            audio_generation_time = (time.time() - audio_generation_start) * 1000
            
            if not audio_data:
                self.generation_stats["failed_requests"] += 1
                return {
                    "success": False,
                    "error": "Audio generation failed - no audio data returned",
                    "audio_data": None,
                    "metadata": {
                        "request_id": request_id,
                        "processing_time_ms": (time.time() - generation_start) * 1000,
                        "audio_generation_time_ms": audio_generation_time
                    }
                }
            
            # Convert to requested format
            format_conversion_start = time.time()
            formatted_audio_data, audio_metadata = await self._convert_audio_format(
                audio_data, request.format
            )
            format_conversion_time = (time.time() - format_conversion_start) * 1000
            
            total_processing_time = (time.time() - generation_start) * 1000
            
            # Update performance stats
            self.generation_stats["successful_requests"] += 1
            self.generation_stats["total_generation_time_ms"] += total_processing_time
            self.generation_stats["average_generation_time_ms"] = (
                self.generation_stats["total_generation_time_ms"] / 
                self.generation_stats["total_requests"]
            )
            
            # Create response metadata
            metadata = {
                "request_id": request_id,
                "processing_time_ms": total_processing_time,
                "audio_generation_time_ms": audio_generation_time,
                "format_conversion_time_ms": format_conversion_time,
                "voice_used": request.voice,
                "text_length": len(request.text),
                "audio_format": request.format,
                **audio_metadata
            }
            
            # Encode audio data for response
            if request.format.lower() in ["wav", "mp3", "ogg"]:
                # Return base64 encoded for binary formats
                encoded_audio = base64.b64encode(formatted_audio_data).decode('utf-8')
            else:
                encoded_audio = formatted_audio_data
            
            tts_service_logger.info(
                f"✅ TTS request {request_id} completed in {total_processing_time:.1f}ms "
                f"(generation: {audio_generation_time:.1f}ms, conversion: {format_conversion_time:.1f}ms)"
            )
            
            return {
                "success": True,
                "audio_data": encoded_audio,
                "metadata": metadata,
                "error": None
            }
            
        except AudioGenerationError as e:
            self.generation_stats["failed_requests"] += 1
            processing_time = (time.time() - generation_start) * 1000
            
            tts_service_logger.error(f"❌ Audio generation error for request {request_id}: {e}")
            
            return {
                "success": False,
                "error": f"Audio generation failed: {str(e)}",
                "audio_data": None,
                "metadata": {
                    "request_id": request_id,
                    "processing_time_ms": processing_time,
                    "error_type": "audio_generation_error"
                }
            }
            
        except Exception as e:
            self.generation_stats["failed_requests"] += 1
            processing_time = (time.time() - generation_start) * 1000
            
            tts_service_logger.error(f"❌ Unexpected error for request {request_id}: {e}")
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "audio_data": None,
                "metadata": {
                    "request_id": request_id,
                    "processing_time_ms": processing_time,
                    "error_type": "unexpected_error"
                }
            }
    
    def _validate_request(self, request: TTSRequest) -> Dict[str, Any]:
        """
        Validate TTS request parameters
        """
        try:
            # Check text
            if not request.text or not request.text.strip():
                return {"valid": False, "error": "Text cannot be empty"}
            
            if len(request.text) > 5000:  # Reasonable limit
                return {"valid": False, "error": "Text too long (max 5000 characters)"}
            
            # Check voice
            if request.voice not in self.available_voices:
                return {
                    "valid": False, 
                    "error": f"Invalid voice '{request.voice}'. Available: {', '.join(self.available_voices)}"
                }
            
            # Check format
            supported_formats = ["wav", "mp3", "ogg", "raw"]
            if request.format.lower() not in supported_formats:
                return {
                    "valid": False,
                    "error": f"Unsupported format '{request.format}'. Supported: {', '.join(supported_formats)}"
                }
            
            return {"valid": True, "error": None}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def _convert_audio_format(self, audio_data: bytes, target_format: str) -> tuple[bytes, Dict[str, Any]]:
        """
        Convert audio data to requested format
        """
        try:
            # Calculate audio duration
            audio_duration_ms = (len(audio_data) / 2) / self.sample_rate * 1000  # 16-bit audio
            
            metadata = {
                "audio_duration_ms": audio_duration_ms,
                "sample_rate": self.sample_rate,
                "channels": 1,
                "bit_depth": 16,
                "audio_size_bytes": len(audio_data)
            }
            
            if target_format.lower() == "wav":
                # Convert raw audio to WAV format
                wav_data = self._create_wav_file(audio_data)
                metadata["format"] = "wav"
                return wav_data, metadata
                
            elif target_format.lower() == "raw":
                # Return raw audio data
                metadata["format"] = "raw"
                return audio_data, metadata
                
            elif target_format.lower() in ["mp3", "ogg"]:
                # For now, return WAV format (could implement MP3/OGG conversion later)
                tts_service_logger.warning(f"⚠️ Format '{target_format}' not fully implemented, returning WAV")
                wav_data = self._create_wav_file(audio_data)
                metadata["format"] = "wav"
                metadata["requested_format"] = target_format
                return wav_data, metadata
                
            else:
                # Default to WAV
                wav_data = self._create_wav_file(audio_data)
                metadata["format"] = "wav"
                return wav_data, metadata
                
        except Exception as e:
            tts_service_logger.error(f"❌ Audio format conversion failed: {e}")
            # Return raw data as fallback
            return audio_data, {"format": "raw", "conversion_error": str(e)}
    
    def _create_wav_file(self, audio_data: bytes) -> bytes:
        """
        Create WAV file from raw audio data
        """
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)  # 24kHz
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            tts_service_logger.error(f"❌ WAV file creation failed: {e}")
            raise AudioGenerationError(f"WAV file creation failed: {e}")
    
    async def stream_speech(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """
        Stream speech generation (placeholder for future streaming implementation)
        """
        # For now, generate complete audio and yield in chunks
        try:
            result = await self.generate_speech_async(text, voice, "raw")
            
            if result["success"] and result["audio_data"]:
                # Decode base64 if needed
                if isinstance(result["audio_data"], str):
                    audio_data = base64.b64decode(result["audio_data"])
                else:
                    audio_data = result["audio_data"]
                
                # Yield in chunks of 4096 bytes
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i + chunk_size]
                    await asyncio.sleep(0.01)  # Small delay for streaming effect
            else:
                tts_service_logger.error(f"❌ Streaming failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            tts_service_logger.error(f"❌ Speech streaming failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get TTS service performance statistics"""
        return {
            "service_info": {
                "is_initialized": self.is_initialized,
                "sample_rate": self.sample_rate,
                "available_voices": len(self.available_voices)
            },
            "performance_stats": self.generation_stats.copy(),
            "model_info": self.orpheus_model.get_model_info() if self.orpheus_model else None
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.generation_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_generation_time_ms": 0.0,
            "total_generation_time_ms": 0.0
        }
        tts_service_logger.info("📊 Performance statistics reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of TTS service
        """
        try:
            health_status = {
                "service_initialized": self.is_initialized,
                "orpheus_model_available": self.orpheus_model is not None,
                "orpheus_model_initialized": self.orpheus_model.is_initialized if self.orpheus_model else False,
                "timestamp": time.time()
            }
            
            if self.is_initialized and self.orpheus_model:
                # Test with a simple generation
                test_start = time.time()
                try:
                    test_result = await self.generate_speech_async("Test", "ऋतिका", "raw")
                    test_time = (time.time() - test_start) * 1000
                    
                    health_status.update({
                        "test_generation_success": test_result["success"],
                        "test_generation_time_ms": test_time,
                        "status": "healthy" if test_result["success"] else "degraded"
                    })
                    
                except Exception as e:
                    health_status.update({
                        "test_generation_success": False,
                        "test_generation_error": str(e),
                        "status": "unhealthy"
                    })
            else:
                health_status["status"] = "not_ready"
            
            return health_status
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }

# Global TTS service instance
tts_service_direct = TTSServiceDirect()