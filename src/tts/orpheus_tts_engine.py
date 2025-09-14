"""
Orpheus TTS Engine - Proper Implementation
Based on research of Orpheus TTS model and SNAC neural codec
"""

import os
import sys
import json
import time
import asyncio
import logging
import httpx
import base64
import wave
import io
import re
import numpy as np
import torch
from typing import Dict, Any, Optional, List

from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("orpheus_tts")
tts_logger.setLevel(logging.INFO)

class OrpheusTTSEngine:
    """
    Orpheus TTS Engine - Proper Implementation
    Uses Orpheus model with SNAC neural codec for high-quality TTS
    """
    
    def __init__(self):
        self.is_initialized = False
        self.sample_rate = 24000
        
        # Server configuration
        self.orpheus_server_url = f"http://{config.tts.orpheus_server.host}:{config.tts.orpheus_server.port}"
        self.timeout = config.tts.orpheus_server.timeout
        
        # SNAC model for audio conversion
        self.snac_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
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
        
        tts_logger.info(f"OrpheusTTSEngine initialized")
        tts_logger.info(f"🎯 Default voice: {self.default_voice}")
        tts_logger.info(f"🔧 Device: {self.device}")
    
    async def initialize(self):
        """Initialize the Orpheus TTS Engine"""
        try:
            tts_logger.info("🚀 Initializing Orpheus TTS Engine...")
            start_time = time.time()
            
            # Initialize SNAC model first
            await self._load_snac_model()
            
            # Test server connectivity
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.get(f"{self.orpheus_server_url}/v1/models")
                    if response.status_code == 200:
                        tts_logger.info("✅ Orpheus server accessible")
                        self.is_initialized = True
                    else:
                        tts_logger.error(f"❌ Server error: {response.status_code}")
                        self.is_initialized = False
                        return
                except httpx.ConnectError:
                    tts_logger.error(f"❌ Cannot connect to {self.orpheus_server_url}")
                    self.is_initialized = False
                    return
            
            init_time = time.time() - start_time
            tts_logger.info(f"🎉 Engine initialized in {init_time:.2f}s")
            
        except Exception as e:
            tts_logger.error(f"❌ Initialization failed: {e}")
            self.is_initialized = False
    
    async def _load_snac_model(self):
        """Load SNAC model for audio conversion"""
        try:
            from snac import SNAC
            tts_logger.info("📥 Loading SNAC model...")
            
            self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
            if self.device == "cuda":
                self.snac_model = self.snac_model.cuda()
            
            tts_logger.info(f"✅ SNAC model loaded on {self.device}")
            
        except ImportError:
            tts_logger.error("❌ SNAC not installed. Run: pip install snac")
            raise
        except Exception as e:
            tts_logger.error(f"❌ SNAC loading failed: {e}")
            raise
    
    async def _generate_with_orpheus_server(self, text: str, voice: str) -> Optional[bytes]:
        """Generate audio using Orpheus server and SNAC conversion"""
        try:
            tts_logger.info(f"🎵 Generating TTS for '{text[:30]}...' with voice '{voice}'")
            
            # Correct prompt format for Orpheus TTS
            prompt = f"<|start_header_id|>user<|end_header_id|>\n\nGenerate speech for the following text using voice '{voice}': {text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            
            payload = {
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.1,
                "stream": False,
                "stop": ["<|eot_id|>"]
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.orpheus_server_url}/v1/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "choices" in result and result["choices"]:
                        generated_text = result["choices"][0].get("text", "").strip()
                        tts_logger.info(f"📝 Generated {len(generated_text)} chars")
                        
                        # Extract TTS tokens
                        tokens = self._extract_tts_tokens(generated_text)
                        
                        if tokens:
                            tts_logger.info(f"🎵 Found {len(tokens)} TTS tokens")
                            # Convert tokens to audio using SNAC
                            audio_data = await self._tokens_to_audio_snac(tokens)
                            return audio_data
                        else:
                            tts_logger.warning("⚠️ No TTS tokens found")
                            return None
                    else:
                        tts_logger.error("❌ No response choices")
                        return None
                else:
                    tts_logger.error(f"❌ Server error: {response.status_code}")
                    return None
                    
        except Exception as e:
            tts_logger.error(f"❌ Generation failed: {e}")
            return None
    
    def _extract_tts_tokens(self, text: str) -> List[int]:
        """Extract TTS tokens from generated text"""
        try:
            # Extract <custom_token_XXXX> patterns
            pattern = r'<custom_token_(\d+)>'
            matches = re.findall(pattern, text)
            
            tokens = []
            for match in matches:
                try:
                    token_id = int(match)
                    # Ensure token is in valid range
                    if 0 <= token_id <= 4095:
                        tokens.append(token_id)
                except ValueError:
                    continue
            
            return tokens
            
        except Exception as e:
            tts_logger.error(f"❌ Token extraction failed: {e}")
            return []
    
    async def _tokens_to_audio_snac(self, tokens: List[int]) -> Optional[bytes]:
        """Convert TTS tokens to audio using SNAC"""
        try:
            if not self.snac_model:
                tts_logger.error("❌ SNAC model not loaded")
                return None
            
            if len(tokens) < 7:
                tts_logger.warning("⚠️ Not enough tokens for SNAC")
                return None
            
            tts_logger.info(f"🔧 Converting {len(tokens)} tokens to audio")
            
            # Pad tokens to multiple of 7 (SNAC requirement)
            while len(tokens) % 7 != 0:
                tokens.append(0)
            
            num_frames = len(tokens) // 7
            
            # Create SNAC codes
            device = next(self.snac_model.parameters()).device
            
            codes_0 = torch.tensor([tokens[i*7] for i in range(num_frames)], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            codes_1 = torch.tensor([tokens[i*7+1] for i in range(num_frames)] + 
                                 [tokens[i*7+4] for i in range(num_frames)], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            codes_2 = torch.tensor([tokens[i*7+j] for i in range(num_frames) for j in [2,3,5,6]], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            
            codes = [codes_0, codes_1, codes_2]
            
            # Decode with SNAC
            with torch.inference_mode():
                audio_hat = self.snac_model.decode(codes)
                
                # Extract audio
                if audio_hat.dim() == 3:
                    audio = audio_hat[0, 0, :]
                else:
                    audio = audio_hat.flatten()
                
                # Convert to numpy
                audio_np = audio.cpu().numpy() if device == "cuda" else audio.numpy()
                
                # Normalize and convert to 16-bit
                audio_np = np.clip(audio_np, -1.0, 1.0)
                audio_int16 = (audio_np * 32767).astype(np.int16)
                
                # Create WAV
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_int16.tobytes())
                
                tts_logger.info(f"✅ SNAC conversion successful")
                return wav_buffer.getvalue()
                
        except Exception as e:
            tts_logger.error(f"❌ SNAC conversion failed: {e}")
            return None
    async def generate_audio(self, text: str, voice: str = None) -> Optional[bytes]:
        """Generate audio from text using Orpheus TTS"""
        voice = voice or self.default_voice
        
        if not self.is_initialized:
            tts_logger.error("❌ Engine not initialized")
            return None
        
        try:
            return await self._generate_with_orpheus_server(text, voice)
        except Exception as e:
            tts_logger.error(f"❌ Audio generation failed: {e}")
            return None
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get TTS model information"""
        return {
            "engine": "Orpheus-SNAC",
            "server_url": self.orpheus_server_url,
            "sample_rate": self.sample_rate,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "initialized": self.is_initialized
        }
    
    async def close(self):
        """Cleanup resources"""
        if self.snac_model:
            del self.snac_model
            self.snac_model = None
        tts_logger.info("🧹 Resources cleaned up")





