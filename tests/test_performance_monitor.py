"""
Unit tests for Performance Monitor
Tests timing operations, latency tracking, and performance analysis
"""

import pytest
import time
import sys
import os
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.performance_monitor import (
    PerformanceMonitor, 
    LatencyBreakdown,
    TimingOperation,
    PerformanceDegradationError,
    LatencyExceededError
)

class TestPerformanceMonitor:
    """Test suite for Performance Monitor"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = PerformanceMonitor()
    
    def test_initialization(self):
        """Test PerformanceMonitor initialization"""
        assert len(self.monitor.active_timings) == 0
        assert len(self.monitor.completed_operations) == 0
        assert len(self.monitor.latency_history) == 0
        assert self.monitor.consecutive_failures == 0
        assert self.monitor.baseline_latency_ms is None
        
        # Check default targets
        assert self.monitor.targets["voxtral_processing_ms"] == 100
        assert self.monitor.targets["orpheus_generation_ms"] == 150
        assert self.monitor.targets["audio_conversion_ms"] == 50
        assert self.monitor.targets["total_end_to_end_ms"] == 300
    
    def test_start_timing(self):
        """Test starting timing operations"""
        operation_id = self.monitor.start_timing("test_operation")
        
        assert operation_id is not None
        assert operation_id in self.monitor.active_timings
        
        timing_op = self.monitor.active_timings[operation_id]
        assert timing_op.operation_name == "test_operation"
        assert timing_op.start_time > 0
        assert timing_op.end_time is None
        assert timing_op.duration_ms is None
    
    def test_start_timing_with_metadata(self):
        """Test starting timing with metadata"""
        metadata = {"component": "voxtral", "chunk_size": 1024}
        operation_id = self.monitor.start_timing("voxtral_processing", metadata)
        
        timing_op = self.monitor.active_timings[operation_id]
        assert timing_op.metadata == metadata
    
    def test_end_timing(self):
        """Test ending timing operations"""
        operation_id = self.monitor.start_timing("test_operation")
        
        # Add small delay to ensure measurable duration
        time.sleep(0.01)
        
        duration = self.monitor.end_timing(operation_id)
        
        assert duration > 0
        assert operation_id not in self.monitor.active_timings
        assert len(self.monitor.completed_operations) == 1
        
        completed_op = self.monitor.completed_operations[0]
        assert completed_op.operation_name == "test_operation"
        assert completed_op.duration_ms == duration
        assert completed_op.end_time is not None
    
    def test_end_timing_invalid_id(self):
        """Test ending timing with invalid operation ID"""
        duration = self.monitor.end_timing("invalid_id")
        assert duration == 0.0
    
    def test_log_latency_breakdown_within_target(self):
        """Test logging latency breakdown within targets"""
        components = {
            "voxtral_processing_ms": 80,
            "orpheus_generation_ms": 120,
            "audio_conversion_ms": 30
        }
        
        self.monitor.log_latency_breakdown(components)
        
        assert len(self.monitor.latency_history) == 1
        breakdown = self.monitor.latency_history[0]
        
        assert breakdown.voxtral_processing_ms == 80
        assert breakdown.orpheus_generation_ms == 120
        assert breakdown.audio_conversion_ms == 30
        assert breakdown.total_latency_ms == 230
        assert breakdown.target_met is True
        
        assert self.monitor.stats["total_operations"] == 1
        assert self.monitor.stats["operations_within_target"] == 1
        assert self.monitor.consecutive_failures == 0
    
    def test_log_latency_breakdown_exceeds_target(self):
        """Test logging latency breakdown that exceeds targets"""
        components = {
            "voxtral_processing_ms": 150,  # Exceeds 100ms target
            "orpheus_generation_ms": 200,  # Exceeds 150ms target
            "audio_conversion_ms": 80      # Exceeds 50ms target
        }
        
        self.monitor.log_latency_breakdown(components)
        
        breakdown = self.monitor.latency_history[0]
        assert breakdown.total_latency_ms == 430
        assert breakdown.target_met is False
        
        assert self.monitor.stats["operations_exceeded_target"] == 1
        assert self.monitor.consecutive_failures == 1
    
    def test_check_performance_targets_no_data(self):
        """Test checking performance targets with no data"""
        results = self.monitor.check_performance_targets()
        assert results["no_data"] is True
    
    def test_check_performance_targets_with_data(self):
        """Test checking performance targets with data"""
        # Add some test data
        for i in range(5):
            components = {
                "voxtral_processing_ms": 90 + i * 5,  # 90, 95, 100, 105, 110
                "orpheus_generation_ms": 140 + i * 5,  # 140, 145, 150, 155, 160
                "audio_conversion_ms": 40 + i * 2      # 40, 42, 44, 46, 48
            }
            self.monitor.log_latency_breakdown(components)
        
        results = self.monitor.check_performance_targets()
        
        # Check that results contain expected keys
        assert "voxtral_processing_ms" in results
        assert "orpheus_generation_ms" in results
        assert "audio_conversion_ms" in results
        assert "total_end_to_end_ms" in results
        assert "overall_success_rate" in results
        
        # Check averages
        assert results["voxtral_processing_ms_avg"] == 100.0  # Average of 90,95,100,105,110
        assert results["orpheus_generation_ms_avg"] == 150.0  # Average of 140,145,150,155,160
    
    def test_consecutive_failures_tracking(self):
        """Test tracking of consecutive failures"""
        # Add operations that exceed targets
        for i in range(3):
            components = {
                "voxtral_processing_ms": 200,  # Exceeds target
                "orpheus_generation_ms": 250,  # Exceeds target
                "audio_conversion_ms": 100     # Exceeds target
            }
            self.monitor.log_latency_breakdown(components)
        
        assert self.monitor.consecutive_failures == 3
        
        # Add operation within target
        components = {
            "voxtral_processing_ms": 80,
            "orpheus_generation_ms": 120,
            "audio_conversion_ms": 30
        }
        self.monitor.log_latency_breakdown(components)
        
        assert self.monitor.consecutive_failures == 0
    
    def test_baseline_establishment(self):
        """Test baseline latency establishment"""
        assert self.monitor.baseline_latency_ms is None
        
        # Add 10 operations to establish baseline
        for i in range(10):
            components = {
                "voxtral_processing_ms": 90,
                "orpheus_generation_ms": 140,
                "audio_conversion_ms": 40
            }
            self.monitor.log_latency_breakdown(components)
        
        # Baseline should be established
        assert self.monitor.baseline_latency_ms is not None
        assert self.monitor.baseline_latency_ms == 270.0  # 90 + 140 + 40
    
    def test_statistics_update(self):
        """Test statistics updates"""
        # Start with clean stats
        assert self.monitor.stats["min_latency_ms"] == float('inf')
        assert self.monitor.stats["max_latency_ms"] == 0.0
        
        # Add timing operations with different durations
        durations = [100, 200, 150, 300, 50]
        
        for duration in durations:
            operation_id = self.monitor.start_timing("test_op")
            # Simulate the duration by directly setting it
            timing_op = self.monitor.active_timings[operation_id]
            timing_op.duration_ms = duration
            timing_op.end_time = timing_op.start_time + (duration / 1000)
            
            # Move to completed operations
            self.monitor.active_timings.pop(operation_id)
            self.monitor.completed_operations.append(timing_op)
            self.monitor._update_statistics(timing_op)
        
        # Check statistics
        assert self.monitor.stats["min_latency_ms"] == 50
        assert self.monitor.stats["max_latency_ms"] == 300
        assert self.monitor.stats["average_latency_ms"] == 160.0  # Mean of [100,200,150,300,50]
    
    def test_get_performance_summary(self):
        """Test getting performance summary"""
        # Add some test data
        components = {
            "voxtral_processing_ms": 90,
            "orpheus_generation_ms": 140,
            "audio_conversion_ms": 40
        }
        self.monitor.log_latency_breakdown(components)
        
        summary = self.monitor.get_performance_summary()
        
        assert "statistics" in summary
        assert "targets" in summary
        assert "recent_performance" in summary
        assert "active_timings" in summary
        assert "completed_operations" in summary
        assert "latency_history_size" in summary
        assert "consecutive_failures" in summary
        assert "baseline_latency_ms" in summary
        
        assert summary["latency_history_size"] == 1
        assert summary["consecutive_failures"] == 0
    
    def test_get_optimization_recommendations_no_data(self):
        """Test getting recommendations with no data"""
        recommendations = self.monitor.get_optimization_recommendations()
        assert len(recommendations) == 1
        assert "No performance data available" in recommendations[0]
    
    def test_get_optimization_recommendations_good_performance(self):
        """Test getting recommendations with good performance"""
        # Add operations within targets
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 80,
                "orpheus_generation_ms": 120,
                "audio_conversion_ms": 30
            }
            self.monitor.log_latency_breakdown(components)
        
        recommendations = self.monitor.get_optimization_recommendations()
        assert any("Performance is within targets" in rec for rec in recommendations)
    
    def test_get_optimization_recommendations_slow_voxtral(self):
        """Test getting recommendations for slow Voxtral processing"""
        # Add operations with slow Voxtral
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 150,  # Exceeds 100ms target
                "orpheus_generation_ms": 120,
                "audio_conversion_ms": 30
            }
            self.monitor.log_latency_breakdown(components)
        
        recommendations = self.monitor.get_optimization_recommendations()
        assert any("Voxtral processing is slow" in rec for rec in recommendations)
    
    def test_get_optimization_recommendations_slow_orpheus(self):
        """Test getting recommendations for slow Orpheus generation"""
        # Add operations with slow Orpheus
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 80,
                "orpheus_generation_ms": 200,  # Exceeds 150ms target
                "audio_conversion_ms": 30
            }
            self.monitor.log_latency_breakdown(components)
        
        recommendations = self.monitor.get_optimization_recommendations()
        assert any("Orpheus generation is slow" in rec for rec in recommendations)
    
    def test_get_optimization_recommendations_slow_conversion(self):
        """Test getting recommendations for slow audio conversion"""
        # Add operations with slow conversion
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 80,
                "orpheus_generation_ms": 120,
                "audio_conversion_ms": 80  # Exceeds 50ms target
            }
            self.monitor.log_latency_breakdown(components)
        
        recommendations = self.monitor.get_optimization_recommendations()
        assert any("Audio conversion is slow" in rec for rec in recommendations)
    
    def test_reset_statistics(self):
        """Test resetting statistics"""
        # Add some data
        operation_id = self.monitor.start_timing("test_op")
        self.monitor.end_timing(operation_id)
        
        components = {"voxtral_processing_ms": 90, "orpheus_generation_ms": 140, "audio_conversion_ms": 40}
        self.monitor.log_latency_breakdown(components)
        
        # Verify data exists
        assert len(self.monitor.completed_operations) > 0
        assert len(self.monitor.latency_history) > 0
        assert self.monitor.stats["total_operations"] > 0
        
        # Reset
        self.monitor.reset_statistics()
        
        # Verify reset
        assert len(self.monitor.completed_operations) == 0
        assert len(self.monitor.latency_history) == 0
        assert len(self.monitor.active_timings) == 0
        assert self.monitor.stats["total_operations"] == 0
        assert self.monitor.consecutive_failures == 0
        assert self.monitor.baseline_latency_ms is None
    
    def test_latency_breakdown_dataclass(self):
        """Test LatencyBreakdown dataclass"""
        breakdown = LatencyBreakdown(
            voxtral_processing_ms=90,
            text_generation_ms=20,
            orpheus_generation_ms=140,
            audio_conversion_ms=40,
            total_latency_ms=290,
            target_met=True
        )
        
        assert breakdown.voxtral_processing_ms == 90
        assert breakdown.text_generation_ms == 20
        assert breakdown.orpheus_generation_ms == 140
        assert breakdown.audio_conversion_ms == 40
        assert breakdown.total_latency_ms == 290
        assert breakdown.target_met is True
    
    def test_timing_operation_dataclass(self):
        """Test TimingOperation dataclass"""
        metadata = {"test": "value"}
        timing_op = TimingOperation(
            operation_id="test_123",
            operation_name="test_operation",
            start_time=time.time(),
            metadata=metadata
        )
        
        assert timing_op.operation_id == "test_123"
        assert timing_op.operation_name == "test_operation"
        assert timing_op.start_time > 0
        assert timing_op.end_time is None
        assert timing_op.duration_ms is None
        assert timing_op.metadata == metadata

if __name__ == "__main__":
    pytest.main([__file__])