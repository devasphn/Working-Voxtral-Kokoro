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
from typing import Dict, Any, Optional

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
        
        # HTTP client for Orpheus-FastAPI communication
        self.http_client = None
        
        tts_logger.info(f"OrpheusTTSEngine initialized for Orpheus-FastAPI at {self.orpheus_server_url}")
        tts_logger.info(f"🎯 Default voice: {self.default_voice}")
    
    async def initialize(self):
        """Initialize the Orpheus TTS Engine"""
        try:
            tts_logger.info("🚀 Initializing Orpheus TTS Engine...")
            start_time = time.time()
            
            # Initialize HTTP client for Orpheus-FastAPI communication
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
            # Test connection to Orpheus-FastAPI server
            await self._test_orpheus_connection()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            tts_logger.info(f"🎉 Orpheus TTS Engine initialized in {init_time:.2f}s")
            
        except Exception as e:
            tts_logger.error(f"❌ Failed to initialize Orpheus TTS Engine: {e}")
            # Don't raise - allow fallback TTS to work
            self.is_initialized = False
    
    async def _test_orpheus_connection(self):
        """Test connection to Orpheus-FastAPI server"""
        try:
            response = await self.http_client.get(f"{self.orpheus_server_url}/health")
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
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()
    
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
            # Try Orpheus-FastAPI first
            if self.is_initialized and self.http_client:
                audio_data = await self._generate_with_orpheus_fastapi(text, voice)
                if audio_data:
                    tts_logger.info(f"✅ Audio generated with Orpheus-FastAPI ({len(audio_data)} bytes)")
                    return audio_data
                else:
                    tts_logger.warning("⚠️ Orpheus-FastAPI failed, trying fallback...")
            
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
            # Prepare request payload for Orpheus-FastAPI
            payload = {
                "text": text,
                "voice": voice,
                "language": self._get_language_for_voice(voice),
                "speed": 1.0,
                "pitch": 1.0
            }
            
            tts_logger.info(f"🌐 Sending request to Orpheus-FastAPI: {payload}")
            
            # Send request to Orpheus-FastAPI
            response = await self.http_client.post(
                f"{self.orpheus_server_url}/generate_speech",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # Check if response is JSON (error) or binary (audio)
                content_type = response.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    # Error response
                    error_data = response.json()
                    tts_logger.error(f"❌ Orpheus-FastAPI error: {error_data}")
                    return None
                elif "audio" in content_type or "application/octet-stream" in content_type:
                    # Audio response
                    audio_data = response.content
                    tts_logger.info(f"🎵 Received audio from Orpheus-FastAPI ({len(audio_data)} bytes)")
                    return audio_data
                else:
                    # Try to treat as audio anyway
                    audio_data = response.content
                    if len(audio_data) > 44:  # Minimum WAV file size
                        tts_logger.info(f"🎵 Received audio from Orpheus-FastAPI ({len(audio_data)} bytes)")
                        return audio_data
                    else:
                        tts_logger.warning("⚠️ Received data too small to be audio")
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
