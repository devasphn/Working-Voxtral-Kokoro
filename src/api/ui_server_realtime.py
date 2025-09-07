"""
FIXED UI server with proper module imports and main execution
Enhanced for REAL-TIME streaming with corrected import paths
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
import logging
import sys
import os

# Add current directory to Python path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.config import config
from src.utils.logging_config import logger

# Initialize FastAPI app
app = FastAPI(
    title="Voxtral Real-time Streaming UI",
    description="Web interface for Voxtral REAL-TIME audio streaming",
    version="2.0.0"
)

# Enhanced logging for real-time streaming
streaming_logger = logging.getLogger("realtime_streaming")
streaming_logger.setLevel(logging.DEBUG)

# Global variables for lazy initialization
_voxtral_model = None
_audio_processor = None

def get_voxtral_model():
    """Lazy initialization of Voxtral model"""
    global _voxtral_model
    if _voxtral_model is None:
        from src.models.voxtral_model_realtime import voxtral_model
        _voxtral_model = voxtral_model
        streaming_logger.info("Voxtral model lazy-loaded")
    return _voxtral_model

def get_audio_processor():
    """Lazy initialization of Audio processor"""
    global _audio_processor
    if _audio_processor is None:
        from src.models.audio_processor_realtime import AudioProcessor
        _audio_processor = AudioProcessor()
        streaming_logger.info("Audio processor lazy-loaded")
    return _audio_processor

# Setup static files if directory exists
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve REAL-TIME streaming web interface"""
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
        .connect-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
        }
        .stream-btn {
            background: linear-gradient(45deg, #00b894, #00a085);
            color: white;
        }
        .stop-btn {
            background: linear-gradient(45deg, #e17055, #d63031);
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
            max-height: 400px;
            overflow-y: auto;
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
        .streaming {
            background: #0984e3;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
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
        .realtime-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #e17055;
            border-radius: 50%;
            margin-left: 10px;
        }
        .realtime-indicator.active {
            background: #00b894;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        .volume-meter {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }
        .volume-bar {
            height: 100%;
            background: linear-gradient(45deg, #00b894, #74b9ff);
            width: 0%;
            transition: width 0.1s;
        }
        .log-panel {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
        }
        select, input {
            padding: 10px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        Disconnected
    </div>
    
    <div class="container">
        <h1>🎙️ Voxtral Real-time Streaming</h1>
        <p style="text-align: center; opacity: 0.8;">TRUE real-time streaming - continuous audio processing</p>
        
        <div class="url-info" id="urlInfo">
            <strong>WebSocket URL:</strong> <span id="wsUrl">Detecting...</span><br>
            <strong>Environment:</strong> <span id="envInfo">Detecting...</span><br>
            <strong>Mode:</strong> Real-time continuous streaming
        </div>
        
        <div class="status" id="status">
            Ready to connect. Click "Connect" to start real-time streaming.
        </div>
        
        <div class="controls">
            <button id="connectBtn" class="connect-btn" onclick="connect()">Connect</button>
            <button id="streamBtn" class="stream-btn" onclick="startRealtimeStreaming()" disabled>Start Real-time Stream</button>
            <button id="stopBtn" class="stop-btn" onclick="stopRealtimeStreaming()" disabled>Stop Stream</button>
        </div>
        
        <div class="audio-controls">
            <label>Mode:</label>
            <select id="modeSelect">
                <option value="transcribe">Transcribe</option>
                <option value="understand">Understand</option>
            </select>
            
            <label>Prompt:</label>
            <input type="text" id="promptInput" placeholder="Optional prompt..." style="flex: 1; min-width: 200px;">
            
            <span>Real-time:</span>
            <span class="realtime-indicator" id="realtimeIndicator"></span>
        </div>
        
        <div class="volume-meter">
            <div class="volume-bar" id="volumeBar"></div>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" id="latencyMetric">-</div>
                <div class="metric-label">Avg Latency (ms)</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="chunksMetric">0</div>
                <div class="metric-label">Chunks Processed</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="durationMetric">00:00</div>
                <div class="metric-label">Stream Duration</div>
            </div>
        </div>
        
        <div class="response" id="response" style="display: none;">
            Real-time responses will appear here...
        </div>
        
        <div class="log-panel" id="logPanel" style="display: none;">
            <div id="logContent"></div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let audioContext = null;
        let mediaStream = null;
        let audioWorkletNode = null;
        let isStreaming = false;
        let wsUrl = '';
        let chunkCounter = 0;
        let streamStartTime = null;
        let latencySum = 0;
        let responseCount = 0;
        
        // Streaming configuration
        const CHUNK_SIZE = 4096;  // Audio buffer size
        const CHUNK_INTERVAL = 1000; // Send chunks every 1 second
        const SAMPLE_RATE = 16000;
        
        function log(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const logPanel = document.getElementById('logPanel');
            const logContent = document.getElementById('logContent');
            
            logPanel.style.display = 'block';
            
            const logEntry = document.createElement('div');
            logEntry.innerHTML = `<span style="color: #74b9ff;">[${timestamp}]</span> ${message}`;
            logContent.appendChild(logEntry);
            logContent.scrollTop = logContent.scrollHeight;
            
            console.log(`[Voxtral Real-time] ${message}`);
        }
        
        // Detect environment and construct WebSocket URL
        function detectEnvironment() {
            const hostname = window.location.hostname;
            const protocol = window.location.protocol;
            
            if (hostname.includes('proxy.runpod.net')) {
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo').textContent = 'RunPod Cloud (HTTP Proxy)';
            } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
                wsUrl = `ws://${hostname}:8000/ws`;
                document.getElementById('envInfo').textContent = 'Local Development';
            } else {
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo').textContent = 'Custom Deployment';
            }
            
            document.getElementById('wsUrl').textContent = wsUrl;
            log(`WebSocket URL detected: ${wsUrl}`);
        }
        
        function updateStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            
            // Update visual styling
            if (type === 'loading') {
                status.style.borderLeftColor = '#f39c12';
            } else {
                status.style.borderLeftColor = type === 'error' ? '#e17055' : 
                                               type === 'success' ? '#00b894' : '#74b9ff';
            }
            
            log(message, type);
        }
        
        function updateConnectionStatus(connected, streaming = false) {
            const status = document.getElementById('connectionStatus');
            const indicator = document.getElementById('realtimeIndicator');
            
            if (streaming) {
                status.textContent = 'Streaming';
                status.className = 'connection-status streaming';
                indicator.classList.add('active');
            } else if (connected) {
                status.textContent = 'Connected';
                status.className = 'connection-status connected';
                indicator.classList.remove('active');
            } else {
                status.textContent = 'Disconnected';
                status.className = 'connection-status disconnected';
                indicator.classList.remove('active');
            }
        }
        
        async function connect() {
            try {
                updateStatus('Connecting to Voxtral streaming server...', 'loading');
                log('Attempting WebSocket connection...');
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    updateStatus('Connected! Ready to start real-time streaming.', 'success');
                    updateConnectionStatus(true);
                    document.getElementById('connectBtn').disabled = true;
                    document.getElementById('streamBtn').disabled = false;
                    log('WebSocket connection established');
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = (event) => {
                    updateStatus(`Disconnected from server (Code: ${event.code})`, 'error');
                    updateConnectionStatus(false);
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('streamBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = true;
                    log(`WebSocket connection closed: ${event.code}`);
                };
                
                ws.onerror = (error) => {
                    updateStatus('Connection error - check console for details', 'error');
                    updateConnectionStatus(false);
                    log('WebSocket error occurred');
                    console.error('WebSocket error:', error);
                };
                
            } catch (error) {
                updateStatus('Failed to connect: ' + error.message, 'error');
                log('Connection failed: ' + error.message);
            }
        }
        
        function handleWebSocketMessage(data) {
            log(`Received message type: ${data.type}`);
            
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
                    
                case 'info':
                    updateStatus(data.message, 'loading');
                    break;
                    
                default:
                    log(`Unknown message type: ${data.type}`);
            }
        }
        
        function displayResponse(data) {
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            
            // Append new response with timestamp
            const timestamp = new Date().toLocaleTimeString();
            const responseEntry = `[${timestamp}] ${data.text}\\n`;
            responseDiv.textContent += responseEntry;
            responseDiv.scrollTop = responseDiv.scrollHeight;
            
            // Update metrics
            responseCount++;
            if (data.processing_time_ms) {
                latencySum += data.processing_time_ms;
                document.getElementById('latencyMetric').textContent = 
                    Math.round(latencySum / responseCount);
            }
            
            document.getElementById('chunksMetric').textContent = responseCount;
            
            log(`Response received: "${data.text}" (${data.processing_time_ms}ms)`);
        }
        
        function updateStreamDuration() {
            if (streamStartTime && isStreaming) {
                const duration = Math.floor((Date.now() - streamStartTime) / 1000);
                const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
                const seconds = (duration % 60).toString().padStart(2, '0');
                document.getElementById('durationMetric').textContent = `${minutes}:${seconds}`;
            }
        }
        
        // REAL-TIME AUDIO STREAMING FUNCTIONS
        
        async function startRealtimeStreaming() {
            try {
                log('Starting real-time audio streaming...');
                updateStatus('Initializing real-time audio capture...', 'loading');
                
                // Request microphone access
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        sampleRate: SAMPLE_RATE,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                
                log('Microphone access granted');
                
                // Create AudioContext
                audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: SAMPLE_RATE
                });
                
                await audioContext.resume();
                log(`Audio context created with sample rate: ${audioContext.sampleRate}`);
                
                // Create ScriptProcessorNode for real-time audio processing
                audioWorkletNode = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
                const source = audioContext.createMediaStreamSource(mediaStream);
                
                // Connect audio processing chain
                source.connect(audioWorkletNode);
                audioWorkletNode.connect(audioContext.destination);
                
                // Real-time audio processing
                let audioBuffer = [];
                let lastChunkTime = Date.now();
                
                audioWorkletNode.onaudioprocess = (event) => {
                    if (!isStreaming) return;
                    
                    const inputBuffer = event.inputBuffer;
                    const inputData = inputBuffer.getChannelData(0);
                    
                    // Update volume meter
                    updateVolumeMeter(inputData);
                    
                    // Add audio to buffer
                    audioBuffer.push(...inputData);
                    
                    // Send chunk every CHUNK_INTERVAL milliseconds
                    const now = Date.now();
                    if (now - lastChunkTime >= CHUNK_INTERVAL && audioBuffer.length > 0) {
                        sendAudioChunk(new Float32Array(audioBuffer));
                        audioBuffer = [];
                        lastChunkTime = now;
                    }
                };
                
                // Start streaming
                isStreaming = true;
                streamStartTime = Date.now();
                
                // Update UI
                document.getElementById('streamBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                updateConnectionStatus(true, true);
                updateStatus('🎙️ Real-time streaming active - speak into microphone', 'success');
                
                // Start duration timer
                setInterval(updateStreamDuration, 1000);
                
                log('Real-time streaming started successfully');
                
            } catch (error) {
                updateStatus('Failed to start streaming: ' + error.message, 'error');
                log('Streaming start failed: ' + error.message);
                console.error('Streaming error:', error);
            }
        }
        
        function stopRealtimeStreaming() {
            isStreaming = false;
            
            log('Stopping real-time streaming...');
            
            if (audioWorkletNode) {
                audioWorkletNode.disconnect();
                audioWorkletNode = null;
            }
            
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
            
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            
            // Update UI
            document.getElementById('streamBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            updateConnectionStatus(true, false);
            updateStatus('Real-time streaming stopped. Ready to stream again.', 'info');
            
            // Reset volume meter
            document.getElementById('volumeBar').style.width = '0%';
            
            log('Real-time streaming stopped');
        }
        
        function updateVolumeMeter(audioData) {
            // Calculate RMS volume
            let sum = 0;
            for (let i = 0; i < audioData.length; i++) {
                sum += audioData[i] * audioData[i];
            }
            const rms = Math.sqrt(sum / audioData.length);
            const volume = Math.min(100, rms * 100 * 10); // Scale and limit to 100%
            
            document.getElementById('volumeBar').style.width = volume + '%';
        }
        
        function sendAudioChunk(audioData) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('Cannot send audio - WebSocket not connected');
                return;
            }
            
            try {
                // Convert Float32Array to base64
                const base64Audio = arrayBufferToBase64(audioData.buffer);
                
                const message = {
                    type: 'audio_chunk',
                    audio_data: base64Audio,
                    mode: document.getElementById('modeSelect').value,
                    prompt: document.getElementById('promptInput').value,
                    chunk_id: chunkCounter++,
                    timestamp: Date.now()
                };
                
                ws.send(JSON.stringify(message));
                log(`Sent audio chunk ${chunkCounter} (${audioData.length} samples)`);
                
            } catch (error) {
                log('Error sending audio chunk: ' + error.message);
                console.error('Audio chunk error:', error);
            }
        }
        
        // Helper function for base64 conversion
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
        
        // Initialize on page load
        window.addEventListener('load', () => {
            detectEnvironment();
            updateStatus('Ready to connect for real-time streaming');
            log('Application initialized');
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (isStreaming) {
                stopRealtimeStreaming();
            }
            if (ws) {
                ws.close();
            }
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

# WebSocket endpoint for REAL-TIME streaming
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for REAL-TIME continuous audio streaming"""
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    streaming_logger.info(f"[REALTIME] Client connected: {client_id}")
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "message": "Connected to Voxtral real-time streaming server",
            "server_config": {
                "sample_rate": config.audio.sample_rate,
                "chunk_size": config.audio.chunk_size,
                "latency_target": config.streaming.latency_target_ms,
                "streaming_mode": "real_time_continuous"
            }
        }))
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            
            streaming_logger.debug(f"[REALTIME] Received message type: {msg_type} from {client_id}")
            
            if msg_type == "audio_chunk":
                # Handle real-time audio chunk
                await handle_realtime_audio_chunk(websocket, message, client_id)
                
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
                streaming_logger.warning(f"[REALTIME] Unknown message type: {msg_type}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                }))
                
    except WebSocketDisconnect:
        streaming_logger.info(f"[REALTIME] Client disconnected: {client_id}")
    except Exception as e:
        streaming_logger.error(f"[REALTIME] WebSocket error for {client_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Server error: {str(e)}"
            }))
        except:
            pass

async def handle_realtime_audio_chunk(websocket: WebSocket, data: dict, client_id: str):
    """Process real-time audio chunks as they arrive"""
    try:
        chunk_start_time = time.time()
        chunk_id = data.get("chunk_id", 0)
        
        streaming_logger.info(f"[REALTIME] Processing chunk {chunk_id} for {client_id}")
        
        # Get models with lazy initialization
        voxtral_model = get_voxtral_model()
        audio_processor = get_audio_processor()
        
        # Initialize model if needed (first time use)
        if not voxtral_model.is_initialized:
            streaming_logger.info(f"[REALTIME] Initializing Voxtral model for {client_id}")
            await websocket.send_text(json.dumps({
                "type": "info",
                "message": "Loading AI model for real-time processing... This may take 30+ seconds"
            }))
            await voxtral_model.initialize()
            streaming_logger.info(f"[REALTIME] Model initialized for {client_id}")
        
        # Extract and validate audio data
        audio_b64 = data.get("audio_data")
        if not audio_b64:
            streaming_logger.warning(f"[REALTIME] No audio data in chunk {chunk_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "No audio data provided"
            }))
            return
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_b64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            streaming_logger.debug(f"[REALTIME] Decoded {len(audio_array)} audio samples from chunk {chunk_id}")
        except Exception as e:
            streaming_logger.error(f"[REALTIME] Audio decoding error for chunk {chunk_id}: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Audio decoding error: {str(e)}"
            }))
            return
        
        # Validate audio format
        if not audio_processor.validate_realtime_chunk(audio_array, chunk_id):
            streaming_logger.warning(f"[REALTIME] Invalid audio format in chunk {chunk_id}")
            await websocket.send_text(json.dumps({
                "type": "error", 
                "message": "Invalid audio format - chunk too small or corrupted"
            }))
            return
        
        # Preprocess audio
        try:
            audio_tensor = audio_processor.preprocess_realtime_chunk(audio_array, chunk_id)
            streaming_logger.debug(f"[REALTIME] Preprocessed audio tensor shape: {audio_tensor.shape}")
        except Exception as e:
            streaming_logger.error(f"[REALTIME] Audio preprocessing error for chunk {chunk_id}: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Audio preprocessing error: {str(e)}"
            }))
            return
        
        # Get processing parameters
        mode = data.get("mode", "transcribe")
        prompt = data.get("prompt", "")
        
        streaming_logger.debug(f"[REALTIME] Processing chunk {chunk_id} in mode '{mode}'")
        
        # Process with Voxtral
        try:
            if mode == "transcribe":
                response = await voxtral_model.transcribe_audio(audio_tensor)
            elif mode == "understand":
                if not prompt:
                    prompt = "What can you tell me about this audio?"
                response = await voxtral_model.understand_audio(audio_tensor, prompt)
            else:
                response = await voxtral_model.process_audio_stream(audio_tensor, prompt)
                
            processing_time = (time.time() - chunk_start_time) * 1000
            
            streaming_logger.info(f"[REALTIME] Chunk {chunk_id} processed in {processing_time:.1f}ms: '{response[:50]}...'")
            
        except Exception as e:
            streaming_logger.error(f"[REALTIME] Voxtral processing error for chunk {chunk_id}: {e}")
            response = f"Processing error: {str(e)}"
            processing_time = (time.time() - chunk_start_time) * 1000
        
        # Send response
        await websocket.send_text(json.dumps({
            "type": "response",
            "mode": mode,
            "text": response,
            "chunk_id": chunk_id,
            "processing_time_ms": round(processing_time, 1),
            "audio_duration_ms": len(audio_array) / config.audio.sample_rate * 1000,
            "timestamp": data.get("timestamp", time.time())
        }))
        
        streaming_logger.info(f"[REALTIME] Response sent for chunk {chunk_id} to {client_id}")
        
    except Exception as e:
        streaming_logger.error(f"[REALTIME] Error handling audio chunk: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Chunk processing error: {str(e)}"
        }))

# FIXED: Add proper main execution block
if __name__ == "__main__":
    streaming_logger.info("Starting Voxtral Real-time Streaming UI Server")
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.http_port,
        log_level="info"
    )
