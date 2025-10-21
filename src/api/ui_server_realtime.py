"""
FIXED UI server for CONVERSATIONAL real-time streaming
Improved WebSocket handling and silence detection UI feedback
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
    title="Voxtral Conversational Streaming UI",
    description="Web interface for Voxtral CONVERSATIONAL audio streaming with VAD",
    version="2.2.0"
)

# Enhanced logging for real-time streaming
streaming_logger = logging.getLogger("realtime_streaming")
streaming_logger.setLevel(logging.DEBUG)

# Global variables for unified model management
_unified_manager = None
_audio_processor = None
_performance_monitor = None

# Response deduplication tracking
recent_responses = {}  # client_id -> last_response_text

def get_unified_manager():
    """Get unified model manager instance"""
    global _unified_manager
    if _unified_manager is None:
        from src.models.unified_model_manager import unified_model_manager
        _unified_manager = unified_model_manager
        streaming_logger.info("Unified model manager loaded")
    return _unified_manager

def get_audio_processor():
    """Lazy initialization of Audio processor"""
    global _audio_processor
    if _audio_processor is None:
        from src.models.audio_processor_realtime import AudioProcessor
        _audio_processor = AudioProcessor()
        streaming_logger.info("Audio processor lazy-loaded")
    return _audio_processor

def get_performance_monitor():
    """Get performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        from src.utils.performance_monitor import performance_monitor
        _performance_monitor = performance_monitor
        streaming_logger.info("Performance monitor loaded")
    return _performance_monitor

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve CONVERSATIONAL streaming web interface with VAD feedback"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voxtral Conversational AI with VAD</title>
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
        .conversation {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
            border-left: 4px solid #74b9ff;
            max-height: 400px;
            overflow-y: auto;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
        }
        .user-message {
            background: rgba(0, 184, 148, 0.3);
            text-align: right;
        }
        .ai-message {
            background: rgba(116, 185, 255, 0.3);
        }
        .silence-message {
            background: rgba(155, 155, 155, 0.3);
            font-style: italic;
            opacity: 0.7;
        }
        .timestamp {
            font-size: 0.8em;
            opacity: 0.7;
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
        .vad-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .vad-status {
            padding: 5px 15px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 0.9em;
        }
        .vad-speech {
            background: #00b894;
            color: white;
        }
        .vad-silence {
            background: #636e72;
            color: white;
        }
        .vad-processing {
            background: #fdcb6e;
            color: #2d3436;
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
        .realtime-indicator.speech {
            background: #fdcb6e;
            animation: pulse-speech 0.5s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        @keyframes pulse-speech {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }
        .streaming-container {
            margin: 20px 0;
            padding: 15px;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            background-color: #f9f9f9;
        }
        .streaming-response {
            min-height: 60px;
            padding: 15px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            font-family: Arial, sans-serif;
            line-height: 1.5;
            color: #333;
            animation: pulse 1s infinite;
        }
        .streaming-response.final {
            animation: none;
            background-color: #e8f5e8;
            border-color: #4CAF50;
        }
        .streaming-stats {
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }
        .streaming-stats span {
            margin-right: 20px;
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
        .volume-bar.speech {
            background: linear-gradient(45deg, #fdcb6e, #e17055);
        }
        select, input {
            padding: 10px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        .performance-warning {
            background: rgba(241, 196, 15, 0.3);
            border-left: 4px solid #f1c40f;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 0.9em;
        }
        .vad-stats {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            margin-top: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        Disconnected
    </div>
    
    <div class="container">
        <h1>🎙️ Voxtral Conversational AI</h1>
        <p style="text-align: center; opacity: 0.8;">Intelligent conversation with Voice Activity Detection & Real-time Transcription</p>
        
        <div class="vad-indicator">
            <strong>🎤 Voice Status:</strong>
            <span class="vad-status vad-silence" id="vadStatus">Waiting</span>
            <span>Live:</span>
            <span class="realtime-indicator" id="realtimeIndicator"></span>
        </div>
        
        <div class="status" id="status">
            Ready to connect. Click "Connect" to start conversation.
        </div>
        
        <div class="controls">
            <button id="connectBtn" class="connect-btn" onclick="connect()">Connect</button>
            <button id="streamBtn" class="stream-btn" onclick="startConversation()" disabled>Start Conversation</button>
            <button id="stopBtn" class="stop-btn" onclick="stopConversation()" disabled>Stop Conversation</button>
        </div>

        <!-- Mode Selection -->
        <div class="audio-controls" style="justify-content: center; margin-bottom: 20px;">
            <div style="text-align: center; padding: 15px; background: rgba(255, 255, 255, 0.1); border-radius: 10px;">
                <strong>🤖 Conversation Mode</strong>
                <div style="margin: 10px 0;">
                    <label style="margin-right: 20px;">
                        <input type="radio" name="mode" value="transcribe" checked onchange="updateMode()">
                        📝 Transcribe
                    </label>
                </div>
                <p style="margin: 5px 0; opacity: 0.8; font-size: 0.9em;" id="modeDescription">AI assistant ready for text-based conversation</p>
            </div>
        </div>


        
        <div class="volume-meter">
            <div class="volume-bar" id="volumeBar"></div>
        </div>
        
        <div class="vad-stats" id="vadStats" style="display: none;">
            <strong>VAD Statistics:</strong><br>
            Speech Chunks: <span id="speechChunks">0</span> | 
            Silence Chunks: <span id="silenceChunks">0</span> | 
            Processing Rate: <span id="processingRate">0%</span>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" id="latencyMetric">-</div>
                <div class="metric-label">Avg Latency (ms)</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="chunksMetric">0</div>
                <div class="metric-label">Speech Processed</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="silenceSkipped">0</div>
                <div class="metric-label">Silence Skipped</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="durationMetric">00:00</div>
                <div class="metric-label">Conversation Duration</div>
            </div>
        </div>
        
        <!-- RESPONSE DISPLAY -->
        <div class="streaming-container">
            <h3>🎯 AI Response:</h3>
            <div id="response-display" class="streaming-response">
                <!-- AI response will appear here -->
            </div>
        </div>
        
        <div class="conversation" id="conversation" style="display: none;">
            <div id="conversationContent">
                <div class="message ai-message">
                    <div><strong>AI:</strong> Hello! I'm ready to have a conversation. I'll only respond when I detect speech, so there's no need to worry about background noise.</div>
                    <div class="timestamp">Ready to chat with VAD enabled</div>
                </div>
            </div>
        </div>


        
        <div id="performanceWarning" class="performance-warning" style="display: none;">
            ⚠️ High latency detected. For better performance, try using "Simple Transcription" mode or check your internet connection.
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
        let speechChunks = 0;
        let silenceChunks = 0;
        let lastVadUpdate = 0;

        // Enhanced continuous speech buffering variables
        let continuousAudioBuffer = [];
        let speechStartTime = null;
        let lastSpeechTime = null;
        let isSpeechActive = false;
        let silenceStartTime = null;
        let pendingResponse = false;
        let lastResponseText = '';  // For deduplication

        // Audio playback queue management
        let audioQueue = [];
        let isPlayingAudio = false;
        let currentAudio = null;
        
        // Mode variables (Voxtral ASR-only)
        let currentMode = 'transcribe';

        // Initialize audio context properly
        function initializeAudioContext() {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 16000,
                    latencyHint: 'interactive'
                });
            }
            return audioContext;
        }
        
        // Sequential audio playback
        function playNextAudioChunk() {
            if (audioQueue.length === 0) {
                isPlayingAudio = false;
                return;
            }
            
            isPlayingAudio = true;
            const audioItem = audioQueue.shift();
            const source = audioContext.createBufferSource();
            source.buffer = audioItem.buffer;
            source.connect(audioContext.destination);
            
            source.onended = () => {
                log(`✅ Audio chunk ${audioItem.chunk_id} played`);
                
                // Play next chunk immediately
                if (audioQueue.length > 0) {
                    setTimeout(playNextAudioChunk, 50); // Small gap between chunks
                } else {
                    isPlayingAudio = false;
                    log('🎉 All audio chunks played');
                }
            };
            
            source.start();
        }
        
        // Update response display for chunked text
        function updateResponseDisplay(text, isFinal) {
            const responseElement = document.getElementById('response-display');
            if (responseElement) {
                if (isFinal) {
                    responseElement.innerHTML = '<strong>Response:</strong> ' + text;
                } else {
                    responseElement.innerHTML += text + ' ';
                }
                responseElement.scrollTop = responseElement.scrollHeight;
            }
        }

        // ULTRA-LOW LATENCY frontend settings
        const SAMPLE_RATE = 16000;
        const CHUNK_SIZE = 4096;
        const MIN_SPEECH_DURATION = 800;     // INCREASED: Minimum speech duration (was 500)
        const END_OF_SPEECH_SILENCE = 1200;   // INCREASED: End of speech silence (was 800)
        const SPEECH_THRESHOLD = 0.025;     // INCREASED: Speech threshold (was 0.01)
        const LATENCY_WARNING_THRESHOLD = 1000;
        
        function log(message, type = 'info') {
            console.log(`[Voxtral VAD] ${message}`);
        }

        // Enhanced VAD function for continuous speech detection
        function detectSpeechInBuffer(inputData) {
            // Calculate RMS energy
            let sum = 0;
            for (let i = 0; i < inputData.length; i++) {
                sum += inputData[i] * inputData[i];
            }
            const rms = Math.sqrt(sum / inputData.length);
            
            // FIXED: Higher threshold to avoid false positives
            const speechThreshold = 0.02;  // INCREASED from 0.01 to 0.02
            return rms > speechThreshold;
        }
        
        // Detect environment and construct WebSocket URL
        function detectEnvironment() {
            const hostname = window.location.hostname;
            const protocol = window.location.protocol;
            
            if (hostname.includes('proxy.runpod.net')) {
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo') && (document.getElementById('envInfo').textContent = 'RunPod Cloud (HTTP Proxy)');
            } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
                wsUrl = `ws://${hostname}:8000/ws`;
                document.getElementById('envInfo') && (document.getElementById('envInfo').textContent = 'Local Development');
            } else {
                const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${wsProtocol}//${hostname}/ws`;
                document.getElementById('envInfo') && (document.getElementById('envInfo').textContent = 'Custom Deployment');
            }
            
            log(`WebSocket URL detected: ${wsUrl}`);
        }
        
        function updateStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            
            status.style.borderLeftColor = type === 'error' ? '#e17055' : 
                                           type === 'success' ? '#00b894' : '#74b9ff';
            log(message, type);
        }
        
        function updateConnectionStatus(connected, streaming = false) {
            const status = document.getElementById('connectionStatus');
            const indicator = document.getElementById('realtimeIndicator');
            
            if (streaming) {
                status.textContent = 'Conversing';
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
        
        function updateVadStatus(status, hasSpeech = false) {
            const vadStatus = document.getElementById('vadStatus');
            const indicator = document.getElementById('realtimeIndicator');
            
            if (status === 'speech') {
                vadStatus.textContent = 'Speaking';
                vadStatus.className = 'vad-status vad-speech';
                indicator.classList.add('speech');
                indicator.classList.remove('active');
            } else if (status === 'silence') {
                vadStatus.textContent = 'Silent';
                vadStatus.className = 'vad-status vad-silence';
                indicator.classList.remove('speech');
                if (isStreaming) indicator.classList.add('active');
            } else if (status === 'processing') {
                vadStatus.textContent = 'Processing';
                vadStatus.className = 'vad-status vad-processing';
            } else {
                vadStatus.textContent = 'Waiting';
                vadStatus.className = 'vad-status vad-silence';
                indicator.classList.remove('speech', 'active');
            }
        }
        
        function updateVadStats() {
            document.getElementById('speechChunks').textContent = speechChunks;
            document.getElementById('silenceChunks').textContent = silenceChunks;
            const total = speechChunks + silenceChunks;
            const processingRate = total > 0 ? Math.round((speechChunks / total) * 100) : 0;
            document.getElementById('processingRate').textContent = processingRate;
            document.getElementById('silenceSkipped').textContent = silenceChunks;
        }

        // Mode update function (Voxtral ASR-only mode)
        function updateMode() {
            const mode = document.querySelector('input[name="mode"]:checked').value;
            currentMode = mode;

            const description = document.getElementById('modeDescription');
            description.textContent = 'AI assistant ready for transcription';

            log(`Mode updated to: ${mode}`);
        }

        function updateVoiceSettings() {
            // Voice settings removed - Voxtral is ASR-only (no TTS)
            log('Voxtral ASR-only mode - no voice settings needed');
        }



        function addToSpeechHistory(userText, aiText, conversationId, emotionAnalysis = null) {
            // Speech-to-Speech history removed - Voxtral is ASR-only
            return;
        }

        async function connect() {
            try {
                updateStatus('Connecting to Voxtral conversational AI...', 'loading');
                log('Attempting WebSocket connection...');
                
                ws = new WebSocket(wsUrl);
                
                return new Promise((resolve, reject) => {
                    ws.onopen = () => {
                        updateStatus('Connected! Ready to start conversation.', 'success');
                        updateConnectionStatus(true);
                        document.getElementById('connectBtn').disabled = true;
                        document.getElementById('streamBtn').disabled = false;
                        log('WebSocket connection established');
                        resolve();
                    };
                    
                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    ws.onclose = (event) => {
                        updateStatus('Disconnected from server (Code: ' + event.code + ')', 'error');
                        updateConnectionStatus(false);
                        updateVadStatus('waiting');
                        document.getElementById('connectBtn').disabled = false;
                        document.getElementById('streamBtn').disabled = true;
                        document.getElementById('stopBtn').disabled = true;
                        log('WebSocket connection closed: ' + event.code);
                    };
                    
                    ws.onerror = (error) => {
                        updateStatus('Connection error - check console for details', 'error');
                        updateConnectionStatus(false);
                        updateVadStatus('waiting');
                        log('WebSocket error occurred');
                        console.error('WebSocket error:', error);
                        reject(error);
                    };
                    
                    // Timeout after 10 seconds
                    setTimeout(() => {
                        if (ws.readyState !== WebSocket.OPEN) {
                            reject(new Error('Connection timeout'));
                        }
                    }, 10000);
                });
                
            } catch (error) {
                updateStatus('Failed to connect: ' + error.message, 'error');
                log('Connection failed: ' + error.message);
                throw error;
            }
        }
        
        function handleWebSocketMessage(data) {
            log('Received message type: ' + data.type);
            
            // Handle different message types
            switch(data.type) {
                case 'connection':
                    log('Connected to Voxtral AI');
                    updateConnectionStatus(true);
                    break;
                    
                case 'text_chunk':
                    // Handle chunked text responses
                    log('📝 Text Chunk: "' + data.text + '"');
                    displayPartialResponse(data.text, data.is_final || false);
                    break;
                    
                case 'text_response':
                    log('📝 Response: "' + data.text + '"');
                    displayResponse(data.text);
                    resetForNextInput();
                    break;
                    
                case 'audio_chunk_stream':
                    // Handle chunked audio responses
                    log('🎵 Playing audio chunk');
                    playAudioChunk(data);
                    break;
                    
                case 'audio_response':
                    log('🎵 Playing audio response');
                    playAudioChunk(data);
                    break;
                    
                case 'error':
                    log('❌ Server error: ' + (data.message || data.error));
                    resetForNextInput();
                    break;
                    
                case 'transcription':
                    log(`Transcription received: "${data.text}"`);
                    break;

                case 'response_text':
                    log(`AI response text: "${data.text}"`);
                    break;

                case 'speech_response':
                    log(`Speech response received`);
                    break;

                case 'conversation_complete':
                    // Update metrics
                    if (data.total_latency_ms) {
                        latencySum += data.total_latency_ms;
                        responseCount++;
                        updateMetrics();

                        if (data.total_latency_ms > LATENCY_WARNING_THRESHOLD) {
                            document.getElementById('performanceWarning').style.display = 'block';
                        }
                    }

                    log(`Conversation complete: ${data.total_latency_ms}ms (target: ${data.meets_target ? 'met' : 'exceeded'})`);
                    break;

                default:
                    log(`Unknown message type: ${data.type}`);
            }
        }

        // ADDED: Display partial responses for chunked streaming
        function displayPartialResponse(text, isFinal) {
            const responseDiv = document.getElementById('response') || createResponseDiv();
            if (isFinal) {
                responseDiv.innerHTML = '<strong>Complete:</strong> ' + text;
            } else {
                responseDiv.innerHTML += text + ' ';
            }
            responseDiv.scrollTop = responseDiv.scrollHeight;
        }

        // ADDED: Display complete response
        function displayResponse(text) {
            const responseDiv = document.getElementById('response') || createResponseDiv();
            responseDiv.innerHTML = '<strong>Response:</strong> ' + text;
        }

        // ADDED: Create response div if missing
        function createResponseDiv() {
            let responseDiv = document.getElementById('response');
            if (!responseDiv) {
                responseDiv = document.createElement('div');
                responseDiv.id = 'response';
                responseDiv.style.cssText = 'margin: 10px 0; padding: 10px; border: 1px solid #ccc; background: #f9f9f9;';
                document.body.appendChild(responseDiv);
            }
            return responseDiv;
        }

        // ADDED: Play audio chunks with proper error handling
        async function playAudioChunk(data) {
            try {
                if (!audioContext) {
                    audioContext = initializeAudioContext();
                }
                if (audioContext.state === 'suspended') {
                    await audioContext.resume();
                }

                // Decode audio data
                const audioBytes = Uint8Array.from(atob(data.audio_data), c => c.charCodeAt(0));
                const audioFloat32 = new Float32Array(audioBytes.buffer);

                // Create and play audio buffer
                const audioBuffer = audioContext.createBuffer(1, audioFloat32.length, data.sample_rate);
                audioBuffer.copyToChannel(audioFloat32, 0);

                const source = audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(audioContext.destination);
                
                source.onended = () => {
                    log('✅ Audio played successfully');
                    // Don't reset here - let the text response handle it
                };
                
                source.start();
            } catch (error) {
                console.error('Audio playback error:', error);
                log('❌ Audio playback failed: ' + error.message);
            }
        }

        // ADDED: Reset system for next input
        function resetForNextInput() {
            pendingResponse = false;
            updateVadStatus('silence');
            
            // Reset speech detection state
            isSpeechActive = false;
            speechStartTime = null;
            lastSpeechTime = null;
            silenceStartTime = null;
            
            log('🔄 Ready for next input');
        }

        function handleAudioResponse(data) {
            try {
                log(`🎵 Received TTS audio response for chunk ${data.chunk_id} (${data.audio_data.length} chars)`);

                // Add to audio queue for sequential playback
                audioQueue.push({
                    chunkId: data.chunk_id,
                    audioData: data.audio_data,
                    metadata: data.metadata || {},
                    voice: data.voice || 'unknown'
                });

                log(`🎵 Added audio to queue. Queue length: ${audioQueue.length}`);

                // Start processing queue if not already playing
                if (!isPlayingAudio) {
                    processAudioQueue();
                }

            } catch (error) {
                log(`❌ Error handling audio response: ${error}`);
                updateStatus('Error processing audio response', 'error');
                console.error('Audio response error:', error);
            }
        }

        async function processAudioQueue() {
            if (isPlayingAudio || audioQueue.length === 0) {
                return;
            }

            isPlayingAudio = true;

            while (audioQueue.length > 0) {
                const audioItem = audioQueue.shift();

                try {
                    log(`🎵 Processing audio chunk ${audioItem.chunkId} from queue`);
                    await playAudioItem(audioItem);
                    log(`✅ Completed playing audio chunk ${audioItem.chunkId}`);
                } catch (error) {
                    log(`❌ Error playing audio chunk ${audioItem.chunkId}: ${error}`);
                    console.error('Audio playback error:', error);
                }

                // Small delay between audio chunks to prevent overlap
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            isPlayingAudio = false;
            updateStatus('Ready for conversation', 'success');
            log('🎵 Audio queue processing completed');
        }

        function playAudioItem(audioItem) {
            return new Promise((resolve, reject) => {
                try {
                    const { chunkId, audioData, metadata, voice } = audioItem;

                    log(`🎵 Converting base64 audio for chunk ${chunkId} (${audioData.length} chars)`);

                    // Convert base64 to blob with proper error handling
                    const binaryString = atob(audioData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }

                    log(`🎵 Created audio buffer: ${bytes.length} bytes`);

                    // Create audio blob with explicit WAV headers
                    const audioBlob = new Blob([bytes], { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    // Create audio element with enhanced configuration
                    const audio = new Audio();
                    audio.preload = 'auto';
                    audio.volume = 1.0;

                    // Enhanced audio debugging
                    log(`🎵 Audio metadata: ${JSON.stringify(metadata)}`);
                    log(`🎵 Audio blob size: ${audioBlob.size} bytes, type: ${audioBlob.type}`);

                    // Store reference for cleanup
                    currentAudio = audio;

                    // Set up event listeners BEFORE setting src
                    audio.addEventListener('loadstart', () => {
                        log(`🎵 Started loading audio chunk ${chunkId}`);
                    });

                    audio.addEventListener('loadedmetadata', () => {
                        log(`🎵 Audio metadata loaded - Duration: ${audio.duration}s, Sample Rate: ${audio.sampleRate || 'unknown'}Hz`);
                    });

                    audio.addEventListener('canplaythrough', () => {
                        log(`🎵 Audio chunk ${chunkId} ready to play (${metadata.audio_duration_ms || 'unknown'}ms)`);
                        log(`🎵 Browser audio info - Duration: ${audio.duration}s, Buffered: ${audio.buffered.length} ranges`);
                    });

                    audio.addEventListener('play', () => {
                        log(`🎵 Started playing audio chunk ${chunkId} with voice '${voice}'`);
                        log(`🎵 Playback info - Current time: ${audio.currentTime}s, Volume: ${audio.volume}, Playback rate: ${audio.playbackRate}`);
                        updateStatus(`🔊 Playing AI response (${voice})...`, 'success');
                    });

                    audio.addEventListener('timeupdate', () => {
                        if (audio.currentTime > 0) {
                            log(`🎵 Playing chunk ${chunkId} - Progress: ${audio.currentTime.toFixed(2)}s / ${audio.duration.toFixed(2)}s`);
                        }
                    });

                    audio.addEventListener('ended', () => {
                        log(`✅ Finished playing audio chunk ${chunkId} - Total duration: ${audio.duration}s`);
                        URL.revokeObjectURL(audioUrl);
                        currentAudio = null;
                        resolve();
                    });

                    audio.addEventListener('error', (e) => {
                        const errorDetails = {
                            code: audio.error?.code,
                            message: audio.error?.message,
                            networkState: audio.networkState,
                            readyState: audio.readyState
                        };
                        log(`❌ Audio playback error for chunk ${chunkId}: ${JSON.stringify(errorDetails)}`);
                        log(`❌ Audio element state - src: ${audio.src.substring(0, 50)}..., duration: ${audio.duration}`);
                        URL.revokeObjectURL(audioUrl);
                        currentAudio = null;
                        reject(new Error(`Audio playback failed: ${JSON.stringify(errorDetails)}`));
                    });

                    audio.addEventListener('abort', () => {
                        log(`⚠️ Audio playback aborted for chunk ${chunkId}`);
                        URL.revokeObjectURL(audioUrl);
                        currentAudio = null;
                        resolve(); // Don't reject on abort, just continue
                    });

                    // Set source and start loading
                    audio.src = audioUrl;

                    // Start playback with retry logic
                    const playWithRetry = async (retries = 3) => {
                        try {
                            await audio.play();
                        } catch (playError) {
                            log(`⚠️ Play attempt failed for chunk ${chunkId}: ${playError.message}`);

                            if (retries > 0 && !playError.message.includes('aborted')) {
                                log(`🔄 Retrying playback for chunk ${chunkId} (${retries} attempts left)`);
                                setTimeout(() => playWithRetry(retries - 1), 200);
                            } else {
                                URL.revokeObjectURL(audioUrl);
                                currentAudio = null;
                                reject(new Error(`Failed to play audio after retries: ${playError.message}`));
                            }
                        }
                    };

                    // Wait for audio to be ready, then play
                    if (audio.readyState >= 3) { // HAVE_FUTURE_DATA
                        playWithRetry();
                    } else {
                        audio.addEventListener('canplay', () => playWithRetry(), { once: true });
                    }

                } catch (error) {
                    log(`❌ Error creating audio for chunk ${audioItem.chunkId}: ${error}`);
                    reject(error);
                }
            });
        }

        function displayConversationMessage(data) {
            const conversationDiv = document.getElementById('conversation');
            const contentDiv = document.getElementById('conversationContent');
            conversationDiv.style.display = 'block';
            document.getElementById('vadStats').style.display = 'block';
            
            const timestamp = new Date().toLocaleTimeString();
            
            // Check if this was a silence response (empty or skipped)
            if (!data.text || data.text.trim() === '' || data.skipped_reason === 'no_speech_detected') {
                silenceChunks++;
                updateVadStatus('silence');
                
                // Optionally show silence messages (uncomment if desired)
                /*
                const silenceMessage = document.createElement('div');
                silenceMessage.className = 'message silence-message';
                silenceMessage.innerHTML = `
                    <div><em>🔇 Silence detected - no response needed</em></div>
                    <div class="timestamp">${timestamp} (${data.processing_time_ms}ms)</div>
                `;
                contentDiv.appendChild(silenceMessage);
                */
            } else {
                // This was a real speech response
                speechChunks++;
                responseCount++;
                updateVadStatus('processing');
                
                const aiMessage = document.createElement('div');
                aiMessage.className = 'message ai-message';
                aiMessage.innerHTML = `
                    <div><strong>AI:</strong> ${data.text}</div>
                    <div class="timestamp">${timestamp} (${data.processing_time_ms}ms)</div>
                `;
                
                contentDiv.appendChild(aiMessage);
                conversationDiv.scrollTop = conversationDiv.scrollHeight;
                
                // Update metrics
                if (data.processing_time_ms) {
                    latencySum += data.processing_time_ms;
                    const avgLatency = Math.round(latencySum / responseCount);
                    document.getElementById('latencyMetric').textContent = avgLatency;
                    
                    // Show performance warning if latency is high
                    const warningDiv = document.getElementById('performanceWarning');
                    if (data.processing_time_ms > LATENCY_WARNING_THRESHOLD) {
                        warningDiv.style.display = 'block';
                    } else if (avgLatency < LATENCY_WARNING_THRESHOLD) {
                        warningDiv.style.display = 'none';
                    }
                }
                
                setTimeout(() => updateVadStatus('silence'), 2000);
                
                log(`AI Response: "${data.text}" (${data.processing_time_ms}ms)`);
            }
            
            document.getElementById('chunksMetric').textContent = speechChunks;
            updateVadStats();
        }
        
        function updateStreamDuration() {
            if (streamStartTime && isStreaming) {
                const duration = Math.floor((Date.now() - streamStartTime) / 1000);
                const minutes = Math.floor(duration / 60).toString().padStart(2, '0');
                const seconds = (duration % 60).toString().padStart(2, '0');
                document.getElementById('durationMetric').textContent = `${minutes}:${seconds}`;
            }
        }
        
        // STREAMING AUDIO PLAYBACK: Queue and play chunks seamlessly
        const audioChunkQueue = [];
        let isPlayingChunks = false;
        
        async function playAudioChunkStreaming(audioBuffer, chunkId) {
            return new Promise((resolve, reject) => {
                try {
                    // Add to queue
                    audioChunkQueue.push({ buffer: audioBuffer, id: chunkId, resolve, reject });
                    
                    // Start playing if not already
                    if (!isPlayingChunks) {
                        processAudioChunkQueue();
                    }
                } catch (error) {
                    reject(error);
                }
            });
        }
        
        async function processAudioChunkQueue() {
            if (isPlayingChunks || audioChunkQueue.length === 0) {
                return;
            }
            
            isPlayingChunks = true;
            
            while (audioChunkQueue.length > 0) {
                const chunk = audioChunkQueue.shift();
                
                try {
                    // Create and play audio source
                    const source = audioContext.createBufferSource();
                    source.buffer = chunk.buffer;
                    source.connect(audioContext.destination);
                    
                    // Play and wait for completion
                    await new Promise((resolve) => {
                        source.onended = resolve;
                        source.start();
                    });
                    
                    chunk.resolve();
                } catch (error) {
                    console.error(`Audio chunk ${chunk.id} playback error:`, error);
                    chunk.reject(error);
                }
            }
            
            isPlayingChunks = false;
            log('🎵 All audio chunks played');
        }
        

        
        async function startConversation() {
            // CRITICAL: Reset VAD state variables for fresh conversation
            continuousAudioBuffer = [];
            speechStartTime = null;
            lastSpeechTime = null;
            isSpeechActive = false;
            silenceStartTime = null;
            pendingResponse = false;
            lastResponseText = '';

            // CRITICAL: Ensure WebSocket is connected first
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('WebSocket not connected - establishing connection first...');
                await connect();

                // Wait for connection to be established
                await new Promise(resolve => {
                    const checkConnection = () => {
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            resolve();
                        } else {
                            setTimeout(checkConnection, 100);
                        }
                    };
                    checkConnection();
                });
            }

            try {
                log('Starting conversational audio streaming with VAD...');
                updateStatus('Initializing microphone for conversation...', 'loading');
                
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
                
                audioContext = initializeAudioContext();
                await audioContext.resume();
                log('Audio context created with sample rate: ' + audioContext.sampleRate);
                
                audioWorkletNode = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
                const source = audioContext.createMediaStreamSource(mediaStream);
                
                source.connect(audioWorkletNode);
                audioWorkletNode.connect(audioContext.destination);
                
                let audioBuffer = [];
                let lastChunkTime = Date.now();

                audioWorkletNode.onaudioprocess = (event) => {
                    if (!isStreaming || pendingResponse) return;

                    const inputBuffer = event.inputBuffer;
                    const inputData = inputBuffer.getChannelData(0);

                    // Update volume meter and VAD indicator
                    updateVolumeMeter(inputData);

                    // Add to continuous buffer
                    continuousAudioBuffer.push(...inputData);

                    // Detect speech in current chunk
                    const hasSpeech = detectSpeechInBuffer(inputData);
                    const now = Date.now();

                    if (hasSpeech) {
                        if (!isSpeechActive) {
                            // Speech started
                            speechStartTime = now;
                            isSpeechActive = true;
                            silenceStartTime = null;
                            log('Speech detected - starting continuous capture');
                            updateVadStatus('speech');
                        }
                        lastSpeechTime = now;
                    } else if (isSpeechActive && !silenceStartTime) {
                        // Silence started after speech
                        silenceStartTime = now;
                        updateVadStatus('silence');
                    }

                    // Check if we should process accumulated speech
                    if (isSpeechActive && silenceStartTime && 
                        (now - silenceStartTime >= END_OF_SPEECH_SILENCE) && 
                        (lastSpeechTime - speechStartTime >= MIN_SPEECH_DURATION)) {

                        // Process the complete utterance
                        log(`Processing ULTRA-FAST utterance: ${continuousAudioBuffer.length} samples, ${lastSpeechTime - speechStartTime}ms duration`);
                        sendCompleteUtterance(new Float32Array(continuousAudioBuffer));

                        // FIXED: Reset for next utterance
                        continuousAudioBuffer = [];
                        isSpeechActive = false;
                        speechStartTime = null;
                        lastSpeechTime = null;
                        silenceStartTime = null;
                        pendingResponse = true; // Prevent processing until response received
                        updateVadStatus('processing'); // ADDED: Show processing state
                    }

                    // Prevent buffer from growing too large (max 5 seconds)
                    const maxBufferSize = SAMPLE_RATE * 5;
                    if (continuousAudioBuffer.length > maxBufferSize) {
                        continuousAudioBuffer = continuousAudioBuffer.slice(-maxBufferSize);
                    }
                };
                
                isStreaming = true;
                streamStartTime = Date.now();
                
                document.getElementById('streamBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                updateConnectionStatus(true, true);
                updateStatus('🎙️ Conversation active with VAD - speak naturally!', 'success');
                updateVadStatus('silence');
                
                setInterval(updateStreamDuration, 1000);
                
                log('Conversational streaming with VAD started successfully');
                
            } catch (error) {
                updateStatus('Failed to start conversation: ' + error.message, 'error');
                log('Conversation start failed: ' + error.message);
                console.error('Conversation error:', error);
            }
        }
        
        function stopConversation() {
            isStreaming = false;

            log('Stopping conversational streaming...');

            // Stop and clear audio playback
            if (currentAudio) {
                currentAudio.pause();
                currentAudio = null;
            }

            // Clear audio queue
            audioQueue = [];
            isPlayingAudio = false;
            log('🎵 Audio queue cleared');
            
            if (audioWorkletNode) {
                audioWorkletNode.disconnect();
                audioWorkletNode = null;
            }

            if (audioContext && audioContext.state !== 'closed') {
                // CRITICAL FIX: Suspend instead of close to allow reuse
                audioContext.suspend().catch(e => log('Warning: Could not suspend audio context: ' + e.message));
                // Don't set to null - allow reuse on next startConversation()
            }

            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            
            document.getElementById('streamBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            updateConnectionStatus(true, false);
            updateStatus('Conversation ended. Ready to start a new conversation.', 'info');
            updateVadStatus('waiting');

            document.getElementById('volumeBar').style.width = '0%';
            document.getElementById('volumeBar').classList.remove('speech');

            log('Conversational streaming stopped');
        }
        
        function updateVolumeMeter(audioData) {
            let sum = 0;
            for (let i = 0; i < audioData.length; i++) {
                sum += audioData[i] * audioData[i];
            }
            const rms = Math.sqrt(sum / audioData.length);
            const volume = Math.min(100, rms * 100 * 10);
            
            const volumeBar = document.getElementById('volumeBar');
            volumeBar.style.width = volume + '%';
            
            // Simple client-side VAD indication based on volume
            const now = Date.now();
            if (volume > 5 && now - lastVadUpdate > 100) { // Throttle updates
                updateVadStatus('speech');
                volumeBar.classList.add('speech');
                lastVadUpdate = now;
                
                // Reset to silence after 500ms of no update
                setTimeout(() => {
                    if (Date.now() - lastVadUpdate >= 400) {
                        updateVadStatus('silence');
                        volumeBar.classList.remove('speech');
                    }
                }, 500);
            }
        }
        
        function sendCompleteUtterance(audioData) {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                log('Cannot send audio - WebSocket not connected');
                return;
            }

            try {
                const base64Audio = arrayBufferToBase64(audioData.buffer);

                const message = {
                    type: 'audio_chunk',
                    audio_data: base64Audio,
                    mode: 'transcribe',
                    prompt: '',
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
            // Don't auto-connect - user must click Connect first
            updateStatus('Ready to connect. Click Connect to start conversation.');
            log('Conversational application with VAD initialized');
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (isStreaming) {
                stopConversation();
            }
            if (ws) {
                ws.close();
            }
        });

        // Initialize the interface
        updateMode();
        updateVoiceSettings();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def api_status():
    """API endpoint for unified model system status"""
    try:
        unified_manager = get_unified_manager()
        performance_monitor = get_performance_monitor()
        
        # Get comprehensive system status
        model_info = unified_manager.get_model_info()
        memory_stats = unified_manager.get_memory_stats()
        performance_summary = performance_monitor.get_performance_summary()
        
        # Determine overall health status
        is_healthy = (
            unified_manager.is_initialized and
            model_info['unified_manager']['voxtral_initialized']
        )

        voxtral_model = get_voxtral_model()
        model_info = voxtral_model.get_model_info()

        return JSONResponse({
            "status": "healthy" if is_healthy else "initializing",
            "timestamp": time.time(),
            "unified_system": {
                "initialized": unified_manager.is_initialized,
                "voxtral_ready": model_info['unified_manager']['voxtral_initialized'],
                "memory_manager_ready": model_info['unified_manager']['memory_manager_initialized']
            },
            "memory_stats": memory_stats.get("memory_stats", {}),
            "performance_stats": {
                "total_operations": performance_summary["statistics"]["total_operations"],
                "average_latency_ms": performance_summary["statistics"]["average_latency_ms"],
                "operations_within_target": performance_summary["statistics"]["operations_within_target"]
            },
            "model": model_info,
            "config": {
                "sample_rate": config.audio.sample_rate,
                "tcp_ports": config.server.tcp_ports,
                "latency_target": config.streaming.latency_target_ms,
                "mode": "voxtral_vad_asr_llm",
                "integration_type": "voxtral_only"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "timestamp": time.time(),
            "error": str(e),
            "integration_type": "voxtral_only"
        }, status_code=500)

# WebSocket endpoint for CHUNKED STREAMING
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = f"{websocket.client.host}:{websocket.client.port}"
    streaming_logger.info(f"[CONVERSATION] Client connected: {client_id}")
    
    try:
        await websocket.send_json({
            "type": "connection", 
            "message": "Connected to Voxtral AI",
            "streaming_enabled": True
        })
        
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                message_type = message.get("type")
                
                if message_type == "audio_chunk":
                    chunk_id = message.get("chunk_id", int(time.time() * 1000))
                    streaming_logger.debug(f"[CHUNKED] Processing chunk {chunk_id} for {client_id}")
                    
                    # Decode audio data
                    try:
                        audio_data_b64 = message.get("audio_data", "")
                        if not audio_data_b64:
                            continue
                        
                        audio_bytes = base64.b64decode(audio_data_b64)
                        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
                    except Exception as e:
                        streaming_logger.error(f"❌ Audio decoding error: {e}")
                        continue
                    
                    # Process with CHUNKED STREAMING
                    unified_manager = get_unified_manager()
                    
                    try:
                        # Use CHUNKED STREAMING method
                        chunk_counter = 0
                        async for text_chunk in unified_manager.voxtral_model.process_realtime_chunk_streaming(
                            audio_data, chunk_id, mode="conversation"
                        ):
                            if text_chunk['success'] and text_chunk['text'].strip():
                                # Send text chunk immediately
                                await websocket.send_json({
                                    "type": "text_chunk",
                                    "chunk_id": f"{chunk_id}_{chunk_counter}",
                                    "text": text_chunk['text'],
                                    "is_final": text_chunk.get('is_final', False),
                                    "processing_time_ms": text_chunk.get('processing_time_ms', 0)
                                })
                                streaming_logger.debug(f"📤 Text chunk {chunk_counter}: '{text_chunk['text']}'")
                                chunk_counter += 1
                        
                        streaming_logger.info(f"✅ CHUNKED STREAMING complete for {chunk_id}: {chunk_counter} chunks")
                        
                    except Exception as e:
                        streaming_logger.error(f"❌ CHUNKED STREAMING error for {chunk_id}: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Sorry, there was an error.",
                            "error": str(e)
                        })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                streaming_logger.error(f"❌ WebSocket error for {client_id}: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Processing error occurred"
                    })
                except:
                    break
                    
    except WebSocketDisconnect:
        streaming_logger.info(f"[CONVERSATION] Client disconnected: {client_id}")
    except Exception as e:
        streaming_logger.error(f"❌ WebSocket connection error for {client_id}: {e}")
    finally:
        streaming_logger.info(f"[CONVERSATION] Connection closed: {client_id}")



async def initialize_models_at_startup():
    """Initialize with ULTRA-FAST mode for <500ms latency"""
    streaming_logger.info("🚀 Initializing ULTRA-FAST unified model system...")

    try:
        unified_manager = get_unified_manager()
        
        if not unified_manager.is_initialized:
            streaming_logger.info("📥 Initializing unified model manager...")
            success = await unified_manager.initialize()
            
            if success:
                # CRITICAL: Enable ultra-fast mode and warmup
                streaming_logger.info("🔥 Enabling ULTRA-FAST mode...")
                warmup_success = await unified_manager.warmup_models_for_speed()
                
                if warmup_success:
                    streaming_logger.info("✅ ULTRA-FAST mode ready - <500ms latency target!")
                else:
                    streaming_logger.warning("⚠️ Ultra-fast mode setup had issues but continuing...")
                
                # Log final performance status
                model_info = unified_manager.get_model_info()
                optimization_status = unified_manager.get_optimization_status()

                streaming_logger.info(f"📊 Final Status:")
                streaming_logger.info(f"   Voxtral: {model_info['unified_manager']['voxtral_initialized']}")
                streaming_logger.info(f"   FlashAttention2: {optimization_status['optimizations_enabled'].get('flash_attention_available', False)}")
                streaming_logger.info(f"   TF32 Enabled: {optimization_status['optimizations_enabled'].get('allow_tf32', False)}")
                
            else:
                raise Exception("Unified model manager initialization failed")
        
        streaming_logger.info("🎉 ULTRA-FAST system ready for <500ms conversations!")

    except Exception as e:
        streaming_logger.error(f"❌ ULTRA-FAST initialization failed: {e}")
        raise

if __name__ == "__main__":
    streaming_logger.info("Starting Voxtral Conversational Streaming UI Server with VAD")

    # Pre-load models before starting server
    import asyncio
    asyncio.run(initialize_models_at_startup())

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.http_port,
        log_level="info"
    )
