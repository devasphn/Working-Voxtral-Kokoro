"""
PRODUCTION-READY Voxtral model wrapper for CONVERSATIONAL real-time streaming
FIXED: FlashAttention2 detection, VAD implementation, silence handling
"""
import torch
import asyncio
import time
from typing import Optional, List, Dict, Any
# ADD these imports at the top
import gc
from contextlib import contextmanager
# Import with compatibility layer
try:
    from transformers import VoxtralForConditionalGeneration, AutoProcessor
    VOXTRAL_AVAILABLE = True
except ImportError:
    from src.utils.compatibility import FallbackVoxtralModel
    VoxtralForConditionalGeneration = FallbackVoxtralModel
    AutoProcessor = None
    VOXTRAL_AVAILABLE = False

import logging
from threading import Lock
import base64

# Import mistral_common with fallback
try:
    from mistral_common.audio import Audio
    from mistral_common.protocol.instruct.messages import AudioChunk, TextChunk, UserMessage
    MISTRAL_COMMON_AVAILABLE = True
except ImportError:
    # Fallback implementations
    Audio = None
    AudioChunk = None
    TextChunk = None
    UserMessage = None
    MISTRAL_COMMON_AVAILABLE = False
import tempfile
import soundfile as sf
import numpy as np
import os
from collections import deque
import sys

# Add current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import config with fallback
try:
    from src.utils.config import config
except ImportError:
    from src.utils.compatibility import get_config
    config = get_config()

# Enhanced logging for real-time streaming
realtime_logger = logging.getLogger("voxtral_realtime")
realtime_logger.setLevel(logging.DEBUG)

