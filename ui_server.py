"""
FastAPI UI server for web interface
Serves the web UI and handles HTTP endpoints
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
import json
import time
from pathlib import Path

from src.utils.config import config
from src.models.voxtral_model import voxtral_model

# Initialize FastAPI app
app = FastAPI(
    title="Voxtral Real-time Streaming UI",
    description="Web interface for Voxtral real-time audio streaming",
    version="1.0.0"
)

# Setup static files and templates
static_path = Path(__file__).parent.parent.parent / "static"
templates_path = Path(__file__).parent.parent.parent / "templates"

if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Initialize templates if directory exists
templates = None
if templates_path.exists():
    templates = Jinja2Templates(directory=str(templates_path))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface"""
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
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        Disconnected
    </div>
    
    <div class="container">
        <h1>🎙️ Voxtral Real-time Streaming</h1>
        
        <div class="status" id="status">
            Initializing...
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
        
        function updateStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.style.borderLeftColor = type === 'error' ? '#e17055' : type === 'success' ? '#00b894' : '#74b9ff';
        }
        
        function updateConnectionStatus(connected) {
            const status = document.getElementById('connectionStatus');
            status.textContent = connected ? 'Connected' : 'Disconnected';
            status.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
        }
        
        async function connect() {
            try {
                const wsUrl = `ws://${window.location.hostname}:8765`;
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
                
                ws.onclose = () => {
                    updateStatus('Disconnected from server');
                    updateConnectionStatus(false);
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = true;
                };
                
                ws.onerror = (error) => {
                    updateStatus('Connection error: ' + error.message, 'error');
                    updateConnectionStatus(false);
                };
                
            } catch (error) {
                updateStatus('Failed to connect: ' + error.message, 'error');
            }
        }
        
        function handleWebSocketMessage(data) {
            switch (data.type) {
                case 'connection':
                    updateStatus(data.message, 'success');
                    break;
                    
                case 'response':
                    displayResponse(data);
                    break;
                    
                case 'error':
                    updateStatus('Error: ' + data.message, 'error');
                    break;
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
        }
        
        async function startRecording() {
            try {
                audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(audioStream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    await sendAudioData(audioBlob);
                };
                
                mediaRecorder.start();
                isRecording = true;
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                updateStatus('Recording... Click stop when finished', 'success');
                
            } catch (error) {
                updateStatus('Microphone access denied: ' + error.message, 'error');
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                updateStatus('Processing audio...', 'info');
            }
        }
        
        async function sendAudioData(audioBlob) {
            try {
                const arrayBuffer = await audioBlob.arrayBuffer();
                const audioData = new Float32Array(arrayBuffer);
                const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData.buffer)));
                
                const message = {
                    type: 'audio',
                    audio_data: base64Audio,
                    mode: document.getElementById('modeSelect').value,
                    prompt: document.getElementById('promptInput').value
                };
                
                ws.send(JSON.stringify(message));
                
            } catch (error) {
                updateStatus('Error sending audio: ' + error.message, 'error');
            }
        }
        
        // Initialize
        updateStatus('Click Connect to start');
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def api_status():
    """API endpoint for server status"""
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

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    if not voxtral_model.is_initialized:
        asyncio.create_task(voxtral_model.initialize())

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