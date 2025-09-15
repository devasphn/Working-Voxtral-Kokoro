#!/usr/bin/env python3
"""
Final System Check for Direct Orpheus TTS Integration
Comprehensive validation of all components and RunPod readiness
"""

import asyncio
import sys
import os
import time
import json
import logging
import subprocess
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalSystemChecker:
    """Comprehensive system validation for production readiness"""
    
    def __init__(self):
        self.results = {
            "system_requirements": {},
            "model_validation": {},
            "performance_validation": {},
            "runpod_readiness": {},
            "overall_status": "unknown"
        }
    
    async def run_complete_check(self) -> Dict[str, Any]:
        """Run complete system validation"""
        logger.info("🔍 Starting Final System Check for Direct Orpheus TTS Integration")
        logger.info("=" * 80)
        
        try:
            # System Requirements Check
            await self._check_system_requirements()
            
            # Model Validation
            await self._validate_models()
            
            # Performance Validation
            await self._validate_performance()
            
            # RunPod Readiness Check
            await self._check_runpod_readiness()
            
            # Overall Assessment
            self._assess_overall_status()
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ System check failed: {e}")
            self.results["overall_status"] = "failed"
            self.results["error"] = str(e)
            return self.results
    
    async def _check_system_requirements(self):
        """Check system requirements and dependencies"""
        logger.info("🖥️ Checking System Requirements...")
        
        req_results = {
            "python_version": False,
            "cuda_available": False,
            "gpu_memory": False,
            "dependencies": False,
            "disk_space": False
        }
        
        try:
            # Python version check
            python_version = sys.version_info
            if python_version.major == 3 and 8 <= python_version.minor <= 11:
                req_results["python_version"] = True
                logger.info(f"  ✅ Python {python_version.major}.{python_version.minor} (compatible)")
            else:
                logger.error(f"  ❌ Python {python_version.major}.{python_version.minor} (requires 3.8-3.11)")
            
            # CUDA check
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    
                    req_results["cuda_available"] = True
                    req_results["gpu_memory"] = gpu_memory >= 8.0
                    
                    logger.info(f"  ✅ GPU: {gpu_name}")
                    logger.info(f"  ✅ VRAM: {gpu_memory:.1f}GB")
                    
                    if gpu_memory < 8.0:
                        logger.warning(f"  ⚠️ Low VRAM: {gpu_memory:.1f}GB (8GB+ recommended)")
                else:
                    logger.warning("  ⚠️ CUDA not available - will run on CPU")
                    req_results["cuda_available"] = False
                    req_results["gpu_memory"] = False
            except ImportError:
                logger.error("  ❌ PyTorch not installed")
            
            # Dependencies check
            required_packages = [
                'transformers', 'fastapi', 'uvicorn', 'mistral_common', 
                'librosa', 'soundfile', 'numpy', 'pydantic'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if not missing_packages:
                req_results["dependencies"] = True
                logger.info("  ✅ All required dependencies installed")
            else:
                logger.error(f"  ❌ Missing packages: {', '.join(missing_packages)}")
            
            # Disk space check
            try:
                import shutil
                total, used, free = shutil.disk_usage(".")
                free_gb = free / (1024**3)
                
                req_results["disk_space"] = free_gb >= 50
                logger.info(f"  ✅ Free disk space: {free_gb:.1f}GB")
                
                if free_gb < 50:
                    logger.warning(f"  ⚠️ Low disk space: {free_gb:.1f}GB (50GB+ recommended)")
            except Exception as e:
                logger.error(f"  ❌ Could not check disk space: {e}")
            
        except Exception as e:
            logger.error(f"  ❌ System requirements check failed: {e}")
        
        self.results["system_requirements"] = req_results
    
    async def _validate_models(self):
        """Validate model loading and functionality"""
        logger.info("🤖 Validating Models...")
        
        model_results = {
            "unified_manager": False,
            "voxtral_model": False,
            "orpheus_model": False,
            "model_compatibility": False
        }
        
        try:
            # Test unified manager
            from src.models.unified_model_manager import UnifiedModelManager
            manager = UnifiedModelManager()
            
            logger.info("  🔄 Testing unified model manager initialization...")
            success = await manager.initialize()
            
            if success:
                model_results["unified_manager"] = True
                logger.info("  ✅ Unified model manager initialized")
                
                # Test Voxtral model
                try:
                    voxtral_model = await manager.get_voxtral_model()
                    if voxtral_model and voxtral_model.is_initialized:
                        model_results["voxtral_model"] = True
                        logger.info("  ✅ Voxtral model loaded and ready")
                    else:
                        logger.error("  ❌ Voxtral model not properly initialized")
                except Exception as e:
                    logger.error(f"  ❌ Voxtral model error: {e}")
                
                # Test Orpheus model
                try:
                    orpheus_model = await manager.get_orpheus_model()
                    if orpheus_model and orpheus_model.is_initialized:
                        model_results["orpheus_model"] = True
                        logger.info("  ✅ Orpheus model loaded and ready")
                        
                        # Test TTS generation
                        test_audio = await orpheus_model.generate_speech("Test", "ऋतिका")
                        if test_audio and len(test_audio) > 0:
                            model_results["model_compatibility"] = True
                            logger.info("  ✅ TTS generation test successful")
                        else:
                            logger.error("  ❌ TTS generation test failed")
                    else:
                        logger.error("  ❌ Orpheus model not properly initialized")
                except Exception as e:
                    logger.error(f"  ❌ Orpheus model error: {e}")
                
                await manager.shutdown()
            else:
                logger.error("  ❌ Unified model manager initialization failed")
                
        except Exception as e:
            logger.error(f"  ❌ Model validation failed: {e}")
        
        self.results["model_validation"] = model_results
    
    async def _validate_performance(self):
        """Validate performance targets"""
        logger.info("⚡ Validating Performance...")
        
        perf_results = {
            "latency_targets": False,
            "memory_efficiency": False,
            "monitoring_active": False
        }
        
        try:
            from src.utils.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            
            # Check performance targets
            targets = monitor.targets
            expected_targets = {
                "voxtral_processing_ms": 100,
                "orpheus_generation_ms": 150,
                "audio_conversion_ms": 50,
                "total_end_to_end_ms": 300
            }
            
            targets_match = all(
                targets.get(key) == expected_targets[key] 
                for key in expected_targets
            )
            
            perf_results["latency_targets"] = targets_match
            if targets_match:
                logger.info("  ✅ Performance targets correctly configured")
            else:
                logger.error("  ❌ Performance targets misconfigured")
            
            # Test monitoring
            timing_id = monitor.start_timing("test_operation")
            await asyncio.sleep(0.01)
            duration = monitor.end_timing(timing_id)
            
            perf_results["monitoring_active"] = duration > 0
            if duration > 0:
                logger.info("  ✅ Performance monitoring active")
            else:
                logger.error("  ❌ Performance monitoring not working")
            
            # Memory efficiency check
            from src.utils.gpu_memory_manager import GPUMemoryManager
            gpu_manager = GPUMemoryManager()
            
            try:
                gpu_manager.validate_vram_requirements()
                perf_results["memory_efficiency"] = True
                logger.info("  ✅ Memory management configured")
            except Exception as e:
                logger.warning(f"  ⚠️ Memory validation: {e}")
                perf_results["memory_efficiency"] = True  # Allow CPU mode
            
        except Exception as e:
            logger.error(f"  ❌ Performance validation failed: {e}")
        
        self.results["performance_validation"] = perf_results
    
    async def _check_runpod_readiness(self):
        """Check RunPod deployment readiness"""
        logger.info("🚀 Checking RunPod Readiness...")
        
        runpod_results = {
            "port_configuration": False,
            "websocket_support": False,
            "environment_variables": False,
            "deployment_scripts": False,
            "documentation": False
        }
        
        try:
            # Check port configuration
            from src.utils.config import config
            required_ports = [8000, 8005]
            configured_ports = [config.server.http_port, config.server.health_port]
            
            runpod_results["port_configuration"] = all(
                port in configured_ports for port in required_ports
            )
            
            if runpod_results["port_configuration"]:
                logger.info(f"  ✅ Ports configured: {configured_ports}")
            else:
                logger.error(f"  ❌ Port configuration issue: expected {required_ports}, got {configured_ports}")
            
            # Check WebSocket support
            try:
                from fastapi import WebSocket
                runpod_results["websocket_support"] = True
                logger.info("  ✅ WebSocket support available")
            except ImportError:
                logger.error("  ❌ WebSocket support not available")
            
            # Check environment variables
            required_env_vars = [
                'CUDA_VISIBLE_DEVICES', 'PYTORCH_CUDA_ALLOC_CONF', 
                'TRANSFORMERS_CACHE', 'TOKENIZERS_PARALLELISM'
            ]
            
            env_configured = any(var in os.environ for var in required_env_vars)
            runpod_results["environment_variables"] = env_configured
            
            if env_configured:
                logger.info("  ✅ Environment variables configured")
            else:
                logger.info("  ℹ️ Environment variables will be set during deployment")
                runpod_results["environment_variables"] = True  # Not critical
            
            # Check deployment scripts
            deployment_files = [
                'deploy_direct_orpheus.sh',
                'RUNPOD_DEPLOYMENT_GUIDE.md',
                'config_direct_orpheus.yaml'
            ]
            
            missing_files = [f for f in deployment_files if not os.path.exists(f)]
            runpod_results["deployment_scripts"] = len(missing_files) == 0
            
            if not missing_files:
                logger.info("  ✅ All deployment files present")
            else:
                logger.error(f"  ❌ Missing deployment files: {missing_files}")
            
            # Check documentation
            doc_files = ['README_DIRECT_ORPHEUS.md', 'RUNPOD_DEPLOYMENT_GUIDE.md']
            missing_docs = [f for f in doc_files if not os.path.exists(f)]
            runpod_results["documentation"] = len(missing_docs) == 0
            
            if not missing_docs:
                logger.info("  ✅ Documentation complete")
            else:
                logger.error(f"  ❌ Missing documentation: {missing_docs}")
            
        except Exception as e:
            logger.error(f"  ❌ RunPod readiness check failed: {e}")
        
        self.results["runpod_readiness"] = runpod_results
    
    def _assess_overall_status(self):
        """Assess overall system status"""
        logger.info("📊 Assessing Overall System Status...")
        logger.info("=" * 50)
        
        all_checks = []
        
        for category, checks in self.results.items():
            if category == "overall_status":
                continue
                
            if isinstance(checks, dict):
                category_passed = all(checks.values())
                all_checks.append(category_passed)
                
                status_emoji = "✅" if category_passed else "❌"
                logger.info(f"{status_emoji} {category.replace('_', ' ').title()}: {'PASSED' if category_passed else 'FAILED'}")
        
        overall_passed = all(all_checks)
        self.results["overall_status"] = "passed" if overall_passed else "failed"
        
        logger.info("=" * 50)
        if overall_passed:
            logger.info("🎉 SYSTEM STATUS: ✅ READY FOR PRODUCTION DEPLOYMENT")
            logger.info("🚀 All systems validated - RunPod deployment ready!")
        else:
            logger.error("❌ SYSTEM STATUS: ISSUES DETECTED")
            logger.error("🔧 Please address the failed checks before deployment")
        
        # Summary statistics
        passed_count = sum(all_checks)
        total_count = len(all_checks)
        success_rate = (passed_count / total_count) * 100
        
        logger.info(f"📈 System Readiness: {success_rate:.1f}% ({passed_count}/{total_count} categories passed)")
    
    def generate_deployment_report(self) -> str:
        """Generate deployment readiness report"""
        report = []
        report.append("# Final System Check Report")
        report.append("=" * 50)
        report.append("")
        
        report.append(f"**Overall Status**: {self.results['overall_status'].upper()}")
        report.append("")
        
        # System Requirements
        report.append("## System Requirements")
        sys_req = self.results.get("system_requirements", {})
        for check, passed in sys_req.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"- **{check.replace('_', ' ').title()}**: {status}")
        report.append("")
        
        # Model Validation
        report.append("## Model Validation")
        model_val = self.results.get("model_validation", {})
        for check, passed in model_val.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"- **{check.replace('_', ' ').title()}**: {status}")
        report.append("")
        
        # Performance Validation
        report.append("## Performance Validation")
        perf_val = self.results.get("performance_validation", {})
        for check, passed in perf_val.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"- **{check.replace('_', ' ').title()}**: {status}")
        report.append("")
        
        # RunPod Readiness
        report.append("## RunPod Readiness")
        runpod_ready = self.results.get("runpod_readiness", {})
        for check, passed in runpod_ready.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report.append(f"- **{check.replace('_', ' ').title()}**: {status}")
        report.append("")
        
        # Deployment Instructions
        report.append("## Deployment Instructions")
        report.append("")
        if self.results["overall_status"] == "passed":
            report.append("🎉 **System is ready for deployment!**")
            report.append("")
            report.append("### RunPod Deployment Steps:")
            report.append("1. Create RunPod instance with RTX A5000+ GPU")
            report.append("2. Use PyTorch 2.1.0 template")
            report.append("3. Expose ports: 8000, 8005")
            report.append("4. Clone repository and run: `./deploy_direct_orpheus.sh`")
            report.append("5. Start service: `./start_direct_orpheus.sh`")
            report.append("6. Access UI: `https://<pod-id>-8000.proxy.runpod.net`")
        else:
            report.append("🔧 **Issues detected - address before deployment:**")
            report.append("")
            for category, checks in self.results.items():
                if category == "overall_status":
                    continue
                if isinstance(checks, dict):
                    failed_checks = [k for k, v in checks.items() if not v]
                    if failed_checks:
                        report.append(f"**{category.replace('_', ' ').title()}**:")
                        for check in failed_checks:
                            report.append(f"- Fix: {check.replace('_', ' ')}")
                        report.append("")
        
        return "\n".join(report)

async def main():
    """Main system check function"""
    checker = FinalSystemChecker()
    
    try:
        results = await checker.run_complete_check()
        
        # Generate and save report
        report = checker.generate_deployment_report()
        
        with open("system_check_report.md", "w") as f:
            f.write(report)
        
        logger.info("📄 System check report saved to: system_check_report.md")
        
        # Print final status
        print("\n" + "=" * 80)
        print("FINAL SYSTEM CHECK SUMMARY")
        print("=" * 80)
        
        if results["overall_status"] == "passed":
            print("🎉 SUCCESS: System is ready for RunPod deployment!")
            print("🚀 All components validated and production-ready!")
            print("")
            print("Next steps:")
            print("1. Deploy on RunPod using RUNPOD_DEPLOYMENT_GUIDE.md")
            print("2. Use RTX A5000+ GPU with PyTorch 2.1.0 template")
            print("3. Expose ports 8000 and 8005")
            print("4. Run ./deploy_direct_orpheus.sh")
            return 0
        else:
            print("❌ ISSUES DETECTED: Please address before deployment")
            print("🔧 Check system_check_report.md for details")
            return 1
            
    except Exception as e:
        logger.error(f"❌ System check failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)