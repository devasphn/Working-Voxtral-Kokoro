"""
Unit tests for GPU Memory Manager
Tests memory allocation, cleanup, and monitoring functionality
"""

import pytest
import torch
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.gpu_memory_manager import (
    GPUMemoryManager, 
    InsufficientVRAMError, 
    MemoryAllocationError,
    MemoryStats
)

class TestGPUMemoryManager:
    """Test suite for GPU Memory Manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = GPUMemoryManager()
    
    def test_initialization(self):
        """Test GPU Memory Manager initialization"""
        assert self.manager.device in ["cuda", "cpu"]
        assert self.manager.allocated_memory == {}
        assert self.manager.voxtral_memory_gb == 0.0
        assert self.manager.orpheus_memory_gb == 0.0
        assert self.manager.min_vram_gb == 8.0
        assert self.manager.recommended_vram_gb == 16.0
    
    @patch('torch.cuda.is_available')
    def test_device_detection_cuda(self, mock_cuda_available):
        """Test CUDA device detection"""
        mock_cuda_available.return_value = True
        manager = GPUMemoryManager()
        assert manager.device == "cuda"
    
    @patch('torch.cuda.is_available')
    def test_device_detection_cpu(self, mock_cuda_available):
        """Test CPU fallback detection"""
        mock_cuda_available.return_value = False
        manager = GPUMemoryManager()
        assert manager.device == "cpu"
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    @patch('torch.cuda.memory_allocated')
    def test_validate_vram_requirements_sufficient(self, mock_memory_allocated, 
                                                  mock_device_properties, mock_cuda_available):
        """Test VRAM validation with sufficient memory"""
        mock_cuda_available.return_value = True
        
        # Mock GPU with 16GB VRAM
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 16 * 1024**3  # 16GB in bytes
        mock_device_properties.return_value = mock_device_props
        
        # Mock 2GB currently allocated
        mock_memory_allocated.return_value = 2 * 1024**3  # 2GB in bytes
        
        manager = GPUMemoryManager()
        result = manager.validate_vram_requirements()
        assert result is True
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_validate_vram_requirements_insufficient(self, mock_device_properties, mock_cuda_available):
        """Test VRAM validation with insufficient memory"""
        mock_cuda_available.return_value = True
        
        # Mock GPU with only 4GB VRAM (below minimum)
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 4 * 1024**3  # 4GB in bytes
        mock_device_properties.return_value = mock_device_props
        
        manager = GPUMemoryManager()
        
        with pytest.raises(InsufficientVRAMError) as exc_info:
            manager.validate_vram_requirements()
        
        assert "Insufficient VRAM" in str(exc_info.value)
        assert "4.00 GB available" in str(exc_info.value)
        assert "minimum 8.00 GB required" in str(exc_info.value)
    
    @patch('torch.cuda.is_available')
    def test_validate_vram_requirements_cpu_mode(self, mock_cuda_available):
        """Test VRAM validation in CPU mode"""
        mock_cuda_available.return_value = False
        manager = GPUMemoryManager()
        
        result = manager.validate_vram_requirements()
        assert result is True
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.empty_cache')
    @patch('torch.cuda.set_per_process_memory_fraction')
    def test_create_shared_memory_pool_cuda(self, mock_set_fraction, mock_empty_cache, mock_cuda_available):
        """Test shared memory pool creation for CUDA"""
        mock_cuda_available.return_value = True
        manager = GPUMemoryManager()
        
        result = manager.create_shared_memory_pool()
        
        mock_empty_cache.assert_called_once()
        mock_set_fraction.assert_called_once_with(0.9)
    
    @patch('torch.cuda.is_available')
    def test_create_shared_memory_pool_cpu(self, mock_cuda_available):
        """Test shared memory pool creation for CPU"""
        mock_cuda_available.return_value = False
        manager = GPUMemoryManager()
        
        result = manager.create_shared_memory_pool()
        assert result is None
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.empty_cache')
    @patch('torch.cuda.memory_allocated')
    @patch('torch.cuda.memory_reserved')
    @patch('gc.collect')
    def test_cleanup_unused_memory_cuda(self, mock_gc_collect, mock_memory_reserved, 
                                       mock_memory_allocated, mock_empty_cache, mock_cuda_available):
        """Test memory cleanup for CUDA"""
        mock_cuda_available.return_value = True
        
        # Mock memory stats before and after cleanup
        mock_memory_allocated.side_effect = [3 * 1024**3, 2 * 1024**3]  # 3GB -> 2GB
        mock_memory_reserved.side_effect = [4 * 1024**3, 2.5 * 1024**3]  # 4GB -> 2.5GB
        
        manager = GPUMemoryManager()
        manager.cleanup_unused_memory()
        
        mock_empty_cache.assert_called_once()
        mock_gc_collect.assert_called_once()
    
    @patch('torch.cuda.is_available')
    @patch('gc.collect')
    def test_cleanup_unused_memory_cpu(self, mock_gc_collect, mock_cuda_available):
        """Test memory cleanup for CPU"""
        mock_cuda_available.return_value = False
        manager = GPUMemoryManager()
        
        manager.cleanup_unused_memory()
        mock_gc_collect.assert_called_once()
    
    def test_track_model_memory(self):
        """Test model memory tracking"""
        manager = GPUMemoryManager()
        
        # Track Voxtral memory
        manager.track_model_memory("voxtral", 4.5)
        assert manager.voxtral_memory_gb == 4.5
        assert manager.allocated_memory["voxtral"] == 4.5
        
        # Track Orpheus memory
        manager.track_model_memory("orpheus", 2.5)
        assert manager.orpheus_memory_gb == 2.5
        assert manager.allocated_memory["orpheus"] == 2.5
        
        # Track other model
        manager.track_model_memory("other_model", 1.0)
        assert manager.allocated_memory["other_model"] == 1.0
        # Should not affect voxtral/orpheus specific tracking
        assert manager.voxtral_memory_gb == 4.5
        assert manager.orpheus_memory_gb == 2.5
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    @patch('torch.cuda.memory_allocated')
    @patch('psutil.virtual_memory')
    def test_get_memory_stats_cuda(self, mock_virtual_memory, mock_memory_allocated, 
                                  mock_device_properties, mock_cuda_available):
        """Test memory statistics retrieval for CUDA"""
        mock_cuda_available.return_value = True
        
        # Mock GPU memory
        mock_device_props = MagicMock()
        mock_device_props.total_memory = 16 * 1024**3  # 16GB
        mock_device_properties.return_value = mock_device_props
        mock_memory_allocated.return_value = 8 * 1024**3  # 8GB used
        
        # Mock system memory
        mock_memory = MagicMock()
        mock_memory.total = 32 * 1024**3  # 32GB total
        mock_memory.used = 16 * 1024**3   # 16GB used
        mock_virtual_memory.return_value = mock_memory
        
        manager = GPUMemoryManager()
        manager.voxtral_memory_gb = 4.5
        manager.orpheus_memory_gb = 2.5
        
        stats = manager.get_memory_stats()
        
        assert isinstance(stats, MemoryStats)
        assert stats.total_vram_gb == 16.0
        assert stats.used_vram_gb == 8.0
        assert stats.available_vram_gb == 8.0
        assert stats.voxtral_memory_gb == 4.5
        assert stats.orpheus_memory_gb == 2.5
        assert stats.system_ram_gb == 32.0
        assert stats.system_ram_used_gb == 16.0
    
    @patch('torch.cuda.is_available')
    @patch('psutil.virtual_memory')
    def test_get_memory_stats_cpu(self, mock_virtual_memory, mock_cuda_available):
        """Test memory statistics retrieval for CPU"""
        mock_cuda_available.return_value = False
        
        # Mock system memory
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024**3  # 16GB total
        mock_memory.used = 8 * 1024**3    # 8GB used
        mock_virtual_memory.return_value = mock_memory
        
        manager = GPUMemoryManager()
        stats = manager.get_memory_stats()
        
        assert isinstance(stats, MemoryStats)
        assert stats.total_vram_gb == 0.0
        assert stats.used_vram_gb == 0.0
        assert stats.available_vram_gb == 0.0
        assert stats.system_ram_gb == 16.0
        assert stats.system_ram_used_gb == 8.0
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    def test_optimize_memory_allocation_high_vram(self, mock_get_stats):
        """Test memory optimization for high VRAM systems"""
        # Mock high VRAM stats
        mock_stats = MemoryStats(
            total_vram_gb=24.0, used_vram_gb=8.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=16.0,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        recommendations = manager.optimize_memory_allocation()
        
        assert recommendations["optimization_level"] == "performance"
        assert recommendations["precision"] == "fp16"
        assert recommendations["memory_efficient"] is False
        assert recommendations["preload_models"] is True
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    def test_optimize_memory_allocation_medium_vram(self, mock_get_stats):
        """Test memory optimization for medium VRAM systems"""
        # Mock medium VRAM stats
        mock_stats = MemoryStats(
            total_vram_gb=12.0, used_vram_gb=4.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=8.0,
            system_ram_gb=16.0, system_ram_used_gb=8.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        recommendations = manager.optimize_memory_allocation()
        
        assert recommendations["optimization_level"] == "balanced"
        assert recommendations["precision"] == "fp16"
        assert recommendations["memory_efficient"] is True
        assert recommendations["preload_models"] is False
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    def test_optimize_memory_allocation_low_vram(self, mock_get_stats):
        """Test memory optimization for low VRAM systems"""
        # Mock low VRAM stats
        mock_stats = MemoryStats(
            total_vram_gb=6.0, used_vram_gb=2.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=4.0,
            system_ram_gb=8.0, system_ram_used_gb=4.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        recommendations = manager.optimize_memory_allocation()
        
        assert recommendations["optimization_level"] == "memory_efficient"
        assert recommendations["precision"] == "fp32"
        assert recommendations["memory_efficient"] is True
        assert recommendations["preload_models"] is False
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    @patch('time.time')
    def test_monitor_memory_usage_healthy(self, mock_time, mock_get_stats):
        """Test memory monitoring with healthy usage"""
        mock_time.return_value = 1234567890.0
        
        # Mock healthy memory stats
        mock_stats = MemoryStats(
            total_vram_gb=16.0, used_vram_gb=8.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=8.0,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        manager.voxtral_memory_gb = 4.5
        manager.orpheus_memory_gb = 2.5
        
        monitoring_data = manager.monitor_memory_usage()
        
        assert monitoring_data["status"] == "healthy"
        assert monitoring_data["vram_usage_percent"] == 50.0
        assert monitoring_data["ram_usage_percent"] == 50.0
        assert len(monitoring_data["warnings"]) == 0
        assert monitoring_data["timestamp"] == 1234567890.0
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    def test_monitor_memory_usage_high_usage(self, mock_get_stats):
        """Test memory monitoring with high usage"""
        # Mock high memory usage stats
        mock_stats = MemoryStats(
            total_vram_gb=16.0, used_vram_gb=14.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=2.0,
            system_ram_gb=32.0, system_ram_used_gb=30.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        manager.voxtral_memory_gb = 4.5
        manager.orpheus_memory_gb = 2.5
        
        monitoring_data = manager.monitor_memory_usage()
        
        assert monitoring_data["status"] == "warning"
        assert monitoring_data["vram_usage_percent"] == 87.5
        assert monitoring_data["ram_usage_percent"] == 93.75
        assert "VRAM usage high (>80%)" in monitoring_data["warnings"]
        assert "System RAM usage critically high (>90%)" in monitoring_data["warnings"]
    
    @patch.object(GPUMemoryManager, 'get_memory_stats')
    def test_monitor_memory_usage_memory_leak(self, mock_get_stats):
        """Test memory monitoring with potential memory leak"""
        # Mock stats indicating potential memory leak
        mock_stats = MemoryStats(
            total_vram_gb=16.0, used_vram_gb=12.0, voxtral_memory_gb=4.5,
            orpheus_memory_gb=2.5, available_vram_gb=4.0,
            system_ram_gb=32.0, system_ram_used_gb=16.0
        )
        mock_get_stats.return_value = mock_stats
        
        manager = GPUMemoryManager()
        manager.voxtral_memory_gb = 4.5
        manager.orpheus_memory_gb = 2.5
        
        monitoring_data = manager.monitor_memory_usage()
        
        assert "Potential memory leak detected" in monitoring_data["warnings"]
        # 12GB used vs 7GB expected (4.5 + 2.5) * 1.5 = 10.5GB threshold

if __name__ == "__main__":
    pytest.main([__file__])