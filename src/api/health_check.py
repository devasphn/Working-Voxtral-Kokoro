"""
Health check API for monitoring server status (FIXED)
Removed potential conflicts and improved error handling
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import time
import psutil
import torch
from typing import Dict, Any
import logging

from src.utils.config import config

# Create separate logger for health check
health_logger = logging.getLogger("health_check")

# Initialize FastAPI app with minimal configuration
app = FastAPI(
    title="Voxtral Streaming Health Check", 
    version="1.0.0",
    docs_url=None,  # Disable docs to avoid conflicts
    redoc_url=None  # Disable redoc to avoid conflicts
)

# Global variable to track model status (avoid circular imports)
_model_status = {"initialized": False, "info": {}}

def update_model_status(status: Dict[str, Any]):
    """Update model status from external sources"""
    global _model_status
    _model_status = status

@app.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "voxtral-streaming",
        "version": "1.0.0"
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
            "config": {
                "http_port": config.server.http_port,
                "health_port": config.server.health_port,
                "tcp_ports": config.server.tcp_ports,
                "sample_rate": config.audio.sample_rate,
                "latency_target": config.streaming.latency_target_ms
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
        
        if model_initialized:
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
    except Exception as e:
        health_logger.error(f"Error in readiness check: {e}")
        return JSONResponse({
            "ready": False,
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=500)

@app.get("/ping")
async def ping() -> JSONResponse:
    """Simple ping endpoint"""
    return JSONResponse({
        "pong": True,
        "timestamp": time.time()
    })

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Health check startup"""
    health_logger.info("Health check server starting...")

@app.on_event("shutdown")
async def shutdown_event():
    """Health check shutdown"""
    health_logger.info("Health check server shutting down...")

def main():
    """Run health check server"""
    try:
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

if __name__ == "__main__":
    main()
