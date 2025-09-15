"""
Integration tests for Unified Model Manager
Tests shared GPU memory management and model coordination
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.unified_model_manager import (
    UnifiedModelManager, 
    ModelInitializationError
)

class TestUnifiedModelManager:
    """Test suite for Unified Model Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = UnifiedModelManager()
    
    def test_initialization(self):
        """Test UnifiedModelManager initialization"""
        assert self.manager.voxtral_model is None
        assert self.manager.orpheus_model is None
        assert self.manager.gpu_memory_manager is None
        assert not self.manager.is_initialized
        assert not self.manager.voxtral_initialized
        assert not self.manager.orpheus_initialized
        assert not self.manager.memory_manager_initialized
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_successful_initialization(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test successful initialization of all components"""
        # Mock GPU Memory Manager
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.return_value = True
        mock_gpu_manager.create_shared_memory_pool.return_value = Mock()
        mock_gpu_manager.device = "cuda"
        mock_gpu_manager.memory_pool = Mock()
        mock_gpu_manager.track_model_memory = Mock()
        mock_gpu_manager.cleanup_unused_memory = Mock()
        mock_gpu_manager.optimize_memory_allocation.return_value = {"optimization_level": "performance"}
        mock_gpu_manager.get_memory_stats.return_value = Mock(
            total_vram_gb=16.0, used_vram_gb=8.0, available_vram_gb=8.0,
            voxtral_memory_gb=4.5, orpheus_memory_gb=2.5,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Mock Voxtral Model
        mock_voxtral = Mock()
        mock_voxtral.initialize = AsyncMock()
        mock_voxtral.is_initialized = True
        mock_voxtral.get_model_info.return_value = {"status": "initialized"}
        mock_voxtral_class.return_value = mock_voxtral
        
        # Mock Orpheus Model
        mock_orpheus = Mock()
        mock_orpheus.initialize = AsyncMock()
        mock_orpheus.is_initialized = True
        mock_orpheus.get_model_info.return_value = {"is_initialized": True}
        mock_orpheus_class.return_value = mock_orpheus
        
        # Mock torch.cuda.memory_allocated for memory tracking
        with patch('torch.cuda.memory_allocated', side_effect=[4.5 * 1024**3, 7.0 * 1024**3]):
            # Test initialization
            result = await self.manager.initialize()
            
            assert result is True
            assert self.manager.is_initialized
            assert self.manager.voxtral_initialized
            assert self.manager.orpheus_initialized
            assert self.manager.memory_manager_initialized
            
            # Verify initialization order
            mock_gpu_manager.validate_vram_requirements.assert_called_once()
            mock_gpu_manager.create_shared_memory_pool.assert_called_once()
            mock_voxtral.initialize.assert_called_once()
            mock_orpheus.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    async def test_memory_manager_initialization_failure(self, mock_gpu_manager_class):
        """Test handling of memory manager initialization failure"""
        # Mock GPU Memory Manager to raise exception
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.side_effect = Exception("VRAM validation failed")
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Test initialization - should raise ModelInitializationError
        with pytest.raises(ModelInitializationError) as exc_info:
            await self.manager.initialize()
        
        assert "Memory manager initialization failed" in str(exc_info.value)
        assert not self.manager.is_initialized
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    async def test_voxtral_initialization_failure(self, mock_voxtral_class, mock_gpu_manager_class):
        """Test handling of Voxtral initialization failure"""
        # Mock successful GPU Memory Manager
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.return_value = True
        mock_gpu_manager.create_shared_memory_pool.return_value = Mock()
        mock_gpu_manager.device = "cuda"
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Mock Voxtral Model to fail initialization
        mock_voxtral = Mock()
        mock_voxtral.initialize = AsyncMock(side_effect=Exception("Voxtral init failed"))
        mock_voxtral_class.return_value = mock_voxtral
        
        # Test initialization - should raise ModelInitializationError
        with pytest.raises(ModelInitializationError) as exc_info:
            await self.manager.initialize()
        
        assert "Voxtral initialization failed" in str(exc_info.value)
        assert not self.manager.is_initialized
        assert not self.manager.voxtral_initialized
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_orpheus_initialization_failure(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test handling of Orpheus initialization failure"""
        # Mock successful GPU Memory Manager
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.return_value = True
        mock_gpu_manager.create_shared_memory_pool.return_value = Mock()
        mock_gpu_manager.device = "cuda"
        mock_gpu_manager.memory_pool = Mock()
        mock_gpu_manager.track_model_memory = Mock()
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Mock successful Voxtral Model
        mock_voxtral = Mock()
        mock_voxtral.initialize = AsyncMock()
        mock_voxtral.is_initialized = True
        mock_voxtral_class.return_value = mock_voxtral
        
        # Mock Orpheus Model to fail initialization
        mock_orpheus = Mock()
        mock_orpheus.initialize = AsyncMock(side_effect=Exception("Orpheus init failed"))
        mock_orpheus_class.return_value = mock_orpheus
        
        with patch('torch.cuda.memory_allocated', return_value=4.5 * 1024**3):
            # Test initialization - should raise ModelInitializationError
            with pytest.raises(ModelInitializationError) as exc_info:
                await self.manager.initialize()
        
        assert "Orpheus initialization failed" in str(exc_info.value)
        assert not self.manager.is_initialized
        assert not self.manager.orpheus_initialized
    
    @pytest.mark.asyncio
    async def test_get_voxtral_model_not_initialized(self):
        """Test getting Voxtral model when not initialized"""
        with pytest.raises(ModelInitializationError) as exc_info:
            await self.manager.get_voxtral_model()
        
        assert "Voxtral model not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_orpheus_model_not_initialized(self):
        """Test getting Orpheus model when not initialized"""
        with pytest.raises(ModelInitializationError) as exc_info:
            await self.manager.get_orpheus_model()
        
        assert "Orpheus model not initialized" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_get_models_after_initialization(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test getting models after successful initialization"""
        # Setup mocks for successful initialization
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.return_value = True
        mock_gpu_manager.create_shared_memory_pool.return_value = Mock()
        mock_gpu_manager.device = "cuda"
        mock_gpu_manager.memory_pool = Mock()
        mock_gpu_manager.track_model_memory = Mock()
        mock_gpu_manager.cleanup_unused_memory = Mock()
        mock_gpu_manager.optimize_memory_allocation.return_value = {"optimization_level": "performance"}
        mock_gpu_manager.get_memory_stats.return_value = Mock(
            total_vram_gb=16.0, used_vram_gb=8.0, available_vram_gb=8.0,
            voxtral_memory_gb=4.5, orpheus_memory_gb=2.5,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        mock_voxtral = Mock()
        mock_voxtral.initialize = AsyncMock()
        mock_voxtral.is_initialized = True
        mock_voxtral.get_model_info.return_value = {"status": "initialized"}
        mock_voxtral_class.return_value = mock_voxtral
        
        mock_orpheus = Mock()
        mock_orpheus.initialize = AsyncMock()
        mock_orpheus.is_initialized = True
        mock_orpheus.get_model_info.return_value = {"is_initialized": True}
        mock_orpheus_class.return_value = mock_orpheus
        
        with patch('torch.cuda.memory_allocated', side_effect=[4.5 * 1024**3, 7.0 * 1024**3]):
            # Initialize
            await self.manager.initialize()
            
            # Test getting models
            voxtral_model = await self.manager.get_voxtral_model()
            orpheus_model = await self.manager.get_orpheus_model()
            
            assert voxtral_model is mock_voxtral
            assert orpheus_model is mock_orpheus
    
    @pytest.mark.asyncio
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.empty_cache')
    @patch('gc.collect')
    async def test_cleanup_gpu_memory(self, mock_gc_collect, mock_empty_cache, mock_cuda_available):
        """Test GPU memory cleanup"""
        mock_cuda_available.return_value = True
        
        # Mock GPU memory manager
        mock_gpu_manager = Mock()
        mock_gpu_manager.cleanup_unused_memory = Mock()
        self.manager.gpu_memory_manager = mock_gpu_manager
        
        # Test cleanup
        await self.manager.cleanup_gpu_memory()
        
        # Verify cleanup calls
        mock_gpu_manager.cleanup_unused_memory.assert_called_once()
        mock_empty_cache.assert_called_once()
        mock_gc_collect.assert_called_once()
    
    def test_get_memory_stats_no_manager(self):
        """Test getting memory stats when manager not initialized"""
        stats = self.manager.get_memory_stats()
        
        assert "error" in stats
        assert stats["error"] == "Memory manager not initialized"
    
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    def test_get_memory_stats_with_manager(self, mock_gpu_manager_class):
        """Test getting memory stats with initialized manager"""
        # Mock GPU memory manager
        mock_gpu_manager = Mock()
        mock_stats = Mock(
            total_vram_gb=16.0, used_vram_gb=8.0, available_vram_gb=8.0,
            voxtral_memory_gb=4.5, orpheus_memory_gb=2.5,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_gpu_manager.get_memory_stats.return_value = mock_stats
        mock_gpu_manager.device = "cuda"
        
        self.manager.gpu_memory_manager = mock_gpu_manager
        self.manager.is_initialized = True
        self.manager.voxtral_initialized = True
        self.manager.orpheus_initialized = True
        
        stats = self.manager.get_memory_stats()
        
        assert "memory_stats" in stats
        assert stats["memory_stats"]["total_vram_gb"] == 16.0
        assert stats["memory_stats"]["voxtral_memory_gb"] == 4.5
        assert stats["memory_stats"]["orpheus_memory_gb"] == 2.5
        
        assert "initialization_stats" in stats
        assert stats["initialization_stats"]["is_initialized"] is True
        assert stats["initialization_stats"]["voxtral_initialized"] is True
        assert stats["initialization_stats"]["orpheus_initialized"] is True
    
    def test_get_model_info_basic(self):
        """Test getting basic model info"""
        info = self.manager.get_model_info()
        
        assert "unified_manager" in info
        assert info["unified_manager"]["is_initialized"] is False
        assert info["unified_manager"]["voxtral_initialized"] is False
        assert info["unified_manager"]["orpheus_initialized"] is False
        assert info["unified_manager"]["memory_manager_initialized"] is False
    
    @pytest.mark.asyncio
    async def test_shutdown_basic(self):
        """Test basic shutdown functionality"""
        # Mock some initialized state
        mock_orpheus = Mock()
        mock_orpheus.cleanup = AsyncMock()
        self.manager.orpheus_model = mock_orpheus
        self.manager.orpheus_initialized = True
        
        mock_voxtral = Mock()
        self.manager.voxtral_model = mock_voxtral
        self.manager.voxtral_initialized = True
        
        mock_gpu_manager = Mock()
        mock_gpu_manager.cleanup_unused_memory = Mock()
        self.manager.gpu_memory_manager = mock_gpu_manager
        self.manager.memory_manager_initialized = True
        
        self.manager.is_initialized = True
        
        # Test shutdown
        await self.manager.shutdown()
        
        # Verify cleanup
        mock_orpheus.cleanup.assert_called_once()
        mock_gpu_manager.cleanup_unused_memory.assert_called_once()
        
        # Verify state reset
        assert self.manager.orpheus_model is None
        assert self.manager.voxtral_model is None
        assert self.manager.gpu_memory_manager is None
        assert not self.manager.is_initialized
        assert not self.manager.voxtral_initialized
        assert not self.manager.orpheus_initialized
        assert not self.manager.memory_manager_initialized
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_memory_tracking_during_initialization(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test memory tracking during model initialization"""
        # Mock GPU Memory Manager
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.return_value = True
        mock_gpu_manager.create_shared_memory_pool.return_value = Mock()
        mock_gpu_manager.device = "cuda"
        mock_gpu_manager.memory_pool = Mock()
        mock_gpu_manager.track_model_memory = Mock()
        mock_gpu_manager.cleanup_unused_memory = Mock()
        mock_gpu_manager.optimize_memory_allocation.return_value = {"optimization_level": "performance"}
        mock_gpu_manager.get_memory_stats.return_value = Mock(
            total_vram_gb=16.0, used_vram_gb=8.0, available_vram_gb=8.0,
            voxtral_memory_gb=4.5, orpheus_memory_gb=2.5,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Mock models
        mock_voxtral = Mock()
        mock_voxtral.initialize = AsyncMock()
        mock_voxtral.is_initialized = True
        mock_voxtral.get_model_info.return_value = {"status": "initialized"}
        mock_voxtral_class.return_value = mock_voxtral
        
        mock_orpheus = Mock()
        mock_orpheus.initialize = AsyncMock()
        mock_orpheus.is_initialized = True
        mock_orpheus.get_model_info.return_value = {"is_initialized": True}
        mock_orpheus_class.return_value = mock_orpheus
        
        # Mock memory allocation tracking
        with patch('torch.cuda.memory_allocated', side_effect=[4.5 * 1024**3, 7.0 * 1024**3]):
            await self.manager.initialize()
            
            # Verify memory tracking calls
            assert mock_gpu_manager.track_model_memory.call_count == 2
            
            # Check specific calls
            calls = mock_gpu_manager.track_model_memory.call_args_list
            assert calls[0][0] == ("voxtral", 4.5)  # First call for Voxtral
            assert calls[1][0] == ("orpheus", 2.5)  # Second call for Orpheus (7.0 - 4.5)
    
    @pytest.mark.asyncio
    async def test_already_initialized(self):
        """Test calling initialize when already initialized"""
        # Set as already initialized
        self.manager.is_initialized = True
        
        # Should return True without doing anything
        result = await self.manager.initialize()
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__])