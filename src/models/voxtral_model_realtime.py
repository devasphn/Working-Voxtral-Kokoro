"""
FIXED Voxtral model wrapper for REAL-TIME streaming 
Fixed import paths and added proper main execution block
"""
import torch
import asyncio
import time
from typing import Optional, List, Dict, Any
from transformers import VoxtralForConditionalGeneration, AutoProcessor
import logging
from threading import Lock
import base64
from mistral_common.audio import Audio
from mistral_common.protocol.instruct.messages import AudioChunk, TextChunk, UserMessage
import tempfile
import soundfile as sf
import numpy as np
import os
from collections import deque
import sys

# Add current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.config import config

# Enhanced logging for real-time streaming
realtime_logger = logging.getLogger("voxtral_realtime")
realtime_logger.setLevel(logging.DEBUG)

class VoxtralModel:
    """Enhanced Voxtral model optimized for real-time streaming"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.audio_processor = None  # Will be lazy-loaded
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Real-time streaming optimization
        self.recent_chunks = deque(maxlen=10)  # Keep recent audio chunks for context
        self.processing_history = deque(maxlen=100)  # Performance tracking
        
        # Performance optimization settings
        self.device = config.model.device
        self.torch_dtype = getattr(torch, config.model.torch_dtype)
        
        realtime_logger.info(f"VoxtralModel initialized for {self.device} with {self.torch_dtype}")
        
    def get_audio_processor(self):
        """Lazy initialization of Audio processor"""
        if self.audio_processor is None:
            from src.models.audio_processor_realtime import AudioProcessor
            self.audio_processor = AudioProcessor()
            realtime_logger.info("Audio processor lazy-loaded into Voxtral model")
        return self.audio_processor
        
    async def initialize(self):
        """Initialize the Voxtral model with real-time optimizations"""
        try:
            realtime_logger.info("🚀 Starting Voxtral model initialization for real-time streaming...")
            start_time = time.time()
            
            # Load processor
            realtime_logger.info(f"📥 Loading AutoProcessor from {config.model.name}")
            self.processor = AutoProcessor.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir
            )
            realtime_logger.info("✅ AutoProcessor loaded successfully")
            
            # Load model with optimized settings for real-time
            realtime_logger.info(f"📥 Loading Voxtral model from {config.model.name}")
            self.model = VoxtralForConditionalGeneration.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir,
                dtype=self.torch_dtype,
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            realtime_logger.info("✅ Voxtral model loaded successfully")
            
            # Set model to evaluation mode for inference
            self.model.eval()
            realtime_logger.info("🔧 Model set to evaluation mode")
            
            # Enable real-time optimizations
            if hasattr(torch, 'compile') and self.device == "cuda":
                try:
                    realtime_logger.info("⚡ Attempting to compile model with torch.compile()...")
                    self.model = torch.compile(self.model, mode="reduce-overhead")
                    realtime_logger.info("✅ Model compiled successfully for faster inference")
                except Exception as e:
                    realtime_logger.warning(f"⚠️ Could not compile model: {e}")
            
            # Warm up the model for real-time processing
            realtime_logger.info("🔥 Starting model warmup for real-time performance...")
            await self._warmup_model()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            realtime_logger.info(f"🎉 Voxtral model fully initialized in {init_time:.2f}s and ready for real-time streaming!")
            
        except Exception as e:
            realtime_logger.error(f"❌ Failed to initialize Voxtral model: {e}")
            raise
    
    async def _warmup_model(self):
        """Enhanced warmup with real-time performance testing"""
        try:
            realtime_logger.info("🔥 Warming up model with real-time test audio...")
            
            # Generate multiple dummy audio samples of different lengths for comprehensive warmup
            sample_rate = 16000
            test_durations = [0.5, 1.0, 2.0]  # Different chunk sizes
            
            for i, duration in enumerate(test_durations):
                realtime_logger.info(f"🧪 Warmup test {i+1}/3: {duration}s audio chunk")
                
                # Generate test audio
                dummy_samples = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
                dummy_samples = dummy_samples.astype(np.float32)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    sf.write(tmp_file.name, dummy_samples, sample_rate)
                    
                    try:
                        warmup_start = time.time()
                        
                        # Load using mistral_common Audio
                        audio = Audio.from_file(tmp_file.name, strict=False)
                        audio_chunk = AudioChunk.from_audio(audio)
                        
                        # Create proper message format
                        text_chunk = TextChunk(text="Test warmup audio")
                        user_message = UserMessage(content=[audio_chunk, text_chunk])
                        openai_message = user_message.to_openai()
                        
                        # Run inference
                        with torch.no_grad():
                            inputs = self.processor.apply_chat_template([openai_message], return_tensors="pt")
                            
                            # Move to correct device
                            if hasattr(inputs, 'to'):
                                inputs = inputs.to(self.device)
                            elif isinstance(inputs, dict):
                                inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                                        for k, v in inputs.items()}
                            
                            # Generate with minimal tokens for warmup
                            outputs = self.model.generate(
                                **inputs,
                                max_new_tokens=3,
                                do_sample=False,
                                pad_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None
                            )
                        
                        warmup_time = (time.time() - warmup_start) * 1000
                        realtime_logger.info(f"✅ Warmup {i+1} completed: {duration}s audio processed in {warmup_time:.1f}ms")
                        
                    except Exception as warmup_error:
                        realtime_logger.warning(f"⚠️ Warmup test {i+1} had issues but continuing: {warmup_error}")
                    
                    finally:
                        # Cleanup temporary file
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
            
            realtime_logger.info("🎯 Model warmup completed - ready for real-time processing!")
            
        except Exception as e:
            realtime_logger.warning(f"⚠️ Model warmup encountered issues: {e}")
    
    async def process_realtime_chunk(self, audio_data: torch.Tensor, chunk_id: int, prompt: str = "Transcribe this audio.") -> Dict[str, Any]:
        """
        Optimized processing for real-time audio chunks
        
        Args:
            audio_data: Preprocessed audio tensor
            chunk_id: Unique identifier for this chunk
            prompt: Text prompt for the model
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        try:
            chunk_start_time = time.time()
            realtime_logger.debug(f"🎵 Processing real-time chunk {chunk_id} with {len(audio_data)} samples")
            
            with self.model_lock:
                # Store chunk in recent history for potential context
                self.recent_chunks.append({
                    'chunk_id': chunk_id,
                    'audio_data': audio_data,
                    'timestamp': chunk_start_time
                })
                
                # Ensure audio_data is properly formatted
                if not audio_data.data.is_contiguous():
                    audio_data = audio_data.contiguous()
                    realtime_logger.debug(f"🔧 Made audio data contiguous for chunk {chunk_id}")
                
                # Convert tensor to numpy with explicit copy
                audio_np = audio_data.detach().cpu().numpy().copy()
                sample_rate = config.audio.sample_rate
                
                realtime_logger.debug(f"🔊 Audio stats for chunk {chunk_id}: length={len(audio_np)}, max_val={np.max(np.abs(audio_np)):.4f}")
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    try:
                        # Write audio to temporary file
                        sf.write(tmp_file.name, audio_np, sample_rate)
                        realtime_logger.debug(f"💾 Written chunk {chunk_id} to temporary file: {tmp_file.name}")
                        
                        # Load using mistral_common Audio
                        audio = Audio.from_file(tmp_file.name, strict=False)
                        audio_chunk = AudioChunk.from_audio(audio)
                        
                        # Create message format
                        text_chunk = TextChunk(text=prompt)
                        user_message = UserMessage(content=[audio_chunk, text_chunk])
                        openai_message = user_message.to_openai()
                        
                        # Process inputs
                        inputs = self.processor.apply_chat_template([openai_message], return_tensors="pt")
                        
                        # Move to device
                        if hasattr(inputs, 'to'):
                            inputs = inputs.to(self.device)
                        elif isinstance(inputs, dict):
                            inputs = {k: v.to(self.device) if hasattr(v, 'to') else v 
                                    for k, v in inputs.items()}
                        
                        realtime_logger.debug(f"🚀 Starting inference for chunk {chunk_id}")
                        inference_start = time.time()
                        
                        # Generate response with real-time optimized settings
                        with torch.no_grad():
                            with torch.autocast(device_type="cuda" if "cuda" in self.device else "cpu", dtype=self.torch_dtype):
                                outputs = self.model.generate(
                                    **inputs,
                                    max_new_tokens=50,  # Balanced for real-time
                                    do_sample=False,    # Greedy decoding for speed
                                    temperature=1.0,
                                    pad_token_id=self.processor.tokenizer.eos_token_id if hasattr(self.processor, 'tokenizer') else None,
                                    use_cache=True      # Use KV cache for speed
                                )
                        
                        inference_time = (time.time() - inference_start) * 1000
                        realtime_logger.debug(f"⚡ Inference completed for chunk {chunk_id} in {inference_time:.1f}ms")
                        
                        # Decode response
                        if hasattr(inputs, 'input_ids'):
                            input_length = inputs.input_ids.shape[1]
                        elif 'input_ids' in inputs:
                            input_length = inputs['input_ids'].shape[1]
                        else:
                            input_length = 0
                            
                        response = self.processor.batch_decode(
                            outputs[:, input_length:], 
                            skip_special_tokens=True
                        )[0]
                        
                        total_processing_time = (time.time() - chunk_start_time) * 1000
                        
                        # Store performance metrics
                        performance_data = {
                            'chunk_id': chunk_id,
                            'total_time_ms': total_processing_time,
                            'inference_time_ms': inference_time,
                            'audio_length_s': len(audio_np) / sample_rate,
                            'response_length': len(response),
                            'timestamp': chunk_start_time
                        }
                        self.processing_history.append(performance_data)
                        
                        realtime_logger.info(f"✅ Chunk {chunk_id} processed in {total_processing_time:.1f}ms: '{response[:50]}{'...' if len(response) > 50 else ''}'")
                        
                        return {
                            'response': response.strip(),
                            'processing_time_ms': total_processing_time,
                            'inference_time_ms': inference_time,
                            'chunk_id': chunk_id,
                            'audio_duration_s': len(audio_np) / sample_rate,
                            'success': True
                        }
                        
                    finally:
                        # Cleanup temporary file
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass
                
        except Exception as e:
            processing_time = (time.time() - chunk_start_time) * 1000
            realtime_logger.error(f"❌ Error processing chunk {chunk_id}: {e}")
            
            # Return error response with timing info
            error_msg = "Processing error: "
            if "Index put requires" in str(e):
                error_msg += "Data type conversion issue. Please try again."
            elif "CUDA out of memory" in str(e):
                error_msg += "GPU memory error. Try shorter audio clips."
            else:
                error_msg += str(e)
            
            return {
                'response': error_msg,
                'processing_time_ms': processing_time,
                'chunk_id': chunk_id,
                'success': False,
                'error': str(e)
            }
    
    async def transcribe_audio(self, audio_data: torch.Tensor) -> str:
        """Fast transcription for real-time chunks"""
        result = await self.process_realtime_chunk(
            audio_data, 
            chunk_id=int(time.time() * 1000),  # Use timestamp as chunk ID
            prompt="Transcribe this audio accurately."
        )
        return result['response']
    
    async def understand_audio(self, audio_data: torch.Tensor, question: str) -> str:
        """Audio understanding for real-time chunks"""
        result = await self.process_realtime_chunk(
            audio_data,
            chunk_id=int(time.time() * 1000),
            prompt=f"Answer this question about the audio: {question}"
        )
        return result['response']
    
    async def process_audio_stream(self, audio_data: torch.Tensor, prompt: str = "Transcribe this audio.") -> str:
        """General audio processing for real-time chunks"""
        result = await self.process_realtime_chunk(
            audio_data,
            chunk_id=int(time.time() * 1000),
            prompt=prompt
        )
        return result['response']
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get enhanced model information with real-time stats"""
        base_info = {
            "status": "initialized" if self.is_initialized else "not_initialized",
            "model_name": config.model.name,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "parameters": self.model.num_parameters() if self.model and hasattr(self.model, 'num_parameters') else "unknown"
        }
        
        if self.is_initialized and self.processing_history:
            # Calculate real-time performance stats
            recent_history = list(self.processing_history)[-20:]  # Last 20 chunks
            if recent_history:
                avg_processing_time = np.mean([h['total_time_ms'] for h in recent_history])
                avg_inference_time = np.mean([h['inference_time_ms'] for h in recent_history])
                total_chunks = len(self.processing_history)
                
                base_info.update({
                    "realtime_stats": {
                        "total_chunks_processed": total_chunks,
                        "avg_processing_time_ms": round(avg_processing_time, 1),
                        "avg_inference_time_ms": round(avg_inference_time, 1),
                        "recent_chunks_in_memory": len(self.recent_chunks),
                        "performance_history_size": len(self.processing_history)
                    }
                })
        
        return base_info
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics for real-time monitoring"""
        if not self.processing_history:
            return {"message": "No processing history available"}
        
        history = list(self.processing_history)
        
        # Calculate various statistics
        processing_times = [h['total_time_ms'] for h in history]
        inference_times = [h['inference_time_ms'] for h in history]
        audio_lengths = [h['audio_length_s'] for h in history]
        
        return {
            "total_chunks": len(history),
            "processing_time": {
                "avg_ms": round(np.mean(processing_times), 1),
                "min_ms": round(np.min(processing_times), 1),
                "max_ms": round(np.max(processing_times), 1),
                "std_ms": round(np.std(processing_times), 1)
            },
            "inference_time": {
                "avg_ms": round(np.mean(inference_times), 1),
                "min_ms": round(np.min(inference_times), 1),
                "max_ms": round(np.max(inference_times), 1)
            },
            "audio_characteristics": {
                "avg_length_s": round(np.mean(audio_lengths), 2),
                "total_audio_processed_s": round(np.sum(audio_lengths), 2)
            },
            "realtime_ratio": round(np.mean([
                h['audio_length_s'] / (h['total_time_ms'] / 1000) 
                for h in history if h['total_time_ms'] > 0
            ]), 2) if history else 0
        }

# Global model instance for real-time streaming
voxtral_model = VoxtralModel()

# FIXED: Add proper main execution block for testing
if __name__ == "__main__":
    import asyncio
    
    async def test_model():
        """Test model initialization and basic functionality"""
        print("🧪 Testing Voxtral Real-time Model...")
        
        try:
            # Initialize model
            await voxtral_model.initialize()
            
            # Test with dummy audio
            dummy_audio = torch.randn(16000)  # 1 second of dummy audio
            result = await voxtral_model.transcribe_audio(dummy_audio)
            
            print(f"✅ Test completed successfully")
            print(f"📊 Model info: {voxtral_model.get_model_info()}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    asyncio.run(test_model())
