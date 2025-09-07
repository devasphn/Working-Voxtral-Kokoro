"""
Voxtral model wrapper for real-time streaming (FIXED)
Optimized for <200ms latency inference with proper audio format handling
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

from src.utils.config import config
from src.models.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

class VoxtralModel:
    """Optimized Voxtral model for real-time streaming"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.audio_processor = AudioProcessor()
        self.model_lock = Lock()
        self.is_initialized = False
        
        # Performance optimization settings
        self.device = config.model.device
        self.torch_dtype = getattr(torch, config.model.torch_dtype)
        
    async def initialize(self):
        """Initialize the Voxtral model asynchronously"""
        try:
            logger.info("Initializing Voxtral model...")
            start_time = time.time()
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir
            )
            
            # Load model with optimizations (FIXED: use dtype instead of torch_dtype)
            self.model = VoxtralForConditionalGeneration.from_pretrained(
                config.model.name,
                cache_dir=config.model.cache_dir,
                dtype=self.torch_dtype,  # FIXED: changed from torch_dtype to dtype
                device_map="auto",
                low_cpu_mem_usage=True,
                trust_remote_code=True
            )
            
            # Set model to evaluation mode for inference
            self.model.eval()
            
            # Enable optimizations
            if hasattr(torch, 'compile') and self.device == "cuda":
                try:
                    self.model = torch.compile(self.model, mode="reduce-overhead")
                    logger.info("Model compiled with torch.compile")
                except Exception as e:
                    logger.warning(f"Could not compile model: {e}")
            
            # Warm up the model with dummy data (FIXED)
            await self._warmup_model()
            
            self.is_initialized = True
            init_time = time.time() - start_time
            logger.info(f"Voxtral model initialized in {init_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize Voxtral model: {e}")
            raise
    
    async def _warmup_model(self):
        """Warm up the model with dummy audio to optimize first inference (FIXED)"""
        try:
            logger.info("Warming up model...")
            
            # Create proper dummy audio using mistral_common format
            import numpy as np
            import tempfile
            import soundfile as sf
            
            # Generate 1 second of dummy audio at 16kHz
            sample_rate = 16000
            duration = 1.0
            dummy_samples = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
            dummy_samples = dummy_samples.astype(np.float32)
            
            # Save to temporary file and load with mistral_common
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, dummy_samples, sample_rate)
                
                # Load using mistral_common Audio
                audio = Audio.from_file(tmp_file.name, strict=False)
                audio_chunk = AudioChunk.from_audio(audio)
                
                # Create proper message format
                text_chunk = TextChunk(text="Hello")
                user_message = UserMessage(content=[audio_chunk, text_chunk])
                
                # Convert to OpenAI format for the processor
                openai_message = user_message.to_openai()
                
                # Run dummy inference with proper format
                with torch.no_grad():
                    try:
                        inputs = self.processor.apply_chat_template(
                            [openai_message], 
                            return_tensors="pt"
                        )
                        inputs = inputs.to(self.device)
                        
                        # Generate with minimal tokens for warmup
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=10,
                            do_sample=False,
                            pad_token_id=self.processor.tokenizer.eos_token_id
                        )
                        logger.info("Model warmup completed successfully")
                        
                    except Exception as warmup_error:
                        logger.warning(f"Model warmup had issues but continuing: {warmup_error}")
                
                # Cleanup temporary file
                import os
                os.unlink(tmp_file.name)
            
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    async def process_audio_stream(self, audio_data: torch.Tensor, prompt: str = "Transcribe this audio.") -> str:
        """
        Process streaming audio and return transcription/response (FIXED)
        Optimized for <200ms latency
        
        Args:
            audio_data: Preprocessed audio tensor
            prompt: Text prompt for the model
            
        Returns:
            Model response text
        """
        if not self.is_initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")
        
        try:
            start_time = time.time()
            
            with self.model_lock:
                # Convert tensor to proper format for Voxtral (FIXED)
                import tempfile
                import soundfile as sf
                
                # Convert tensor to numpy and save as temporary file
                audio_np = audio_data.numpy()
                sample_rate = config.audio.sample_rate
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    sf.write(tmp_file.name, audio_np, sample_rate)
                    
                    # Load using mistral_common Audio
                    audio = Audio.from_file(tmp_file.name, strict=False)
                    audio_chunk = AudioChunk.from_audio(audio)
                    
                    # Create message format
                    text_chunk = TextChunk(text=prompt)
                    user_message = UserMessage(content=[audio_chunk, text_chunk])
                    
                    # Convert to OpenAI format
                    openai_message = user_message.to_openai()
                    
                    # Process inputs
                    inputs = self.processor.apply_chat_template(
                        [openai_message], 
                        return_tensors="pt"
                    )
                    inputs = inputs.to(self.device, dtype=self.torch_dtype)
                    
                    # Generate response with optimized settings
                    with torch.no_grad():
                        with torch.autocast(device_type="cuda" if "cuda" in self.device else "cpu"):
                            outputs = self.model.generate(
                                **inputs,
                                max_new_tokens=100,  # Limit for low latency
                                do_sample=False,  # Greedy decoding for speed
                                temperature=1.0,
                                pad_token_id=self.processor.tokenizer.eos_token_id,
                                use_cache=True  # Use KV cache for speed
                            )
                    
                    # Decode response
                    response = self.processor.batch_decode(
                        outputs[:, inputs.input_ids.shape[1]:], 
                        skip_special_tokens=True
                    )[0]
                    
                    processing_time = time.time() - start_time
                    logger.debug(f"Audio processed in {processing_time*1000:.1f}ms")
                    
                    # Cleanup temporary file
                    import os
                    os.unlink(tmp_file.name)
                    
                    return response.strip()
                
        except Exception as e:
            logger.error(f"Error processing audio stream: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: torch.Tensor) -> str:
        """
        Fast transcription-only mode
        
        Args:
            audio_data: Preprocessed audio tensor
            
        Returns:
            Transcription text
        """
        return await self.process_audio_stream(
            audio_data, 
            prompt="Transcribe this audio accurately."
        )
    
    async def understand_audio(self, audio_data: torch.Tensor, question: str) -> str:
        """
        Audio understanding with question answering
        
        Args:
            audio_data: Preprocessed audio tensor
            question: Question about the audio content
            
        Returns:
            Answer to the question
        """
        return await self.process_audio_stream(
            audio_data,
            prompt=f"Answer this question about the audio: {question}"
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "model_name": config.model.name,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "parameters": self.model.num_parameters() if hasattr(self.model, 'num_parameters') else "unknown"
        }

# Global model instance
voxtral_model = VoxtralModel()