class VoxtralModel:
    """PRODUCTION-READY Voxtral model for conversational real-time streaming with VAD"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.audio_processor = None
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Real-time streaming optimization
        self.recent_chunks = deque(maxlen=5)  # Reduced for faster processing
        self.processing_history = deque(maxlen=50)  # Reduced memory usage
        
        # Performance optimization settings
        self.device = config.model.device
        self.torch_dtype = getattr(torch, config.model.torch_dtype)
        
        # ENHANCED VAD settings aligned with config.yaml
        self.silence_threshold = getattr(config.vad, 'threshold', 0.010)
        self.min_speech_duration = getattr(config.vad, 'min_voice_duration_ms', 300) / 1000  # Convert to seconds
        self.max_silence_duration = getattr(config.vad, 'min_silence_duration_ms', 800) / 1000
        self.vad_sensitivity = getattr(config.vad, 'sensitivity', 'balanced')
        
        # ADDED: Advanced VAD parameters
        self.spectral_rolloff_threshold = 0.85  # For speech quality detection
        self.zero_crossing_rate_threshold = 0.1  # For voiced/unvoiced detection
        
        # Performance optimization flags
        self.use_torch_compile = False  # Disabled by default for stability
        self.flash_attention_available = False
        
        realtime_logger.info(f"VoxtralModel initialized for {self.device} with {self.torch_dtype}")
    
    @contextmanager
    def _optimized_inference_context(self):
        """Context manager for optimized inference"""
        try:
            # Enable optimized memory usage
            torch.backends.cudnn.benchmark = True
            if hasattr(torch.backends.cudnn, 'allow_tf32'):
                torch.backends.cudnn.allow_tf32 = True
            if hasattr(torch.backends.cuda, 'matmul'):
                torch.backends.cuda.matmul.allow_tf32 = True
            yield
        finally:
            # Cleanup after inference
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
    def get_audio_processor(self):
        """Lazy initialization of Audio processor"""
        if self.audio_processor is None:
            from src.models.audio_processor_realtime import AudioProcessor
            self.audio_processor = AudioProcessor()
            realtime_logger.info("Audio processor lazy-loaded into Voxtral model")
        return self.audio_processor
    
    def _check_flash_attention_availability(self):
        """ENHANCED: Detect and optimize FlashAttention2"""
        try:
            import flash_attn
            from flash_attn import flash_attn_func
            if self.device == "cuda" and torch.cuda.is_available():
                # Get GPU info
                gpu_capability = torch.cuda.get_device_capability()
                major, minor = gpu_capability
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                
                # Enhanced FlashAttention support detection
                if major >= 8:  # Ampere and newer
                    self.flash_attention_available = True
                    realtime_logger.info(f"✅ FlashAttention2 OPTIMIZED - GPU: {major}.{minor}, Memory: {gpu_memory:.1f}GB")
                    # Enable additional optimizations for FlashAttention2
                    os.environ['FLASH_ATTENTION_SKIP_CUDA_CHECK'] = '1'
                    return "flash_attention_2"
                elif major >= 7:  # Turing
                    realtime_logger.info(f"💡 FlashAttention2 available but not optimal for SM{major}.{minor}")
                    return "flash_attention_2"  # Still use it
                else:
                    realtime_logger.info(f"⚠️ GPU compute capability {major}.{minor} < 7.0, using eager attention")
                    return "eager"
            else:
                realtime_logger.info("💡 CUDA not available, using eager attention")
                return "eager"
        except ImportError:
            realtime_logger.warning("⚠️ FlashAttention2 not installed!")
            realtime_logger.info("🚀 INSTALL: pip install flash-attn --no-build-isolation")
            return "eager"
        except Exception as e:
            realtime_logger.error(f"❌ FlashAttention2 check failed: {e}")
            return "eager"
    
    def _calculate_audio_energy(self, audio_data: np.ndarray) -> float:
        """
        Calculate RMS energy of audio signal for VAD
        """
        try:
            # Calculate RMS (Root Mean Square) energy
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            return float(rms_energy)
        except Exception as e:
            realtime_logger.warning(f"Error calculating audio energy: {e}")
            return 0.0
    
    def _is_speech_detected(self, audio_data: np.ndarray, duration_s: float) -> bool:
        """ENHANCED VAD: Multi-parameter speech detection"""
        try:
            # Basic energy check
            energy = self._calculate_audio_energy(audio_data)
            if energy < self.silence_threshold:
                realtime_logger.debug(f"🔇 Low energy ({energy:.6f}) - likely silence")
                return False
            
            # Duration check
            if duration_s < self.min_speech_duration:
                realtime_logger.debug(f"⏱️ Too short ({duration_s:.2f}s) - likely noise")
                return False
            
            # ENHANCED: Spectral characteristics for better accuracy
            try:
                # Calculate spectral features using librosa
                import librosa
                
                # Spectral rolloff (frequency distribution)
                rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=config.audio.sample_rate)[0]
                avg_rolloff = np.mean(rolloff) / (config.audio.sample_rate / 2)  # Normalize
                
                # Zero crossing rate (speech vs noise)
                zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
                avg_zcr = np.mean(zcr)
                
                # Speech characteristics check
                if avg_rolloff > self.spectral_rolloff_threshold:
                    realtime_logger.debug(f"📊 High spectral rolloff ({avg_rolloff:.3f}) - likely not speech")
                    return False
                
                if avg_zcr > self.zero_crossing_rate_threshold:
                    realtime_logger.debug(f"📈 High ZCR ({avg_zcr:.3f}) - likely noise")
                    return False
                
                realtime_logger.debug(f"🎙️ SPEECH DETECTED - Energy: {energy:.6f}, Rolloff: {avg_rolloff:.3f}, ZCR: {avg_zcr:.3f}")
                return True
                
            except ImportError:
                # Fallback to basic detection if librosa features not available
                spectral_variation = np.std(audio_data)
                if spectral_variation < self.silence_threshold * 0.3:
                    realtime_logger.debug(f"📊 Low variation ({spectral_variation:.6f}) - likely silence")
                    return False
                
                realtime_logger.debug(f"🎙️ Speech detected - Energy: {energy:.6f}, Variation: {spectral_variation:.6f}")
                return True
                
        except Exception as e:
            realtime_logger.error(f"❌ VAD error: {e}")
            return False  # Conservative: reject on error
    
    async def initialize(self):
        """Initialize the Voxtral model with FIXED attention implementation handling"""
        try:
            realtime_logger.info("🚀 Starting Voxtral model initialization for conversational streaming...")
            start_time = time.time()
            
            # Load processor
            realtime_logger.info(f"📥 Loading AutoProcessor from {config.model.name}")
            self.processor = AutoProcessor.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir
            )
            realtime_logger.info("✅ AutoProcessor loaded successfully")
            
            # FIXED: Determine attention implementation with proper detection
            attn_implementation = self._check_flash_attention_availability()
            realtime_logger.info(f"🔧 Using attention implementation: {attn_implementation}")
            
            # Load model with FIXED attention settings
            realtime_logger.info(f"📥 Loading Voxtral model from {config.model.name}")
            
            model_kwargs = {
                "cache_dir": config.model.cache_dir,
                "torch_dtype": self.torch_dtype,
                "device_map": "auto",
                "low_cpu_mem_usage": True,
                "trust_remote_code": True,
                "attn_implementation": attn_implementation
            }
            
            try:
                self.model = VoxtralForConditionalGeneration.from_pretrained(
                    config.model.name,
                    **model_kwargs
                )
                realtime_logger.info(f"✅ Voxtral model loaded successfully with {attn_implementation} attention")
                
            except Exception as model_load_error:
                # Fallback to eager attention
                if attn_implementation != "eager":
                    realtime_logger.warning(f"⚠️ Model loading with {attn_implementation} failed: {model_load_error}")
                    realtime_logger.info("🔄 Retrying with eager attention as fallback...")
                    
                    model_kwargs["attn_implementation"] = "eager"
                    self.model = VoxtralForConditionalGeneration.from_pretrained(
                        config.model.name,
                        **model_kwargs
                    )
                    realtime_logger.info("✅ Voxtral model loaded successfully with eager attention fallback")
                else:
                    raise model_load_error
            
            # Set model to evaluation mode
            self.model.eval()
            realtime_logger.info("🔧 Model set to evaluation mode")
            
            # FIXED: Conditional torch.compile with safety checks
            if self.use_torch_compile and hasattr(torch, 'compile') and self.device == "cuda" and not self.flash_attention_available:
                try:
                    realtime_logger.info("⚡ Attempting to compile model with torch.compile()...")
                    self.model = torch.compile(self.model, mode="default")  # Use default mode for stability
                    realtime_logger.info("✅ Model compiled successfully for faster inference")
                except Exception as e:
                    realtime_logger.warning(f"⚠️ Could not compile model: {e}")
                    realtime_logger.info("💡 Continuing without torch.compile...")
            else:
                if self.flash_attention_available:
                    realtime_logger.info("💡 Skipping torch.compile (using FlashAttention2)")
                else:
                    realtime_logger.info("💡 Skipping torch.compile (disabled for stability)")
            
            self.is_initialized = True
            init_time = time.time() - start_time
            realtime_logger.info(f"🎉 Voxtral model fully initialized in {init_time:.2f}s and ready for conversation!")
            
        except Exception as e:
            realtime_logger.error(f"❌ Failed to initialize Voxtral model: {e}")
            import traceback
            realtime_logger.error(f"❌ Full error traceback: {traceback.format_exc()}")
            raise
    
    async def process_realtime_chunk(self, audio_data: torch.Tensor, chunk_id: int, mode: str = "conversation", prompt: str = "") -> Dict[str, Any]:
        """
        PRODUCTION-READY processing for conversational real-time audio chunks with VAD
        """
        if not self.is_initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        try:
            chunk_start_time = time.time()
            realtime_logger.debug(f"🎵 Processing conversational chunk {chunk_id} with {len(audio_data)} samples")
            
            # Convert tensor to numpy for VAD analysis
            audio_np = audio_data.detach().cpu().numpy().copy()
            sample_rate = config.audio.sample_rate
            duration_s = len(audio_np) / sample_rate
            
            # CRITICAL: Apply VAD before processing
            if not self._is_speech_detected(audio_np, duration_s):
                realtime_logger.debug(f"🔇 Chunk {chunk_id} contains no speech - skipping processing")
                return {
                    'response': '',  # Empty response for silence
                    'processing_time_ms': (time.time() - chunk_start_time) * 1000,
                    'chunk_id': chunk_id,
                    'audio_duration_s': duration_s,
                    'success': True,
                    'is_silence': True
                }
            
            with self.model_lock:
                # Store chunk in recent history
                self.recent_chunks.append({
                    'chunk_id': chunk_id,
                    'timestamp': chunk_start_time,
                    'has_speech': True
                })
                
                # Ensure audio_data is properly formatted
                if not audio_data.data.is_contiguous():
                    audio_data = audio_data.contiguous()
                
                realtime_logger.debug(f"🔊 Audio stats for chunk {chunk_id}: length={len(audio_np)}, max_val={np.max(np.abs(audio_np)):.4f}")
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    try:
                        # Write audio to temporary file
                        sf.write(tmp_file.name, audio_np, sample_rate)
                        realtime_logger.debug(f"💾 Written chunk {chunk_id} to temporary file: {tmp_file.name}")
                        
                        # Load using mistral_common Audio with updated API
                        audio = Audio.from_file(tmp_file.name)
                        audio_chunk = AudioChunk.from_audio(audio)
                        
                        # OPTIMIZED: Single unified conversational prompt for Smart Conversation Mode
                        conversation_prompt = "You are a helpful AI assistant in a natural voice conversation. Listen carefully to what the person is saying and respond naturally, as if you're having a friendly chat. Keep your responses conversational, concise (1-2 sentences), and engaging. Respond directly to what they said without repeating their words back to them."
                        
                        # Create message format using updated API
                        text_chunk = TextChunk(text=conversation_prompt)
                        user_message = UserMessage(content=[audio_chunk, text_chunk])
                        
                        # Convert to chat format for processor
                        messages = [user_message.model_dump()]
                        
                        # Process inputs with updated API
                        inputs = self.processor.apply_chat_template(messages, return_tensors="pt")
                        
                        # Move to device
                        if hasattr(inputs, 'to'):
                            inputs = inputs.to(self.device)
                        elif isinstance(inputs, dict):
                            inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                                    for k, v in inputs.items()}
                        
                        realtime_logger.debug(f"🚀 Starting inference for chunk {chunk_id}")
                        inference_start = time.time()
                        
                        # ENHANCED: Generate response with optimized inference context
                        with self._optimized_inference_context():
                            with torch.no_grad():
                                # ENHANCED: Use mixed precision with optimizations
                                with torch.autocast(device_type="cuda" if "cuda" in self.device else "cpu", dtype=self.torch_dtype,
                                                  enabled=True):  # Always enable for performance
                                    outputs = self.model.generate(
                                        **inputs,
                                        max_new_tokens=128,     # OPTIMIZED: Balanced length (was 200)
                                        min_new_tokens=3,       # OPTIMIZED: Faster start (was 5)
                                        do_sample=True,         
                                        num_beams=1,           
                                        temperature=0.15,       # OPTIMIZED: Slightly more focused (was 0.2)
                                        top_p=0.9,             # OPTIMIZED: Slightly more focused (was 0.95)
                                        repetition_penalty=1.05, # OPTIMIZED: Lighter penalty (was 1.1)
                                        pad_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None,
                                        use_cache=True,         # ADDED: Performance optimization
                                        early_stopping=False,   # Let model decide naturally
                                        length_penalty=0.95,    # Slight preference for shorter responses
                                        no_repeat_ngram_size=3, # Prevent 3-gram repetition
                                    )
                        
                        inference_time = (time.time() - inference_start) * 1000
                        realtime_logger.debug(f"⚡ Inference completed for chunk {chunk_id} in {inference_time:.1f}ms")
                        
                        # Decode response
                        if hasattr(inputs, 'input_ids'):
                            input_length = inputs.input_ids.shape[1]
                        elif 'input_ids' in inputs:
                            input_length = inputs['input_ids'].shape[1]
                        else:
                            input_length = 0
                            
                        response = self.processor.batch_decode(
                            outputs[:, input_length:], 
                            skip_special_tokens=True
                        )[0]
                        
                        total_processing_time = (time.time() - chunk_start_time) * 1000
                        
                        # Store performance metrics
                        performance_data = {
                            'chunk_id': chunk_id,
                            'total_time_ms': total_processing_time,
                            'inference_time_ms': inference_time,
                            'audio_length_s': len(audio_np) / sample_rate,
                            'response_length': len(response),
                            'timestamp': chunk_start_time,
                            'has_speech': True
                        }
                        self.processing_history.append(performance_data)
                        
                        # Clean and optimize response
                        cleaned_response = response.strip()
                        
                        # Filter out common noise responses
                        noise_responses = [
                            "I'm not sure what you're asking",
                            "I can't understand",
                            "Could you repeat that",
                            "I didn't catch that",
                            "Yeah, I think it's a good idea"  # This seems to be a common noise response
                        ]
                        
                        # If response is too short or matches noise patterns, treat as silence
                        if len(cleaned_response) < 3 or any(noise in cleaned_response for noise in noise_responses):
                            realtime_logger.debug(f"🔇 Filtering out noise response: '{cleaned_response}'")
                            return {
                                'response': '',
                                'processing_time_ms': total_processing_time,
                                'chunk_id': chunk_id,
                                'audio_duration_s': duration_s,
                                'success': True,
                                'is_silence': True,
                                'filtered_response': cleaned_response
                            }
                        
                        if not cleaned_response:
                            cleaned_response = "[Audio processed]"
                        
                        realtime_logger.info(f"✅ Chunk {chunk_id} processed in {total_processing_time:.1f}ms: '{cleaned_response[:50]}{'...' if len(cleaned_response) > 50 else ''}'")
                        
                        return {
                            'response': cleaned_response,
                            'processing_time_ms': total_processing_time,
                            'inference_time_ms': inference_time,
                            'chunk_id': chunk_id,
                            'audio_duration_s': len(audio_np) / sample_rate,
                            'success': True,
                            'is_silence': False
                        }
                        
                    finally:
                        # Cleanup temporary file
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
                
        except Exception as e:
            processing_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.error(f"❌ Error processing chunk {chunk_id}: {e}")
            
            # Return error response with timing info
            error_msg = "Could not process audio"
            if "CUDA out of memory" in str(e):
                error_msg = "GPU memory error"
            elif "timeout" in str(e).lower():
                error_msg = "Processing timeout"
            
            return {
                'response': error_msg,
                'processing_time_ms': processing_time,
                'chunk_id': chunk_id,
                'success': False,
                'error': str(e),
                'is_silence': False
            }

    async def transcribe_audio(self, audio_data: torch.Tensor) -> str:
        """Unified conversational processing (legacy method)"""
        result = await self.process_realtime_chunk(
            audio_data,
            chunk_id=int(time.time() * 1000),
            mode="conversation"
        )
        return result['response']

    async def understand_audio(self, audio_data: torch.Tensor, question: str = "") -> str:
        """Unified conversational processing (legacy method)"""
        result = await self.process_realtime_chunk(
            audio_data,
            chunk_id=int(time.time() * 1000),
            mode="conversation"
        )
        return result['response']

    async def process_audio_stream(self, audio_data: torch.Tensor, prompt: str = "") -> str:
        """Unified conversational processing (legacy method)"""
        result = await self.process_realtime_chunk(
            audio_data,
            chunk_id=int(time.time() * 1000),
            mode="conversation"
        )
        return result['response']
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get enhanced model information with real-time stats"""
        base_info = {
            "status": "initialized" if self.is_initialized else "not_initialized",
            "model_name": config.model.name,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "mode": "conversational_optimized",
            "flash_attention_available": self.flash_attention_available,
            "torch_compile_enabled": self.use_torch_compile,
            "vad_settings": {
                "silence_threshold": self.silence_threshold,
                "min_speech_duration": self.min_speech_duration,
                "max_silence_duration": self.max_silence_duration
            }
        }
        
        if self.is_initialized and self.processing_history:
            # Calculate real-time performance stats
            recent_history = list(self.processing_history)[-10:]  # Last 10 chunks
            if recent_history:
                avg_processing_time = np.mean([h['total_time_ms'] for h in recent_history])
                avg_inference_time = np.mean([h['inference_time_ms'] for h in recent_history])
                total_chunks = len(self.processing_history)
                speech_chunks = len([h for h in recent_history if h.get('has_speech', False)])
                
                base_info.update({
                    "realtime_stats": {
                        "total_chunks_processed": total_chunks,
                        "speech_chunks_in_recent_10": speech_chunks,
                        "avg_processing_time_ms": round(avg_processing_time, 1),
                        "avg_inference_time_ms": round(avg_inference_time, 1),
                        "recent_chunks_in_memory": len(self.recent_chunks),
                        "performance_history_size": len(self.processing_history)
                    }
                })
        
        return base_info

# Global model instance for real-time streaming
voxtral_model = VoxtralModel()

# FIXED: Add proper main execution block for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_model():
        """Test model initialization and basic functionality"""
        print("🧪 Testing Voxtral Conversational Model with VAD...")
        
        try:
            # Initialize model
            await voxtral_model.initialize()
            
            # Test with dummy audio (silence)
            silent_audio = torch.zeros(16000) + 0.001  # Very quiet audio
            result = await voxtral_model.process_realtime_chunk(silent_audio, 1)
            print(f"Silent audio result: {result}")
            
            # Test with dummy audio (louder)
            loud_audio = torch.randn(16000) * 0.1  # Louder audio
            result = await voxtral_model.process_realtime_chunk(loud_audio, 2)
            print(f"Loud audio result: {result}")
            
            print(f"✅ Test completed successfully")
            print(f"📊 Model info: {voxtral_model.get_model_info()}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(test_model())
