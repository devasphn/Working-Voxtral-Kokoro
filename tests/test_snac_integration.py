"""
Unit tests for SNAC codec integration
Tests audio conversion from tokens using SNAC neural codec
"""

import pytest
import torch
import numpy as np
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tts.orpheus_direct_model import OrpheusDirectModel, AudioGenerationError

class TestSNACIntegration:
    """Test suite for SNAC codec integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.model = OrpheusDirectModel()
        
        # Mock SNAC model for testing
        self.mock_snac = Mock()
        self.model.snac_model = self.mock_snac
        
        # Setup mock device
        self.mock_snac.parameters.return_value = [Mock()]
        self.mock_snac.parameters.return_value[0].device = torch.device("cpu")
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_basic(self):
        """Test basic token to audio conversion"""
        # Create test tokens (multiple of 7 for SNAC)
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)  # Batch, channels, samples
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Verify SNAC was called
        self.mock_snac.decode.assert_called_once()
        
        # Verify audio data was generated
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_padding(self):
        """Test token padding to multiple of 7"""
        # Test tokens not multiple of 7 (should be padded)
        test_tokens = [100, 200, 300, 400, 500]  # 5 tokens, needs 2 padding
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Verify SNAC was called with padded tokens
        call_args = self.mock_snac.decode.call_args[0][0]  # First positional argument (codes)
        
        # Should have 3 code levels
        assert len(call_args) == 3
        
        # Verify audio data was generated
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_insufficient_tokens(self):
        """Test handling of insufficient tokens (< 7)"""
        # Test with too few tokens
        test_tokens = [100, 200, 300]  # Only 3 tokens, need at least 7
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Should return None for insufficient tokens
        assert audio_data is None
        
        # SNAC should not be called
        self.mock_snac.decode.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_code_structure(self):
        """Test the correct SNAC code structure generation"""
        # Test with exactly 14 tokens (2 frames)
        test_tokens = list(range(100, 114))  # 14 tokens
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Verify SNAC was called
        self.mock_snac.decode.assert_called_once()
        
        # Get the codes passed to SNAC
        call_args = self.mock_snac.decode.call_args[0][0]
        
        # Should have 3 code levels
        assert len(call_args) == 3
        
        # Code 0: 2 frames (14 tokens / 7 = 2 frames)
        assert call_args[0].shape == (1, 2)  # batch_size=1, num_frames=2
        
        # Code 1: 4 values (2 frames * 2)
        assert call_args[1].shape == (1, 4)
        
        # Code 2: 8 values (2 frames * 4)
        assert call_args[2].shape == (1, 8)
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_range_validation(self):
        """Test token range validation"""
        # Test with tokens outside valid range
        test_tokens = [5000, 6000, 7000, 8000, 9000, 10000, 11000]  # All > 4096
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion - should return None for out-of-range tokens
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Should return None for invalid token ranges
        assert audio_data is None
        
        # SNAC should not be called due to range validation
        self.mock_snac.decode.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_valid_range(self):
        """Test token conversion with valid range tokens"""
        # Test with tokens in valid range (0-4096)
        test_tokens = [1000, 2000, 3000, 4000, 1500, 2500, 3500]
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Should succeed with valid tokens
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
        
        # SNAC should be called
        self.mock_snac.decode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_audio_slice_extraction(self):
        """Test correct audio slice extraction [2048:4096]"""
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Create mock audio output with known values
        # Shape: (batch=1, channels=1, samples=8192)
        mock_audio_tensor = torch.zeros(1, 1, 8192)
        
        # Put specific values in the slice we expect to extract [2048:4096]
        mock_audio_tensor[:, :, 2048:4096] = torch.ones(1, 1, 2048) * 0.5
        
        self.mock_snac.decode.return_value = mock_audio_tensor
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Convert back to verify correct slice was extracted
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Should have extracted 2048 samples (slice length)
        assert len(audio_array) == 2048
        
        # Values should be around 0.5 * 32767 = 16383 (allowing for int16 conversion)
        expected_value = int(0.5 * 32767)
        assert np.all(np.abs(audio_array - expected_value) < 100)  # Allow small conversion errors
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_gpu_optimization(self):
        """Test GPU optimization path"""
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Mock CUDA device
        mock_device = Mock()
        mock_device.type = "cuda"
        self.mock_snac.parameters.return_value[0].device = mock_device
        
        # Mock SNAC decode output
        mock_audio_output = torch.randn(1, 1, 4096)
        mock_audio_slice = Mock()
        mock_audio_slice.__mul__ = Mock(return_value=Mock())
        mock_audio_slice.__mul__.return_value.to = Mock(return_value=Mock())
        mock_audio_slice.__mul__.return_value.to.return_value.cpu = Mock(return_value=Mock())
        mock_audio_slice.__mul__.return_value.to.return_value.cpu.return_value.numpy = Mock(return_value=Mock())
        mock_audio_slice.__mul__.return_value.to.return_value.cpu.return_value.numpy.return_value.tobytes = Mock(return_value=b"test_audio")
        
        # Mock the slice operation
        mock_audio_output.__getitem__ = Mock(return_value=mock_audio_slice)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Should use GPU optimization path
        assert audio_data == b"test_audio"
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_cpu_fallback(self):
        """Test CPU fallback path"""
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Mock CPU device
        mock_device = Mock()
        mock_device.type = "cpu"
        self.mock_snac.parameters.return_value[0].device = mock_device
        
        # Mock SNAC decode output with CPU processing path
        mock_audio_output = torch.randn(1, 1, 4096)
        self.mock_snac.decode.return_value = mock_audio_output
        
        # Test conversion
        audio_data = await self.model.tokens_to_audio(test_tokens)
        
        # Should succeed with CPU path
        assert audio_data is not None
        assert isinstance(audio_data, bytes)
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_error_handling(self):
        """Test error handling in SNAC conversion"""
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Mock SNAC to raise an exception
        self.mock_snac.decode.side_effect = RuntimeError("SNAC decode failed")
        
        # Test conversion - should raise AudioGenerationError
        with pytest.raises(AudioGenerationError) as exc_info:
            await self.model.tokens_to_audio(test_tokens)
        
        assert "SNAC conversion failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_no_snac_model(self):
        """Test handling when SNAC model is not loaded"""
        test_tokens = [100, 200, 300, 400, 500, 600, 700]
        
        # Remove SNAC model
        self.model.snac_model = None
        
        # Test conversion - should raise AudioGenerationError
        with pytest.raises(AudioGenerationError) as exc_info:
            await self.model.tokens_to_audio(test_tokens)
        
        assert "SNAC model not loaded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_tokens_to_audio_frame_calculation(self):
        """Test correct frame calculation for different token counts"""
        # Test various token counts
        test_cases = [
            (7, 1),    # 7 tokens = 1 frame
            (14, 2),   # 14 tokens = 2 frames
            (21, 3),   # 21 tokens = 3 frames
            (8, 2),    # 8 tokens = 2 frames (padded to 14)
            (15, 3),   # 15 tokens = 3 frames (padded to 21)
        ]
        
        for token_count, expected_frames in test_cases:
            test_tokens = list(range(100, 100 + token_count))
            
            # Mock SNAC decode output
            mock_audio_output = torch.randn(1, 1, 4096)
            self.mock_snac.decode.return_value = mock_audio_output
            
            # Reset mock
            self.mock_snac.decode.reset_mock()
            
            # Test conversion
            audio_data = await self.model.tokens_to_audio(test_tokens)
            
            # Verify SNAC was called
            self.mock_snac.decode.assert_called_once()
            
            # Get the codes passed to SNAC
            call_args = self.mock_snac.decode.call_args[0][0]
            
            # Verify frame count in code structure
            assert call_args[0].shape[1] == expected_frames  # Code 0 has one value per frame
            assert call_args[1].shape[1] == expected_frames * 2  # Code 1 has two values per frame
            assert call_args[2].shape[1] == expected_frames * 4  # Code 2 has four values per frame

if __name__ == "__main__":
    pytest.main([__file__])