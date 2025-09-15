"""
Orpheus Direct Model - Direct Integration without FastAPI
Implements direct Orpheus model loading using transformers for TTS generation
"""

import torch
import asyncio
import time
import logging
import re
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
from threading import Lock
import gc

# Setup logging
orpheus_logger = logging.getLogger("orpheus_direct")
orpheus_logger.setLevel(logging.INFO)

class ModelInitializationError(Exception):
    """Raised when Orpheus model initialization fails"""
    pass

class TokenProcessingError(Exception):
    """Raised when token extraction/processing fails"""
    pass

class AudioGenerationError(Exception):
    """Raised when TTS generation fails"""
    pass

class OrpheusDirectModel:
    """
    Direct Orpheus model integration without FastAPI dependency
    Loads Orpheus model directly using transformers for high-performance TTS
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.snac_model = None
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Model configuration - Updated to correct Orpheus model
        self.model_name = "canopy-ai/Orpheus-3b"  # Correct Orpheus model from Canopy AI
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # Performance settings
        self.max_new_tokens = 1000
        self.temperature = 0.1
        self.top_p = 0.95
        self.sample_rate = 24000
        
        # Voice configuration
        self.available_voices = [
            "ऋतिका",  # Hindi - Primary voice
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",  # English
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",  # German
            "유나", "준서",  # Korean
            "长乐", "白芷",  # Mandarin
            "javi", "sergio", "maria",  # Spanish
            "pietro", "giulia", "carlo"  # Italian
        ]
        self.default_voice = "ऋतिका"
        
        # Memory management
        self.shared_memory_pool = None
        self.memory_stats = {"model_memory_gb": 0.0, "snac_memory_gb": 0.0}
        
        orpheus_logger.info(f"OrpheusDirectModel initialized for device: {self.device}")
    
    async def initialize(self, device: str = None, shared_memory_pool: Any = None) -> bool:
        """
        Initialize Orpheus model directly with transformers
        """
        try:
            orpheus_logger.info("🚀 Initializing Orpheus Direct Model...")
            start_time = time.time()
            
            # Use provided device or default
            if device:
                self.device = device
                orpheus_logger.info(f"🎯 Using specified device: {self.device}")
            
            # Store shared memory pool reference
            self.shared_memory_pool = shared_memory_pool
            
            # Load tokenizer first
            orpheus_logger.info(f"📥 Loading Orpheus tokenizer from {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=True
            )
            
            # Ensure tokenizer has required tokens
            if not hasattr(self.tokenizer, 'eos_token_id') or self.tokenizer.eos_token_id is None:
                self.tokenizer.eos_token_id = self.tokenizer.convert_tokens_to_ids('</s>')
            
            orpheus_logger.info("✅ Tokenizer loaded successfully")
            
            # Load Orpheus model
            orpheus_logger.info(f"📥 Loading Orpheus model from {self.model_name}")
            
            model_kwargs = {
                "torch_dtype": self.torch_dtype,
                "device_map": "auto" if self.device == "cuda" else None,
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
                "attn_implementation": "eager"  # Use eager attention for stability
            }
            
            # Load model with error handling
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    **model_kwargs
                )
                orpheus_logger.info("✅ Orpheus model loaded successfully")
                
            except Exception as model_error:
                orpheus_logger.error(f"❌ Failed to load Orpheus model: {model_error}")
                # Try fallback with different settings
                orpheus_logger.info("🔄 Trying fallback model loading...")
                model_kwargs.update({
                    "torch_dtype": torch.float32,
                    "device_map": None
                })
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    **model_kwargs
                )
                
                # Move to device manually if needed
                if self.device == "cuda":
                    self.model = self.model.to(self.device)
                
                orpheus_logger.info("✅ Orpheus model loaded with fallback settings")
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Track model memory usage
            if self.device == "cuda":
                model_memory = torch.cuda.memory_allocated() / (1024**3)
                self.memory_stats["model_memory_gb"] = model_memory
                orpheus_logger.info(f"📊 Orpheus model using {model_memory:.2f} GB VRAM")
            
            # Initialize SNAC model
            await self._load_snac_model()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            orpheus_logger.info(f"🎉 Orpheus Direct Model initialized in {init_time:.2f}s")
            
            return True
            
        except Exception as e:
            orpheus_logger.error(f"❌ Orpheus model initialization failed: {e}")
            import traceback
            orpheus_logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise ModelInitializationError(f"Failed to initialize Orpheus model: {e}")
    
    async def _load_snac_model(self):
        """Load SNAC model for audio conversion"""
        try:
            orpheus_logger.info("📥 Loading SNAC model for audio conversion...")
            
            # Import SNAC
            try:
                from snac import SNAC
            except ImportError:
                orpheus_logger.error("❌ SNAC not installed. Run: pip install snac")
                raise ModelInitializationError("SNAC package not installed")
            
            # Load SNAC model
            self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
            
            # Move to device
            if self.device == "cuda":
                self.snac_model = self.snac_model.to(self.device)
            
            # Track SNAC memory usage
            if self.device == "cuda":
                snac_memory = (torch.cuda.memory_allocated() / (1024**3)) - self.memory_stats["model_memory_gb"]
                self.memory_stats["snac_memory_gb"] = max(0, snac_memory)
                orpheus_logger.info(f"📊 SNAC model using {snac_memory:.2f} GB VRAM")
            
            orpheus_logger.info("✅ SNAC model loaded successfully")
            
        except Exception as e:
            orpheus_logger.error(f"❌ SNAC model loading failed: {e}")
            raise ModelInitializationError(f"Failed to load SNAC model: {e}")
    
    async def generate_speech(self, text: str, voice: str = None) -> bytes:
        """
        Generate speech audio from text using direct Orpheus model
        """
        if not self.is_initialized:
            raise AudioGenerationError("Model not initialized")
        
        voice = voice or self.default_voice
        
        try:
            orpheus_logger.info(f"🎵 Generating speech for '{text[:50]}...' with voice '{voice}'")
            generation_start = time.time()
            
            # Generate TTS tokens
            tokens = await self.generate_tokens(text, voice)
            
            if not tokens:
                raise AudioGenerationError("No TTS tokens generated")
            
            # Convert tokens to audio
            audio_data = await self.tokens_to_audio(tokens)
            
            if not audio_data:
                raise AudioGenerationError("Failed to convert tokens to audio")
            
            generation_time = (time.time() - generation_start) * 1000
            orpheus_logger.info(f"✅ Speech generated in {generation_time:.1f}ms")
            
            return audio_data
            
        except Exception as e:
            orpheus_logger.error(f"❌ Speech generation failed: {e}")
            raise AudioGenerationError(f"Speech generation failed: {e}")
    
    async def generate_tokens(self, text: str, voice: str) -> List[int]:
        """
        Generate TTS tokens from text using Orpheus model
        """
        try:
            orpheus_logger.debug(f"🔤 Generating tokens for text: '{text[:30]}...' with voice: {voice}")
            
            with self.model_lock:
                # Create prompt in Orpheus format
                prompt = self._create_tts_prompt(text, voice)
                
                # Tokenize input
                inputs = self.tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=2048
                )
                
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Generate with Orpheus model
                with torch.no_grad():
                    with torch.autocast(device_type="cuda" if "cuda" in self.device else "cpu", 
                                       dtype=self.torch_dtype):
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=self.max_new_tokens,
                            min_new_tokens=50,
                            do_sample=True,
                            temperature=self.temperature,
                            top_p=self.top_p,
                            repetition_penalty=1.1,
                            pad_token_id=self.tokenizer.eos_token_id,
                            use_cache=True,
                            num_beams=1
                        )
                
                # Decode generated text
                input_length = inputs['input_ids'].shape[1]
                generated_text = self.tokenizer.decode(
                    outputs[0][input_length:], 
                    skip_special_tokens=False
                )
                
                orpheus_logger.debug(f"📝 Generated text length: {len(generated_text)} chars")
                
                # Extract TTS tokens from generated text
                tokens = self._extract_tts_tokens(generated_text)
                
                orpheus_logger.debug(f"🎵 Extracted {len(tokens)} TTS tokens")
                return tokens
                
        except Exception as e:
            orpheus_logger.error(f"❌ Token generation failed: {e}")
            raise TokenProcessingError(f"Token generation failed: {e}")
    
    def _create_tts_prompt(self, text: str, voice: str) -> str:
        """
        Create properly formatted prompt for Orpheus TTS generation
        Based on official Orpheus repository format
        """
        # Updated Orpheus TTS prompt format based on official repository
        prompt = f"<|im_start|>user\nGenerate speech in the voice of {voice}: {text}<|im_end|>\n<|im_start|>assistant\n"
        return prompt
    
    def _extract_tts_tokens(self, text: str) -> List[int]:
        """
        Extract TTS tokens from generated text using official Orpheus format
        Updated based on official Orpheus repository
        """
        try:
            # Look for audio tokens in the format used by official Orpheus
            # Pattern may be different - checking for various token formats
            patterns = [
                r'<\|audio_(\d+)\|>',  # Official Orpheus format
                r'<audio_(\d+)>',      # Alternative format
                r'<custom_token_(\d+)>', # Legacy format
                r'<\|(\d+)\|>'         # Numeric token format
            ]
            
            tokens = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    orpheus_logger.debug(f"🔍 Found {len(matches)} tokens with pattern: {pattern}")
                    
                    for i, match in enumerate(matches):
                        try:
                            token_id = int(match)
                            
                            # For official Orpheus, tokens might not need the complex processing
                            # Use direct token IDs if they're in valid range
                            if 0 <= token_id <= 4096:
                                tokens.append(token_id)
                            else:
                                # Apply processing if needed for legacy compatibility
                                processed_token = token_id - 10 - ((i % 7) * 4096)
                                if processed_token > 0:
                                    tokens.append(processed_token)
                                    
                        except ValueError:
                            continue
                    
                    if tokens:
                        break  # Use first successful pattern
            
            if not tokens:
                orpheus_logger.warning("⚠️ No audio tokens found in generated text")
                return []
            
            orpheus_logger.debug(f"🔍 Extracted {len(tokens)} valid audio tokens")
            return tokens
            
        except Exception as e:
            orpheus_logger.error(f"❌ Token extraction failed: {e}")
            raise TokenProcessingError(f"Token extraction failed: {e}")
    
    async def tokens_to_audio(self, tokens: List[int]) -> Optional[bytes]:
        """
        Convert TTS tokens to audio using SNAC codec with Orpheus-FastAPI algorithm
        """
        try:
            if not self.snac_model:
                raise AudioGenerationError("SNAC model not loaded")
            
            if len(tokens) < 7:
                orpheus_logger.warning("⚠️ Not enough tokens for SNAC conversion")
                return None
            
            orpheus_logger.debug(f"🔧 Converting {len(tokens)} tokens to audio")
            
            # Pad tokens to multiple of 7 (SNAC requirement)
            while len(tokens) % 7 != 0:
                tokens.append(0)
            
            num_frames = len(tokens) // 7
            device = next(self.snac_model.parameters()).device
            
            # Pre-allocate tensors for better performance (from Orpheus-FastAPI)
            codes_0 = torch.zeros(num_frames, dtype=torch.int32, device=device)
            codes_1 = torch.zeros(num_frames * 2, dtype=torch.int32, device=device)
            codes_2 = torch.zeros(num_frames * 4, dtype=torch.int32, device=device)
            
            # Use vectorized operations (from Orpheus-FastAPI)
            frame_tensor = torch.tensor(tokens, dtype=torch.int32, device=device)
            
            # Direct indexing is much faster than concatenation (from Orpheus-FastAPI)
            for j in range(num_frames):
                idx = j * 7
                
                # Code 0 - single value per frame
                codes_0[j] = frame_tensor[idx]
                
                # Code 1 - two values per frame
                codes_1[j*2] = frame_tensor[idx+1]
                codes_1[j*2+1] = frame_tensor[idx+4]
                
                # Code 2 - four values per frame
                codes_2[j*4] = frame_tensor[idx+2]
                codes_2[j*4+1] = frame_tensor[idx+3]
                codes_2[j*4+2] = frame_tensor[idx+5]
                codes_2[j*4+3] = frame_tensor[idx+6]
            
            # Reshape codes into expected format
            codes = [
                codes_0.unsqueeze(0), 
                codes_1.unsqueeze(0), 
                codes_2.unsqueeze(0)
            ]
            
            # Check tokens are in valid range (from Orpheus-FastAPI)
            if (torch.any(codes[0] < 0) or torch.any(codes[0] > 4096) or 
                torch.any(codes[1] < 0) or torch.any(codes[1] > 4096) or 
                torch.any(codes[2] < 0) or torch.any(codes[2] > 4096)):
                orpheus_logger.warning("⚠️ Some tokens out of valid range")
                return None
            
            # Decode with SNAC (from Orpheus-FastAPI)
            with torch.inference_mode():
                audio_hat = self.snac_model.decode(codes)
                
                # Extract the relevant slice (from Orpheus-FastAPI)
                # This is the critical audio slice that produces real speech
                audio_slice = audio_hat[:, :, 2048:4096]
                
                # Process on GPU if possible, with minimal data transfer (from Orpheus-FastAPI)
                if device.type == "cuda":
                    # Scale directly on GPU
                    audio_int16_tensor = (audio_slice * 32767).to(torch.int16)
                    # Only transfer the final result to CPU
                    audio_bytes = audio_int16_tensor.cpu().numpy().tobytes()
                else:
                    # For non-CUDA devices, fall back to the original approach
                    detached_audio = audio_slice.detach().cpu()
                    audio_np = detached_audio.numpy()
                    audio_int16 = (audio_np * 32767).astype(np.int16)
                    audio_bytes = audio_int16.tobytes()
                
                orpheus_logger.debug(f"✅ SNAC conversion successful, generated {len(audio_bytes)} bytes")
                return audio_bytes
                
        except Exception as e:
            orpheus_logger.error(f"❌ SNAC conversion failed: {e}")
            raise AudioGenerationError(f"SNAC conversion failed: {e}")
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "is_initialized": self.is_initialized,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "sample_rate": self.sample_rate,
            "memory_stats": self.memory_stats,
            "performance_settings": {
                "max_new_tokens": self.max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p
            }
        }
    
    async def cleanup(self):
        """Cleanup model resources"""
        try:
            orpheus_logger.info("🧹 Cleaning up Orpheus Direct Model resources...")
            
            if self.model:
                del self.model
                self.model = None
            
            if self.tokenizer:
                del self.tokenizer
                self.tokenizer = None
            
            if self.snac_model:
                del self.snac_model
                self.snac_model = None
            
            # Clear GPU cache
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            # Force garbage collection
            gc.collect()
            
            self.is_initialized = False
            orpheus_logger.info("✅ Cleanup completed")
            
        except Exception as e:
            orpheus_logger.error(f"❌ Cleanup failed: {e}")

# Global instance for direct access
orpheus_direct_model = OrpheusDirectModel()