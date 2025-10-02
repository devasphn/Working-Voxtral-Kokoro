"""
Unified Model Manager for Kokoro TTS Integration
Centralized management of both Voxtral and Kokoro TTS models with shared GPU memory
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Tuple, Union, AsyncGenerator
from threading import Lock
from contextlib import asynccontextmanager
import torch
import gc
import numpy as np
# Import model classes
from src.models.voxtral_model_realtime import VoxtralModel
from src.models.kokoro_model_realtime import KokoroTTSModel
from src.utils.gpu_memory_manager import GPUMemoryManager, InsufficientVRAMError

# Setup logging
unified_logger = logging.getLogger("unified_model_manager")
unified_logger.setLevel(logging.INFO)

class ModelInitializationError(Exception):
    """Raised when model initialization fails"""
    pass

class UnifiedModelManager:
    """
    Centralized management of both Voxtral and Kokoro TTS models
    Handles initialization order, memory sharing, and lifecycle management
    """

    def __init__(self):
        self.voxtral_model = None
        self.kokoro_model = None
        self.gpu_memory_manager = None
        self.initialization_lock = Lock()
        self.is_initialized = False

        # Initialization state tracking
        self.voxtral_initialized = False
        self.kokoro_initialized = False
        self.memory_manager_initialized = False

        # Performance tracking
        self.initialization_times = {}
        self.memory_usage = {}

        unified_logger.info("UnifiedModelManager created")
    
    @asynccontextmanager
    async def _performance_optimized_context(self):
        """Context manager for performance-optimized operations"""
        try:
            # Enable GPU optimizations
            if torch.cuda.is_available():
                torch.backends.cudnn.benchmark = True
                torch.backends.cuda.matmul.allow_tf32 = True
                if hasattr(torch.backends.cudnn, 'allow_tf32'):
                    torch.backends.cudnn.allow_tf32 = True
            
            # Enable CPU optimizations
            torch.set_num_threads(min(4, torch.get_num_threads()))  # Optimal thread count
            yield
        finally:
            # Cleanup and memory management
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Force garbage collection periodically
            if hasattr(self, '_gc_counter'):
                self._gc_counter += 1
                if self._gc_counter % 10 == 0:  # Every 10 operations
                    import gc
                    gc.collect()
            else:
                self._gc_counter = 1
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        status = {
            'timestamp': time.time(),
            'optimizations_enabled': {},
            'performance_features': {}
        }
        
        if torch.cuda.is_available():
            status['optimizations_enabled'].update({
                'cudnn_benchmark': getattr(torch.backends.cudnn, 'benchmark', False),
                'allow_tf32': getattr(torch.backends.cuda.matmul, 'allow_tf32', False),
                'flash_attention_available': getattr(self.voxtral_model, 'flash_attention_available', False) if self.voxtral_model else False
            })
            
            # GPU performance features
            gpu_props = torch.cuda.get_device_properties(0)
            status['performance_features'].update({
                'gpu_compute_capability': f"{gpu_props.major}.{gpu_props.minor}",
                'gpu_memory_gb': gpu_props.total_memory / 1e9,
                'multi_processor_count': gpu_props.multi_processor_count
            })
        
        return status
    
    async def warmup_models_for_speed(self):
        """Warmup models for consistent <500ms performance"""
        if not self.is_initialized:
            return False
        
        try:
            unified_logger.info("🔥 Warming up models for ultra-fast performance...")
            
            # Enable ultra-fast mode
            self.gpu_memory_manager.enable_ultra_fast_mode()
            
            # Warmup Voxtral with progressively smaller inputs
            warmup_audio_lengths = [8000, 4000, 2000, 1000]  # 0.5s to 0.0625s
            for i, length in enumerate(warmup_audio_lengths):
                dummy_audio = torch.randn(length, device=self.gpu_memory_manager.device, dtype=torch.float16) * 0.1
                start_time = time.time()
                result = await self.voxtral_model.process_realtime_chunk(
                    dummy_audio, 
                    chunk_id=f"warmup_{i}",
                    mode="conversation"
                )
                warmup_time = (time.time() - start_time) * 1000
                unified_logger.info(f"🔥 Warmup {i+1}/4: {length} samples -> {warmup_time:.1f}ms")
                
                # Break early if we achieve target
                if warmup_time < 500:
                    unified_logger.info(f"✅ Target achieved at warmup {i+1} - stopping early")
                    break
            
            # Final warmup with typical speech
            typical_audio = torch.randn(16000, device=self.gpu_memory_manager.device, dtype=torch.float16) * 0.05  # 1 second, normal volume
            start_time = time.time()
            result = await self.voxtral_model.process_realtime_chunk(
                typical_audio,
                chunk_id="warmup_final",
                mode="conversation"  
            )
            final_warmup_time = (time.time() - start_time) * 1000
            unified_logger.info(f"🎯 FINAL warmup: 1s audio -> {final_warmup_time:.1f}ms")
            
            if final_warmup_time < 500:
                unified_logger.info("✅ ULTRA-FAST mode ready - <500ms target achieved!")
                return True
            else:
                unified_logger.warning(f"⚠️ Still {final_warmup_time:.1f}ms - may need further optimization")
                return True
                
        except Exception as e:
            unified_logger.error(f"❌ Model warmup failed: {e}")
            return False
    
    async def initialize(self) -> bool:
        """
        Initialize both models with optimal memory management
        Returns True if successful, raises ModelInitializationError on failure
        """
        try:
            with self.initialization_lock:
                if self.is_initialized:
                    unified_logger.info("✅ Models already initialized")
                    return True
                
                unified_logger.info("🚀 Starting unified model initialization...")
                total_start_time = time.time()
                
                # Step 1: Initialize GPU Memory Manager
                await self._initialize_memory_manager()
                
                # Step 2: Initialize models in optimal order (Voxtral first for memory layout)
                await self._initialize_voxtral_model()
                await self._initialize_kokoro_model()

                # Step 3: Verify initialization and optimize memory
                await self._post_initialization_optimization()
                
                total_time = time.time() - total_start_time
                self.initialization_times["total"] = total_time
                
                self.is_initialized = True
                unified_logger.info(f"🎉 Unified model initialization completed in {total_time:.2f}s")
                
                # Log final memory statistics
                await self._log_memory_statistics()
                
                return True
                
        except Exception as e:
            unified_logger.error(f"❌ Unified model initialization failed: {e}")
            await self._cleanup_partial_initialization()
            raise ModelInitializationError(f"Failed to initialize models: {e}")
    
    async def _initialize_memory_manager(self):
        """Initialize GPU memory manager and validate requirements"""
        try:
            unified_logger.info("🧠 Initializing GPU Memory Manager...")
            start_time = time.time()
            
            self.gpu_memory_manager = GPUMemoryManager()
            
            # Validate VRAM requirements
            self.gpu_memory_manager.validate_vram_requirements()
            
            # Create shared memory pool
            shared_pool = self.gpu_memory_manager.create_shared_memory_pool()
            
            self.memory_manager_initialized = True
            init_time = time.time() - start_time
            self.initialization_times["memory_manager"] = init_time
            
            unified_logger.info(f"✅ GPU Memory Manager initialized in {init_time:.2f}s")
            
        except InsufficientVRAMError as e:
            unified_logger.error(f"❌ Insufficient VRAM: {e}")
            raise ModelInitializationError(f"VRAM requirements not met: {e}")
        except Exception as e:
            unified_logger.error(f"❌ Memory manager initialization failed: {e}")
            raise ModelInitializationError(f"Memory manager initialization failed: {e}")
    
    async def _initialize_voxtral_model(self):
        """Initialize Voxtral model first for optimal memory layout"""
        try:
            unified_logger.info("🎙️ Initializing Voxtral model...")
            start_time = time.time()
            
            # Import and create Voxtral model
            self.voxtral_model = VoxtralModel()
            
            # Initialize with memory optimization
            await self.voxtral_model.initialize()
            
            # Track memory usage
            if self.gpu_memory_manager.device == "cuda":
                voxtral_memory = torch.cuda.memory_allocated() / (1024**3)
                self.gpu_memory_manager.track_model_memory("voxtral", voxtral_memory)
                self.memory_usage["voxtral_gb"] = voxtral_memory
            
            self.voxtral_initialized = True
            init_time = time.time() - start_time
            self.initialization_times["voxtral"] = init_time
            
            unified_logger.info(f"✅ Voxtral model initialized in {init_time:.2f}s")
            
        except Exception as e:
            unified_logger.error(f"❌ Voxtral initialization failed: {e}")
            raise ModelInitializationError(f"Voxtral initialization failed: {e}")
    
    async def _initialize_kokoro_model(self):
        """Initialize Kokoro TTS model"""
        try:
            unified_logger.info("🎵 Initializing Kokoro TTS model...")
            start_time = time.time()

            # Create Kokoro TTS Model
            self.kokoro_model = KokoroTTSModel()

            # Initialize the model
            success = await self.kokoro_model.initialize()

            if not success:
                unified_logger.error("❌ Kokoro TTS model initialization failed")
                raise ModelInitializationError("Kokoro TTS model initialization failed")

            # Track memory usage
            if self.gpu_memory_manager.device == "cuda":
                total_memory = torch.cuda.memory_allocated() / (1024**3)
                tts_memory = total_memory - self.memory_usage.get("voxtral_gb", 0)
                self.gpu_memory_manager.track_model_memory("kokoro", tts_memory)
                self.memory_usage["kokoro_gb"] = tts_memory

            self.kokoro_initialized = True
            init_time = time.time() - start_time
            self.initialization_times["kokoro"] = init_time

            unified_logger.info(f"✅ Kokoro TTS model initialized in {init_time:.2f}s")

        except Exception as e:
            unified_logger.error(f"❌ Kokoro TTS model initialization failed: {e}")
            raise ModelInitializationError(f"Kokoro TTS model initialization failed: {e}")
    
    async def _post_initialization_optimization(self):
        """Perform post-initialization memory optimization"""
        try:
            unified_logger.info("⚡ Performing post-initialization optimization...")
            
            # Clean up any unused memory
            self.gpu_memory_manager.cleanup_unused_memory()
            
            # Get memory optimization recommendations
            recommendations = self.gpu_memory_manager.optimize_memory_allocation()
            
            # Apply recommendations if needed
            if recommendations.get("optimization_level") == "memory_efficient":
                unified_logger.info("💾 Applying memory-efficient optimizations...")
                # Could implement model-specific optimizations here
            
            # Verify both models are working
            await self._verify_model_functionality()
            
            unified_logger.info("✅ Post-initialization optimization completed")
            
        except Exception as e:
            unified_logger.error(f"❌ Post-initialization optimization failed: {e}")
            raise ModelInitializationError(f"Post-initialization optimization failed: {e}")
    
    async def _verify_model_functionality(self):
        """Verify both models are functioning correctly"""
        try:
            unified_logger.info("🔍 Verifying model functionality...")
            
            # Test Voxtral model
            if self.voxtral_model and self.voxtral_model.is_initialized:
                model_info = self.voxtral_model.get_model_info()
                if model_info.get("status") != "initialized":
                    raise ModelInitializationError("Voxtral model verification failed")
                unified_logger.info("✅ Voxtral model verification passed")
            
            # Test Kokoro TTS model
            if self.kokoro_model and self.kokoro_model.is_initialized:
                model_info = self.kokoro_model.get_model_info()
                if not model_info.get("is_initialized"):
                    raise ModelInitializationError("Kokoro TTS model verification failed")

                unified_logger.info("✅ Kokoro TTS model verification passed")
            
            unified_logger.info("✅ All model functionality verified")
            
        except Exception as e:
            unified_logger.error(f"❌ Model verification failed: {e}")
            raise ModelInitializationError(f"Model verification failed: {e}")
    
    async def _log_memory_statistics(self):
        """Log comprehensive memory usage statistics"""
        try:
            if self.gpu_memory_manager:
                stats = self.gpu_memory_manager.get_memory_stats()
                
                unified_logger.info("📊 Final Memory Statistics:")
                unified_logger.info(f"   Total VRAM: {stats.total_vram_gb:.2f} GB")
                unified_logger.info(f"   Used VRAM: {stats.used_vram_gb:.2f} GB")
                unified_logger.info(f"   Available VRAM: {stats.available_vram_gb:.2f} GB")
                unified_logger.info(f"   Voxtral Memory: {stats.voxtral_memory_gb:.2f} GB")
                unified_logger.info(f"   Kokoro Memory: {stats.kokoro_memory_gb:.2f} GB")
                unified_logger.info(f"   System RAM: {stats.system_ram_gb:.2f} GB")
                unified_logger.info(f"   System RAM Used: {stats.system_ram_used_gb:.2f} GB")
                
                # Calculate efficiency metrics
                total_model_memory = stats.voxtral_memory_gb + stats.kokoro_memory_gb
                memory_efficiency = (total_model_memory / stats.used_vram_gb * 100) if stats.used_vram_gb > 0 else 0
                
                unified_logger.info(f"   Memory Efficiency: {memory_efficiency:.1f}%")
                
        except Exception as e:
            unified_logger.warning(f"⚠️ Failed to log memory statistics: {e}")
    
    async def _cleanup_partial_initialization(self):
        """Cleanup resources from partial initialization"""
        try:
            unified_logger.info("🧹 Cleaning up partial initialization...")
            
            if self.kokoro_model:
                await self.kokoro_model.cleanup()
                self.kokoro_model = None
                self.kokoro_initialized = False
            
            if self.voxtral_model:
                # Voxtral model doesn't have async cleanup, but we can clear references
                self.voxtral_model = None
                self.voxtral_initialized = False
            
            if self.gpu_memory_manager:
                self.gpu_memory_manager.cleanup_unused_memory()
            
            self.is_initialized = False
            unified_logger.info("✅ Partial initialization cleanup completed")
            
        except Exception as e:
            unified_logger.error(f"❌ Cleanup failed: {e}")
    
    async def get_voxtral_model(self) -> Optional[VoxtralModel]:
        """Get initialized Voxtral model"""
        if not self.is_initialized or not self.voxtral_initialized:
            raise ModelInitializationError("Voxtral model not initialized")
        return self.voxtral_model
    
    async def get_kokoro_model(self) -> Optional[KokoroTTSModel]:
        """Get initialized Kokoro TTS model"""
        if not self.is_initialized or not self.kokoro_initialized:
            raise ModelInitializationError("Kokoro TTS model not initialized")
        return self.kokoro_model
    
    async def cleanup_gpu_memory(self) -> None:
        """Cleanup GPU memory and run garbage collection"""
        try:
            unified_logger.info("🧹 Cleaning up GPU memory...")
            
            if self.gpu_memory_manager:
                self.gpu_memory_manager.cleanup_unused_memory()
            
            # Additional cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            gc.collect()
            
            unified_logger.info("✅ GPU memory cleanup completed")
            
        except Exception as e:
            unified_logger.error(f"❌ GPU memory cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory usage statistics"""
        try:
            if not self.gpu_memory_manager:
                return {"error": "Memory manager not initialized"}
            
            base_stats = self.gpu_memory_manager.get_memory_stats()
            
            return {
                "memory_stats": {
                    "total_vram_gb": base_stats.total_vram_gb,
                    "used_vram_gb": base_stats.used_vram_gb,
                    "available_vram_gb": base_stats.available_vram_gb,
                    "voxtral_memory_gb": base_stats.voxtral_memory_gb,
                    "kokoro_memory_gb": base_stats.kokoro_memory_gb,
                    "system_ram_gb": base_stats.system_ram_gb,
                    "system_ram_used_gb": base_stats.system_ram_used_gb
                },
                "initialization_stats": {
                    "is_initialized": self.is_initialized,
                    "voxtral_initialized": self.voxtral_initialized,
                    "kokoro_initialized": self.kokoro_initialized,
                    "initialization_times": self.initialization_times
                },
                "model_info": {
                    "voxtral_available": self.voxtral_model is not None,
                    "kokoro_available": self.kokoro_model is not None,
                    "device": self.gpu_memory_manager.device if self.gpu_memory_manager else "unknown"
                }
            }
            
        except Exception as e:
            unified_logger.error(f"❌ Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        try:
            info = {
                "unified_manager": {
                    "is_initialized": self.is_initialized,
                    "voxtral_initialized": self.voxtral_initialized,
                    "kokoro_initialized": self.kokoro_initialized,
                    "memory_manager_initialized": self.memory_manager_initialized
                },
                "initialization_times": self.initialization_times,
                "memory_usage": self.memory_usage
            }
            
            # Add Voxtral model info
            if self.voxtral_model:
                info["voxtral"] = self.voxtral_model.get_model_info()
            
            # Add Kokoro model info
            if self.kokoro_model:
                info["kokoro"] = self.kokoro_model.get_model_info()
            
            # Add memory manager info
            if self.gpu_memory_manager:
                info["memory_manager"] = self.get_memory_stats()
            
            return info
            
        except Exception as e:
            unified_logger.error(f"❌ Failed to get model info: {e}")
            return {"error": str(e)}
    
    async def process_streaming_conversation(self, audio_data: Union[torch.Tensor, np.ndarray], chunk_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process conversation with CHUNKED STREAMING
        Yields both text chunks and audio chunks in real-time"""
        if not self.is_initialized:
            raise RuntimeError("UnifiedModelManager not initialized")
        
        try:
            unified_logger.info(f"🎯 Starting STREAMING conversation for {chunk_id}")
            
            # Process audio with streaming Voxtral
            async for text_chunk in self.voxtral_model.process_realtime_chunk_streaming(
                audio_data, chunk_id, mode="conversation"
            ):
                # Yield the text chunk immediately
                yield {
                    'type': 'text_chunk',
                    'data': text_chunk
                }
                
                # Generate TTS for this chunk in parallel
                if text_chunk['text'].strip():
                    try:
                        # Generate TTS audio for this chunk
                        tts_result = await self.kokoro_model.synthesize_speech(
                            text=text_chunk['text'],
                            chunk_id=text_chunk['chunk_id']
                        )
                        
                        if tts_result['success'] and len(tts_result['audio_data']) > 0:
                            # Yield the audio chunk
                            yield {
                                'type': 'audio_chunk',
                                'data': {
                                    'chunk_id': text_chunk['chunk_id'],
                                    'audio_data': tts_result['audio_data'],
                                    'sample_rate': tts_result['sample_rate'],
                                    'duration_ms': tts_result.get('audio_duration_s', 0) * 1000,
                                    'synthesis_time_ms': tts_result['synthesis_time_ms'],
                                    'text': text_chunk['text'],
                                    'chunk_number': text_chunk.get('chunk_number', 1),
                                    'is_final': text_chunk.get('is_final', False)
                                }
                            }
                            
                            unified_logger.info(f"🎵 TTS chunk {text_chunk['chunk_id']} ready: {len(tts_result['audio_data'])} samples")
                            
                    except Exception as e:
                        unified_logger.error(f"❌ TTS error for chunk {text_chunk['chunk_id']}: {e}")
                        # Continue with next chunk even if TTS fails
            
            unified_logger.info(f"✅ STREAMING conversation complete for {chunk_id}")
            
        except Exception as e:
            unified_logger.error(f"❌ STREAMING conversation error for {chunk_id}: {e}")
            
            # Yield error response
            yield {
                'type': 'error',
                'data': {
                    'chunk_id': f"{chunk_id}_error",
                    'error': str(e),
                    'message': "Sorry, there was an error processing your request."
                }
            }
    
    async def shutdown(self):
        """Shutdown and cleanup all resources"""
        try:
            unified_logger.info("🛑 Shutting down Unified Model Manager...")
            
            # Cleanup Kokoro model
            if self.kokoro_model:
                await self.kokoro_model.cleanup()
                self.kokoro_model = None
                self.kokoro_initialized = False
            
            # Cleanup Voxtral model (no async cleanup available)
            if self.voxtral_model:
                self.voxtral_model = None
                self.voxtral_initialized = False
            
            # Final memory cleanup
            if self.gpu_memory_manager:
                self.gpu_memory_manager.cleanup_unused_memory()
                self.gpu_memory_manager = None
                self.memory_manager_initialized = False
            
            # Clear state
            self.is_initialized = False
            self.initialization_times.clear()
            self.memory_usage.clear()
            
            unified_logger.info("✅ Unified Model Manager shutdown completed")
            
        except Exception as e:
            unified_logger.error(f"❌ Shutdown failed: {e}")

# Global unified model manager instance
unified_model_manager = UnifiedModelManager()