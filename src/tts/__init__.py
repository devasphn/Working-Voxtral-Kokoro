"""
TTS (Text-to-Speech) module for Voxtral integration
Integrates Orpheus-FastAPI TTS engine for high-quality speech synthesis
"""

from .orpheus_tts_engine import OrpheusTTSEngine
from .tts_service import TTSService

__all__ = ['OrpheusTTSEngine', 'TTSService']
