"""
TTS (Text-to-Speech) module for Voxtral integration
Integrates Orpheus-FastAPI TTS engine for high-quality speech synthesis
"""

from .orpheus_perfect_model import OrpheusPerfectModel
from .tts_service_perfect import TTSServicePerfect
from .tts_service import TTSService

__all__ = ['OrpheusTTSEngine', 'TTSService']
