"""
FIXED Enhanced Audio processor for REAL-TIME streaming 
Fixed import paths and optimized for continuous chunk processing
"""
import numpy as np
import librosa
import torch
import torchaudio
from typing import Tuple, Optional
import logging
from collections import deque
import time
import sys
import os

# Add current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.config import config

# Enhanced logging for real-time audio processing
audio_logger = logging.getLogger("realtime_audio")
audio_logger.setLevel(logging.DEBUG)

class AudioProcessor:
    """Enhanced audio processor optimized for real-time streaming"""
    
    def __init__(self):
        self.sample_rate = config.audio.sample_rate
        self.n_mels = config.spectrogram.n_mels
        self.hop_length = config.spectrogram.hop_length
        self.win_length = config.spectrogram.win_length
        self.n_fft = config.spectrogram.n_fft
        
        # Real-time processing metrics
        self.processing_history = deque(maxlen=100)
        self.chunk_counter = 0
        
        # Ensure n_fft is sufficient for n_mels
        min_n_fft = 2 * (self.n_mels - 1)
        if self.n_fft < min_n_fft:
            self.n_fft = 1024
            audio_logger.info(f"📈 Adjusted n_fft to {self.n_fft} to accommodate {self.n_mels} mel bins")
        
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
        
        audio_logger.info(f"🔊 AudioProcessor initialized for real-time streaming:")
        audio_logger.info(f"   📊 Sample rate: {self.sample_rate} Hz")
        audio_logger.info(f"   🎵 Mel bins: {self.n_mels}")
        audio_logger.info(f"   📐 FFT size: {self.n_fft}")
        audio_logger.info(f"   ⏱️  Hop length: {self.hop_length}")
        audio_logger.info(f"   🪟 Window length: {self.win_length}")
    
    def preprocess_realtime_chunk(self, audio_data: np.ndarray, chunk_id: int = None, sample_rate: Optional[int] = None) -> torch.Tensor:
        """
        Enhanced preprocessing specifically optimized for real-time audio chunks
        
        Args:
            audio_data: Raw audio data as numpy array
            chunk_id: Unique identifier for this chunk (for logging)
            sample_rate: Sample rate of input audio
            
        Returns:
            Preprocessed audio tensor ready for Voxtral
        """
        start_time = time.time()
        chunk_id = chunk_id or self.chunk_counter
        self.chunk_counter += 1
        
        try:
            audio_logger.debug(f"🎵 Processing real-time audio chunk {chunk_id}")
            audio_logger.debug(f"   📏 Input shape: {audio_data.shape}")
            audio_logger.debug(f"   📊 Input dtype: {audio_data.dtype}")
            audio_logger.debug(f"   📈 Input range: [{np.min(audio_data):.4f}, {np.max(audio_data):.4f}]")
            
            # Ensure audio_data is writeable
            if not audio_data.flags.writeable:
                audio_data = audio_data.copy()
                audio_logger.debug(f"   🔧 Made audio data writeable for chunk {chunk_id}")
            
            # Convert to float32 if needed
            if audio_data.dtype != np.float32:
                original_dtype = audio_data.dtype
                audio_data = audio_data.astype(np.float32)
                audio_logger.debug(f"   🔄 Converted dtype from {original_dtype} to float32")
            
            # Check for invalid values
            nan_count = np.sum(np.isnan(audio_data))
            inf_count = np.sum(np.isinf(audio_data))
            if nan_count > 0 or inf_count > 0:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} has {nan_count} NaN and {inf_count} infinite values - cleaning")
                audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)
            
            # Normalize audio to [-1, 1] range with enhanced handling for real-time
            max_val = np.max(np.abs(audio_data))
            audio_logger.debug(f"   📊 Max amplitude: {max_val:.6f}")
            
            if max_val > 1.0:
                audio_data = audio_data / max_val
                audio_logger.debug(f"   🔧 Normalized loud audio (max: {max_val:.4f}) for chunk {chunk_id}")
            elif max_val < 1e-8:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} is very quiet (max: {max_val:.2e}), amplifying carefully")
                # More conservative amplification for real-time
                audio_data = audio_data * 100.0
                audio_data = np.clip(audio_data, -1.0, 1.0)
            elif max_val < 1e-4:
                audio_logger.debug(f"   🔊 Quiet audio detected (max: {max_val:.6f}), gentle amplification")
                audio_data = audio_data * 10.0
                audio_data = np.clip(audio_data, -1.0, 1.0)
            
            # Resample if necessary (real-time optimized)
            if sample_rate and sample_rate != self.sample_rate:
                audio_logger.info(f"🔄 Resampling chunk {chunk_id} from {sample_rate}Hz to {self.sample_rate}Hz")
                resample_start = time.time()
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=self.sample_rate,
                    res_type='fast'  # Fast resampling for real-time
                )
                resample_time = (time.time() - resample_start) * 1000
                audio_logger.debug(f"   ⚡ Resampling completed in {resample_time:.1f}ms")
            
            # Create tensor with explicit copy for writeability
            audio_tensor = torch.from_numpy(audio_data.copy()).float()
            
            # Ensure mono audio
            if len(audio_tensor.shape) > 1:
                audio_tensor = torch.mean(audio_tensor, dim=0)
                audio_logger.debug(f"   🎵 Converted to mono audio for chunk {chunk_id}")
            
            # Ensure tensor is contiguous
            if not audio_tensor.is_contiguous():
                audio_tensor = audio_tensor.contiguous()
                audio_logger.debug(f"   🔧 Made tensor contiguous for chunk {chunk_id}")
            
            # Calculate processing metrics
            processing_time = (time.time() - start_time) * 1000
            audio_duration_s = len(audio_tensor) / self.sample_rate
            
            # Store processing stats for monitoring
            processing_stats = {
                'chunk_id': chunk_id,
                'processing_time_ms': processing_time,
                'audio_duration_s': audio_duration_s,
                'input_samples': len(audio_data),
                'output_samples': len(audio_tensor),
                'max_amplitude': float(torch.max(torch.abs(audio_tensor))),
                'timestamp': time.time()
            }
            self.processing_history.append(processing_stats)
            
            audio_logger.info(f"✅ Chunk {chunk_id} preprocessed in {processing_time:.1f}ms ({audio_duration_s:.2f}s audio)")
            audio_logger.debug(f"   📊 Output shape: {audio_tensor.shape}")
            audio_logger.debug(f"   📈 Output range: [{torch.min(audio_tensor):.4f}, {torch.max(audio_tensor):.4f}]")
            
            return audio_tensor
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            audio_logger.error(f"❌ Error preprocessing chunk {chunk_id} after {processing_time:.1f}ms: {e}")
            raise
    
    def preprocess_audio(self, audio_data: np.ndarray, sample_rate: Optional[int] = None) -> torch.Tensor:
        """Legacy method that redirects to real-time preprocessing"""
        return self.preprocess_realtime_chunk(audio_data, sample_rate=sample_rate)
    
    def validate_realtime_chunk(self, audio_data: np.ndarray, chunk_id: int = None) -> bool:
        """
        Enhanced validation specifically for real-time audio chunks
        
        Args:
            audio_data: Audio data to validate
            chunk_id: Chunk identifier for logging
            
        Returns:
            True if valid, False otherwise
        """
        chunk_id = chunk_id or f"chunk_{int(time.time()*1000)}"
        
        try:
            audio_logger.debug(f"🔍 Validating real-time chunk {chunk_id}")
            
            # Check if audio data exists and is not empty
            if audio_data is None or len(audio_data) == 0:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} is empty")
                return False
            
            # Check for valid data types
            if not isinstance(audio_data, np.ndarray):
                audio_logger.warning(f"⚠️  Chunk {chunk_id} is not a numpy array: {type(audio_data)}")
                return False
            
            # Check for NaN or infinite values
            nan_count = np.sum(np.isnan(audio_data))
            inf_count = np.sum(np.isinf(audio_data))
            if nan_count > 0 or inf_count > 0:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} contains {nan_count} NaN and {inf_count} inf values")
                # Don't reject - we can clean these
                return True
            
            # Check amplitude range - more lenient for real-time
            max_amplitude = np.max(np.abs(audio_data))
            if max_amplitude < 1e-10:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} is silent or nearly silent (max: {max_amplitude:.2e})")
                return False
            
            if max_amplitude > 10000:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} has very high amplitude (max: {max_amplitude:.2e})")
                # Don't reject - we can normalize
            
            # Check for reasonable audio length - more permissive for real-time
            min_samples = int(0.05 * self.sample_rate)  # At least 50ms
            if len(audio_data) < min_samples:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} too short: {len(audio_data)} samples, minimum: {min_samples}")
                return False
            
            # Check for maximum length - allow up to 5 seconds for real-time chunks
            max_samples = int(5.0 * self.sample_rate)
            if len(audio_data) > max_samples:
                audio_logger.info(f"📏 Chunk {chunk_id} is long: {len(audio_data)} samples, will process anyway")
                # Don't reject - just note it
            
            # Check data variance (avoid completely flat signals)
            data_variance = np.var(audio_data)
            if data_variance < 1e-12:
                audio_logger.warning(f"⚠️  Chunk {chunk_id} has very low variance: {data_variance:.2e}")
                return False
            
            audio_logger.debug(f"✅ Chunk {chunk_id} validation passed")
            return True
            
        except Exception as e:
            audio_logger.error(f"❌ Error validating chunk {chunk_id}: {e}")
            return False
    
    def validate_audio_format(self, audio_data: np.ndarray) -> bool:
        """Legacy method that redirects to real-time validation"""
        return self.validate_realtime_chunk(audio_data)
    
    def generate_log_mel_spectrogram(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """
        Generate log-mel spectrogram optimized for real-time processing
        """
        try:
            audio_logger.debug(f"🎵 Generating log-mel spectrogram")
            start_time = time.time()
            
            # Ensure audio tensor has the right shape
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Generate mel spectrogram
            mel_spec = self.mel_transform(audio_tensor)
            
            # Convert to log scale with numerical stability
            log_mel_spec = torch.log(mel_spec + 1e-8)
            
            processing_time = (time.time() - start_time) * 1000
            audio_logger.debug(f"✅ Log-mel spectrogram generated in {processing_time:.1f}ms")
            audio_logger.debug(f"   📊 Output shape: {log_mel_spec.shape}")
            
            return log_mel_spec.squeeze(0)  # Remove batch dimension
            
        except Exception as e:
            audio_logger.error(f"❌ Error generating log-mel spectrogram: {e}")
            raise
    
    def get_processing_stats(self) -> dict:
        """Get real-time processing statistics"""
        if not self.processing_history:
            return {"message": "No processing history available"}
        
        history = list(self.processing_history)
        processing_times = [h['processing_time_ms'] for h in history]
        audio_durations = [h['audio_duration_s'] for h in history]
        
        return {
            "total_chunks_processed": len(history),
            "avg_processing_time_ms": round(np.mean(processing_times), 2),
            "min_processing_time_ms": round(np.min(processing_times), 2),
            "max_processing_time_ms": round(np.max(processing_times), 2),
            "avg_audio_duration_s": round(np.mean(audio_durations), 3),
            "total_audio_processed_s": round(np.sum(audio_durations), 2),
            "realtime_factor": round(np.mean([
                h['audio_duration_s'] / (h['processing_time_ms'] / 1000)
                for h in history if h['processing_time_ms'] > 0
            ]), 2),
            "current_chunk_counter": self.chunk_counter
        }
    
    def process_streaming_audio(self, audio_chunk: np.ndarray, chunk_id: int = None) -> torch.Tensor:
        """
        Enhanced method for processing streaming audio chunks in real-time
        """
        return self.preprocess_realtime_chunk(audio_chunk, chunk_id=chunk_id)
    
    def chunk_audio(self, audio_tensor: torch.Tensor, chunk_duration: float = 2.0) -> list:
        """
        Chunk audio for real-time processing (shorter chunks for better latency)
        """
        try:
            chunk_samples = int(chunk_duration * self.sample_rate)
            chunks = []
            
            audio_logger.debug(f"🔪 Chunking audio into {chunk_duration}s segments")
            
            for i, start_idx in enumerate(range(0, len(audio_tensor), chunk_samples)):
                end_idx = min(start_idx + chunk_samples, len(audio_tensor))
                chunk = audio_tensor[start_idx:end_idx]
                
                # Pad chunk to exact size if needed (only for the last chunk)
                if len(chunk) < chunk_samples and i > 0:
                    padding = chunk_samples - len(chunk)
                    chunk = torch.cat([chunk, torch.zeros(padding)])
                    audio_logger.debug(f"   🔧 Padded last chunk with {padding} zeros")
                
                chunks.append(chunk)
                audio_logger.debug(f"   📦 Chunk {i}: {len(chunk)} samples ({len(chunk)/self.sample_rate:.2f}s)")
            
            audio_logger.info(f"✅ Audio chunked into {len(chunks)} segments of ~{chunk_duration}s each")
            return chunks
            
        except Exception as e:
            audio_logger.error(f"❌ Error chunking audio: {e}")
            raise

# FIXED: Add proper main execution block for testing
if __name__ == "__main__":
    """Test audio processor functionality"""
    print("🧪 Testing Audio Processor...")
    
    try:
        # Initialize processor
        processor = AudioProcessor()
        
        # Test with dummy audio
        sample_rate = 16000
        duration = 1.0
        dummy_audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        dummy_audio = dummy_audio.astype(np.float32)
        
        print(f"📊 Input audio: {len(dummy_audio)} samples, {duration}s")
        
        # Test validation
        is_valid = processor.validate_realtime_chunk(dummy_audio, chunk_id=1)
        print(f"✅ Validation passed: {is_valid}")
        
        # Test preprocessing
        audio_tensor = processor.preprocess_realtime_chunk(dummy_audio, chunk_id=1)
        print(f"✅ Preprocessing completed: {audio_tensor.shape}")
        
        # Test mel spectrogram generation
        mel_spec = processor.generate_log_mel_spectrogram(audio_tensor)
        print(f"✅ Mel spectrogram generated: {mel_spec.shape}")
        
        # Test performance stats
        stats = processor.get_processing_stats()
        print(f"📊 Processing stats: {stats}")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
