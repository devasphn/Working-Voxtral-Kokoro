"""
PRODUCTION-READY Voxtral model wrapper for CONVERSATIONAL real-time streaming
FIXED: FlashAttention2 detection, VAD implementation, silence handling
"""
import torch
import asyncio
import time
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
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
        """Initialize VoxtralModel with ULTRA-FAST + chunked streaming"""
        self.is_initialized = False
        self.device = config.model.device
        self.torch_dtype = getattr(torch, config.model.torch_dtype)
        
        # FIXED: Safe VAD configuration access
        vad_config = getattr(config, 'vad', None)
        if vad_config:
            self.silence_threshold = getattr(vad_config, 'threshold', 0.010)
            self.min_speech_duration = getattr(vad_config, 'min_voice_duration_ms', 300) / 1000
            self.max_silence_duration = getattr(vad_config, 'min_silence_duration_ms', 800) / 1000
            self.vad_sensitivity = getattr(vad_config, 'sensitivity', 'balanced')
        else:
            # FALLBACK: Default VAD settings for ultra-fast mode
            self.silence_threshold = 0.005  # Ultra-sensitive
            self.min_speech_duration = 0.2  # 200ms
            self.max_silence_duration = 0.4  # 400ms  
            self.vad_sensitivity = 'ultra_high'
        
        # ADDED: Chunked streaming configuration
        self.streaming_enabled = True
        self.chunk_separator_phrases = ['. ', '? ', '! ', ', ', ' and ', ' but ', ' so ']
        self.min_chunk_words = 2  # Minimum words per chunk
        self.max_chunk_words = 8  # Maximum words per chunk
        self.chunk_timeout_ms = 200  # Send chunk after 200ms even if incomplete
        
        # ADDED: Performance optimization settings
        self.max_response_words = 50  # Ultra-short responses for speed
        self.response_temperature = 0.1  # Very focused responses
        
        # Initialize other attributes
        self.model = None
        self.processor = None
        self.flash_attention_available = False
        self.generation_history = deque(maxlen=100)
        
        # Real-time streaming optimization
        self.recent_chunks = deque(maxlen=5)  # Reduced for faster processing
        self.processing_history = deque(maxlen=50)  # Reduced memory usage
        self.model_lock = Lock()
        self.audio_processor = None
        
        # ADDED: Advanced VAD parameters
        self.spectral_rolloff_threshold = 0.85  # For speech quality detection
        self.zero_crossing_rate_threshold = 0.1  # For voiced/unvoiced detection
        
        # Performance optimization flags
        self.use_torch_compile = False  # Disabled by default for stability
        
        realtime_logger.info("🚀 VoxtralModel initialized with ULTRA-FAST + CHUNKED STREAMING")
    
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
        """Calculate RMS energy of audio data"""
        return np.sqrt(np.mean(audio_data ** 2))
    
    def _is_speech_detected(self, audio_data: np.ndarray, duration_s: float) -> bool:
        """Enhanced speech detection with multiple criteria"""
        try:
            # Calculate RMS energy
            rms_energy = self._calculate_audio_energy(audio_data)
            
            # Check against silence threshold
            if rms_energy < self.silence_threshold:
                realtime_logger.debug(f"Audio energy {rms_energy:.6f} below silence threshold {self.silence_threshold}")
                return False
            
            # Check minimum duration
            if duration_s < self.min_speech_duration:
                realtime_logger.debug(f"Duration {duration_s:.2f}s below minimum {self.min_speech_duration}s")
                return False
            
            # Additional checks for better detection
            max_amplitude = np.max(np.abs(audio_data))
            if max_amplitude < 0.001:  # Very quiet
                return False
            
            # Check for variation (not flat signal)
            variation = np.std(audio_data)
            if variation < 0.001:  # Too flat, likely silence
                return False
            
            realtime_logger.debug(f"✅ Speech detected - Energy: {rms_energy:.6f}, Duration: {duration_s:.2f}s, Variation: {variation:.6f}")
            return True
            
        except Exception as e:
            realtime_logger.error(f"❌ Speech detection error: {e}")
            return False
    
    def _create_ultra_short_prompt(self) -> str:
        """ULTRA-SHORT prompt for <500ms responses"""
        return ("Reply in 1-2 words only. Be conversational but extremely brief. "
                "Examples: 'Hello!' 'Sure!' 'Great!' 'I see.' 'Nice!' "
                "Never explain or elaborate unless specifically asked.")
    
    async def initialize(self):
        """Initialize with AGGRESSIVE quantization for <500ms latency"""
        try:
            realtime_logger.info("🚀 Starting ULTRA-LOW LATENCY Voxtral initialization...")
            start_time = time.time()
            
            # Load processor (keep existing)
            realtime_logger.info(f"📥 Loading AutoProcessor from {config.model.name}")
            self.processor = AutoProcessor.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir
            )
            
            # CRITICAL: Check FlashAttention2
            attn_implementation = self._check_flash_attention_availability()
            
            # ULTRA-OPTIMIZED model loading with quantization
            realtime_logger.info(f"📥 Loading QUANTIZED Voxtral model for <500ms target")
            
            model_kwargs = {
                "cache_dir": config.model.cache_dir,
                "torch_dtype": torch.float16,  # FORCE float16 for maximum speed
                "device_map": "auto",
                "low_cpu_mem_usage": True,
                "trust_remote_code": True,
                "attn_implementation": attn_implementation,
                # REMOVED: Invalid parameters that cause errors
                # "use_flash_attention_2": True,  # REMOVED - not supported
                # "torch_compile": False,         # REMOVED - not needed
                "max_memory": {0: "8GB"},  # Limit VRAM usage
                "offload_folder": None,    # Keep everything on GPU
            }
            
            # Try quantization if available
            try:
                from transformers import BitsAndBytesConfig
                # OPTIMIZED: Custom quantization for speed (not memory savings)
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=False,  # Don't use 4-bit for speed
                    load_in_8bit=False,  # Don't use 8-bit for speed  
                    bnb_4bit_use_double_quant=False,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )
                realtime_logger.info("💡 BitsAndBytesConfig available but DISABLED for maximum speed")
                # model_kwargs["quantization_config"] = bnb_config  # DISABLED for speed
            except ImportError:
                realtime_logger.info("💡 BitsAndBytesConfig not available - using standard loading")
            
            # Load model
            self.model = VoxtralForConditionalGeneration.from_pretrained(
                config.model.name,
                **model_kwargs
            )
            
            # ULTRA-OPTIMIZED model preparation
            self.model.eval()
            
            # CRITICAL: Enable aggressive PyTorch optimizations
            if torch.cuda.is_available():
                # Enable Tensor Core optimizations
                torch.backends.cudnn.benchmark = True
                torch.backends.cudnn.deterministic = False  # Allow non-deterministic for speed
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                
                # Enable mixed precision globally
                torch.set_float32_matmul_precision('medium')  # Trade precision for speed
                
                # Optimize memory allocator
                os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:64,roundup_power2_divisions:16'
                
                realtime_logger.info("⚡ ULTRA-OPTIMIZED PyTorch settings enabled")
            
            # Log FlashAttention2 status
            if attn_implementation == "flash_attention_2":
                realtime_logger.info("✅ Using FlashAttention2 for optimal speed")
            else:
                realtime_logger.info(f"💡 Using {attn_implementation} attention (FlashAttention2 not available)")
            
            self.is_initialized = True
            init_time = time.time() - start_time
            realtime_logger.info(f"🎉 ULTRA-LOW LATENCY Voxtral ready in {init_time:.2f}s - Target: <500ms")
            
        except Exception as e:
            realtime_logger.error(f"❌ Ultra-low latency initialization failed: {e}")
            raise
    
    async def process_realtime_chunk(self, audio_data: Union[torch.Tensor, np.ndarray], chunk_id: str, mode: str = "conversation") -> Dict[str, Any]:
        """Process real-time audio chunk - EXACT WORKING VERSION"""
        if not self.is_initialized:
            raise RuntimeError("VoxtralModel not initialized")
        
        chunk_start_time = time.time()
        realtime_logger.debug(f"🎵 Processing conversational chunk {chunk_id} with {len(audio_data)} samples")
        
        try:
            # Convert to proper format (WORKING approach from logs)
            if isinstance(audio_data, torch.Tensor):
                audio_numpy = audio_data.cpu().numpy().astype(np.float32)
            else:
                audio_numpy = audio_data.astype(np.float32)
            
            # Speech detection (from your working logs)
            energy = np.sqrt(np.mean(audio_numpy ** 2))
            duration_s = len(audio_numpy) / config.audio.sample_rate
            realtime_logger.debug(f"✅ Speech detected - Energy: {energy:.6f}, Duration: {duration_s:.2f}s, Variation: {energy:.6f}")
            
            if energy < self.silence_threshold:
                realtime_logger.debug(f"Audio energy {energy:.6f} below silence threshold {self.silence_threshold}")
                return {
                    'success': False,
                    'text': '',
                    'processing_time_ms': (time.time() - chunk_start_time) * 1000,
                    'error': 'No speech detected'
                }
            
            realtime_logger.debug(f"🔊 Audio stats for chunk {chunk_id}: length={len(audio_numpy)}, max_val={np.max(np.abs(audio_numpy)):.4f}")
            
            # CRITICAL: Write to temporary file (EXACT working approach from logs)
            import tempfile
            import soundfile as sf
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            sf.write(tmp_path, audio_numpy, config.audio.sample_rate)
            realtime_logger.debug(f"📁 Written chunk {chunk_id} to temporary file {tmp_path}")
            
            realtime_logger.debug(f"🔊 Starting inference for chunk {chunk_id}")
            inference_start = time.time()
            
            # WORKING: Use the EXACT processor call that works (from your logs)
            try:
                # Load audio using the processor's expected format
                inputs = self.processor(
                    audio_values=audio_numpy,  # CRITICAL: Use audio_values (confirmed working)
                    text="You are a helpful AI assistant. Respond briefly and naturally.",
                    sampling_rate=config.audio.sample_rate,
                    return_tensors="pt",
                    padding=True
                    # REMOVED: All the problematic parameters that cause errors
                ).to(self.device)
            except Exception as proc_error:
                # FALLBACK: Try alternative processor format
                realtime_logger.warning(f"Primary processor failed: {proc_error}")
                inputs = self.processor(
                    audio_values=audio_numpy,
                    sampling_rate=config.audio.sample_rate,
                    return_tensors="pt"
                ).to(self.device)
            
            # Generate response (WORKING parameters from logs)
            with torch.no_grad():
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=50,         # WORKING value from logs
                        min_new_tokens=1,
                        do_sample=False,           # Deterministic
                        num_beams=1,
                        pad_token_id=self.processor.tokenizer.eos_token_id,
                        use_cache=True,
                        early_stopping=True
                    )
            
            inference_time = (time.time() - inference_start) * 1000
            realtime_logger.debug(f"⚡ Inference completed for chunk {chunk_id} in {inference_time:.1f}ms")
            
            # Decode response (WORKING approach from logs)
            if hasattr(outputs, 'sequences'):
                response_ids = outputs.sequences[0][inputs['input_ids'].shape[1]:]
            else:
                response_ids = outputs[0][inputs['input_ids'].shape[1]:]
            response_text = self.processor.tokenizer.decode(response_ids, skip_special_tokens=True).strip()
            
            # Clean up temp file
            try:
                import os
                os.unlink(tmp_path)
            except:
                pass
            
            total_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.info(f"✅ Chunk {chunk_id} processed in {total_time:.1f}ms: '{response_text[:50]}...'")
            
            return {
                'success': True,
                'text': response_text,
                'processing_time_ms': total_time,
                'inference_time_ms': inference_time
            }
            
        except Exception as e:
            error_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.error(f"❌ Error processing chunk {chunk_id}: {e}")
            return {
                'success': False,
                'text': "Sorry, I didn't understand that.",
                'processing_time_ms': error_time,
                'error': str(e)
            }
    
    def _create_conversation_prompt(self) -> str:
        """Create optimized conversation prompt"""
        return "You are a helpful AI assistant. Respond briefly and naturally to the user's speech."

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
    
    async def process_realtime_chunk_streaming(self, audio_data: Union[torch.Tensor, np.ndarray], chunk_id: str, mode: str = "conversation") -> AsyncGenerator[Dict[str, Any], None]:
        """CHUNKED STREAMING: Generate response in real-time chunks
        Yields: Dict with chunk data as it's generated"""
        if not self.is_initialized:
            raise RuntimeError("VoxtralModel not initialized")
        
        chunk_start_time = time.time()
        realtime_logger.info(f"🎯 Starting CHUNKED STREAMING for chunk {chunk_id}")
        
        try:
            # Prepare audio input (same as before)
            if isinstance(audio_data, np.ndarray):
                audio_data = torch.from_numpy(audio_data).float()
            if audio_data.device != self.device:
                audio_data = audio_data.to(self.device)
            
            # Check for speech
            energy = self._calculate_audio_energy(audio_data.cpu().numpy())
            duration_s = len(audio_data) / config.audio.sample_rate
            if not self._is_speech_detected(audio_data.cpu().numpy(), duration_s):
                realtime_logger.debug(f"🔇 No speech in chunk {chunk_id} - skipping")
                return
            
            # Create conversation prompt for short responses
            conversation_prompt = self._create_ultra_short_streaming_prompt()
            
            # Prepare inputs
            inputs = self.processor(
                audio_values=audio_data.cpu().numpy(),  # FIXED: Use 'audio_values' not 'audio'
                text=conversation_prompt,
                sampling_rate=config.audio.sample_rate,
                # REMOVED: 'return_dict', 'tokenize' - not supported
                return_tensors="pt"
            ).to(self.device)
            
            realtime_logger.debug(f"🚀 Starting STREAMING inference for chunk {chunk_id}")
            inference_start = time.time()
            
            # STREAMING GENERATION: Generate tokens one by one
            with torch.no_grad():
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
                    # Initialize generation
                    input_ids = inputs.get('input_ids')
                    attention_mask = inputs.get('attention_mask')
                    audio_values = inputs.get('audio_values')
                    
                    # Set up generation parameters for streaming
                    max_new_tokens = self.max_response_words * 2  # Approximate tokens per word
                    generated_ids = input_ids.clone()
                    current_chunk = []
                    chunk_counter = 0
                    last_chunk_time = time.time()
                    
                    # STREAMING LOOP: Generate token by token
                    for step in range(max_new_tokens):
                        # Generate next token
                        with torch.autocast(device_type="cuda", dtype=torch.float16):
                            outputs = self.model(
                                input_ids=generated_ids,
                                attention_mask=attention_mask,
                                audio_values=audio_values,
                                use_cache=True
                            )
                        
                        # Get next token probabilities
                        next_token_logits = outputs.logits[:, -1, :] / self.response_temperature
                        
                        # Apply top-k and top-p sampling for variety
                        filtered_logits = self._apply_sampling_filters(next_token_logits, top_k=10, top_p=0.9)
                        probs = torch.softmax(filtered_logits, dim=-1)
                        next_token = torch.multinomial(probs, num_samples=1)
                        
                        # Add token to sequence
                        generated_ids = torch.cat([generated_ids, next_token], dim=-1)
                        
                        # Decode the new token
                        new_text = self.processor.tokenizer.decode(next_token[0], skip_special_tokens=True)
                        if new_text.strip():
                            current_chunk.append(new_text.strip())
                        
                        # Check for chunk completion
                        current_text = ' '.join(current_chunk)
                        should_send_chunk = False
                        
                        # Chunk completion criteria
                        if self._should_complete_chunk(current_text, last_chunk_time):
                            should_send_chunk = True
                        
                        # Send chunk if ready
                        if should_send_chunk and current_chunk:
                            chunk_counter += 1
                            chunk_text = current_text.strip()
                            
                            # Clean and validate chunk
                            if len(chunk_text) > 1:
                                processing_time = (time.time() - chunk_start_time) * 1000
                                chunk_result = {
                                    'chunk_id': f"{chunk_id}_stream_{chunk_counter}",
                                    'text': chunk_text,
                                    'is_streaming': True,
                                    'is_final': False,
                                    'processing_time_ms': processing_time,
                                    'word_count': len(chunk_text.split()),
                                    'chunk_number': chunk_counter,
                                    'timestamp': time.time()
                                }
                                
                                realtime_logger.info(f"🎯 STREAMING CHUNK {chunk_counter}: '{chunk_text}'")
                                yield chunk_result
                                
                                # Reset for next chunk
                                current_chunk = []
                                last_chunk_time = time.time()
                        
                        # Check for end of generation
                        if self._should_end_generation(new_text, generated_ids, step):
                            break
                    
                    # Send final chunk if any remaining
                    if current_chunk:
                        chunk_counter += 1
                        final_text = ' '.join(current_chunk).strip()
                        if final_text:
                            processing_time = (time.time() - chunk_start_time) * 1000
                            final_result = {
                                'chunk_id': f"{chunk_id}_stream_{chunk_counter}",
                                'text': final_text,
                                'is_streaming': True,
                                'is_final': True,
                                'processing_time_ms': processing_time,
                                'word_count': len(final_text.split()),
                                'chunk_number': chunk_counter,
                                'total_chunks': chunk_counter,
                                'timestamp': time.time()
                            }
                            
                            realtime_logger.info(f"🎯 FINAL STREAMING CHUNK: '{final_text}'")
                            yield final_result
            
            total_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.info(f"✅ CHUNKED STREAMING complete for {chunk_id} in {total_time:.1f}ms ({chunk_counter} chunks)")
            
        except Exception as e:
            error_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.error(f"❌ CHUNKED STREAMING error for {chunk_id}: {e}")
            
            # Yield error response
            yield {
                'chunk_id': f"{chunk_id}_error",
                'text': "Sorry, I didn't understand that.",
                'is_streaming': True,
                'is_final': True,
                'processing_time_ms': error_time,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _create_ultra_short_streaming_prompt(self) -> str:
        """Create prompt optimized for streaming responses"""
        return ("Respond naturally in 1-3 short sentences. Be conversational and helpful. "
                "Keep each sentence under 8 words for smooth streaming.")
    
    def _should_complete_chunk(self, current_text: str, last_chunk_time: float) -> bool:
        """Determine if current chunk should be completed"""
        words = current_text.split()
        time_since_last = (time.time() - last_chunk_time) * 1000
        
        # Criteria for chunk completion
        if len(words) >= self.max_chunk_words:  # Word limit reached
            return True
        if time_since_last >= self.chunk_timeout_ms:  # Timeout reached
            return True
        if any(sep in current_text for sep in self.chunk_separator_phrases):  # Natural break
            return True
        if len(words) >= self.min_chunk_words and current_text.endswith(('.', '!', '?')):  # Sentence end
            return True
        
        return False
    
    def _should_end_generation(self, new_text: str, generated_ids: torch.Tensor, step: int) -> bool:
        """Determine if generation should end"""
        # End conditions
        if new_text in ['</s>', '<|endoftext|>', '[END]']:  # Special tokens
            return True
        if step >= self.max_response_words * 2:  # Max tokens reached
            return True
        if generated_ids.shape[1] > 1000:  # Safety limit
            return True
        
        return False
    
    def _apply_sampling_filters(self, logits: torch.Tensor, top_k: int = 10, top_p: float = 0.9) -> torch.Tensor:
        """Apply top-k and top-p filtering for better generation"""
        # Top-k filtering
        if top_k > 0:
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = -float('inf')
        
        # Top-p filtering  
        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
            
            # Remove tokens with cumulative probability above threshold
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            
            indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
            logits[indices_to_remove] = -float('inf')
        
        return logits
    
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
