"""
Orpheus TTS Engine - Integrated TTS functionality for Voxtral
Adapted from Orpheus-FastAPI for seamless integration
"""

import os
import sys
import json
import time
import wave
import numpy as np
import torch
import asyncio
import threading
import queue
from typing import List, Dict, Any, Optional, Generator, Union, Tuple
from concurrent.futures import ThreadPoolExecutor
import logging

from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("orpheus_tts")
tts_logger.setLevel(logging.INFO)

class OrpheusTTSEngine:
    """
    Orpheus TTS Engine integrated with Voxtral system
    Provides high-quality text-to-speech synthesis
    """
    
    def __init__(self):
        self.is_initialized = False
        self.model = None
        self.snac_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 24000
        
        # Voice configuration
        self.available_voices = [
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",  # English
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",  # German
            "유나", "준서",  # Korean
            "ऋतिका",  # Hindi
            "长乐", "白芷",  # Mandarin
            "javi", "sergio", "maria",  # Spanish
            "pietro", "giulia", "carlo"  # Italian
        ]
        self.default_voice = "tara"
        
        # Performance settings
        self.high_end_gpu = self._detect_high_end_gpu()
        self.num_workers = 4 if self.high_end_gpu else 2
        
        # Token processing cache
        self.token_id_cache = {}
        self.max_cache_size = 10000
        
        tts_logger.info(f"OrpheusTTSEngine initialized for {self.device}")
        if self.high_end_gpu:
            tts_logger.info("🚀 High-end GPU detected - using optimized settings")
    
    def _detect_high_end_gpu(self) -> bool:
        """Detect if we have a high-end GPU for optimization"""
        if not torch.cuda.is_available():
            return False
            
        props = torch.cuda.get_device_properties(0)
        gpu_mem_gb = props.total_memory / (1024**3)
        
        # High-end if: ≥16GB VRAM OR compute capability ≥8.0 OR ≥12GB VRAM with ≥7.0 CC
        return (gpu_mem_gb >= 16.0 or 
                props.major >= 8 or 
                (gpu_mem_gb >= 12.0 and props.major >= 7))
    
    async def initialize(self):
        """Initialize the TTS models"""
        try:
            tts_logger.info("🚀 Initializing Orpheus TTS Engine...")
            start_time = time.time()
            
            # Import SNAC model
            try:
                from snac import SNAC
                tts_logger.info("📥 Loading SNAC model...")
                self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
                self.snac_model = self.snac_model.to(self.device)
                tts_logger.info("✅ SNAC model loaded successfully")
            except ImportError:
                tts_logger.error("❌ SNAC model not available. Please install: pip install snac")
                raise
            
            # Setup CUDA stream for parallel processing if available
            self.cuda_stream = None
            if self.device == "cuda":
                self.cuda_stream = torch.cuda.Stream()
                tts_logger.info("🔧 CUDA stream configured for parallel processing")
            
            self.is_initialized = True
            init_time = time.time() - start_time
            tts_logger.info(f"🎉 Orpheus TTS Engine initialized in {init_time:.2f}s")
            
        except Exception as e:
            tts_logger.error(f"❌ Failed to initialize Orpheus TTS Engine: {e}")
            raise
    
    def format_prompt(self, text: str, voice: str = None) -> str:
        """Format text prompt for Orpheus model"""
        if voice is None:
            voice = self.default_voice
            
        if voice not in self.available_voices:
            tts_logger.warning(f"Voice '{voice}' not available, using '{self.default_voice}'")
            voice = self.default_voice
        
        # Format with voice prefix and special tokens
        formatted_prompt = f"{voice}: {text}"
        special_start = "<|audio|>"
        special_end = "<|eot_id|>"
        
        return f"{special_start}{formatted_prompt}{special_end}"
    
    def turn_token_into_id(self, token_string: str, index: int) -> Optional[int]:
        """Convert token string to ID with caching"""
        custom_token_prefix = "<custom_token_"
        
        # Check cache first
        cache_key = (token_string, index % 7)
        if cache_key in self.token_id_cache:
            return self.token_id_cache[cache_key]
        
        # Early rejection for non-matches
        if custom_token_prefix not in token_string:
            return None
        
        token_string = token_string.strip()
        last_token_start = token_string.rfind(custom_token_prefix)
        
        if last_token_start == -1:
            return None
        
        last_token = token_string[last_token_start:]
        
        if not (last_token.startswith(custom_token_prefix) and last_token.endswith(">")):
            return None
        
        try:
            number_str = last_token[14:-1]
            token_id = int(number_str) - 10 - ((index % 7) * 4096)
            
            # Cache the result if valid
            if len(self.token_id_cache) < self.max_cache_size:
                self.token_id_cache[cache_key] = token_id
            
            return token_id
        except (ValueError, IndexError):
            return None
    
    def convert_to_audio(self, multiframe: List[int], count: int) -> Optional[bytes]:
        """Convert token frames to audio using SNAC model"""
        if not self.is_initialized or self.snac_model is None:
            return None
            
        if len(multiframe) < 7:
            return None
        
        num_frames = len(multiframe) // 7
        frame = multiframe[:num_frames * 7]
        
        # Pre-allocate tensors for efficiency
        codes_0 = torch.zeros(num_frames, dtype=torch.int32, device=self.device)
        codes_1 = torch.zeros(num_frames * 2, dtype=torch.int32, device=self.device)
        codes_2 = torch.zeros(num_frames * 4, dtype=torch.int32, device=self.device)
        
        frame_tensor = torch.tensor(frame, dtype=torch.int32, device=self.device)
        
        # Direct indexing for performance
        for j in range(num_frames):
            idx = j * 7
            codes_0[j] = frame_tensor[idx]
            codes_1[j*2] = frame_tensor[idx+1]
            codes_1[j*2+1] = frame_tensor[idx+4]
            codes_2[j*4] = frame_tensor[idx+2]
            codes_2[j*4+1] = frame_tensor[idx+3]
            codes_2[j*4+2] = frame_tensor[idx+5]
            codes_2[j*4+3] = frame_tensor[idx+6]
        
        codes = [codes_0.unsqueeze(0), codes_1.unsqueeze(0), codes_2.unsqueeze(0)]
        
        # Validate token ranges
        if (torch.any(codes[0] < 0) or torch.any(codes[0] > 4096) or 
            torch.any(codes[1] < 0) or torch.any(codes[1] > 4096) or 
            torch.any(codes[2] < 0) or torch.any(codes[2] > 4096)):
            return None
        
        # Use CUDA stream if available
        stream_ctx = torch.cuda.stream(self.cuda_stream) if self.cuda_stream else torch.no_grad()
        
        with stream_ctx, torch.inference_mode():
            # Decode audio
            audio_hat = self.snac_model.decode(codes)
            audio_slice = audio_hat[:, :, 2048:4096]
            
            # Convert to bytes efficiently
            if self.device == "cuda":
                audio_int16_tensor = (audio_slice * 32767).to(torch.int16)
                audio_bytes = audio_int16_tensor.cpu().numpy().tobytes()
            else:
                detached_audio = audio_slice.detach().cpu()
                audio_np = detached_audio.numpy()
                audio_int16 = (audio_np * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
        
        return audio_bytes
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get TTS model information"""
        return {
            "engine": "Orpheus-FastAPI",
            "device": self.device,
            "sample_rate": self.sample_rate,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "high_end_gpu": self.high_end_gpu,
            "initialized": self.is_initialized
        }
