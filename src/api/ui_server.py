"""
FastAPI UI server with integrated WebSocket (FIXED)
Fixed JavaScript base64 conversion for large audio files
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
import time
import json
import base64
import numpy as np
from pathlib import Path

from src.utils.config import config
from src.utils.logging_config import logger

# Initialize FastAPI app
app = FastAPI(
    title="Voxtral Real-time Streaming UI",
    description="Web interface for Voxtral real-time audio streaming",
    version="1.0.0"
)

# Global variables for lazy initialization
_voxtral_model = None
_audio_processor = None

def get_voxtral_model():
    """Lazy initialization of Voxtral model"""
    global _voxtral_model
    if _voxtral_model is None:
        from src.models.voxtral_model import voxtral_model
        _voxtral_model = voxtral_model
    return _voxtral_model

def get_audio_processor():
    """Lazy initialization of Audio processor"""
    global _audio_processor
    if _audio_processor is None:
        from src.models.audio_processor import AudioProcessor
        _audio_processor = AudioProcessor()
    return _audio_processor

# Setup static files if directory exists
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface with RunPod WebSocket compatibility"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxtral Real-time Streaming</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 30px;
            justify-content: center;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            min-width: 120px;
        }
        .primary-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
        }
        .secondary-btn {
            background: linear-gradient(45deg, #74b9ff, #0984e3);
            color: white;
        }
        .success-btn {
            background: linear-gradient(45deg, #00b894, #00a085);
            color: white;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            border-left: 4px solid #00b894;
        }
        .response {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
            border-left: 4px solid #74b9ff;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
        }
        select, input {
            padding: 10px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        .audio-controls {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
        }
        .connected {
            background: #00b894;
        }
        .disconnected {
            background: #e17055;
        }
        .url-info {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 4px solid #74b9ff;
        }
        .loading {
            border-left: 4px solid #f39c12;
        }
        .loading .status {
            border-left-color: #f39c12;
        }
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        Disconnected
    </div>
    
    <div class="container">
        <h1>🎙️ Voxtral Real-time Streaming</h1>
        
        <div class="url-info" id="urlInfo">
            <strong>WebSocket URL:</strong> <span id="wsUrl">Detecting...</span><br>
            <strong>Environment:</strong> <span id="envInfo">Detecting...</span>
        </div>
        
        <div class="status" id="status">
            Initializing... Click Connect to start
        </div>
        
        <div class="controls">
            <button id="connectBtn" class="primary-btn" onclick="connect()">Connect</button>
            <button id="startBtn" class="success-btn" onclick="startRecording()" disabled>Start Recording</button>
            <button id="stopBtn" class="secondary-btn" onclick="stopRecording()" disabled>Stop Recording</button>
        </div>
        
        <div class="audio-controls">
            <label>Mode:</label>
            <select id="modeSelect">
                <option value="transcribe">Transcribe</option>
                <option value="understand">Understand</option>
            </select>
            
            <label>Prompt:</label>
            <input type="text" id="promptInput" placeholder="Optional prompt..." style="flex: 1; min-width: 200px;">
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" id="latencyMetric">-</div>
                <div class="metric-label">Latency (ms)</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="audioLengthMetric">-</div>
                <div class="metric-label">Audio Length (s)</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="processingTimeMetric">-</div>
                <div class="metric-label">Processing Time (ms)</div>
            </div>
        </div>
        
        <div class="response" id="response" style="display: none;">
            Response will appear here...
        </div>
    </div>
    
    <script>
        let ws = null;
        let mediaRecorder = null;
        let audioStream = null;
        let audioChunks = [];  
        let isRecording = false;
        let wsUrl = '';
        let isModelLoading = false;
        
        // Detect environment and construct WebSocket URL
        function detectEnvironment() {
            const hostname = window.location.hostname;
            const protocol = window.location.protocol;
            
            // For RunPod, use the same host but with /ws endpoint
            if (hostname.includes('proxy.runpod.net')) {
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo').textContent = 'RunPod Cloud (HTTP Proxy)';
            } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
                // Local development
                wsUrl = `ws://${hostname}:8000/ws`;
                document.getElementById('envInfo').textContent = 'Local Development';
            } else {
                // Other cloud or custom deployment
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo').textContent = 'Custom Deployment';
            }
            
            document.getElementById('wsUrl').textContent = wsUrl;
        }
        
        function updateStatus(message, type = 'info') {
            const status = document.getElementById('status');
            const container = document.getElementById('status').parentElement;
            
            status.textContent = message;
            
            // Update visual styling based on type
            if (type === 'loading') {
                status.style.borderLeftColor = '#f39c12';
                container.classList.add('loading');
            } else {
                container.classList.remove('loading');
                status.style.borderLeftColor = type === 'error' ? '#e17055' : type === 'success' ? '#00b894' : '#74b9ff';
            }
        }
        
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            status.textContent = connected ? 'Connected' : 'Disconnected';
            status.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
        }
        
        async function connect() {
            try {
                updateStatus('Attempting to connect...', 'info');
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    updateStatus('Connected to Voxtral streaming server', 'success');
                    updateConnectionStatus(true);
                    document.getElementById('connectBtn').disabled = true;
                    document.getElementById('startBtn').disabled = false;
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = (event) => {
                    updateStatus(`Disconnected from server (Code: ${event.code})`, 'error');
                    updateConnectionStatus(false);
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = true;
                    isModelLoading = false;
                };
                
                ws.onerror = (error) => {
                    updateStatus('Connection error - check console for details', 'error');
                    updateConnectionStatus(false);
                    console.error('WebSocket error:', error);
                };
                
            } catch (error) {
                updateStatus('Failed to connect: ' + error.message, 'error');
                console.error('Connection failed:', error);
            }
        }
        
        function handleWebSocketMessage(data) {
            switch (data.type) {
                case 'connection':
                    updateStatus(data.message, 'success');
                    break;
                    
                case 'response':
                    displayResponse(data);
                    isModelLoading = false;
                    break;
                    
                case 'error':
                    updateStatus('Error: ' + data.message, 'error');
                    isModelLoading = false;
                    break;
                    
                case 'info':
                    updateStatus(data.message, 'loading');
                    break;
                    
                default:
                    console.log('Unknown message type:', data);
            }
        }
        
        function displayResponse(data) {
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.textContent = data.text;
            
            // Update metrics
            document.getElementById('processingTimeMetric').textContent = data.processing_time_ms || '-';
            document.getElementById('audioLengthMetric').textContent = 
                data.audio_duration_ms ? (data.audio_duration_ms / 1000).toFixed(1) : '-';
            
            // Calculate latency (approximate)
            const latency = data.processing_time_ms || 0;
            document.getElementById('latencyMetric').textContent = latency;
            
            updateStatus('Ready for next recording', 'success');
        }
        
        async function startRecording() {
            try {
                audioStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    }
                });
                
                mediaRecorder = new MediaRecorder(audioStream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await sendAudioData(audioBlob);
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                updateStatus('🎙️ Recording... Click stop when finished', 'success');
                
            } catch (error) {
                updateStatus('Microphone access denied: ' + error.message, 'error');
                console.error('Recording error:', error);
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                
                if (!isModelLoading) {
                    updateStatus('🤖 Processing audio... (First time may take 30+ seconds for model loading)', 'loading');
                    isModelLoading = true;
                } else {
                    updateStatus('🤖 Processing audio...', 'loading');
                }
                
                // Stop audio stream
                if (audioStream) {
                    audioStream.getTracks().forEach(track => track.stop());
                }
            }
        }
        
        // FIXED: Proper base64 conversion that handles large files
        function arrayBufferToBase64(buffer) {
            const bytes = new Uint8Array(buffer);
            let binary = '';
            const chunkSize = 8192;
            
            for (let i = 0; i < bytes.length; i += chunkSize) {
                const chunk = bytes.slice(i, i + chunkSize);
                binary += String.fromCharCode.apply(null, chunk);
            }
            
            return btoa(binary);
        }
        
        async function sendAudioData(audioBlob) {
            try {
                // Convert to ArrayBuffer first, then to Float32Array
                const arrayBuffer = await audioBlob.arrayBuffer();
                
                // Create an audio context to decode the audio
                const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 16000
                });
                
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                const float32Array = audioBuffer.getChannelData(0); // Get mono channel
                
                // FIXED: Convert to base64 properly for large files
                const base64Audio = arrayBufferToBase64(float32Array.buffer);
                
                const message = {
                    type: 'audio',
                    audio_data: base64Audio,
                    mode: document.getElementById('modeSelect').value,
                    prompt: document.getElementById('promptInput').value
                };
                
                ws.send(JSON.stringify(message));
                
            } catch (error) {
                updateStatus('Error sending audio: ' + error.message, 'error');
                console.error('Audio processing error:', error);
                isModelLoading = false;
            }
        }
        
        // Initialize on page load
        window.addEventListener('load', () => {
            detectEnvironment();
            updateStatus('Click Connect to start');
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def api_status():
    """API endpoint for server status"""
    try:
        voxtral_model = get_voxtral_model()
        model_info = voxtral_model.get_model_info()
        return JSONResponse({
            "status": "healthy" if voxtral_model.is_initialized else "initializing",
            "timestamp": time.time(),
            "model": model_info,
            "config": {
                "sample_rate": config.audio.sample_rate,
                "tcp_ports": config.server.tcp_ports,
                "latency_target": config.streaming.latency_target_ms
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "timestamp": time.time(),
            "error": str(e)
        }, status_code=500)

# WebSocket endpoint for RunPod compatibility
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint integrated into FastAPI for RunPod compatibility"""
    await websocket.accept()
    logger.info(f"WebSocket client connected: {websocket.client}")
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "Connected to Voxtral streaming server",
            "server_config": {
                "sample_rate": config.audio.sample_rate,
                "chunk_size": config.audio.chunk_size,
                "latency_target": config.streaming.latency_target_ms
            }
        }))
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "audio":
                await handle_audio_data(websocket, message)
                
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong", 
                    "timestamp": time.time()
                }))
                
            elif msg_type == "status":
                voxtral_model = get_voxtral_model()
                model_info = voxtral_model.get_model_info()
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "model_info": model_info
                }))
                
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))
        except:
            pass

