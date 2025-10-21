"""
FIXED Health check API for monitoring server status
Resolved deprecation warnings and improved error handling
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import time
import psutil
import torch
from typing import Dict, Any
import logging
import sys
import os

# Add current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.config import config

# Create separate logger for health check
health_logger = logging.getLogger("health_check")

# Global variable to track model status (avoid circular imports)
_model_status = {"initialized": False, "info": {}}
_speech_to_speech_status = {"initialized": False, "info": {}}

def update_model_status(status: Dict[str, Any]):
    """Update model status from external sources"""
    global _model_status
    _model_status = status

def update_speech_to_speech_status(status: Dict[str, Any]):
    """Update speech-to-speech pipeline status from external sources"""
    global _speech_to_speech_status
    _speech_to_speech_status = status

# FIXED: Use lifespan event handler instead of deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    health_logger.info("Health check server starting...")
    yield
    # Shutdown
    health_logger.info("Health check server shutting down...")

# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="Voxtral Streaming Health Check", 
    version="1.0.0",
    docs_url=None,  # Disable docs to avoid conflicts
    redoc_url=None,  # Disable redoc to avoid conflicts
    lifespan=lifespan
)

@app.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "voxtral-streaming",
        "version": "2.0.0"
    })

@app.get("/status")
async def detailed_status() -> JSONResponse:
    """Detailed system status"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Faster check
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # GPU metrics
        gpu_info = {}
        try:
            if torch.cuda.is_available():
                gpu_info = {
                    "gpu_available": True,
                    "gpu_count": torch.cuda.device_count(),
                    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None,
                    "gpu_memory_allocated": torch.cuda.memory_allocated(0) / 1e9 if torch.cuda.device_count() > 0 else 0,
                    "gpu_memory_cached": torch.cuda.memory_reserved(0) / 1e9 if torch.cuda.device_count() > 0 else 0
                }
            else:
                gpu_info = {"gpu_available": False}
        except Exception as e:
            gpu_info = {"gpu_available": False, "error": str(e)}
        
        # Model status (from global variable to avoid circular imports)
        model_info = _model_status.get("info", {"status": "unknown"})
        speech_to_speech_info = _speech_to_speech_status.get("info", {"status": "unknown"})

        # Calculate performance metrics
        performance_metrics = {}
        if speech_to_speech_info.get("performance_stats"):
            perf = speech_to_speech_info["performance_stats"]
            performance_metrics = {
                "avg_total_latency_ms": perf.get("avg_total_latency_ms", 0),
                "latency_target_ms": config.speech_to_speech.latency_target_ms,
                "target_met_rate_percent": perf.get("target_met_rate_percent", 0),
                "total_conversations": speech_to_speech_info.get("total_conversations", 0)
            }

        return JSONResponse({
            "status": "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / 1e9, 2),
                "disk_free_gb": round(disk.free / 1e9, 2)
            },
            "gpu": gpu_info,
            "model": model_info,
            "speech_to_speech": {
                "enabled": config.speech_to_speech.enabled,
                "initialized": _speech_to_speech_status.get("initialized", False),
                "pipeline_info": speech_to_speech_info,
                "performance_metrics": performance_metrics
            },
            "config": {
                "http_port": config.server.http_port,
                "health_port": config.server.health_port,
                "tcp_ports": config.server.tcp_ports,
                "sample_rate": config.audio.sample_rate,
                "latency_target": config.streaming.latency_target_ms,
                "speech_to_speech_enabled": config.speech_to_speech.enabled,
                "speech_to_speech_latency_target": config.speech_to_speech.latency_target_ms
            }
        })
        
    except Exception as e:
        health_logger.error(f"Error in detailed status: {e}")
        return JSONResponse({
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=500)

@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe for model initialization"""
    try:
        model_initialized = _model_status.get("initialized", False)
        speech_to_speech_initialized = _speech_to_speech_status.get("initialized", False)

        # Check if speech-to-speech is enabled and required
        speech_to_speech_required = config.speech_to_speech.enabled

        if model_initialized and (not speech_to_speech_required or speech_to_speech_initialized):
            return JSONResponse({
                "ready": True,
                "timestamp": time.time(),
                "model_status": "initialized",
                "speech_to_speech_status": "initialized" if speech_to_speech_initialized else "not_required",
                "speech_to_speech_enabled": speech_to_speech_required
            })
        else:
            return JSONResponse({
                "ready": False,
                "timestamp": time.time(),
                "model_status": "initialized" if model_initialized else "not_initialized",
                "speech_to_speech_status": "initialized" if speech_to_speech_initialized else "not_initialized",
                "speech_to_speech_enabled": speech_to_speech_required,
                "missing_components": [
                    comp for comp, status in [
                        ("voxtral_model", model_initialized),
                        ("speech_to_speech_pipeline", speech_to_speech_initialized or not speech_to_speech_required)
                    ] if not status
                ]
            }, status_code=503)
    except Exception as e:
        health_logger.error(f"Error in readiness check: {e}")
        return JSONResponse({
            "ready": False,
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=500)

@app.get("/speech-to-speech/metrics")
async def speech_to_speech_metrics() -> JSONResponse:
    """Detailed speech-to-speech performance metrics"""
    try:
        if not config.speech_to_speech.enabled:
            return JSONResponse({
                "enabled": False,
                "message": "Speech-to-speech functionality is disabled"
            })

        speech_to_speech_info = _speech_to_speech_status.get("info", {})

        # Extract detailed performance metrics
        metrics = {
            "enabled": True,
            "initialized": _speech_to_speech_status.get("initialized", False),
            "timestamp": time.time(),
            "pipeline_status": {
                "total_conversations": speech_to_speech_info.get("total_conversations", 0),
                "latency_target_ms": config.speech_to_speech.latency_target_ms,
                "emotional_tts_enabled": speech_to_speech_info.get("emotional_tts_enabled", False)
            }
        }

        # Add performance statistics if available
        if "performance_stats" in speech_to_speech_info:
            perf = speech_to_speech_info["performance_stats"]
            metrics["performance"] = {
                "avg_total_latency_ms": perf.get("avg_total_latency_ms", 0),
                "avg_stt_time_ms": perf.get("avg_stt_time_ms", 0),
                "avg_llm_time_ms": perf.get("avg_llm_time_ms", 0),
                "avg_tts_time_ms": perf.get("avg_tts_time_ms", 0),
                "target_met_rate_percent": perf.get("target_met_rate_percent", 0),
                "recent_conversations": perf.get("recent_conversations", 0)
            }

        # Add component status if available
        if "components" in speech_to_speech_info:
            components = speech_to_speech_info["components"]
            metrics["components"] = {
                "voxtral_stt": {
                    "initialized": components.get("voxtral_stt", {}).get("is_initialized", False),
                    "model_type": components.get("voxtral_stt", {}).get("model_type", "unknown")
                }
            }

        return JSONResponse(metrics)

    except Exception as e:
        health_logger.error(f"Error in speech-to-speech metrics: {e}")
        return JSONResponse({
            "enabled": config.speech_to_speech.enabled,
            "error": str(e),
            "timestamp": time.time()
        }, status_code=500)

@app.get("/speech-to-speech/performance")
async def speech_to_speech_performance() -> JSONResponse:
    """Real-time speech-to-speech performance monitoring"""
    try:
        if not config.speech_to_speech.enabled:
            return JSONResponse({
                "enabled": False,
                "message": "Speech-to-speech functionality is disabled"
            })

        speech_to_speech_info = _speech_to_speech_status.get("info", {})

        # Performance analysis
        performance_analysis = {
            "timestamp": time.time(),
            "latency_analysis": {
                "target_ms": config.speech_to_speech.latency_target_ms,
                "status": "unknown"
            },
            "throughput_analysis": {
                "conversations_per_minute": 0,
                "status": "unknown"
            },
            "quality_metrics": {
                "success_rate_percent": 0,
                "emotional_appropriateness_avg": 0
            }
        }

        if "performance_stats" in speech_to_speech_info:
            perf = speech_to_speech_info["performance_stats"]
            avg_latency = perf.get("avg_total_latency_ms", 0)
            target_met_rate = perf.get("target_met_rate_percent", 0)

            # Latency analysis
            performance_analysis["latency_analysis"].update({
                "current_avg_ms": avg_latency,
                "target_met_rate_percent": target_met_rate,
                "status": "excellent" if target_met_rate >= 95 else
                         "good" if target_met_rate >= 80 else
                         "poor" if target_met_rate >= 50 else "critical"
            })

            # Throughput analysis
            total_conversations = speech_to_speech_info.get("total_conversations", 0)
            if total_conversations > 0:
                # Estimate conversations per minute (rough calculation)
                conversations_per_minute = min(60000 / avg_latency, 60) if avg_latency > 0 else 0
                performance_analysis["throughput_analysis"].update({
                    "conversations_per_minute": round(conversations_per_minute, 1),
                    "total_conversations": total_conversations,
                    "status": "excellent" if conversations_per_minute >= 10 else
                             "good" if conversations_per_minute >= 5 else
                             "moderate" if conversations_per_minute >= 2 else "low"
                })

        return JSONResponse(performance_analysis)

    except Exception as e:
        health_logger.error(f"Error in speech-to-speech performance: {e}")
        return JSONResponse({
            "enabled": config.speech_to_speech.enabled,
            "error": str(e),
            "timestamp": time.time()
        }, status_code=500)

@app.get("/ping")
async def ping() -> JSONResponse:
    """Simple ping endpoint"""
    return JSONResponse({
        "pong": True,
        "timestamp": time.time()
    })

# FIXED: Add proper main execution block
if __name__ == "__main__":
    try:
        health_logger.info("Starting Health Check Server")
        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.health_port,
            log_level="info",
            access_log=False  # Reduce log noise
        )
    except Exception as e:
        health_logger.error(f"Failed to start health check server: {e}")
        raise
