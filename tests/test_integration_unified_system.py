"""
Integration tests for the unified model system
Tests the complete integration of UnifiedModelManager, OrpheusDirectModel, and performance monitoring
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.unified_model_manager import UnifiedModelManager
from src.tts.tts_service_direct import TTSServiceDirect
from src.utils.performance_monitor import PerformanceMonitor

class TestUnifiedSystemIntegration:
    """Integration tests for the complete unified system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = UnifiedModelManager()
        self.tts_service = TTSServiceDirect()
        self.performance_monitor = PerformanceMonitor()
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_complete_system_initialization(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test complete system initialization with all components"""
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
        mock_orpheus.generate_speech = AsyncMock(return_value=b"fake_audio_data")
        mock_orpheus_class.return_value = mock_orpheus
        
        with patch('torch.cuda.memory_allocated', side_effect=[4.5 * 1024**3, 7.0 * 1024**3]):
            # Test unified manager initialization
            success = await self.manager.initialize()
            assert success is True
            assert self.manager.is_initialized
            
            # Test getting models
            voxtral_model = await self.manager.get_voxtral_model()
            orpheus_model = await self.manager.get_orpheus_model()
            
            assert voxtral_model is mock_voxtral
            assert orpheus_model is mock_orpheus
            
            # Test TTS service initialization with unified manager
            # Note: This would require modifying TTSServiceDirect to work with unified manager
            # For now, we'll test the components separately
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        # Test timing operations
        timing_id = self.performance_monitor.start_timing("test_operation")
        assert timing_id is not None
        
        # Simulate some processing time
        import time
        time.sleep(0.01)
        
        duration = self.performance_monitor.end_timing(timing_id)
        assert duration > 0
        
        # Test latency breakdown logging
        components = {
            "voxtral_processing_ms": 80,
            "orpheus_generation_ms": 120,
            "audio_conversion_ms": 30
        }
        
        self.performance_monitor.log_latency_breakdown(components)
        
        # Check that latency was recorded
        assert len(self.performance_monitor.latency_history) == 1
        breakdown = self.performance_monitor.latency_history[0]
        assert breakdown.total_latency_ms == 230
        assert breakdown.target_met is True  # Within 300ms target
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_error_handling_integration(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test error handling across the unified system"""
        # Mock GPU Memory Manager to fail
        mock_gpu_manager = Mock()
        mock_gpu_manager.validate_vram_requirements.side_effect = Exception("VRAM validation failed")
        mock_gpu_manager_class.return_value = mock_gpu_manager
        
        # Test that initialization fails gracefully
        with pytest.raises(Exception) as exc_info:
            await self.manager.initialize()
        
        assert "Memory manager initialization failed" in str(exc_info.value)
        assert not self.manager.is_initialized
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_memory_management_integration(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test memory management across the unified system"""
        # Setup successful mocks
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
            # Initialize system
            await self.manager.initialize()
            
            # Test memory cleanup
            await self.manager.cleanup_gpu_memory()
            mock_gpu_manager.cleanup_unused_memory.assert_called()
            
            # Test memory statistics
            stats = self.manager.get_memory_stats()
            assert "memory_stats" in stats
            assert stats["memory_stats"]["total_vram_gb"] == 16.0
            assert stats["memory_stats"]["voxtral_memory_gb"] == 4.5
            assert stats["memory_stats"]["orpheus_memory_gb"] == 2.5
    
    @pytest.mark.asyncio
    @patch('src.models.unified_model_manager.GPUMemoryManager')
    @patch('src.models.unified_model_manager.VoxtralModel')
    @patch('src.models.unified_model_manager.OrpheusDirectModel')
    async def test_system_shutdown_integration(self, mock_orpheus_class, mock_voxtral_class, mock_gpu_manager_class):
        """Test complete system shutdown"""
        # Setup mocks
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
        mock_orpheus.cleanup = AsyncMock()
        mock_orpheus_class.return_value = mock_orpheus
        
        with patch('torch.cuda.memory_allocated', side_effect=[4.5 * 1024**3, 7.0 * 1024**3]):
            # Initialize system
            await self.manager.initialize()
            assert self.manager.is_initialized
            
            # Test shutdown
            await self.manager.shutdown()
            
            # Verify cleanup was called
            mock_orpheus.cleanup.assert_called_once()
            mock_gpu_manager.cleanup_unused_memory.assert_called()
            
            # Verify state reset
            assert not self.manager.is_initialized
            assert not self.manager.voxtral_initialized
            assert not self.manager.orpheus_initialized
    
    def test_performance_recommendations(self):
        """Test performance optimization recommendations"""
        # Add some test data with performance issues
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 150,  # Exceeds 100ms target
                "orpheus_generation_ms": 200,  # Exceeds 150ms target
                "audio_conversion_ms": 80      # Exceeds 50ms target
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        recommendations = self.performance_monitor.get_optimization_recommendations()
        
        # Should have recommendations for each slow component
        assert any("Voxtral processing is slow" in rec for rec in recommendations)
        assert any("Orpheus generation is slow" in rec for rec in recommendations)
        assert any("Audio conversion is slow" in rec for rec in recommendations)
    
    def test_system_health_check(self):
        """Test system health check functionality"""
        # Test with uninitialized system
        model_info = self.manager.get_model_info()
        assert not model_info["unified_manager"]["is_initialized"]
        
        # Test performance monitor
        performance_summary = self.performance_monitor.get_performance_summary()
        assert "statistics" in performance_summary
        assert "targets" in performance_summary

if __name__ == "__main__":
    pytest.main([__file__])