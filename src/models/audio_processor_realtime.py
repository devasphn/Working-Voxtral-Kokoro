"""
FIXED Enhanced Audio processor for REAL-TIME streaming with VAD and silence detection
Added Voice Activity Detection and improved audio filtering
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
import webrtcvad

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
    """Enhanced audio processor with VAD and silence detection for real-time streaming"""
    
    def __init__(self):
        self.sample_rate = config.audio.sample_rate
        self.n_mels = config.spectrogram.n_mels
        self.hop_length = config.spectrogram.hop_length
        self.win_length = config.spectrogram.win_length
        self.n_fft = config.spectrogram.n_fft
        
        # Real-time processing metrics
        self.processing_history = deque(maxlen=100)
        self.chunk_counter = 0
        
        # Voice Activity Detection settings
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3 (2 = moderate)
        self.min_speech_amplitude = 0.002  # Minimum amplitude for speech consideration
        self.silence_threshold = 0.0005  # Below this is considered silence
        
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
        
        audio_logger.info(f"🔊 AudioProcessor initialized for real-time streaming with VAD:")
        audio_logger.info(f"   📊 Sample rate: {self.sample_rate} Hz")
        audio_logger.info(f"   🎵 Mel bins: {self.n_mels}")
        audio_logger.info(f"   📐 FFT size: {self.n_fft}")
        audio_logger.info(f"   ⏱️  Hop length: {self.hop_length}")
        audio_logger.info(f"   🪟 Window length: {self.win_length}")
        audio_logger.info(f"   🎙️ VAD enabled with aggressiveness level 2")
        audio_logger.info(f"   🔇 Silence threshold: {self.silence_threshold}")
        audio_logger.info(f"   📢 Min speech amplitude: {self.min_speech_amplitude}")
    
    def detect_voice_activity(self, audio_data: np.ndarray, chunk_id: int = None) -> dict:
        """
        Enhanced Voice Activity Detection with multiple criteria
        
        Returns:
            dict with 'has_speech', 'confidence', 'reason' keys
        """
        chunk_id = chunk_id or self.chunk_counter
        
        try:
            # Calculate basic audio statistics
            max_amplitude = np.max(np.abs(audio_data))
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            audio_variance = np.var(audio_data)
            
            audio_logger.debug(f"🔍 VAD analysis for chunk {chunk_id}:")
            audio_logger.debug(f"   📊 Max amplitude: {max_amplitude:.6f}")
            audio_logger.debug(f"   ⚡ RMS energy: {rms_energy:.6f}")
            audio_logger.debug(f"   📈 Variance: {audio_variance:.6f}")
            
            # Check for silence based on amplitude
            if max_amplitude < self.silence_threshold:
                return {
                    'has_speech': False,
                    'confidence': 0.9,
                    'reason': f'silence_amplitude_{max_amplitude:.6f}'
                }
            
            # Check for very low energy (background noise)
            if rms_energy < 0.001:
                return {
                    'has_speech': False,
                    'confidence': 0.8,
                    'reason': f'low_energy_{rms_energy:.6f}'
                }
            
            # Check for minimum speech amplitude
            if max_amplitude < self.min_speech_amplitude:
                return {
                    'has_speech': False,
                    'confidence': 0.7,
                    'reason': f'below_speech_threshold_{max_amplitude:.6f}'
                }
            
            # Check for very low variance (flat signal)
            if audio_variance < 1e-10:
                return {
                    'has_speech': False,
                    'confidence': 0.85,
                    'reason': f'flat_signal_{audio_variance:.2e}'
                }
            
            # Use WebRTC VAD for more sophisticated detection
            try:
                # Convert to 16-bit PCM for WebRTC VAD
                audio_int16 = (audio_data * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                
                # WebRTC VAD requires specific frame sizes (10, 20, or 30 ms)
                frame_duration_ms = 30  # 30ms frames
                frame_size = int(self.sample_rate * frame_duration_ms / 1000)
                
                speech_frames = 0
                total_frames = 0
                
                # Process audio in frames
                for i in range(0, len(audio_int16) - frame_size + 1, frame_size):
                    frame = audio_bytes[i*2:(i+frame_size)*2]  # 2 bytes per sample
                    if len(frame) == frame_size * 2:  # Complete frame
                        try:
                            is_speech = self.vad.is_speech(frame, self.sample_rate)
                            if is_speech:
                                speech_frames += 1
                            total_frames += 1
                        except Exception as e:
                            audio_logger.debug(f"VAD frame processing error: {e}")
                
                if total_frames > 0:
                    speech_ratio = speech_frames / total_frames
                    audio_logger.debug(f"   🎙️ VAD speech ratio: {speech_ratio:.2f} ({speech_frames}/{total_frames})")
                    
                    # Require at least 30% of frames to contain speech
                    if speech_ratio >= 0.3:
                        return {
                            'has_speech': True,
                            'confidence': min(0.9, speech_ratio * 1.2),
                            'reason': f'vad_detected_{speech_ratio:.2f}'
                        }
                    else:
                        return {
                            'has_speech': False,
                            'confidence': 1.0 - speech_ratio,
                            'reason': f'vad_rejected_{speech_ratio:.2f}'
                        }
                
            except Exception as vad_error:
                audio_logger.debug(f"WebRTC VAD error for chunk {chunk_id}: {vad_error}")
                
                # Fallback to energy-based detection
                if max_amplitude > self.min_speech_amplitude * 2 and rms_energy > 0.005:
                    return {
                        'has_speech': True,
                        'confidence': 0.6,
                        'reason': f'energy_fallback_{rms_energy:.6f}'
                    }
            
            # Default to no speech detected
            return {
                'has_speech': False,
                'confidence': 0.7,
                'reason': 'default_no_speech'
            }
            
        except Exception as e:
            audio_logger.error(f"❌ VAD error for chunk {chunk_id}: {e}")
            # Conservative fallback - assume no speech on error
            return {
                'has_speech': False,
                'confidence': 0.5,
                'reason': f'vad_error_{str(e)[:20]}'
            }
    
    def validate_realtime_chunk(self, audio_data: np.ndarray, chunk_id: int = None) -> bool:
        """
        Enhanced validation with VAD for real-time audio chunks
        """
        chunk_id = chunk_id or f"chunk_{int(time.time()*1000)}"
        
        try:
            audio_logger.debug(f"🔍 Validating real-time chunk {chunk_id}")
            
            # Basic validation first
            if audio_data is None or len(audio_data) == 0:
                audio_logger.debug(f"❌ Chunk {chunk_id}: Empty audio")
                return False
            
            if not isinstance(audio_data, np.ndarray):
                audio_logger.debug(f"❌ Chunk {chunk_id}: Not numpy array")
                return False
            
            # Check for reasonable audio length
            min_samples = int(0.1 * self.sample_rate)  # At least 100ms
            if len(audio_data) < min_samples:
                audio_logger.debug(f"❌ Chunk {chunk_id}: Too short ({len(audio_data)} samples)")
                return False
            
            # Voice Activity Detection
            vad_result = self.detect_voice_activity(audio_data, chunk_id)
            
            if not vad_result['has_speech']:
                audio_logger.debug(f"❌ Chunk {chunk_id}: No speech detected - {vad_result['reason']} (confidence: {vad_result['confidence']:.2f})")
                return False
            
            audio_logger.debug(f"✅ Chunk {chunk_id}: Speech detected - {vad_result['reason']} (confidence: {vad_result['confidence']:.2f})")
            return True
            
        except Exception as e:
            audio_logger.error(f"❌ Error validating chunk {chunk_id}: {e}")
            return False
    
    def preprocess_realtime_chunk(self, audio_data: np.ndarray, chunk_id: int = None, sample_rate: Optional[int] = None) -> torch.Tensor:
        """
        Enhanced preprocessing with improved audio filtering
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
            
            # Clean invalid values
            nan_count = np.sum(np.isnan(audio_data))
            inf_count = np.sum(np.isinf(audio_data))
            if nan_count > 0 or inf_count > 0:
                audio_logger.warning(f"⚠️  Chunk {chunk_id}: Cleaning {nan_count} NaN and {inf_count} infinite values")
                audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=1.0, neginf=-1.0)
            
            # Enhanced audio normalization
            max_val = np.max(np.abs(audio_data))
            rms_val = np.sqrt(np.mean(audio_data ** 2))
            
            audio_logger.debug(f"   📊 Max amplitude: {max_val:.6f}")
            audio_logger.debug(f"   ⚡ RMS energy: {rms_val:.6f}")
            
            # Intelligent amplification based on signal characteristics
            if max_val > 1.0:
                # Normalize loud audio
                audio_data = audio_data / max_val
                audio_logger.debug(f"   🔧 Normalized loud audio (max: {max_val:.4f})")
            elif max_val > 0.1:
                # Good level audio - minor normalization
                audio_data = audio_data * (0.8 / max_val)
                audio_logger.debug(f"   🔧 Minor normalization applied")
            elif max_val > self.min_speech_amplitude:
                # Amplify quiet speech carefully
                target_level = 0.3
                amplification = min(target_level / max_val, 5.0)  # Max 5x amplification
                audio_data = audio_data * amplification
                audio_logger.debug(f"   🔊 Amplified speech by {amplification:.1f}x")
            else:
                # Very quiet - this should have been filtered by VAD
                audio_logger.warning(f"⚠️  Chunk {chunk_id}: Very quiet audio passed VAD (max: {max_val:.6f})")
            
            # Apply gentle high-pass filter to remove DC offset and low-frequency noise
            if len(audio_data) > 100:  # Only for sufficient data
                from scipy import signal
                # High-pass filter at 80 Hz to remove rumble
                sos = signal.butter(4, 80, btype='high', fs=self.sample_rate, output='sos')
                audio_data = signal.sosfilt(sos, audio_data).astype(np.float32)
                audio_logger.debug(f"   🎛️ Applied high-pass filter")
            
            # Resample if necessary
            if sample_rate and sample_rate != self.sample_rate:
                audio_logger.info(f"🔄 Resampling chunk {chunk_id} from {sample_rate}Hz to {self.sample_rate}Hz")
                resample_start = time.time()
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=self.sample_rate,
                    res_type='kaiser_fast'  # High quality but fast resampling
                )
                resample_time = (time.time() - resample_start) * 1000
                audio_logger.debug(f"   ⚡ Resampling completed in {resample_time:.1f}ms")
            
            # Create tensor
            audio_tensor = torch.from_numpy(audio_data.copy()).float()
            
            # Ensure mono
            if len(audio_tensor.shape) > 1:
                audio_tensor = torch.mean(audio_tensor, dim=0)
                audio_logger.debug(f"   🎵 Converted to mono")
            
            # Ensure contiguous
            if not audio_tensor.is_contiguous():
                audio_tensor = audio_tensor.contiguous()
            
            # Final clipping to safe range
            audio_tensor = torch.clamp(audio_tensor, -1.0, 1.0)
            
            # Calculate processing metrics
            processing_time = (time.time() - start_time) * 1000
            audio_duration_s = len(audio_tensor) / self.sample_rate
            
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
    
    def generate_log_mel_spectrogram(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """Generate log-mel spectrogram optimized for real-time processing"""
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
            "current_chunk_counter": self.chunk_counter,
            "vad_enabled": True,
            "min_speech_amplitude": self.min_speech_amplitude,
            "silence_threshold": self.silence_threshold
        }
    
    def process_streaming_audio(self, audio_chunk: np.ndarray, chunk_id: int = None) -> torch.Tensor:
        """Enhanced method for processing streaming audio chunks with VAD"""
        return self.preprocess_realtime_chunk(audio_chunk, chunk_id=chunk_id)
    
    def chunk_audio(self, audio_tensor: torch.Tensor, chunk_duration: float = 2.0) -> list:
        """Chunk audio for real-time processing"""
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

# Test functionality if run directly
if __name__ == "__main__":
    print("🧪 Testing Enhanced Audio Processor with VAD...")
    
    try:
        processor = AudioProcessor()
        
        # Test with silence
        silence = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        print(f"🔇 Testing silence detection...")
        is_valid = processor.validate_realtime_chunk(silence, chunk_id="silence_test")
        print(f"   Silence validation: {is_valid} (should be False)")
        
        # Test with speech-like signal
        speech = np.sin(2 * np.pi * 300 * np.linspace(0, 1, 16000)) * 0.1  # 300Hz tone
        speech += np.random.normal(0, 0.02, 16000)  # Add some noise
        speech = speech.astype(np.float32)
        print(f"🎙️ Testing speech-like signal...")
        is_valid = processor.validate_realtime_chunk(speech, chunk_id="speech_test")
        print(f"   Speech validation: {is_valid} (should be True)")
        
        if is_valid:
            audio_tensor = processor.preprocess_realtime_chunk(speech, chunk_id="speech_test")
            print(f"   Preprocessing successful: {audio_tensor.shape}")
        
        # Print statistics
        stats = processor.get_processing_stats()
        print(f"📊 Processing stats: {stats}")
        
        print("🎉 VAD-enhanced Audio Processor test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
