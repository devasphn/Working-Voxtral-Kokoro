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
        
        # Voice configuration - focusing on ऋतिका as requested
        self.available_voices = [
            "ऋतिका",  # Hindi - Primary voice as requested
            "tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe",  # English
            "pierre", "amelie", "marie",  # French
            "jana", "thomas", "max",  # German
            "유나", "준서",  # Korean
            "长乐", "白芷",  # Mandarin
            "javi", "sergio", "maria",  # Spanish
            "pietro", "giulia", "carlo"  # Italian
        ]
        self.default_voice = "ऋतिका"  # Set as default as requested
        
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
    
    async def generate_audio(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Generate audio from text using Orpheus TTS with LLM token generation
        """
        if not self.is_initialized:
            tts_logger.error("❌ TTS Engine not initialized")
            return None
            
        voice = voice or self.default_voice
        tts_logger.info(f"🎵 Generating audio for text: '{text[:50]}...' with voice '{voice}'")
        
        try:
            # Try Orpheus TTS first (real implementation)
            audio_data = await self._generate_with_orpheus_tts(text, voice)
            if audio_data:
                tts_logger.info(f"✅ Audio generated with Orpheus TTS ({len(audio_data)} bytes)")
                return audio_data
            else:
                tts_logger.warning("⚠️ Orpheus TTS failed, trying fallback...")
                # Fallback to espeak-ng if Orpheus fails
                audio_data = await self._generate_with_fallback_tts(text, voice)
                if audio_data:
                    tts_logger.info(f"✅ Audio generated with fallback TTS ({len(audio_data)} bytes)")
                    return audio_data
                else:
                    tts_logger.warning("⚠️ All TTS methods failed")
                    return None
                
        except Exception as e:
            tts_logger.error(f"❌ Error generating audio: {e}")
            return None
    
    async def _generate_with_fallback_tts(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate audio using fallback TTS (espeak-ng or pyttsx3)
        This provides immediate functionality while full Orpheus integration is developed
        """
        import tempfile
        import subprocess
        import os
        import asyncio
        
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Try espeak-ng first (better quality)
            try:
                # Map voice names to espeak voices
                espeak_voice_map = {
                    "tara": "en+f3", "leah": "en+f4", "jess": "en+f2", "leo": "en+m3",
                    "dan": "en+m4", "mia": "en+f1", "zac": "en+m2", "zoe": "en+f5",
                    "pierre": "fr+m3", "amelie": "fr+f3", "marie": "fr+f2",
                    "jana": "de+f3", "thomas": "de+m3", "max": "de+m2",
                    "javi": "es+m3", "sergio": "es+m2", "maria": "es+f3",
                    "pietro": "it+m3", "giulia": "it+f3", "carlo": "it+m2"
                }
                
                espeak_voice = espeak_voice_map.get(voice, "en+f3")
                
                # Generate audio with espeak-ng (run in thread pool to avoid blocking)
                cmd = [
                    "espeak-ng",
                    "-v", espeak_voice,
                    "-s", "150",  # Speed
                    "-p", "50",   # Pitch
                    "-a", "100",  # Amplitude
                    "-w", temp_path,  # Output to WAV file
                    text
                ]
                
                # Run subprocess in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                )
                
                if result.returncode == 0 and os.path.exists(temp_path):
                    # Read the generated audio file
                    with open(temp_path, 'rb') as f:
                        audio_data = f.read()
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    if len(audio_data) > 44:  # WAV header is 44 bytes
                        tts_logger.info(f"✅ Generated audio with espeak-ng ({len(audio_data)} bytes)")
                        return audio_data
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
                tts_logger.warning(f"⚠️ espeak-ng failed: {e}")
            
            # Fallback to pyttsx3 if espeak-ng is not available
            try:
                # Run pyttsx3 in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                audio_data = await loop.run_in_executor(None, self._generate_with_pyttsx3, text, voice, temp_path)
                
                if audio_data and len(audio_data) > 44:
                    tts_logger.info(f"✅ Generated audio with pyttsx3 ({len(audio_data)} bytes)")
                    return audio_data
                        
            except ImportError:
                tts_logger.warning("⚠️ pyttsx3 not available, install with: pip install pyttsx3")
            except Exception as e:
                tts_logger.warning(f"⚠️ pyttsx3 failed: {e}")
            
            # Clean up temp file if it still exists
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
            return None
            
        except Exception as e:
            tts_logger.error(f"❌ Fallback TTS generation failed: {e}")
            return None
    
    async def _generate_with_orpheus_tts(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate audio using real Orpheus TTS with LLM token generation
        """
        try:
            # Format the prompt for Orpheus model
            formatted_prompt = self.format_prompt(text, voice)
            tts_logger.info(f"🎯 Formatted prompt for voice '{voice}': {formatted_prompt[:100]}...")
            
            # Generate tokens using LLM server
            tokens = await self._generate_tokens_from_llm(formatted_prompt)
            if not tokens:
                tts_logger.warning("⚠️ No tokens generated from LLM server")
                return None
            
            tts_logger.info(f"🔢 Generated {len(tokens)} tokens from LLM")
            
            # Convert tokens to audio using SNAC model
            audio_data = await self._convert_tokens_to_audio(tokens)
            if audio_data:
                tts_logger.info(f"🎵 Successfully converted tokens to audio ({len(audio_data)} bytes)")
                return audio_data
            else:
                tts_logger.warning("⚠️ Failed to convert tokens to audio")
                return None
                
        except Exception as e:
            tts_logger.error(f"❌ Orpheus TTS generation failed: {e}")
            return None
    
    async def _generate_tokens_from_llm(self, prompt: str) -> Optional[List[int]]:
        """
        Generate tokens from LLM server (llama.cpp or similar)
        """
        import httpx
        import asyncio
        
        # LLM server configuration
        llm_server_url = "http://localhost:8010"  # Default llama.cpp server port
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to generate tokens from LLM server
                response = await client.post(
                    f"{llm_server_url}/completion",
                    json={
                        "prompt": prompt,
                        "max_tokens": 1024,
                        "temperature": 0.7,
                        "stream": False,
                        "stop": ["<|eot_id|>"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("content", "")
                    
                    # Extract tokens from the generated text
                    tokens = self._extract_tokens_from_text(generated_text)
                    return tokens
                else:
                    tts_logger.warning(f"⚠️ LLM server returned status {response.status_code}")
                    return None
                    
        except httpx.ConnectError:
            tts_logger.warning("⚠️ Cannot connect to LLM server on port 8010")
            return None
        except Exception as e:
            tts_logger.error(f"❌ Error communicating with LLM server: {e}")
            return None
    
    def _extract_tokens_from_text(self, text: str) -> List[int]:
        """
        Extract audio tokens from LLM generated text
        Looks for <custom_token_XXXX> patterns and converts them to token IDs
        """
        import re
        
        tokens = []
        # Find all custom token patterns
        token_pattern = r'<custom_token_(\d+)>'
        matches = re.findall(token_pattern, text)
        
        for i, match in enumerate(matches):
            token_id = self.turn_token_into_id(f"<custom_token_{match}>", i)
            if token_id is not None:
                tokens.append(token_id)
        
        tts_logger.info(f"🔍 Extracted {len(tokens)} valid tokens from LLM output")
        return tokens
    
    async def _convert_tokens_to_audio(self, tokens: List[int]) -> Optional[bytes]:
        """
        Convert token list to audio using SNAC model
        """
        if not tokens or len(tokens) < 7:
            tts_logger.warning("⚠️ Not enough tokens for audio generation")
            return None
        
        try:
            # Group tokens into frames (7 tokens per frame)
            num_frames = len(tokens) // 7
            if num_frames == 0:
                return None
            
            # Convert tokens to audio using existing convert_to_audio method
            audio_bytes = self.convert_to_audio(tokens[:num_frames * 7], num_frames)
            
            if audio_bytes:
                # Convert raw audio to WAV format
                wav_audio = self._create_wav_from_raw_audio(audio_bytes)
                return wav_audio
            else:
                return None
                
        except Exception as e:
            tts_logger.error(f"❌ Error converting tokens to audio: {e}")
            return None
    
    def _create_wav_from_raw_audio(self, raw_audio: bytes) -> bytes:
        """
        Create WAV file from raw audio bytes
        """
        import wave
        import io
        
        try:
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)  # 24kHz
                wav_file.writeframes(raw_audio)
            
            wav_data = wav_buffer.getvalue()
            return wav_data
            
        except Exception as e:
            tts_logger.error(f"❌ Error creating WAV file: {e}")
            return raw_audio  # Return raw audio as fallback

    def _generate_with_pyttsx3(self, text: str, voice: str, temp_path: str) -> Optional[bytes]:
        """Generate audio using pyttsx3 (runs in thread pool)"""
        try:
            import pyttsx3
            import os
            
            # Initialize pyttsx3
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices:
                # Try to find a suitable voice
                for v in voices:
                    if 'female' in v.name.lower() and voice in ['tara', 'leah', 'jess', 'mia', 'zoe', 'amelie', 'marie', 'jana', 'maria', 'giulia']:
                        engine.setProperty('voice', v.id)
                        break
                    elif 'male' in v.name.lower() and voice in ['leo', 'dan', 'zac', 'pierre', 'thomas', 'max', 'javi', 'sergio', 'pietro', 'carlo']:
                        engine.setProperty('voice', v.id)
                        break
            
            # Set speech rate and volume
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.9)
            
            # Generate audio
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            if os.path.exists(temp_path):
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(temp_path)
                return audio_data
            
            return None
            
        except Exception as e:
            tts_logger.error(f"❌ pyttsx3 generation failed: {e}")
            return None

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
