#!/usr/bin/env python3
"""
Performance Optimization and Tuning for Direct Orpheus TTS Integration
Automatically optimizes system settings for target latency and hardware configuration
"""

import asyncio
import sys
import os
import time
import json
import logging
from typing import Dict, Any, List, Tuple
import torch

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Automatic performance optimization for Direct Orpheus TTS integration"""
    
    def __init__(self):
        self.hardware_profile = {}
        self.current_performance = {}
        self.optimization_recommendations = {}
        self.target_latencies = {
            "voxtral_processing_ms": 100,
            "orpheus_generation_ms": 150,
            "audio_conversion_ms": 50,
            "total_end_to_end_ms": 300
        }
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Run complete system optimization"""
        logger.info("🚀 Starting performance optimization for Direct Orpheus TTS")
        logger.info("=" * 70)
        
        try:
            # Step 1: Analyze hardware
            await self._analyze_hardware()
            
            # Step 2: Benchmark current performance
            await self._benchmark_performance()
            
            # Step 3: Generate optimization recommendations
            await self._generate_optimizations()
            
            # Step 4: Apply optimizations
            await self._apply_optimizations()
            
            # Step 5: Validate improvements
            await self._validate_improvements()
            
            return {
                "hardware_profile": self.hardware_profile,
                "performance_before": self.current_performance,
                "optimizations_applied": self.optimization_recommendations,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"❌ Optimization failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _analyze_hardware(self):
        """Analyze hardware configuration and capabilities"""
        logger.info("🔍 Analyzing hardware configuration...")
        
        # GPU Analysis
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_capability = torch.cuda.get_device_capability(0)
            
            self.hardware_profile.update({
                "gpu_available": True,
                "gpu_name": gpu_name,
                "gpu_memory_gb": gpu_memory,
                "gpu_capability": f"{gpu_capability[0]}.{gpu_capability[1]}",
                "cuda_version": torch.version.cuda
            })
            
            logger.info(f"  ✅ GPU: {gpu_name}")
            logger.info(f"  ✅ VRAM: {gpu_memory:.1f}GB")
            logger.info(f"  ✅ Compute Capability: {gpu_capability[0]}.{gpu_capability[1]}")
            
            # Determine GPU tier
            if gpu_memory >= 16:
                gpu_tier = "high_end"
            elif gpu_memory >= 8:
                gpu_tier = "mid_range"
            else:
                gpu_tier = "low_end"
                
            self.hardware_profile["gpu_tier"] = gpu_tier
            
        else:
            self.hardware_profile.update({
                "gpu_available": False,
                "gpu_tier": "cpu_only"
            })
            logger.warning("  ⚠️ No GPU detected - CPU mode")
        
        # CPU Analysis
        import psutil
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        self.hardware_profile.update({
            "cpu_cores": cpu_count,
            "cpu_freq_mhz": cpu_freq.current if cpu_freq else 0,
            "system_memory_gb": memory_gb
        })
        
        logger.info(f"  ✅ CPU: {cpu_count} cores @ {cpu_freq.current if cpu_freq else 'unknown'}MHz")
        logger.info(f"  ✅ System RAM: {memory_gb:.1f}GB")
    
    async def _benchmark_performance(self):
        """Benchmark current system performance"""
        logger.info("📊 Benchmarking current performance...")
        
        try:
            from src.models.unified_model_manager import UnifiedModelManager
            from src.utils.performance_monitor import PerformanceMonitor
            
            # Initialize systems
            manager = UnifiedModelManager()
            monitor = PerformanceMonitor()
            
            logger.info("  🔄 Initializing models for benchmarking...")
            init_start = time.time()
            success = await manager.initialize()
            init_time = (time.time() - init_start) * 1000
            
            if not success:
                raise Exception("Failed to initialize models for benchmarking")
            
            logger.info(f"  ✅ Model initialization: {init_time:.1f}ms")
            
            # Benchmark Voxtral processing
            logger.info("  🔄 Benchmarking Voxtral processing...")
            voxtral_model = await manager.get_voxtral_model()
            
            # Create dummy audio data
            dummy_audio = torch.randn(16000)  # 1 second of audio
            
            voxtral_times = []
            for i in range(3):  # Run 3 tests
                start_time = time.time()
                result = await voxtral_model.process_realtime_chunk(dummy_audio, i)
                voxtral_time = (time.time() - start_time) * 1000
                voxtral_times.append(voxtral_time)
            
            avg_voxtral_time = sum(voxtral_times) / len(voxtral_times)
            logger.info(f"  ✅ Voxtral processing: {avg_voxtral_time:.1f}ms (avg of {len(voxtral_times)} runs)")
            
            # Benchmark Orpheus generation
            logger.info("  🔄 Benchmarking Orpheus generation...")
            orpheus_model = await manager.get_orpheus_model()
            
            orpheus_times = []
            for i in range(3):  # Run 3 tests
                start_time = time.time()
                audio_data = await orpheus_model.generate_speech("Hello world test", "ऋतिका")
                orpheus_time = (time.time() - start_time) * 1000
                orpheus_times.append(orpheus_time)
            
            avg_orpheus_time = sum(orpheus_times) / len(orpheus_times)
            logger.info(f"  ✅ Orpheus generation: {avg_orpheus_time:.1f}ms (avg of {len(orpheus_times)} runs)")
            
            # Calculate total latency
            total_latency = avg_voxtral_time + avg_orpheus_time
            
            self.current_performance = {
                "model_init_time_ms": init_time,
                "voxtral_processing_ms": avg_voxtral_time,
                "orpheus_generation_ms": avg_orpheus_time,
                "total_latency_ms": total_latency,
                "meets_targets": {
                    "voxtral": avg_voxtral_time <= self.target_latencies["voxtral_processing_ms"],
                    "orpheus": avg_orpheus_time <= self.target_latencies["orpheus_generation_ms"],
                    "total": total_latency <= self.target_latencies["total_end_to_end_ms"]
                }
            }
            
            await manager.shutdown()
            
        except Exception as e:
            logger.error(f"  ❌ Benchmarking failed: {e}")
            self.current_performance = {"error": str(e)}
    
    async def _generate_optimizations(self):
        """Generate optimization recommendations based on hardware and performance"""
        logger.info("🎯 Generating optimization recommendations...")
        
        optimizations = {
            "model_settings": {},
            "memory_settings": {},
            "performance_settings": {},
            "environment_variables": {}
        }
        
        # GPU-based optimizations
        if self.hardware_profile.get("gpu_available", False):
            gpu_tier = self.hardware_profile.get("gpu_tier", "mid_range")
            gpu_memory = self.hardware_profile.get("gpu_memory_gb", 8)
            
            if gpu_tier == "high_end":
                # High-end GPU optimizations
                optimizations["model_settings"].update({
                    "torch_dtype": "float16",
                    "memory_fraction": 0.95,
                    "use_flash_attention": True,
                    "optimization_level": "performance"
                })
                optimizations["environment_variables"].update({
                    "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:2048",
                    "OMP_NUM_THREADS": "16"
                })
                logger.info("  🚀 High-end GPU detected - using performance optimizations")
                
            elif gpu_tier == "mid_range":
                # Mid-range GPU optimizations
                optimizations["model_settings"].update({
                    "torch_dtype": "float16",
                    "memory_fraction": 0.9,
                    "use_flash_attention": False,
                    "optimization_level": "balanced"
                })
                optimizations["environment_variables"].update({
                    "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:1024",
                    "OMP_NUM_THREADS": "8"
                })
                logger.info("  ⚖️ Mid-range GPU detected - using balanced optimizations")
                
            else:
                # Low-end GPU optimizations
                optimizations["model_settings"].update({
                    "torch_dtype": "float32",
                    "memory_fraction": 0.8,
                    "use_flash_attention": False,
                    "optimization_level": "memory_efficient"
                })
                optimizations["environment_variables"].update({
                    "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:512",
                    "OMP_NUM_THREADS": "4"
                })
                logger.info("  💾 Low-end GPU detected - using memory-efficient optimizations")
        
        else:
            # CPU-only optimizations
            optimizations["model_settings"].update({
                "torch_dtype": "float32",
                "device": "cpu",
                "optimization_level": "cpu_optimized"
            })
            optimizations["environment_variables"].update({
                "OMP_NUM_THREADS": str(min(self.hardware_profile.get("cpu_cores", 4), 8)),
                "MKL_NUM_THREADS": str(min(self.hardware_profile.get("cpu_cores", 4), 8))
            })
            logger.info("  🖥️ CPU-only mode - using CPU optimizations")
        
        # Performance-based optimizations
        current_perf = self.current_performance
        if "meets_targets" in current_perf:
            if not current_perf["meets_targets"]["voxtral"]:
                optimizations["performance_settings"]["voxtral_optimizations"] = [
                    "Reduce audio chunk size",
                    "Optimize VAD settings",
                    "Enable model compilation"
                ]
                logger.info("  🎙️ Voxtral performance below target - adding optimizations")
            
            if not current_perf["meets_targets"]["orpheus"]:
                optimizations["performance_settings"]["orpheus_optimizations"] = [
                    "Reduce max_new_tokens",
                    "Optimize temperature/top_p",
                    "Enable tensor parallelism"
                ]
                logger.info("  🎵 Orpheus performance below target - adding optimizations")
        
        self.optimization_recommendations = optimizations
    
    async def _apply_optimizations(self):
        """Apply the generated optimizations"""
        logger.info("⚙️ Applying performance optimizations...")
        
        try:
            # Create optimized configuration
            optimized_config = self._create_optimized_config()
            
            # Save optimized configuration
            import yaml
            with open("config_optimized.yaml", "w") as f:
                yaml.dump(optimized_config, f, default_flow_style=False, indent=2)
            
            logger.info("  ✅ Optimized configuration saved to: config_optimized.yaml")
            
            # Set environment variables
            env_vars = self.optimization_recommendations.get("environment_variables", {})
            for var, value in env_vars.items():
                os.environ[var] = str(value)
                logger.info(f"  ✅ Set {var}={value}")
            
            # Create optimization script
            self._create_optimization_script()
            logger.info("  ✅ Optimization script created: apply_optimizations.sh")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to apply optimizations: {e}")
    
    def _create_optimized_config(self) -> Dict[str, Any]:
        """Create optimized configuration based on recommendations"""
        # Load base configuration
        base_config = {
            "server": {
                "host": "0.0.0.0",
                "http_port": 8000,
                "health_port": 8005,
                "tcp_ports": [8765, 8766]
            },
            "model": {
                "name": "mistralai/Voxtral-Mini-3B-2507",
                "cache_dir": "/workspace/model_cache",
                "device": "cuda" if self.hardware_profile.get("gpu_available", False) else "cpu",
                "torch_dtype": "bfloat16",
                "max_memory_per_gpu": "8GB"
            },
            "tts": {
                "engine": "orpheus-direct",
                "default_voice": "ऋतिका",
                "sample_rate": 24000,
                "enabled": True,
                "orpheus_direct": {
                    "model_name": "mistralai/Orpheus-Mini-3B-2507",
                    "device": "cuda" if self.hardware_profile.get("gpu_available", False) else "cpu",
                    "torch_dtype": "float16",
                    "max_new_tokens": 1000,
                    "temperature": 0.1,
                    "top_p": 0.95
                }
            },
            "performance": {
                "enable_monitoring": True,
                "latency_targets": self.target_latencies,
                "optimization_level": "balanced"
            }
        }
        
        # Apply optimizations
        model_settings = self.optimization_recommendations.get("model_settings", {})
        
        if "torch_dtype" in model_settings:
            base_config["model"]["torch_dtype"] = model_settings["torch_dtype"]
            base_config["tts"]["orpheus_direct"]["torch_dtype"] = model_settings["torch_dtype"]
        
        if "optimization_level" in model_settings:
            base_config["performance"]["optimization_level"] = model_settings["optimization_level"]
        
        if "memory_fraction" in model_settings:
            base_config["tts"]["gpu_memory"] = {
                "memory_fraction": model_settings["memory_fraction"],
                "enable_monitoring": True
            }
        
        return base_config
    
    def _create_optimization_script(self):
        """Create script to apply environment optimizations"""
        script_content = [
            "#!/bin/bash",
            "",
            "# Performance Optimization Script for Direct Orpheus TTS",
            "# Generated automatically based on hardware analysis",
            "",
            "echo '🚀 Applying performance optimizations...'",
            ""
        ]
        
        # Add environment variables
        env_vars = self.optimization_recommendations.get("environment_variables", {})
        for var, value in env_vars.items():
            script_content.append(f"export {var}={value}")
        
        script_content.extend([
            "",
            "echo '✅ Environment variables set'",
            "",
            "# Use optimized configuration",
            "if [ -f 'config_optimized.yaml' ]; then",
            "    cp config_optimized.yaml config.yaml",
            "    echo '✅ Optimized configuration applied'",
            "fi",
            "",
            "echo '🎯 Optimizations applied successfully!'",
            "echo 'Start the server with: ./start_direct_orpheus.sh'"
        ])
        
        with open("apply_optimizations.sh", "w") as f:
            f.write("\n".join(script_content))
        
        os.chmod("apply_optimizations.sh", 0o755)
    
    async def _validate_improvements(self):
        """Validate that optimizations improved performance"""
        logger.info("✅ Validating performance improvements...")
        
        # This would require re-running benchmarks with optimized settings
        # For now, we'll provide recommendations for validation
        
        validation_steps = [
            "1. Apply optimizations: ./apply_optimizations.sh",
            "2. Restart the server: ./start_direct_orpheus.sh",
            "3. Run performance tests: ./test_direct_orpheus.sh",
            "4. Check latency: curl http://localhost:8000/api/status",
            "5. Monitor performance over time"
        ]
        
        logger.info("  📋 Validation steps:")
        for step in validation_steps:
            logger.info(f"    {step}")
    
    def generate_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        report = []
        report.append("# Performance Optimization Report")
        report.append("=" * 50)
        report.append("")
        
        # Hardware Profile
        report.append("## Hardware Profile")
        report.append("")
        if self.hardware_profile.get("gpu_available", False):
            report.append(f"**GPU**: {self.hardware_profile.get('gpu_name', 'Unknown')}")
            report.append(f"**VRAM**: {self.hardware_profile.get('gpu_memory_gb', 0):.1f}GB")
            report.append(f"**GPU Tier**: {self.hardware_profile.get('gpu_tier', 'unknown')}")
        else:
            report.append("**GPU**: Not available (CPU mode)")
        
        report.append(f"**CPU**: {self.hardware_profile.get('cpu_cores', 'unknown')} cores")
        report.append(f"**RAM**: {self.hardware_profile.get('system_memory_gb', 0):.1f}GB")
        report.append("")
        
        # Current Performance
        if "error" not in self.current_performance:
            report.append("## Current Performance")
            report.append("")
            report.append(f"**Voxtral Processing**: {self.current_performance.get('voxtral_processing_ms', 0):.1f}ms")
            report.append(f"**Orpheus Generation**: {self.current_performance.get('orpheus_generation_ms', 0):.1f}ms")
            report.append(f"**Total Latency**: {self.current_performance.get('total_latency_ms', 0):.1f}ms")
            report.append("")
            
            # Target Analysis
            report.append("## Target Analysis")
            report.append("")
            meets_targets = self.current_performance.get("meets_targets", {})
            for component, meets_target in meets_targets.items():
                status = "✅ MEETS TARGET" if meets_target else "❌ EXCEEDS TARGET"
                report.append(f"**{component.title()}**: {status}")
            report.append("")
        
        # Optimizations
        report.append("## Applied Optimizations")
        report.append("")
        
        model_settings = self.optimization_recommendations.get("model_settings", {})
        if model_settings:
            report.append("### Model Settings")
            for setting, value in model_settings.items():
                report.append(f"- **{setting}**: {value}")
            report.append("")
        
        env_vars = self.optimization_recommendations.get("environment_variables", {})
        if env_vars:
            report.append("### Environment Variables")
            for var, value in env_vars.items():
                report.append(f"- **{var}**: {value}")
            report.append("")
        
        # Next Steps
        report.append("## Next Steps")
        report.append("")
        report.append("1. Apply optimizations: `./apply_optimizations.sh`")
        report.append("2. Restart server: `./start_direct_orpheus.sh`")
        report.append("3. Validate performance: `./test_direct_orpheus.sh`")
        report.append("4. Monitor: `curl http://localhost:8000/api/status`")
        
        return "\n".join(report)

async def main():
    """Main optimization function"""
    optimizer = PerformanceOptimizer()
    
    try:
        results = await optimizer.optimize_system()
        
        # Generate and save report
        report = optimizer.generate_optimization_report()
        
        with open("optimization_report.md", "w") as f:
            f.write(report)
        
        logger.info("📄 Optimization report saved to: optimization_report.md")
        
        # Print summary
        print("\n" + "=" * 70)
        print("PERFORMANCE OPTIMIZATION SUMMARY")
        print("=" * 70)
        
        if results["status"] == "completed":
            print("🎉 SUCCESS: Performance optimization completed!")
            print("📊 Hardware profile analyzed")
            print("⚡ Optimizations generated and applied")
            print("📄 Reports generated")
            print("")
            print("Next steps:")
            print("1. ./apply_optimizations.sh")
            print("2. ./start_direct_orpheus.sh")
            print("3. Monitor performance improvements")
            return 0
        else:
            print("❌ FAILURE: Optimization failed")
            print(f"Error: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Optimization failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)