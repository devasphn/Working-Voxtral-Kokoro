"""
Configuration management for Voxtral Real-time Streaming
"""
import yaml
import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    http_port: int = 8000
    health_port: int = 8005
    tcp_ports: List[int] = [8765, 8766]

class ModelConfig(BaseModel):
    name: str = "mistralai/Voxtral-Mini-3B-2507"
    cache_dir: str = "/workspace/model_cache"
    device: str = "cuda"
    torch_dtype: str = "bfloat16"
    max_memory_per_gpu: str = "6GB"

class AudioConfig(BaseModel):
    sample_rate: int = 16000
    chunk_size: int = 1024
    format: str = "int16"
    channels: int = 1
    frame_duration_ms: int = 30

class SpectrogramConfig(BaseModel):
    n_mels: int = 128
    hop_length: int = 160
    win_length: int = 400
    n_fft: int = 400

class StreamingConfig(BaseModel):
    max_connections: int = 100
    buffer_size: int = 4096
    timeout_seconds: int = 300
    latency_target_ms: int = 200

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "/workspace/logs/voxtral_streaming.log"

class Config(BaseModel):
    server: ServerConfig = ServerConfig()
    model: ModelConfig = ModelConfig()
    audio: AudioConfig = AudioConfig()
    spectrogram: SpectrogramConfig = SpectrogramConfig()
    streaming: StreamingConfig = StreamingConfig()
    logging: LoggingConfig = LoggingConfig()

def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file"""
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        return Config(**config_data)
    else:
        # Return default config if file doesn't exist
        return Config()

# Global config instance
config = load_config()

# Environment variable overrides
if os.getenv("VOXTRAL_HTTP_PORT"):
    config.server.http_port = int(os.getenv("VOXTRAL_HTTP_PORT"))
    
if os.getenv("VOXTRAL_HEALTH_PORT"):
    config.server.health_port = int(os.getenv("VOXTRAL_HEALTH_PORT"))
    
if os.getenv("VOXTRAL_MODEL_NAME"):
    config.model.name = os.getenv("VOXTRAL_MODEL_NAME")
    
if os.getenv("CUDA_VISIBLE_DEVICES"):
    if os.getenv("CUDA_VISIBLE_DEVICES") == "-1":
        config.model.device = "cpu"
