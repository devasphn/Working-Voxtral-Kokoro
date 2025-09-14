"""
Orpheus TTS Engine - Integration with Orpheus-FastAPI
Connects to Orpheus-FastAPI server for high-quality TTS generation
"""

import os
import sys
import json
import time
import asyncio
import logging
import httpx
import torch
import numpy as np
import re
import wave
import io
from typing import Dict, Any, Optional, List

from src.utils.config import config

# Setup logging
tts_logger = logging.getLogger("orpheus_tts")
tts_logger.setLevel(logging.INFO)

class OrpheusTTSEngine:
    """
    Orpheus TTS Engine - Connects to Orpheus-FastAPI server
    Sends text to Orpheus-FastAPI and receives audio back
    """
    
    def __init__(self):
        self.is_initialized = False
        self.orpheus_server_url = "http://localhost:1234"  # Default Orpheus-FastAPI port
        self.sample_rate = 24000
        self.snac_model = None  # Will be loaded during initialization
        
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
        
        tts_logger.info(f"OrpheusTTSEngine initialized for Orpheus-FastAPI at {self.orpheus_server_url}")
        tts_logger.info(f"🎯 Default voice: {self.default_voice}")
    
    async def initialize(self):
        """Initialize the Orpheus TTS Engine"""
        try:
            tts_logger.info("🚀 Initializing Orpheus TTS Engine...")
            start_time = time.time()
            
            # Test connection to Orpheus-FastAPI server
            connection_ok = await self._test_orpheus_connection()
            
            if connection_ok:
                # Initialize SNAC model for audio conversion
                try:
                    from snac import SNAC
                    tts_logger.info("📥 Loading SNAC model for audio conversion...")
                    self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
                    if torch.cuda.is_available():
                        self.snac_model = self.snac_model.cuda()
                    tts_logger.info("✅ SNAC model loaded successfully")
                except ImportError:
                    tts_logger.warning("⚠️ SNAC model not available, will use text-only mode")
                    self.snac_model = None
                except Exception as e:
                    tts_logger.warning(f"⚠️ SNAC model loading failed: {e}")
                    self.snac_model = None
            
            self.is_initialized = connection_ok
            init_time = time.time() - start_time
            tts_logger.info(f"🎉 Orpheus TTS Engine initialized in {init_time:.2f}s")
            
        except Exception as e:
            tts_logger.error(f"❌ Failed to initialize Orpheus TTS Engine: {e}")
            # Don't raise - allow fallback TTS to work
            self.is_initialized = False
    
    async def _test_orpheus_connection(self):
        """Test connection to Orpheus-FastAPI server"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test the models endpoint (llama-cpp-python standard endpoint)
                response = await client.get(f"{self.orpheus_server_url}/v1/models")
                if response.status_code == 200:
                    tts_logger.info("✅ Connected to Orpheus-FastAPI server")
                    return True
                else:
                    tts_logger.warning(f"⚠️ Orpheus-FastAPI server returned status {response.status_code}")
                    return False
        except Exception as e:
            tts_logger.warning(f"⚠️ Cannot connect to Orpheus-FastAPI server: {e}")
            tts_logger.info("💡 Make sure Orpheus-FastAPI is running on port 1234")
            return False
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get TTS model information"""
        return {
            "engine": "Orpheus-FastAPI",
            "server_url": self.orpheus_server_url,
            "sample_rate": self.sample_rate,
            "available_voices": len(self.available_voices),
            "default_voice": self.default_voice,
            "initialized": self.is_initialized
        }
    
    async def close(self):
        """Cleanup resources"""
        # No persistent HTTP client to close since we use context managers
        pass
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return self.available_voices.copy()
    
    async def generate_audio(self, text: str, voice: str = None) -> Optional[bytes]:
        """
        Generate audio from text using Orpheus-FastAPI ONLY (no fallback)
        """
        voice = voice or self.default_voice
        tts_logger.info(f"🎵 Generating audio for text: '{text[:50]}...' with voice '{voice}'")
        
        if not self.is_initialized:
            tts_logger.error("❌ Orpheus-FastAPI not initialized - cannot generate audio")
            return None
        
        try:
            # Use ONLY Orpheus-FastAPI (no fallback as requested)
            audio_data = await self._generate_with_orpheus_fastapi(text, voice)
            if audio_data:
                tts_logger.info(f"✅ Audio generated with Orpheus-FastAPI ({len(audio_data)} bytes)")
                return audio_data
            else:
                tts_logger.error("❌ Orpheus-FastAPI failed to generate audio")
                return None
                
        except Exception as e:
            tts_logger.error(f"❌ Error generating audio with Orpheus-FastAPI: {e}")
            return None
    

    
    async def _generate_with_orpheus_fastapi(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate audio using Orpheus-FastAPI server
        """
        try:
            # Create new HTTP client for each request to avoid event loop issues
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Format prompt specifically for Orpheus TTS model to generate audio tokens
                # The key is to use the correct format that triggers audio token generation
                prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nGenerate speech for the voice '{voice}' saying: \"{text}\"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{voice}: <|audio|>"
                
                # Prepare completion request payload for llama-cpp-python server
                payload = {
                    "prompt": prompt,
                    "max_tokens": 1024,  # Increased for audio tokens
                    "temperature": 0.3,  # Lower temperature for more consistent audio generation
                    "stream": False,
                    "stop": ["<|eot_id|>"],
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
                
                tts_logger.info(f"🌐 Sending TTS request to Orpheus-FastAPI")
                tts_logger.debug(f"🎯 Prompt: {prompt[:100]}...")
                
                # Send request to llama-cpp-python completion endpoint
                response = await client.post(
                    f"{self.orpheus_server_url}/v1/completions",
                    json=payload,
                    timeout=60.0  # Increased timeout for audio generation
                )
                
                if response.status_code == 200:
                    # Parse completion response
                    result = response.json()
                    generated_text = result.get("choices", [{}])[0].get("text", "")
                    
                    tts_logger.info(f"🎯 Generated text from Orpheus: {generated_text[:100]}...")
                    
                    # Convert generated text to audio using SNAC model
                    audio_data = await self._convert_orpheus_text_to_audio(generated_text, voice)
                    
                    if audio_data:
                        tts_logger.info(f"🎵 Generated audio from Orpheus-FastAPI ({len(audio_data)} bytes)")
                        return audio_data
                    else:
                        tts_logger.warning("⚠️ Failed to convert Orpheus text to audio")
                        return None
                else:
                    tts_logger.error(f"❌ Orpheus-FastAPI returned status {response.status_code}")
                    try:
                        error_text = response.text
                        tts_logger.error(f"❌ Error details: {error_text}")
                    except:
                        pass
                    return None
                
        except httpx.ConnectError:
            tts_logger.warning("⚠️ Cannot connect to Orpheus-FastAPI server")
            tts_logger.info("💡 Make sure Orpheus-FastAPI is running on port 1234")
            return None
        except Exception as e:
            tts_logger.error(f"❌ Orpheus-FastAPI communication failed: {e}")
            return None
    
    async def _convert_orpheus_text_to_audio(self, generated_text: str, voice: str) -> Optional[bytes]:
        """
        Convert Orpheus-generated text to audio using SNAC model
        """
        try:
            # Extract audio tokens from the generated text
            tokens = self._extract_audio_tokens(generated_text)
            
            if not tokens:
                tts_logger.warning("⚠️ No audio tokens found in Orpheus output")
                return None
            
            if not self.snac_model:
                tts_logger.warning("⚠️ SNAC model not available, cannot convert tokens to audio")
                return None
            
            # Convert tokens to audio using SNAC
            audio_data = self._tokens_to_audio(tokens)
            
            if audio_data:
                # Convert raw audio to WAV format
                wav_data = self._create_wav_from_raw_audio(audio_data)
                return wav_data
            else:
                return None
                
        except Exception as e:
            tts_logger.error(f"❌ Error converting Orpheus text to audio: {e}")
            return None
    
    def _extract_audio_tokens(self, text: str) -> List[int]:
        """Extract audio tokens from Orpheus-generated text"""
        tokens = []
        
        tts_logger.debug(f"🔍 Analyzing Orpheus output: {text[:200]}...")
        
        # Look for various token patterns that Orpheus might generate
        patterns = [
            r'<custom_token_(\d+)>',  # Standard format
            r'<audio_token_(\d+)>',   # Alternative format
            r'<token_(\d+)>',         # Simplified format
            r'<(\d+)>',               # Minimal format
            r'\[(\d+)\]',             # Bracket format
            r'token_(\d+)',           # Plain format
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    token_id = int(match)
                    if 0 <= token_id <= 4096:  # Valid SNAC token range
                        tokens.append(token_id)
                except ValueError:
                    continue
        
        # If no tokens found, try to extract any numbers that might be tokens
        if not tokens:
            tts_logger.warning("⚠️ No standard tokens found, trying to extract any numbers...")
            number_matches = re.findall(r'\b(\d{1,4})\b', text)
            for match in number_matches:
                try:
                    token_id = int(match)
                    if 0 <= token_id <= 4096:
                        tokens.append(token_id)
                except ValueError:
                    continue
        
        # Remove duplicates while preserving order
        tokens = list(dict.fromkeys(tokens))
        
        tts_logger.info(f"🔍 Extracted {len(tokens)} audio tokens from Orpheus output")
        if tokens:
            tts_logger.debug(f"🎵 First few tokens: {tokens[:10]}")
        else:
            tts_logger.warning(f"⚠️ Full Orpheus output for debugging: {text}")
        
        return tokens
    
    def _tokens_to_audio(self, tokens: List[int]) -> Optional[bytes]:
        """Convert token list to audio using SNAC model"""
        if len(tokens) < 7:
            return None
        
        try:
            # Group tokens into frames (7 tokens per frame for SNAC)
            num_frames = len(tokens) // 7
            frame_tokens = tokens[:num_frames * 7]
            
            # Convert to SNAC format
            device = next(self.snac_model.parameters()).device
            
            # Create SNAC codes (simplified version)
            codes_0 = torch.tensor([frame_tokens[i*7] for i in range(num_frames)], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            codes_1 = torch.tensor([frame_tokens[i*7+1] for i in range(num_frames)] + 
                                 [frame_tokens[i*7+4] for i in range(num_frames)], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            codes_2 = torch.tensor([frame_tokens[i*7+j] for i in range(num_frames) for j in [2,3,5,6]], 
                                 dtype=torch.int32, device=device).unsqueeze(0)
            
            codes = [codes_0, codes_1, codes_2]
            
            # Decode audio using SNAC
            with torch.inference_mode():
                audio_hat = self.snac_model.decode(codes)
                audio_slice = audio_hat[:, :, 2048:4096]  # Extract relevant slice
                
                # Convert to bytes
                if device.type == "cuda":
                    audio_int16_tensor = (audio_slice * 32767).to(torch.int16)
                    audio_bytes = audio_int16_tensor.cpu().numpy().tobytes()
                else:
                    audio_np = audio_slice.detach().cpu().numpy()
                    audio_int16 = (audio_np * 32767).astype(np.int16)
                    audio_bytes = audio_int16.tobytes()
                
                return audio_bytes
                
        except Exception as e:
            tts_logger.error(f"❌ Error in SNAC audio conversion: {e}")
            return None
    
    def _create_wav_from_raw_audio(self, raw_audio: bytes) -> bytes:
        """Create WAV file from raw audio bytes"""
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)  # 24kHz
                wav_file.writeframes(raw_audio)
            
            return wav_buffer.getvalue()
        except Exception as e:
            tts_logger.error(f"❌ Error creating WAV file: {e}")
            return raw_audio  # Return raw audio as fallback
    
    def _get_language_for_voice(self, voice: str) -> str:
        """Get language code for voice"""
        voice_language_map = {
            "ऋतिका": "hi",  # Hindi
            "tara": "en", "leah": "en", "jess": "en", "leo": "en", 
            "dan": "en", "mia": "en", "zac": "en", "zoe": "en",  # English
            "pierre": "fr", "amelie": "fr", "marie": "fr",  # French
            "jana": "de", "thomas": "de", "max": "de",  # German
            "유나": "ko", "준서": "ko",  # Korean
            "长乐": "zh", "白芷": "zh",  # Mandarin
            "javi": "es", "sergio": "es", "maria": "es",  # Spanish
            "pietro": "it", "giulia": "it", "carlo": "it"  # Italian
        }
        return voice_language_map.get(voice, "en")




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
