"""
Tests for Perfect Voxtral + Orpheus TTS System
Simple tests to verify the perfect integration works
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPerfectSystem:
    """Test suite for Perfect System"""
    
    def test_imports(self):
        """Test that all perfect system components can be imported"""
        try:
            from src.tts.orpheus_perfect_model import OrpheusPerfectModel
            from src.tts.tts_service_perfect import TTSServicePerfect
            from src.models.voxtral_model_realtime import VoxtralModel
            from src.models.unified_model_manager import UnifiedModelManager
            assert True  # All imports successful
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_orpheus_perfect_model_creation(self):
        """Test OrpheusPerfectModel can be created"""
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        model = OrpheusPerfectModel()
        assert model is not None
        assert model.model_name == "canopylabs/orpheus-tts-0.1-finetune-prod"
        assert model.max_model_len == 2048
        assert model.sample_rate == 24000
        assert not model.is_initialized
    
    def test_tts_service_perfect_creation(self):
        """Test TTSServicePerfect can be created"""
        from src.tts.tts_service_perfect import TTSServicePerfect
        
        service = TTSServicePerfect()
        assert service is not None
        assert not service.is_initialized
        assert service.generation_count == 0
    
    def test_voxtral_model_creation(self):
        """Test VoxtralModel can be created"""
        from src.models.voxtral_model_realtime import VoxtralModel
        
        model = VoxtralModel()
        assert model is not None
        assert not model.is_initialized
    
    def test_unified_model_manager_creation(self):
        """Test UnifiedModelManager can be created"""
        from src.models.unified_model_manager import UnifiedModelManager
        
        manager = UnifiedModelManager()
        assert manager is not None
        assert not manager.is_initialized
        assert manager.voxtral_model is None
        assert manager.orpheus_model is None
    
    @pytest.mark.asyncio
    @patch('src.tts.orpheus_perfect_model.OrpheusModel')
    async def test_orpheus_perfect_model_initialization(self, mock_orpheus_class):
        """Test OrpheusPerfectModel initialization with mocked OrpheusModel"""
        from src.tts.orpheus_perfect_model import OrpheusPerfectModel
        
        # Mock the OrpheusModel
        mock_orpheus_instance = Mock()
        mock_orpheus_instance.generate_speech.return_value = iter([b'test_audio_chunk'])
        mock_orpheus_class.return_value = mock_orpheus_instance
        
        model = OrpheusPerfectModel()
        
        # Mock the availability check
        with patch('src.tts.orpheus_perfect_model.ORPHEUS_AVAILABLE', True):
            success = await model.initialize()
            
            assert success
            assert model.is_initialized
            mock_orpheus_class.assert_called_once_with(
                model_name="canopylabs/orpheus-tts-0.1-finetune-prod",
                max_model_len=2048
            )
    
    @pytest.mark.asyncio
    @patch('src.tts.orpheus_perfect_model.orpheus_perfect_model')
    async def test_tts_service_perfect_initialization(self, mock_orpheus_model):
        """Test TTSServicePerfect initialization with mocked Orpheus model"""
        from src.tts.tts_service_perfect import TTSServicePerfect
        
        # Mock the orpheus model
        mock_orpheus_model.initialize.return_value = True
        
        service = TTSServicePerfect()
        success = await service.initialize()
        
        assert success
        assert service.is_initialized
        mock_orpheus_model.initialize.assert_called_once()
    
    def test_configuration_values(self):
        """Test that configuration has correct values"""
        from src.utils.config import config
        
        # Test Voxtral model name
        assert "mistralai/Voxtral-Mini-3B-2507" in config.model.name
        
        # Test Orpheus configuration
        assert hasattr(config.tts, 'orpheus_direct')
        assert config.tts.orpheus_direct.model_name == "canopylabs/orpheus-tts-0.1-finetune-prod"
        assert config.tts.orpheus_direct.max_model_len == 2048
        assert config.tts.orpheus_direct.sample_rate == 24000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])