async def handle_audio_data(websocket: WebSocket, data: dict):
    """Process incoming audio data through WebSocket"""
    try:
        start_time = time.time()
        
        # Get models with lazy initialization
        voxtral_model = get_voxtral_model()
        audio_processor = get_audio_processor()
        
        # Initialize model if needed (first time use)
        if not voxtral_model.is_initialized:
            await websocket.send_text(json.dumps({
                "type": "info",
                "message": "Loading AI model... This may take 30+ seconds on first use"
            }))
            await voxtral_model.initialize()
        
        # Extract audio data
        audio_b64 = data.get("audio_data")
        if not audio_b64:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No audio data provided"
            }))
            return
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_b64)
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        
        # Validate audio format
        if not audio_processor.validate_audio_format(audio_array):
            await websocket.send_text(json.dumps({
                "type": "error", 
                "message": "Invalid audio format"
            }))
            return
        
        # Preprocess audio
        audio_tensor = audio_processor.preprocess_audio(audio_array)
        
        # Get processing mode
        mode = data.get("mode", "transcribe")
        prompt = data.get("prompt", "")
        
        # Process with Voxtral
        if mode == "transcribe":
            response = await voxtral_model.transcribe_audio(audio_tensor)
        elif mode == "understand":
            if not prompt:
                prompt = "What can you tell me about this audio?"
            response = await voxtral_model.understand_audio(audio_tensor, prompt)
        else:
            # General processing
            response = await voxtral_model.process_audio_stream(audio_tensor, prompt)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Send response
        await websocket.send_text(json.dumps({
            "type": "response",
            "mode": mode,
            "text": response,
            "processing_time_ms": round(processing_time, 1),
            "audio_duration_ms": len(audio_array) / config.audio.sample_rate * 1000
        }))
        
        logger.debug(f"Processed audio in {processing_time:.1f}ms")
        
    except Exception as e:
        logger.error(f"Error handling audio data: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Processing error: {str(e)}"
        }))

# REMOVED: No automatic model initialization on startup
# This allows the UI server to start quickly

def main():
    """Run the UI server"""
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.http_port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
