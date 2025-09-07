"""
Audio processing module for Voxtral Real-time Streaming (FIXED)
Fixed mel filterbank configuration to eliminate warnings
"""
import numpy as np
import librosa
import torch
import torchaudio
from typing import Tuple, Optional
import logging
from src.utils.config import config

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio preprocessing for Voxtral model"""
    
    def __init__(self):
        self.sample_rate = config.audio.sample_rate
        self.n_mels = config.spectrogram.n_mels
        self.hop_length = config.spectrogram.hop_length
        self.win_length = config.spectrogram.win_length
        self.n_fft = config.spectrogram.n_fft
        
        # FIXED: Ensure n_fft is sufficient for n_mels
        min_n_fft = 2 * (self.n_mels - 1)
        if self.n_fft < min_n_fft:
            self.n_fft = 1024  # Use 1024 for 128 mel bins
            logger.info(f"Adjusted n_fft to {self.n_fft} to accommodate {self.n_mels} mel bins")
        
        # Initialize mel spectrogram transform (matching Voxtral architecture)
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            n_fft=self.n_fft,
            win_length=min(self.win_length, self.n_fft),
            hop_length=self.hop_length,
            n_mels=self.n_mels,
            power=2.0,
            f_min=0.0,
            f_max=self.sample_rate // 2,
            norm='slaney',
            mel_scale='htk'
        )
        
        logger.info(f"AudioProcessor initialized with sample_rate={self.sample_rate}, n_mels={self.n_mels}, n_fft={self.n_fft}")
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: Optional[int] = None) -> torch.Tensor:
        """
        Preprocess audio data for Voxtral model
        
        Args:
            audio_data: Raw audio data as numpy array
            sample_rate: Sample rate of input audio
            
        Returns:
            Preprocessed audio tensor ready for Voxtral
        """
        try:
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio to [-1, 1] range
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Resample if necessary
            if sample_rate and sample_rate != self.sample_rate:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=self.sample_rate
                )
            
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_data).float()
            
            # Ensure mono audio
            if len(audio_tensor.shape) > 1:
                audio_tensor = torch.mean(audio_tensor, dim=0)
            
            return audio_tensor
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            raise
    
    def generate_log_mel_spectrogram(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """
        Generate log-mel spectrogram from audio tensor
        This matches Voxtral's expected input format
        
        Args:
            audio_tensor: Preprocessed audio tensor
            
        Returns:
            Log-mel spectrogram tensor
        """
        try:
            # Ensure audio tensor has the right shape
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)  # Add batch dimension
            
            # Generate mel spectrogram
            mel_spec = self.mel_transform(audio_tensor)
            
            # Convert to log scale (matching Voxtral preprocessing)
            log_mel_spec = torch.log(mel_spec + 1e-8)
            
            return log_mel_spec.squeeze(0)  # Remove batch dimension
            
        except Exception as e:
            logger.error(f"Error generating log-mel spectrogram: {e}")
            raise
    
    def chunk_audio(self, audio_tensor: torch.Tensor, chunk_duration: float = 30.0) -> list:
        """
        Chunk audio into segments for processing
        Voxtral processes 30-second chunks by default
        
        Args:
            audio_tensor: Input audio tensor
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            List of audio chunks
        """
        try:
            chunk_samples = int(chunk_duration * self.sample_rate)
            chunks = []
            
            for start_idx in range(0, len(audio_tensor), chunk_samples):
                end_idx = min(start_idx + chunk_samples, len(audio_tensor))
                chunk = audio_tensor[start_idx:end_idx]
                
                # Pad chunk to exact size if needed
                if len(chunk) < chunk_samples:
                    padding = chunk_samples - len(chunk)
                    chunk = torch.cat([chunk, torch.zeros(padding)])
                
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking audio: {e}")
            raise
    
    def process_streaming_audio(self, audio_chunk: np.ndarray) -> torch.Tensor:
        """
        Process streaming audio chunk for real-time inference
        
        Args:
            audio_chunk: Raw audio chunk from stream
            
        Returns:
            Processed audio tensor ready for model
        """
        try:
            # Just preprocess the chunk - Voxtral will handle spectrogram internally
            audio_tensor = self.preprocess_audio(audio_chunk)
            return audio_tensor
            
        except Exception as e:
            logger.error(f"Error processing streaming audio: {e}")
            raise
    
    def validate_audio_format(self, audio_data: np.ndarray) -> bool:
        """
        Validate audio format meets requirements
        
        Args:
            audio_data: Audio data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if audio data is not empty
            if len(audio_data) == 0:
                return False
            
            # Check for NaN or infinite values
            if np.any(np.isnan(audio_data)) or np.any(np.isinf(audio_data)):
                return False
            
            # Check reasonable amplitude range
            if np.max(np.abs(audio_data)) < 1e-10:
                return False
            
            # Check for reasonable audio length (at least 0.1 seconds)
            min_samples = int(0.1 * self.sample_rate)
            if len(audio_data) < min_samples:
                logger.warning(f"Audio too short: {len(audio_data)} samples, minimum: {min_samples}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating audio format: {e}")
            return False
