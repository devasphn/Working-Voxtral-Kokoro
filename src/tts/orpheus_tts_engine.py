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
        Generate audio from text using Orpheus-FastAPI
        """
        voice = voice or self.default_voice
        tts_logger.info(f"🎵 Generating audio for text: '{text[:50]}...' with voice '{voice}'")
        
        try:
            # Try Orpheus-FastAPI first if initialized
            if self.is_initialized:
                audio_data = await self._generate_with_orpheus_fastapi(text, voice)
                if audio_data:
                    tts_logger.info(f"✅ Audio generated with Orpheus-FastAPI ({len(audio_data)} bytes)")
                    return audio_data
                else:
                    tts_logger.warning("⚠️ Orpheus-FastAPI failed, trying fallback...")
            else:
                tts_logger.info("ℹ️ Orpheus-FastAPI not initialized, using fallback TTS")
            
            # Fallback to espeak-ng if Orpheus-FastAPI fails
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
    
    async def _generate_with_orpheus_fastapi(self, text: str, voice: str) -> Optional[bytes]:
        """
        Generate audio using Orpheus-FastAPI server
        """
        try:
            # Create new HTTP client for each request to avoid event loop issues
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Format prompt for Orpheus TTS model
                prompt = f"{voice}: {text}"
                
                # Prepare completion request payload for llama-cpp-python server
                payload = {
                    "prompt": prompt,
                    "max_tokens": 512,
                    "temperature": 0.7,
                    "stream": False,
                    "stop": ["<|eot_id|>", "\n\n"]
                }
                
                tts_logger.info(f"🌐 Sending completion request to Orpheus-FastAPI: {payload}")
                
                # Send request to llama-cpp-python completion endpoint
                response = await client.post(
                    f"{self.orpheus_server_url}/v1/completions",
                    json=payload,
                    timeout=30.0
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
        
        # Look for custom token patterns like <custom_token_1234>
        token_pattern = r'<custom_token_(\d+)>'
        matches = re.findall(token_pattern, text)
        
        for match in matches:
            try:
                token_id = int(match)
                tokens.append(token_id)
            except ValueError:
                continue
        
        tts_logger.info(f"🔍 Extracted {len(tokens)} audio tokens from Orpheus output")
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
