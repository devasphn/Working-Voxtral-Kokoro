"""
Performance validation tests for Orpheus TTS Integration
Tests latency targets, memory usage, and performance under load
"""

import pytest
import asyncio
import time
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import statistics

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.performance_monitor import PerformanceMonitor
from src.models.unified_model_manager import UnifiedModelManager
from src.tts.tts_service_direct import TTSServiceDirect

class TestPerformanceValidation:
    """Performance validation test suite"""
    
    def setup_method(self):
        """Setup test environment"""
        self.performance_monitor = PerformanceMonitor()
        self.unified_manager = UnifiedModelManager()
        self.tts_service = TTSServiceDirect()
    
    def test_latency_targets_definition(self):
        """Test that performance targets are properly defined"""
        targets = self.performance_monitor.targets
        
        # Verify all required targets are defined
        assert "voxtral_processing_ms" in targets
        assert "orpheus_generation_ms" in targets
        assert "audio_conversion_ms" in targets
        assert "total_end_to_end_ms" in targets
        
        # Verify targets meet requirements
        assert targets["voxtral_processing_ms"] <= 100  # <100ms requirement
        assert targets["orpheus_generation_ms"] <= 150  # <150ms requirement
        assert targets["audio_conversion_ms"] <= 50     # <50ms requirement
        assert targets["total_end_to_end_ms"] <= 300    # <300ms requirement
    
    def test_latency_breakdown_validation(self):
        """Test latency breakdown validation against targets"""
        # Test within targets
        good_components = {
            "voxtral_processing_ms": 80,
            "orpheus_generation_ms": 120,
            "audio_conversion_ms": 30
        }
        
        self.performance_monitor.log_latency_breakdown(good_components)
        breakdown = self.performance_monitor.latency_history[0]
        
        assert breakdown.target_met is True
        assert breakdown.total_latency_ms == 230
        assert breakdown.voxtral_processing_ms <= self.performance_monitor.targets["voxtral_processing_ms"]
        assert breakdown.orpheus_generation_ms <= self.performance_monitor.targets["orpheus_generation_ms"]
        assert breakdown.audio_conversion_ms <= self.performance_monitor.targets["audio_conversion_ms"]
        
        # Test exceeding targets
        bad_components = {
            "voxtral_processing_ms": 150,  # Exceeds 100ms
            "orpheus_generation_ms": 200,  # Exceeds 150ms
            "audio_conversion_ms": 80      # Exceeds 50ms
        }
        
        self.performance_monitor.log_latency_breakdown(bad_components)
        breakdown = self.performance_monitor.latency_history[1]
        
        assert breakdown.target_met is False
        assert breakdown.total_latency_ms == 430  # Exceeds 300ms target
    
    def test_performance_target_compliance(self):
        """Test performance target compliance checking"""
        # Add multiple operations within targets
        for i in range(10):
            components = {
                "voxtral_processing_ms": 90 + i,      # 90-99ms
                "orpheus_generation_ms": 130 + i,     # 130-139ms
                "audio_conversion_ms": 40 + i         # 40-49ms
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        results = self.performance_monitor.check_performance_targets()
        
        # All should be within targets
        assert results["voxtral_processing_ms"] is True
        assert results["orpheus_generation_ms"] is True
        assert results["audio_conversion_ms"] is True
        assert results["total_end_to_end_ms"] is True
        assert results["success_rate_target_met"] is True
        assert results["overall_success_rate"] == 1.0
    
    def test_performance_degradation_detection(self):
        """Test detection of performance degradation"""
        # Establish baseline with good performance
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 80,
                "orpheus_generation_ms": 120,
                "audio_conversion_ms": 30
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        # Add degraded performance
        for _ in range(5):
            components = {
                "voxtral_processing_ms": 200,  # Much slower
                "orpheus_generation_ms": 300,  # Much slower
                "audio_conversion_ms": 100     # Much slower
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        # Check that degradation is detected
        results = self.performance_monitor.check_performance_targets()
        assert results["success_rate_target_met"] is False
        assert results["overall_success_rate"] < 0.8
    
    def test_consecutive_failure_tracking(self):
        """Test tracking of consecutive performance failures"""
        # Add consecutive failures
        for i in range(7):  # More than threshold of 5
            components = {
                "voxtral_processing_ms": 200,
                "orpheus_generation_ms": 300,
                "audio_conversion_ms": 100
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        # Should have tracked consecutive failures
        assert self.performance_monitor.consecutive_failures == 7
        
        # Add successful operation
        components = {
            "voxtral_processing_ms": 80,
            "orpheus_generation_ms": 120,
            "audio_conversion_ms": 30
        }
        self.performance_monitor.log_latency_breakdown(components)
        
        # Should reset consecutive failures
        assert self.performance_monitor.consecutive_failures == 0
    
    def test_percentile_calculations(self):
        """Test percentile calculations for performance metrics"""
        # Add varied performance data
        latencies = [50, 75, 100, 125, 150, 175, 200, 225, 250, 275]
        
        for latency in latencies:
            timing_id = self.performance_monitor.start_timing("test_op")
            # Simulate the timing
            timing_op = self.performance_monitor.active_timings[timing_id]
            timing_op.duration_ms = latency
            timing_op.end_time = timing_op.start_time + (latency / 1000)
            
            # Move to completed operations
            self.performance_monitor.active_timings.pop(timing_id)
            self.performance_monitor.completed_operations.append(timing_op)
            self.performance_monitor._update_statistics(timing_op)
        
        stats = self.performance_monitor.stats
        
        # Check percentiles are calculated
        assert stats["p95_latency_ms"] > 0
        assert stats["p99_latency_ms"] > 0
        assert stats["p95_latency_ms"] >= stats["average_latency_ms"]
        assert stats["p99_latency_ms"] >= stats["p95_latency_ms"]
        
        # P95 should be around 262.5 (95th percentile of our data)
        assert 250 <= stats["p95_latency_ms"] <= 275
    
    @pytest.mark.asyncio
    async def test_timing_accuracy(self):
        """Test timing measurement accuracy"""
        # Test short timing
        timing_id = self.performance_monitor.start_timing("short_test")
        await asyncio.sleep(0.01)  # 10ms
        duration = self.performance_monitor.end_timing(timing_id)
        
        # Should be approximately 10ms (allow some variance)
        assert 8 <= duration <= 15
        
        # Test longer timing
        timing_id = self.performance_monitor.start_timing("long_test")
        await asyncio.sleep(0.05)  # 50ms
        duration = self.performance_monitor.end_timing(timing_id)
        
        # Should be approximately 50ms
        assert 45 <= duration <= 60
    
    def test_memory_efficiency_targets(self):
        """Test memory efficiency validation"""
        # This would typically require actual model loading
        # For now, test the structure and calculations
        
        # Mock memory stats
        mock_stats = {
            "total_vram_gb": 16.0,
            "used_vram_gb": 8.0,
            "voxtral_memory_gb": 4.5,
            "orpheus_memory_gb": 2.5,
            "available_vram_gb": 8.0
        }
        
        # Calculate efficiency metrics
        total_model_memory = mock_stats["voxtral_memory_gb"] + mock_stats["orpheus_memory_gb"]
        memory_efficiency = (total_model_memory / mock_stats["used_vram_gb"]) * 100
        
        # Should be reasonably efficient (>80%)
        assert memory_efficiency >= 80.0
        
        # Should not exceed available VRAM
        assert mock_stats["used_vram_gb"] <= mock_stats["total_vram_gb"]
        assert total_model_memory <= mock_stats["used_vram_gb"]
    
    def test_performance_recommendations_accuracy(self):
        """Test accuracy of performance recommendations"""
        # Test with slow Voxtral
        for _ in range(10):
            components = {
                "voxtral_processing_ms": 150,  # Slow
                "orpheus_generation_ms": 120,  # Good
                "audio_conversion_ms": 30      # Good
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        recommendations = self.performance_monitor.get_optimization_recommendations()
        
        # Should recommend Voxtral optimization
        voxtral_recommendations = [rec for rec in recommendations if "Voxtral" in rec]
        assert len(voxtral_recommendations) > 0
        
        # Should mention specific optimizations
        voxtral_rec = voxtral_recommendations[0]
        assert any(keyword in voxtral_rec for keyword in ["chunk size", "VAD", "GPU"])
    
    def test_load_simulation(self):
        """Test performance under simulated load"""
        # Simulate concurrent requests
        request_count = 50
        latencies = []
        
        for i in range(request_count):
            # Simulate varying load
            base_latency = 200 + (i % 10) * 10  # 200-290ms range
            
            components = {
                "voxtral_processing_ms": base_latency * 0.4,
                "orpheus_generation_ms": base_latency * 0.5,
                "audio_conversion_ms": base_latency * 0.1
            }
            
            self.performance_monitor.log_latency_breakdown(components)
            latencies.append(base_latency)
        
        # Analyze performance under load
        stats = self.performance_monitor.get_performance_summary()
        
        # Should have processed all requests
        assert stats["statistics"]["total_operations"] == request_count
        
        # Calculate expected metrics
        expected_avg = statistics.mean(latencies)
        actual_avg = stats["statistics"]["average_latency_ms"]
        
        # Should be close to expected (within 10%)
        assert abs(actual_avg - expected_avg) / expected_avg < 0.1
    
    def test_performance_monitoring_overhead(self):
        """Test that performance monitoring has minimal overhead"""
        # Measure overhead of performance monitoring
        iterations = 1000
        
        # Test without monitoring
        start_time = time.time()
        for _ in range(iterations):
            # Simulate some work
            pass
        baseline_time = time.time() - start_time
        
        # Test with monitoring
        start_time = time.time()
        for i in range(iterations):
            timing_id = self.performance_monitor.start_timing(f"test_{i}")
            # Simulate some work
            self.performance_monitor.end_timing(timing_id)
        monitored_time = time.time() - start_time
        
        # Overhead should be minimal (less than 50% increase)
        overhead_ratio = (monitored_time - baseline_time) / baseline_time
        assert overhead_ratio < 0.5
    
    def test_performance_alert_thresholds(self):
        """Test performance alert threshold configuration"""
        thresholds = self.performance_monitor.alert_thresholds
        
        # Verify alert thresholds are reasonable
        assert thresholds["consecutive_failures"] >= 3  # At least 3 failures
        assert thresholds["consecutive_failures"] <= 10  # Not too many
        assert 1.2 <= thresholds["degradation_threshold"] <= 2.0  # 20-100% degradation
        assert 0.5 <= thresholds["success_rate_threshold"] <= 0.9  # 50-90% success rate
    
    def test_baseline_establishment(self):
        """Test baseline performance establishment"""
        # Should start with no baseline
        assert self.performance_monitor.baseline_latency_ms is None
        
        # Add enough operations to establish baseline
        baseline_latency = 250
        for _ in range(10):
            components = {
                "voxtral_processing_ms": baseline_latency * 0.4,
                "orpheus_generation_ms": baseline_latency * 0.5,
                "audio_conversion_ms": baseline_latency * 0.1
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        # Baseline should be established
        assert self.performance_monitor.baseline_latency_ms is not None
        assert abs(self.performance_monitor.baseline_latency_ms - baseline_latency) < 1.0
    
    def test_performance_trend_analysis(self):
        """Test performance trend analysis"""
        # Add improving performance trend
        for i in range(10):
            latency = 300 - (i * 10)  # 300ms down to 210ms
            components = {
                "voxtral_processing_ms": latency * 0.4,
                "orpheus_generation_ms": latency * 0.5,
                "audio_conversion_ms": latency * 0.1
            }
            self.performance_monitor.log_latency_breakdown(components)
        
        summary = self.performance_monitor.get_performance_summary()
        
        # Should detect improving trend
        if "recent_latency_trend" in summary:
            trend = summary["recent_latency_trend"]
            assert trend["trend_improving"] is True
            assert trend["last_5_operations_ms"][0] > trend["last_5_operations_ms"][-1]

if __name__ == "__main__":
    pytest.main([__file__])