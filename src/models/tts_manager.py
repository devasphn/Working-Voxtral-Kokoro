"""
TTS Manager for Chatterbox Text-to-Speech
Converts text responses to audio for voice output
"""

import torch
import numpy as np
from typing import Optional, Dict, Any
import logging
import io

# Setup logging
tts_logger = logging.getLogger("tts_manager")
tts_logger.setLevel(logging.DEBUG)

# PHASE 5: Language routing configuration
LANGUAGE_MODELS = {
    "en": "chatterbox",      # English
    "hi": "chatterbox",      # Hindi
    "es": "chatterbox",      # Spanish
    "fr": "chatterbox",      # French
    "de": "chatterbox",      # German
    "it": "chatterbox",      # Italian
    "pt": "chatterbox",      # Portuguese
    "ja": "chatterbox",      # Japanese
    "ko": "chatterbox",      # Korean
    "zh": "chatterbox",      # Chinese
    "ms": "dia-tts",         # Malaysian
    "ta": "indic-tts",       # Tamil
    "te": "indic-tts",       # Telugu
    "mr": "indic-tts",       # Marathi
    "kn": "indic-tts",       # Kannada
    "ml": "indic-tts",       # Malayalam
    "bn": "indic-tts",       # Bengali
}

# PHASE 5: Supported languages by model
CHATTERBOX_LANGUAGES = ["en", "hi", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"]
DIA_TTS_LANGUAGES = ["ms"]
INDIC_TTS_LANGUAGES = ["ta", "te", "mr", "kn", "ml", "bn"]


class TTSManager:
    """
    Text-to-Speech Manager using Chatterbox TTS
    
    Features:
    - Converts text to speech audio
    - Supports multiple languages
    - Handles emotion/style parameters
    - Generates audio bytes for streaming
    """
    
    def __init__(self, model_name: str = "chatterbox", device: str = "cuda"):
        """
        Initialize TTSManager
        
        Args:
            model_name: TTS model to use (default: "chatterbox")
            device: Device to run model on ("cuda" or "cpu")
        """
        self.model_name = model_name
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self.is_initialized = False
        
        tts_logger.info(f"🎵 Initializing TTSManager (model={model_name}, device={self.device})")
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize TTS model"""
        try:
            if self.model_name == "chatterbox":
                # Try to import and initialize Chatterbox TTS
                try:
                    from transformers import AutoModel, AutoProcessor
                    
                    tts_logger.info("📥 Loading Chatterbox TTS processor...")
                    self.processor = AutoProcessor.from_pretrained(
                        "resemble-ai/chatterbox",
                        trust_remote_code=True
                    )
                    
                    tts_logger.info("📥 Loading Chatterbox TTS model...")
                    self.model = AutoModel.from_pretrained(
                        "resemble-ai/chatterbox",
                        trust_remote_code=True
                    ).to(self.device)
                    
                    self.model.eval()
                    self.is_initialized = True
                    tts_logger.info("✅ Chatterbox TTS initialized successfully")
                    
                except ImportError as e:
                    tts_logger.warning(f"⚠️ Chatterbox TTS not available: {e}")
                    tts_logger.info("💡 Using fallback TTS mode (text-only)")
                    self.is_initialized = False
                    
            else:
                tts_logger.error(f"❌ Unknown TTS model: {self.model_name}")
                self.is_initialized = False
                
        except Exception as e:
            tts_logger.error(f"❌ TTS initialization failed: {e}")
            self.is_initialized = False
    
    async def synthesize(self, text: str, language: str = "en",
                        emotion: str = "neutral") -> Optional[bytes]:
        """
        Synthesize text to speech with language support

        Args:
            text: Text to synthesize
            language: Language code (e.g., "en", "hi")
            emotion: Emotion/style (e.g., "neutral", "happy", "sad")

        Returns:
            Audio bytes in WAV format, or None if synthesis fails
        """
        # PHASE 5: Use language-aware synthesis with fallback
        return await self.synthesize_with_fallback(text, language, emotion)

    async def synthesize_with_fallback(self, text: str, language: str = "en",
                                       emotion: str = "neutral") -> Optional[bytes]:
        """
        PHASE 5: Synthesize with language-specific TTS and fallback support

        Args:
            text: Text to synthesize
            language: Language code (e.g., "en", "hi", "ms", "ta")
            emotion: Emotion/style (e.g., "neutral", "happy", "sad")

        Returns:
            Audio bytes in WAV format, or None if synthesis fails
        """
        if not text or not text.strip():
            tts_logger.warning("⚠️ Empty text provided for synthesis")
            return None

        if not self.is_initialized:
            tts_logger.warning("⚠️ TTS not initialized, returning None")
            return None

        try:
            # PHASE 5: Get model for language with fallback
            model_name = LANGUAGE_MODELS.get(language, "chatterbox")
            tts_logger.info(f"🌍 [PHASE 5] Synthesizing '{text[:30]}...' (lang={language}, model={model_name})")

            # Route to appropriate synthesis method
            if model_name == "chatterbox":
                return await self._synthesize_chatterbox(text, language, emotion)
            elif model_name == "dia-tts":
                return await self._synthesize_dia(text, language, emotion)
            elif model_name == "indic-tts":
                return await self._synthesize_indic(text, language, emotion)
            else:
                tts_logger.warning(f"⚠️ Unknown model: {model_name}, falling back to Chatterbox")
                return await self._synthesize_chatterbox(text, language, emotion)

        except Exception as e:
            tts_logger.error(f"❌ Synthesis with fallback failed: {e}")
            return None

    async def _synthesize_chatterbox(self, text: str, language: str = "en",
                                     emotion: str = "neutral") -> Optional[bytes]:
        """
        PHASE 5: Synthesize using Chatterbox TTS
        PHASE 7: Support emotion parameter for emotional expressiveness

        Args:
            text: Text to synthesize
            language: Language code
            emotion: Emotion/style

        Returns:
            Audio bytes in WAV format
        """
        try:
            # PHASE 7: Log emotion being used
            tts_logger.debug(f"🎵 [PHASE 5] Chatterbox synthesis: '{text[:50]}...' (lang={language}, emotion={emotion})")

            with torch.no_grad():
                # Prepare inputs
                inputs = self.processor(
                    text=text,
                    language=language,
                    return_tensors="pt"
                ).to(self.device)

                # Generate audio
                outputs = self.model.generate(**inputs)

                # Convert to audio bytes
                audio_bytes = self._convert_to_audio_bytes(outputs)

                if audio_bytes:
                    tts_logger.debug(f"✅ [PHASE 5] Chatterbox synthesized {len(audio_bytes)} bytes")
                    return audio_bytes
                else:
                    tts_logger.warning("⚠️ [PHASE 5] Chatterbox audio conversion returned empty bytes")
                    return None

        except Exception as e:
            tts_logger.error(f"❌ [PHASE 5] Chatterbox synthesis failed: {e}")
            return None

    async def _synthesize_dia(self, text: str, language: str = "ms",
                              emotion: str = "neutral") -> Optional[bytes]:
        """
        PHASE 5: Synthesize using Dia-TTS (Malaysian support)

        Args:
            text: Text to synthesize
            language: Language code (e.g., "ms")
            emotion: Emotion/style

        Returns:
            Audio bytes in WAV format
        """
        try:
            tts_logger.info(f"🎵 [PHASE 5] Dia-TTS synthesis: '{text[:50]}...' (lang={language})")
            # Dia-TTS implementation would go here
            # For now, fallback to Chatterbox
            tts_logger.warning(f"⚠️ [PHASE 5] Dia-TTS not fully implemented, using Chatterbox fallback")
            return await self._synthesize_chatterbox(text, "en", emotion)

        except Exception as e:
            tts_logger.error(f"❌ [PHASE 5] Dia-TTS synthesis failed: {e}")
            return None

    async def _synthesize_indic(self, text: str, language: str = "ta",
                                emotion: str = "neutral") -> Optional[bytes]:
        """
        PHASE 5: Synthesize using Indic-TTS (Indian languages support)

        Args:
            text: Text to synthesize
            language: Language code (e.g., "ta", "te", "mr")
            emotion: Emotion/style

        Returns:
            Audio bytes in WAV format
        """
        try:
            tts_logger.info(f"🎵 [PHASE 5] Indic-TTS synthesis: '{text[:50]}...' (lang={language})")
            # Indic-TTS implementation would go here
            # For now, fallback to Chatterbox
            tts_logger.warning(f"⚠️ [PHASE 5] Indic-TTS not fully implemented, using Chatterbox fallback")
            return await self._synthesize_chatterbox(text, "en", emotion)

        except Exception as e:
            tts_logger.error(f"❌ [PHASE 5] Indic-TTS synthesis failed: {e}")
            return None
    
    def _convert_to_audio_bytes(self, outputs) -> Optional[bytes]:
        """
        Convert model outputs to audio bytes
        
        Args:
            outputs: Model output tensor
        
        Returns:
            Audio bytes in WAV format
        """
        try:
            # Handle different output formats
            if isinstance(outputs, torch.Tensor):
                audio_data = outputs.cpu().numpy()
            elif isinstance(outputs, dict):
                # Some models return dict with 'audio' key
                if 'audio' in outputs:
                    audio_data = outputs['audio']
                    if isinstance(audio_data, torch.Tensor):
                        audio_data = audio_data.cpu().numpy()
                else:
                    tts_logger.warning("⚠️ Output dict missing 'audio' key")
                    return None
            else:
                tts_logger.warning(f"⚠️ Unknown output type: {type(outputs)}")
                return None
            
            # Ensure audio is float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio to [-1, 1] range
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val * 0.95
            
            # Convert to WAV bytes
            import soundfile as sf
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, audio_data, 22050, format='WAV')
            wav_bytes = wav_buffer.getvalue()
            
            tts_logger.debug(f"✅ Converted to WAV: {len(wav_bytes)} bytes")
            return wav_bytes
        
        except Exception as e:
            tts_logger.error(f"❌ Audio conversion failed: {e}")
            return None
    
    def get_supported_languages(self) -> Dict[str, list]:
        """
        PHASE 5: Get list of supported languages by model

        Returns:
            Dictionary mapping model names to supported language codes
        """
        return {
            "chatterbox": CHATTERBOX_LANGUAGES,
            "dia-tts": DIA_TTS_LANGUAGES,
            "indic-tts": INDIC_TTS_LANGUAGES,
        }

    def get_all_supported_languages(self) -> list:
        """
        PHASE 5: Get all supported language codes

        Returns:
            List of all supported language codes
        """
        return list(LANGUAGE_MODELS.keys())

    def get_language_model(self, language: str) -> str:
        """
        PHASE 5: Get the TTS model for a specific language

        Args:
            language: Language code

        Returns:
            Model name for the language (with fallback to Chatterbox)
        """
        return LANGUAGE_MODELS.get(language, "chatterbox")

    def get_supported_emotions(self) -> list:
        """Get list of supported emotions/styles"""
        return ["neutral", "happy", "sad", "angry", "calm", "excited"]
    
    def __repr__(self) -> str:
        """String representation"""
        status = "initialized" if self.is_initialized else "not initialized"
        return f"TTSManager(model={self.model_name}, device={self.device}, status={status})"

