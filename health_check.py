"""
Health check API for monitoring server status
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import time
import psutil
import torch
from typing import Dict, Any

from src.utils.config import config
from src.models.voxtral_model import voxtral_model

app = FastAPI(title="Voxtral Streaming Health Check", version="1.0.0")

@app.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "voxtral-streaming"
    })

@app.get("/status")
async def detailed_status() -> JSONResponse:
    """Detailed system status"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # GPU metrics
        gpu_info = {}
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
        
        # Model status
        model_info = voxtral_model.get_model_info()
        
        return JSONResponse({
            "status": "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1e9,
                "disk_free_gb": disk.free / 1e9
            },
            "gpu": gpu_info,
            "model": model_info,
            "config": {
                "http_port": config.server.http_port,
                "health_port": config.server.health_port,
                "tcp_ports": config.server.tcp_ports,
                "sample_rate": config.audio.sample_rate,
                "latency_target": config.streaming.latency_target_ms
            }
        })
        
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=500)

@app.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe for model initialization"""
    if voxtral_model.is_initialized:
        return JSONResponse({
            "ready": True,
            "timestamp": time.time(),
            "model_status": "initialized"
        })
    else:
        return JSONResponse({
            "ready": False,
            "timestamp": time.time(), 
            "model_status": "not_initialized"
        }, status_code=503)

def main():
    """Run health check server"""
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.health_port,
        log_level="info"
    )

if __name__ == "__main__":
    main()