"""
Configuration management for Voxtral Real-time Streaming (FIXED)
Updated for Pydantic v2 and pydantic-settings
"""
import yaml
import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any

# Import pydantic_settings with fallback
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_SETTINGS_AVAILABLE = True
except ImportError:
    # Fallback for older pydantic versions or missing pydantic-settings
    try:
        from pydantic import BaseSettings
        SettingsConfigDict = None
        PYDANTIC_SETTINGS_AVAILABLE = True
    except ImportError:
        BaseSettings = BaseModel
        SettingsConfigDict = None
        PYDANTIC_SETTINGS_AVAILABLE = False

class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    http_port: int = 8000
    health_port: int = 8005
    tcp_ports: List[int] = [8765, 8766]

class ModelConfig(BaseModel):
    name: str = "mistralai/Voxtral-Mini-3B-2507"
    cache_dir: str = "./model_cache"
    device: str = "cuda"
    torch_dtype: str = "bfloat16"
    max_memory_per_gpu: str = "8GB"
    ultra_fast_mode: bool = True
    warmup_enabled: bool = True

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

class VADConfig(BaseModel):
    """Voice Activity Detection configuration"""
    threshold: float = 0.005
    min_voice_duration_ms: int = 200
    min_silence_duration_ms: int = 400
    chunk_size_ms: int = 20
    overlap_ms: int = 2
    sensitivity: str = "ultra_high"

class StreamingConfig(BaseModel):
    enabled: bool = True
    chunk_mode: str = "sentence_streaming"
    max_connections: int = 100
    buffer_size: int = 4096
    timeout_seconds: int = 300
    latency_target_ms: int = 50  # ULTRA-AGGRESSIVE: 10x more aggressive
    
class PerformanceConfig(BaseModel):
    """Performance monitoring and optimization configuration"""
    enable_monitoring: bool = True
    latency_targets: Dict[str, int] = {
        "voxtral_processing_ms": 100,
        "audio_conversion_ms": 50,
        "total_end_to_end_ms": 100
    }
    alert_thresholds: Dict[str, float] = {
        "consecutive_failures": 5,
        "degradation_threshold": 1.5,
        "success_rate_threshold": 0.8
    }
    optimization_level: str = "balanced"  # "performance", "balanced", "memory_efficient"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "/workspace/logs/voxtral_streaming.log"

class TTSPerformanceConfig(BaseModel):
    """Performance optimization settings"""
    batch_size: int = 1
    max_queue_size: int = 32
    num_workers: int = 4
    target_latency_ms: int = 100  # Target for ASR processing
    memory_optimization: str = "balanced"  # "performance", "balanced", "memory_efficient"

class GPUMemoryConfig(BaseModel):
    """GPU memory management configuration"""
    min_vram_gb: float = 8.0
    recommended_vram_gb: float = 16.0
    memory_fraction: float = 0.9
    cleanup_frequency: str = "after_each_generation"  # "after_each_generation", "periodic"
    enable_monitoring: bool = True



class Config(BaseSettings):
    """Main configuration class using BaseSettings for environment variable support"""
    server: ServerConfig = ServerConfig()
    model: ModelConfig = ModelConfig()
    audio: AudioConfig = AudioConfig()
    spectrogram: SpectrogramConfig = SpectrogramConfig()
    vad: VADConfig = VADConfig()
    streaming: StreamingConfig = StreamingConfig()
    logging: LoggingConfig = LoggingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    
    # Pydantic v2 settings configuration with fallback
    if PYDANTIC_SETTINGS_AVAILABLE and SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            env_nested_delimiter="__",
            case_sensitive=False,
            extra="ignore"
        )
    else:
        # Fallback configuration for older pydantic versions
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "ignore"

def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file with environment variable override support"""
    config_file = Path(config_path)
    
    if config_file.exists():
        try:
            # Open with explicit UTF-8 encoding to handle Unicode characters
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return Config(**config_data)
        except UnicodeDecodeError:
            print(f"Warning: Unicode decode error in {config_path}. Using default configuration.")
            return Config()
        except Exception as e:
            print(f"Warning: Error loading config from {config_path}: {e}. Using default configuration.")
            return Config()
    else:
        # Return default config if file doesn't exist
        return Config()

# Global config instance
config = load_config()

# Environment variable overrides (still supported for backward compatibility)
if os.getenv("VOXTRAL_HTTP_PORT"):
    config.server.http_port = int(os.getenv("VOXTRAL_HTTP_PORT"))
    
if os.getenv("VOXTRAL_HEALTH_PORT"):
    config.server.health_port = int(os.getenv("VOXTRAL_HEALTH_PORT"))
    
if os.getenv("VOXTRAL_MODEL_NAME"):
    config.model.name = os.getenv("VOXTRAL_MODEL_NAME")
    
if os.getenv("CUDA_VISIBLE_DEVICES"):
    if os.getenv("CUDA_VISIBLE_DEVICES") == "-1":
        config.model.device = "cpu"
