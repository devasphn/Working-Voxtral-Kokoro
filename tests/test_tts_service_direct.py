"""
Unit tests for TTSServiceDirect
Tests the enhanced TTS service with direct Orpheus integration
"""

import pytest
import asyncio
import base64
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tts.tts_service_direct import TTSServiceDirect, TTSRequest, TTSResponse

class TestTTSServiceDirect:
    """Test suite for TTSServiceDirect"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service = TTSServiceDirect()
    
    def test_initialization(self):
        """Test TTSServiceDirect initialization"""
        assert not self.service.is_initialized
        assert self.service.orpheus_model is None
        assert self.service.sample_rate == 24000
        assert len(self.service.available_voices) > 0
        assert "ऋतिका" in self.service.available_voices
        
        # Check initial stats
        assert self.service.generation_stats["total_requests"] == 0
        assert self.service.generation_stats["successful_requests"] == 0
        assert self.service.generation_stats["failed_requests"] == 0
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_successful_initialization(self, mock_unified_manager):
        """Test successful TTS service initialization"""
        # Mock unified manager and Orpheus model
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Test initialization
        result = await self.service.initialize()
        
        assert result is True
        assert self.service.is_initialized
        assert self.service.orpheus_model is mock_orpheus
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_initialization_failure(self, mock_unified_manager):
        """Test TTS service initialization failure"""
        # Mock unified manager to raise exception
        mock_unified_manager.get_orpheus_model = AsyncMock(side_effect=Exception("Model not available"))
        
        # Test initialization
        result = await self.service.initialize()
        
        assert result is False
        assert not self.service.is_initialized
        assert self.service.orpheus_model is None
    
    @pytest.mark.asyncio
    async def test_generate_speech_not_initialized(self):
        """Test speech generation when service not initialized"""
        result = await self.service.generate_speech_async("Hello world")
        
        assert not result["success"]
        assert "not initialized" in result["error"]
        assert result["audio_data"] is None
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_successful_speech_generation(self, mock_unified_manager):
        """Test successful speech generation"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.generate_speech = AsyncMock(return_value=b"fake_audio_data")
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        # Test speech generation
        result = await self.service.generate_speech_async("Hello world", "ऋतिका", "wav")
        
        assert result["success"]
        assert result["audio_data"] is not None
        assert result["metadata"]["voice_used"] == "ऋतिका"
        assert result["metadata"]["text_length"] == 11
        assert result["metadata"]["audio_format"] == "wav"
        
        # Check stats updated
        assert self.service.generation_stats["total_requests"] == 1
        assert self.service.generation_stats["successful_requests"] == 1
        assert self.service.generation_stats["failed_requests"] == 0
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_speech_generation_failure(self, mock_unified_manager):
        """Test speech generation failure"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.generate_speech = AsyncMock(return_value=None)  # Simulate failure
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        # Test speech generation
        result = await self.service.generate_speech_async("Hello world")
        
        assert not result["success"]
        assert "no audio data returned" in result["error"]
        assert result["audio_data"] is None
        
        # Check stats updated
        assert self.service.generation_stats["total_requests"] == 1
        assert self.service.generation_stats["successful_requests"] == 0
        assert self.service.generation_stats["failed_requests"] == 1
    
    def test_request_validation_empty_text(self):
        """Test request validation with empty text"""
        request = TTSRequest(text="", voice="ऋतिका")
        result = self.service._validate_request(request)
        
        assert not result["valid"]
        assert "cannot be empty" in result["error"]
    
    def test_request_validation_long_text(self):
        """Test request validation with text too long"""
        long_text = "a" * 5001  # Exceeds 5000 character limit
        request = TTSRequest(text=long_text, voice="ऋतिका")
        result = self.service._validate_request(request)
        
        assert not result["valid"]
        assert "too long" in result["error"]
    
    def test_request_validation_invalid_voice(self):
        """Test request validation with invalid voice"""
        request = TTSRequest(text="Hello", voice="invalid_voice")
        result = self.service._validate_request(request)
        
        assert not result["valid"]
        assert "Invalid voice" in result["error"]
    
    def test_request_validation_invalid_format(self):
        """Test request validation with invalid format"""
        request = TTSRequest(text="Hello", voice="ऋतिका", format="invalid_format")
        result = self.service._validate_request(request)
        
        assert not result["valid"]
        assert "Unsupported format" in result["error"]
    
    def test_request_validation_valid(self):
        """Test request validation with valid parameters"""
        request = TTSRequest(text="Hello world", voice="ऋतिका", format="wav")
        result = self.service._validate_request(request)
        
        assert result["valid"]
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_audio_format_conversion_wav(self):
        """Test audio format conversion to WAV"""
        raw_audio = b"fake_raw_audio_data"
        
        wav_data, metadata = await self.service._convert_audio_format(raw_audio, "wav")
        
        assert isinstance(wav_data, bytes)
        assert len(wav_data) > len(raw_audio)  # WAV has header
        assert metadata["format"] == "wav"
        assert metadata["sample_rate"] == 24000
        assert metadata["channels"] == 1
        assert metadata["bit_depth"] == 16
    
    @pytest.mark.asyncio
    async def test_audio_format_conversion_raw(self):
        """Test audio format conversion to raw"""
        raw_audio = b"fake_raw_audio_data"
        
        converted_data, metadata = await self.service._convert_audio_format(raw_audio, "raw")
        
        assert converted_data == raw_audio
        assert metadata["format"] == "raw"
        assert metadata["sample_rate"] == 24000
    
    @pytest.mark.asyncio
    async def test_audio_format_conversion_unsupported(self):
        """Test audio format conversion for unsupported format"""
        raw_audio = b"fake_raw_audio_data"
        
        # Should fallback to WAV for unsupported formats like MP3
        wav_data, metadata = await self.service._convert_audio_format(raw_audio, "mp3")
        
        assert isinstance(wav_data, bytes)
        assert metadata["format"] == "wav"
        assert metadata["requested_format"] == "mp3"
    
    def test_create_wav_file(self):
        """Test WAV file creation"""
        # Create fake 16-bit audio data
        import numpy as np
        audio_samples = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        raw_audio = audio_samples.tobytes()
        
        wav_data = self.service._create_wav_file(raw_audio)
        
        assert isinstance(wav_data, bytes)
        assert len(wav_data) > len(raw_audio)  # Should include WAV header
        
        # Check WAV header (first 4 bytes should be "RIFF")
        assert wav_data[:4] == b"RIFF"
        assert wav_data[8:12] == b"WAVE"
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_stream_speech(self, mock_unified_manager):
        """Test speech streaming functionality"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.generate_speech = AsyncMock(return_value=b"fake_audio_data_1234567890")
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        # Test streaming
        chunks = []
        async for chunk in self.service.stream_speech("Hello world", "ऋतिका"):
            chunks.append(chunk)
        
        # Should have received chunks
        assert len(chunks) > 0
        
        # Reconstruct audio
        reconstructed = b"".join(chunks)
        assert len(reconstructed) > 0
    
    def test_get_available_voices(self):
        """Test getting available voices"""
        voices = self.service.get_available_voices()
        
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert "ऋतिका" in voices
        assert "tara" in voices
        assert "pierre" in voices
        
        # Should be a copy, not the original list
        voices.append("test_voice")
        assert "test_voice" not in self.service.get_available_voices()
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_get_service_stats(self, mock_unified_manager):
        """Test getting service statistics"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.get_model_info.return_value = {"model": "orpheus", "initialized": True}
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        stats = self.service.get_service_stats()
        
        assert "service_info" in stats
        assert stats["service_info"]["is_initialized"]
        assert stats["service_info"]["sample_rate"] == 24000
        
        assert "performance_stats" in stats
        assert "model_info" in stats
        assert stats["model_info"]["model"] == "orpheus"
    
    def test_reset_stats(self):
        """Test resetting performance statistics"""
        # Modify stats
        self.service.generation_stats["total_requests"] = 10
        self.service.generation_stats["successful_requests"] = 8
        self.service.generation_stats["failed_requests"] = 2
        
        # Reset
        self.service.reset_stats()
        
        # Check reset
        assert self.service.generation_stats["total_requests"] == 0
        assert self.service.generation_stats["successful_requests"] == 0
        assert self.service.generation_stats["failed_requests"] == 0
        assert self.service.generation_stats["average_generation_time_ms"] == 0.0
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_health_check_healthy(self, mock_unified_manager):
        """Test health check with healthy service"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.generate_speech = AsyncMock(return_value=b"test_audio")
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        health = await self.service.health_check()
        
        assert health["service_initialized"]
        assert health["orpheus_model_available"]
        assert health["orpheus_model_initialized"]
        assert health["test_generation_success"]
        assert health["status"] == "healthy"
        assert "test_generation_time_ms" in health
    
    @pytest.mark.asyncio
    async def test_health_check_not_ready(self):
        """Test health check with uninitialized service"""
        health = await self.service.health_check()
        
        assert not health["service_initialized"]
        assert not health["orpheus_model_available"]
        assert not health["orpheus_model_initialized"]
        assert health["status"] == "not_ready"
    
    @pytest.mark.asyncio
    @patch('src.tts.tts_service_direct.unified_model_manager')
    async def test_health_check_degraded(self, mock_unified_manager):
        """Test health check with degraded service"""
        # Setup mocks
        mock_orpheus = Mock()
        mock_orpheus.is_initialized = True
        mock_orpheus.generate_speech = AsyncMock(side_effect=Exception("Generation failed"))
        mock_unified_manager.get_orpheus_model = AsyncMock(return_value=mock_orpheus)
        
        # Initialize service
        await self.service.initialize()
        
        health = await self.service.health_check()
        
        assert health["service_initialized"]
        assert health["orpheus_model_available"]
        assert health["orpheus_model_initialized"]
        assert not health["test_generation_success"]
        assert health["status"] == "degraded"
        assert "test_generation_error" in health
    
    def test_tts_request_dataclass(self):
        """Test TTSRequest dataclass"""
        request = TTSRequest(
            text="Hello world",
            voice="tara",
            format="mp3",
            quality="high",
            streaming=True
        )
        
        assert request.text == "Hello world"
        assert request.voice == "tara"
        assert request.format == "mp3"
        assert request.quality == "high"
        assert request.streaming is True
    
    def test_tts_response_dataclass(self):
        """Test TTSResponse dataclass"""
        metadata = {"duration": 2.5, "sample_rate": 24000}
        response = TTSResponse(
            audio_data=b"audio_data",
            generation_time_ms=150.0,
            audio_duration_ms=2500.0,
            success=True,
            metadata=metadata,
            error=None
        )
        
        assert response.audio_data == b"audio_data"
        assert response.generation_time_ms == 150.0
        assert response.audio_duration_ms == 2500.0
        assert response.success is True
        assert response.metadata == metadata
        assert response.error is None

if __name__ == "__main__":
    pytest.main([__file__])