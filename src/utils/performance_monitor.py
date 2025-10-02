"""
Enhanced Performance Monitor for Voxtral Real-time Streaming
Tracks latency, memory usage, and system performance
"""
import time
import threading
import logging
from collections import deque, defaultdict
from typing import Dict, Any, Optional
import psutil
import torch

class PerformanceMonitor:
    """Enhanced performance monitoring for real-time streaming"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance_monitor")
        self.lock = threading.Lock()
        
        # Performance targets (from config)
        self.targets = {
            'voxtral_processing_ms': 100,
            'kokoro_generation_ms': 150,
            'audio_conversion_ms': 50,
            'total_end_to_end_ms': 300
        }
        
        # Timing storage
        self.active_timings = {}  # timing_id -> start_info
        self.completed_operations = deque(maxlen=1000)  # Recent operations
        self.operation_stats = defaultdict(list)  # operation_type -> [times]
        
        # System metrics
        self.system_metrics = deque(maxlen=100)
        self.start_monitoring()
        
        self.logger.info("PerformanceMonitor initialized")
        self.logger.info(f"🎯 Performance targets: {self.targets}")
    
    def start_timing(self, operation_type: str, metadata: Optional[Dict] = None) -> str:
        """Start timing an operation"""
        timing_id = f"{operation_type}_{int(time.time() * 1000000)}"
        
        with self.lock:
            self.active_timings[timing_id] = {
                'operation_type': operation_type,
                'start_time': time.time(),
                'metadata': metadata or {}
            }
        
        return timing_id
    
    def end_timing(self, timing_id: str) -> float:
        """End timing and record result"""
        end_time = time.time()
        
        with self.lock:
            if timing_id not in self.active_timings:
                self.logger.warning(f"Unknown timing ID: {timing_id}")
                return 0.0
            
            timing_info = self.active_timings.pop(timing_id)
            duration_ms = (end_time - timing_info['start_time']) * 1000
            
            # Record operation
            operation = {
                'type': timing_info['operation_type'],
                'duration_ms': duration_ms,
                'timestamp': end_time,
                'metadata': timing_info['metadata']
            }
            
            self.completed_operations.append(operation)
            self.operation_stats[timing_info['operation_type']].append(duration_ms)
            
            # Keep only recent stats per operation
            if len(self.operation_stats[timing_info['operation_type']]) > 100:
                self.operation_stats[timing_info['operation_type']] = \
                    self.operation_stats[timing_info['operation_type']][-50:]
            
            return duration_ms
    
    def log_latency_breakdown(self, breakdown: Dict[str, float]):
        """Log detailed latency breakdown"""
        total_time = breakdown.get('total_end_to_end_ms', 0)
        self.logger.info(f"📊 Latency breakdown (Total: {total_time:.1f}ms):")
        
        for component, duration in breakdown.items():
            if component in self.targets:
                target = self.targets[component]
                status = "✅" if duration <= target else "⚠️"
                self.logger.info(f"   {status} {component}: {duration:.1f}ms (target: {target}ms)")
            else:
                self.logger.info(f"   📊 {component}: {duration:.1f}ms")
        
        # Warning for exceeded targets
        for component, duration in breakdown.items():
            if component in self.targets and duration > self.targets[component]:
                target = self.targets[component]
                self.logger.warning(f"⚠️ {component} exceeded target: {duration:.1f}ms (target: {target}ms)")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.lock:
            summary = {
                'timestamp': time.time(),
                'active_operations': len(self.active_timings),
                'total_completed': len(self.completed_operations),
                'targets': self.targets.copy(),
                'statistics': {},
                'system_metrics': {}
            }
            
            # Calculate statistics for each operation type
            for op_type, durations in self.operation_stats.items():
                if durations:
                    summary['statistics'][op_type] = {
                        'count': len(durations),
                        'avg_ms': sum(durations) / len(durations),
                        'min_ms': min(durations),
                        'max_ms': max(durations),
                        'target_ms': self.targets.get(op_type, 'N/A'),
                        'within_target': sum(1 for d in durations if d <= self.targets.get(op_type, float('inf')))
                    }
            
            # Overall statistics
            if self.completed_operations:
                total_ops = len(self.completed_operations)
                avg_latency = sum(op['duration_ms'] for op in self.completed_operations) / total_ops
                within_target = sum(1 for op in self.completed_operations 
                                  if op['duration_ms'] <= self.targets.get(op['type'], float('inf')))
                
                summary['statistics'] = {
                    'total_operations': total_ops,
                    'average_latency_ms': round(avg_latency, 1),
                    'operations_within_target': within_target,
                    'success_rate_percent': round((within_target / total_ops) * 100, 1)
                }
            
            # Recent system metrics
            if self.system_metrics:
                latest_metrics = self.system_metrics[-1]
                summary['system_metrics'] = latest_metrics
            
            return summary
    
    def start_monitoring(self):
        """Start background system monitoring"""
        def monitor_system():
            while True:
                try:
                    # CPU and Memory
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    # GPU metrics if available
                    gpu_metrics = {}
                    if torch.cuda.is_available():
                        gpu_metrics = {
                            'gpu_memory_used_gb': torch.cuda.memory_allocated() / 1e9,
                            'gpu_memory_cached_gb': torch.cuda.memory_reserved() / 1e9,
                            'gpu_memory_total_gb': torch.cuda.get_device_properties(0).total_memory / 1e9,
                            'gpu_utilization_percent': 'N/A'  # Requires nvidia-ml-py
                        }
                    
                    metrics = {
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_used_gb': memory.used / 1e9,
                        'memory_available_gb': memory.available / 1e9,
                        'memory_percent': memory.percent,
                        **gpu_metrics
                    }
                    
                    with self.lock:
                        self.system_metrics.append(metrics)
                        
                except Exception as e:
                    self.logger.error(f"System monitoring error: {e}")
                
                time.sleep(30)  # Update every 30 seconds
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        self.logger.info("Background system monitoring started")

# Global instance
performance_monitor = PerformanceMonitor()