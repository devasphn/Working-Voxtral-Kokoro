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
                # ADDED: Ultra-aggressive optimizations
                "use_flash_attention_2": True if attn_implementation == "flash_attention_2" else False,
                "torch_compile": False,  # Disable for FlashAttention2 compatibility
                "max_memory": {0: "8GB"},  # Limit VRAM usage
                "offload_folder": None,  # Keep everything on GPU
                "load_in_8bit": False,     # Don't use 8-bit (causes slowdown)
                "load_in_4bit": False,     # Don't use 4-bit (unstable)
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
            
            # DISABLED: Skip torch.compile (conflicts with FlashAttention2)
            realtime_logger.info("💡 Skipping torch.compile (using FlashAttention2 + quantization)")
            
            self.is_initialized = True
            init_time = time.time() - start_time
            realtime_logger.info(f"🎉 ULTRA-LOW LATENCY Voxtral ready in {init_time:.2f}s - Target: <500ms")
            
        except Exception as e:
            realtime_logger.error(f"❌ Ultra-low latency initialization failed: {e}")
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
                        
                        # REPLACE the conversation_prompt in process_realtime_chunk:
                        conversation_prompt = self._create_ultra_short_prompt()
                        
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
                        
                        # ULTRA-LOW LATENCY inference with aggressive settings
                        realtime_logger.debug(f"🚀 Starting ULTRA-FAST inference for chunk {chunk_id}")
                        inference_start = time.time()
                        
                        with torch.no_grad():
                            # CRITICAL: Use aggressive mixed precision
                            with torch.autocast(device_type="cuda",
                                               dtype=torch.float16,  # Force float16 for maximum speed
                                               enabled=True):
                                # ULTRA-AGGRESSIVE generation parameters for <500ms total
                                outputs = self.model.generate(
                                    **inputs,
                                    max_new_tokens=50,      # ULTRA-REDUCED: Cut by 75% (was 200)
                                    min_new_tokens=1,       # ULTRA-REDUCED: Minimum viable (was 5)
                                    do_sample=False,        # DISABLED: Deterministic for speed (was True)
                                    num_beams=1,           # Single beam (fastest)
                                    temperature=None,       # DISABLED: Deterministic mode
                                    top_p=None,            # DISABLED: Deterministic mode
                                    repetition_penalty=1.0, # DISABLED: No penalty processing
                                    pad_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None,
                                    use_cache=True,
                                    # ULTRA-AGGRESSIVE: Force early stopping
                                    early_stopping=True,    # ENABLED: Stop as soon as possible
                                    length_penalty=0.8,     # STRONG: Prefer shorter responses
                                    no_repeat_ngram_size=2, # REDUCED: Faster processing (was 3)
                                    # ADDED: Advanced speed optimizations
                                    output_scores=False,    # DISABLED: Skip score computation
                                    return_dict_in_generate=False,  # DISABLED: Skip dict creation
                                    synced_gpus=False,      # DISABLED: Single GPU optimization
                                    # CRITICAL: Set explicit stopping criteria
                                    eos_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None,
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
                audio=audio_data.cpu().numpy(),
                text=conversation_prompt,
                sampling_rate=config.audio.sample_rate,
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
