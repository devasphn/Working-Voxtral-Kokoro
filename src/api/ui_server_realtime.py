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
_speech_to_speech_pipeline = None

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
def get_speech_to_speech_pipeline():
    """Lazy initialization of Speech-to-Speech pipeline"""
    global _speech_to_speech_pipeline
    if _speech_to_speech_pipeline is None:
        from src.models.speech_to_speech_pipeline import speech_to_speech_pipeline
        _speech_to_speech_pipeline = speech_to_speech_pipeline
        streaming_logger.info("Speech-to-Speech pipeline lazy-loaded")
    return _speech_to_speech_pipeline

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
        <p style="text-align: center; opacity: 0.8;">Intelligent conversation with Voice Activity Detection & Speech-to-Speech</p>
        
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
            <button id="speechToSpeechBtn" class="stream-btn" onclick="startSpeechToSpeech()" disabled>🗣️ Speech-to-Speech</button>
        </div>

        <!-- Mode Selection -->
        <div class="audio-controls" style="justify-content: center; margin-bottom: 20px;">
            <div style="text-align: center; padding: 15px; background: rgba(255, 255, 255, 0.1); border-radius: 10px;">
                <strong>🤖 Conversation Mode</strong>
                <div style="margin: 10px 0;">
                    <label style="margin-right: 20px;">
                        <input type="radio" name="mode" value="transcribe" checked onchange="updateMode()">
                        📝 Text Only
                    </label>
                    <label>
                        <input type="radio" name="mode" value="speech_to_speech" onchange="updateMode()">
                        🗣️ Speech-to-Speech
                    </label>
                </div>
                <p style="margin: 5px 0; opacity: 0.8; font-size: 0.9em;" id="modeDescription">AI assistant ready for text-based conversation</p>
            </div>
        </div>

        <!-- Speech-to-Speech Controls -->
        <div class="audio-controls" id="speechToSpeechControls" style="display: none; justify-content: center; margin-bottom: 20px;">
            <div style="text-align: center; padding: 15px; background: rgba(255, 255, 255, 0.1); border-radius: 10px;">
                <strong>🎤 Voice Settings</strong>
                <div style="margin: 10px 0; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                    <div>
                        <label>Voice:</label>
                        <select id="voiceSelect" onchange="updateVoiceSettings()">
                            <option value="hf_alpha" selected>Heart (Calm & Friendly)</option>
                            <option value="auto">🎭 Auto (Emotional)</option>
                            <option value="af_bella">Bella (Energetic & Excited)</option>
                            <option value="af_sarah">Sarah (Gentle & Empathetic)</option>
                            <option value="af_nicole">Nicole (Professional)</option>
                            <option value="af_sky">Sky (Bright & Happy)</option>
                            <option value="am_adam">Adam (Male, Friendly)</option>
                            <option value="am_michael">Michael (Male, Professional)</option>
                            <option value="am_edward">Edward (Male, Calm)</option>
                        </select>
                    </div>
                    <div>
                        <label>Speed:</label>
                        <select id="speedSelect" onchange="updateVoiceSettings()">
                            <option value="0.8">Slow</option>
                            <option value="1.0" selected>Normal</option>
                            <option value="1.2">Fast</option>
                        </select>
                    </div>
                </div>
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

        <!-- Speech-to-Speech Conversation Display -->
        <div class="conversation" id="speechToSpeechConversation" style="display: none;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3>🗣️ Speech-to-Speech Conversation</h3>
                <p style="opacity: 0.8; font-size: 0.9em;">Speak naturally - I'll transcribe, respond, and speak back to you!</p>
            </div>

            <!-- Real-time Transcription Display -->
            <div id="currentTranscription" style="background: rgba(0, 184, 148, 0.2); padding: 15px; border-radius: 10px; margin-bottom: 15px; display: none;">
                <strong>🎤 You said:</strong>
                <div id="transcriptionText" style="font-style: italic; margin-top: 5px;"></div>
                <div class="timestamp" id="transcriptionTime"></div>
            </div>

            <!-- AI Response Text Display -->
            <div id="currentResponse" style="background: rgba(116, 185, 255, 0.2); padding: 15px; border-radius: 10px; margin-bottom: 15px; display: none;">
                <strong>🤖 AI Response:</strong>
                <div id="responseText" style="margin-top: 5px;"></div>
                <div class="timestamp" id="responseTime"></div>
            </div>

            <!-- Audio Playback Controls -->
            <div id="audioPlayback" style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 15px; display: none;">
                <strong>🔊 AI Speech:</strong>
                <div style="margin-top: 10px;">
                    <audio id="responseAudio" controls style="width: 100%; background: rgba(255, 255, 255, 0.1);">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                    Voice: <span id="voiceUsed">-</span> | Speed: <span id="speedUsed">-</span> | Duration: <span id="audioDuration">-</span>
                </div>
            </div>

            <!-- Processing Status -->
            <div id="processingStatus" style="background: rgba(253, 203, 110, 0.2); padding: 15px; border-radius: 10px; margin-bottom: 15px; display: none;">
                <strong>⚡ Processing:</strong>
                <div id="processingMessage" style="margin-top: 5px;">Initializing...</div>
                <div class="timestamp" id="processingTime"></div>
            </div>

            <!-- Conversation History -->
            <div id="speechToSpeechHistory">
                <div class="message ai-message">
                    <div><strong>AI:</strong> Hello! I'm ready for speech-to-speech conversation. Speak naturally and I'll respond with voice!</div>
                    <div class="timestamp">Speech-to-Speech mode ready</div>
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
        
        // Speech-to-Speech specific variables
        let currentMode = 'transcribe';
        let selectedVoice = 'hf_alpha';
        let selectedSpeed = 1.0;
        let currentConversationId = null;
        let speechToSpeechActive = false;

        // ULTRA-LOW LATENCY frontend settings
        const CHUNK_SIZE = 2048;           // REDUCED: 2x smaller (was 4096)
        const CHUNK_INTERVAL = 50;         // REDUCED: 2x faster (was 100ms)
        const SAMPLE_RATE = 16000;
        const MIN_SPEECH_DURATION = 200;   // REDUCED: 2.5x faster (was 500ms)
        const END_OF_SPEECH_SILENCE = 600; // REDUCED: 2.5x faster (was 1500ms)
        const SILENCE_THRESHOLD = 0.005;   // REDUCED: 2x more sensitive (was 0.01)
        const LATENCY_WARNING_THRESHOLD = 1000;
        
        function log(message, type = 'info') {
            console.log(`[Voxtral VAD] ${message}`);
        }

        // Enhanced VAD function for continuous speech detection
        function detectSpeechInBuffer(audioData) {
            if (!audioData || audioData.length === 0) return false;

            // Calculate RMS energy
            let sum = 0;
            for (let i = 0; i < audioData.length; i++) {
                sum += audioData[i] * audioData[i];
            }
            const rms = Math.sqrt(sum / audioData.length);

            // Calculate max amplitude
            const maxAmplitude = Math.max(...audioData.map(Math.abs));

            // Speech detected if both RMS and amplitude exceed thresholds
            const hasSpeech = rms > SILENCE_THRESHOLD && maxAmplitude > 0.002;

            return hasSpeech;
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

        // Speech-to-Speech Functions
        function updateMode() {
            const mode = document.querySelector('input[name="mode"]:checked').value;
            currentMode = mode;

            const description = document.getElementById('modeDescription');
            const speechControls = document.getElementById('speechToSpeechControls');
            const speechBtn = document.getElementById('speechToSpeechBtn');

            if (mode === 'speech_to_speech') {
                description.textContent = 'AI assistant ready for speech-to-speech conversation with voice responses';
                speechControls.style.display = 'flex';
                speechBtn.style.display = 'inline-block';
            } else {
                description.textContent = 'AI assistant ready for text-based conversation';
                speechControls.style.display = 'none';
                speechBtn.style.display = 'none';
            }

            log(`Mode updated to: ${mode}`);
        }

        function updateVoiceSettings() {
            selectedVoice = document.getElementById('voiceSelect').value;
            selectedSpeed = parseFloat(document.getElementById('speedSelect').value);

            // Update description based on voice selection
            const voiceSelect = document.getElementById('voiceSelect');
            const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];

            if (selectedVoice === 'auto') {
                log('Voice settings: Automatic emotional voice selection enabled');
            } else {
                log(`Voice settings updated: ${selectedVoice} (${selectedOption.text}), speed: ${selectedSpeed}`);
            }
        }

        function startSpeechToSpeech() {
            if (currentMode === 'speech_to_speech') {
                speechToSpeechActive = true;
                currentConversationId = 'speech_' + Date.now();

                // Show speech-to-speech conversation area
                document.getElementById('conversation').style.display = 'none';
                document.getElementById('speechToSpeechConversation').style.display = 'block';

                // Update button states
                document.getElementById('speechToSpeechBtn').disabled = true;
                document.getElementById('streamBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;

                startConversation();
                log('Speech-to-Speech mode activated');
            }
        }

        function showProcessingStatus(stage, message) {
            const statusDiv = document.getElementById('processingStatus');
            const messageDiv = document.getElementById('processingMessage');
            const timeDiv = document.getElementById('processingTime');

            messageDiv.textContent = `${stage}: ${message}`;
            timeDiv.textContent = new Date().toLocaleTimeString();
            statusDiv.style.display = 'block';
        }

        function hideProcessingStatus() {
            document.getElementById('processingStatus').style.display = 'none';
        }

        function showTranscription(text, conversationId) {
            const transcriptionDiv = document.getElementById('currentTranscription');
            const textDiv = document.getElementById('transcriptionText');
            const timeDiv = document.getElementById('transcriptionTime');

            textDiv.textContent = text;
            timeDiv.textContent = `Conversation ${conversationId} - ${new Date().toLocaleTimeString()}`;
            transcriptionDiv.style.display = 'block';
        }

        function showResponseText(text, conversationId) {
            const responseDiv = document.getElementById('currentResponse');
            const textDiv = document.getElementById('responseText');
            const timeDiv = document.getElementById('responseTime');

            textDiv.textContent = text;
            timeDiv.textContent = `Response generated - ${new Date().toLocaleTimeString()}`;
            responseDiv.style.display = 'block';
        }

        function showAudioPlayback(audioData, sampleRate, voice, speed, duration) {
            const playbackDiv = document.getElementById('audioPlayback');
            const audioElement = document.getElementById('responseAudio');
            const voiceSpan = document.getElementById('voiceUsed');
            const speedSpan = document.getElementById('speedUsed');
            const durationSpan = document.getElementById('audioDuration');

            // Convert base64 audio to blob and create URL
            const audioBytes = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));
            const audioBlob = new Blob([audioBytes], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);

            audioElement.src = audioUrl;
            voiceSpan.textContent = voice;
            speedSpan.textContent = speed;
            durationSpan.textContent = `${duration.toFixed(1)}s`;

            playbackDiv.style.display = 'block';

            // Auto-play the response
            audioElement.play().catch(e => {
                log('Auto-play failed (user interaction required): ' + e.message);
            });
        }

        function addToSpeechHistory(userText, aiText, conversationId, emotionAnalysis = null) {
            const historyDiv = document.getElementById('speechToSpeechHistory');

            if (userText) {
                const userMessage = document.createElement('div');
                userMessage.className = 'message user-message';
                let emotionInfo = '';
                if (emotionAnalysis && emotionAnalysis.user_emotion) {
                    emotionInfo = ` <span style="opacity: 0.7; font-size: 0.8em;">[${emotionAnalysis.user_emotion}]</span>`;
                }
                userMessage.innerHTML = `
                    <div><strong>You:</strong> ${userText}${emotionInfo}</div>
                    <div class="timestamp">${conversationId} - ${new Date().toLocaleTimeString()}</div>
                `;
                historyDiv.appendChild(userMessage);
            }

            if (aiText) {
                const aiMessage = document.createElement('div');
                aiMessage.className = 'message ai-message';
                let emotionInfo = '';
                if (emotionAnalysis && emotionAnalysis.response_emotion) {
                    const score = emotionAnalysis.appropriateness_score || 0;
                    const scoreColor = score >= 0.9 ? '#00b894' : score >= 0.7 ? '#fdcb6e' : '#e17055';
                    emotionInfo = ` <span style="opacity: 0.7; font-size: 0.8em;">[${emotionAnalysis.response_emotion}, score: <span style="color: ${scoreColor}">${(score * 100).toFixed(0)}%</span>]</span>`;
                }
                aiMessage.innerHTML = `
                    <div><strong>AI:</strong> ${aiText}${emotionInfo}</div>
                    <div class="timestamp">Response - ${new Date().toLocaleTimeString()}</div>
                `;
                historyDiv.appendChild(aiMessage);
            }

            // Scroll to bottom
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }

        function showEmotionalAnalysis(analysis) {
            // Create or update emotional analysis display
            let analysisDiv = document.getElementById('emotionalAnalysis');
            if (!analysisDiv) {
                analysisDiv = document.createElement('div');
                analysisDiv.id = 'emotionalAnalysis';
                analysisDiv.style.cssText = `
                    background: rgba(116, 185, 255, 0.1);
                    padding: 10px;
                    border-radius: 10px;
                    margin-bottom: 15px;
                    font-size: 0.9em;
                    border-left: 4px solid #74b9ff;
                `;

                const speechConversation = document.getElementById('speechToSpeechConversation');
                const historyDiv = document.getElementById('speechToSpeechHistory');
                speechConversation.insertBefore(analysisDiv, historyDiv);
            }

            const scoreColor = analysis.appropriateness_score >= 0.9 ? '#00b894' :
                              analysis.appropriateness_score >= 0.7 ? '#fdcb6e' : '#e17055';

            analysisDiv.innerHTML = `
                <strong>🎭 Emotional Analysis:</strong><br>
                <div style="margin-top: 5px;">
                    <span>User: <strong>${analysis.user_emotion}</strong></span> →
                    <span>AI: <strong>${analysis.response_emotion}</strong></span>
                    <span style="color: ${scoreColor}; margin-left: 10px;">
                        (${(analysis.appropriateness_score * 100).toFixed(0)}% appropriate)
                    </span>
                </div>
                <div style="margin-top: 5px; opacity: 0.8; font-style: italic;">
                    ${analysis.emotional_reasoning}
                </div>
                <div style="margin-top: 5px; font-size: 0.8em; opacity: 0.7;">
                    Voice: ${analysis.voice_selected} | Speed: ${analysis.speed_selected.toFixed(1)}x
                </div>
            `;

            // Auto-hide after 10 seconds
            setTimeout(() => {
                if (analysisDiv && analysisDiv.parentNode) {
                    analysisDiv.style.opacity = '0.5';
                }
            }, 10000);
        }

        async function connect() {
            try {
                updateStatus('Connecting to Voxtral conversational AI...', 'loading');
                log('Attempting WebSocket connection...');
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    updateStatus('Connected! Ready to start conversation.', 'success');
                    updateConnectionStatus(true);
                    document.getElementById('connectBtn').disabled = true;
                    document.getElementById('streamBtn').disabled = false;
                    log('WebSocket connection established');
                };
                
                // CHUNKED STREAMING message handler
                ws.onmessage = async (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'connection') {
                            log('Connected to Voxtral CHUNKED STREAMING AI');
                            updateConnectionStatus(true);
                        }
                        else if (data.type === 'text_chunk') {
                            // Display text chunk immediately
                            log(`📝 Text Chunk ${data.chunk_id}: "${data.text}"`);
                            updateResponseDisplay(data.text, data.is_final);
                        }
                        else if (data.type === 'audio_chunk_stream') {
                            log(`🎵 Playing audio chunk ${data.chunk_id}`);
                            
                            try {
                                // Ensure audio context is initialized
                                const ctx = initializeAudioContext();
                                if (ctx.state === 'suspended') {
                                    await ctx.resume();
                                }
                                
                                // Decode and play audio chunk immediately
                                const audioBytes = Uint8Array.from(atob(data.audio_data), c => c.charCodeAt(0));
                                const audioFloat32 = new Float32Array(audioBytes.buffer);
                                
                                // Create and play audio buffer
                                const audioBuffer = ctx.createBuffer(1, audioFloat32.length, data.sample_rate);
                                audioBuffer.copyToChannel(audioFloat32, 0);
                                
                                // Add to queue for sequential playback
                                audioQueue.push({
                                    buffer: audioBuffer,
                                    chunk_id: data.chunk_id,
                                    is_final: data.is_final
                                });
                                
                                // Start playback if not already playing
                                if (!isPlayingAudio) {
                                    playNextAudioChunk();
                                }
                                
                            } catch (audioError) {
                                console.error('Audio playback error:', audioError);
                                log(`❌ Audio playback failed: ${audioError.message}`);
                            }
                        }
                        else if (data.type === 'error') {
                            console.error('Server error:', data.error);
                            log(`❌ Error: ${data.message}`);
                        }
                        
                    } catch (error) {
                        console.error('Message parsing error:', error);
                    }
                };
                
                ws.onclose = (event) => {
                    updateStatus(`Disconnected from server (Code: ${event.code})`, 'error');
                    updateConnectionStatus(false);
                    updateVadStatus('waiting');
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('streamBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = true;
                    log(`WebSocket connection closed: ${event.code}`);
                };
                
                ws.onerror = (error) => {
                    updateStatus('Connection error - check console for details', 'error');
                    updateConnectionStatus(false);
                    updateVadStatus('waiting');
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
                    // Check for response deduplication
                    if (data.text && data.text.trim() !== '' && data.text !== lastResponseText) {
                        displayConversationMessage(data);
                        lastResponseText = data.text;
                        log(`Received unique response: "${data.text.substring(0, 50)}..."`);
                    } else if (data.text === lastResponseText) {
                        log('Duplicate response detected - skipping display');
                    }

                    // Reset pending response flag to allow new speech processing
                    pendingResponse = false;
                    break;
                    
                case 'error':
                    updateStatus('Error: ' + data.message, 'error');
                    break;
                    
                case 'info':
                    updateStatus(data.message, 'loading');
                    break;

                case 'audio_response':
                    // Handle TTS audio response
                    handleAudioResponse(data);
                // Speech-to-Speech message types
                case 'processing':
                    if (speechToSpeechActive) {
                        showProcessingStatus(data.stage, data.message);
                    }
                    break;

                case 'transcription':
                    if (speechToSpeechActive) {
                        showTranscription(data.text, data.conversation_id);
                        log(`Transcription received: "${data.text}"`);
                    }
                    break;

                case 'response_text':
                    if (speechToSpeechActive) {
                        showResponseText(data.text, data.conversation_id);
                        log(`AI response text: "${data.text}"`);
                    }
                    break;

                case 'speech_response':
                    if (speechToSpeechActive) {
                        hideProcessingStatus();
                        showAudioPlayback(
                            data.audio_data,
                            data.sample_rate,
                            data.voice_used,
                            data.speed_used,
                            data.audio_duration_s
                        );
                        log(`Speech response received: ${data.audio_duration_s}s audio`);
                    }
                    break;

                case 'conversation_complete':
                    if (speechToSpeechActive) {
                        hideProcessingStatus();

                        // Add to conversation history with emotional context
                        const transcription = document.getElementById('transcriptionText').textContent;
                        const responseText = document.getElementById('responseText').textContent;

                        if (transcription || responseText) {
                            addToSpeechHistory(transcription, responseText, data.conversation_id, data.emotion_analysis);
                        }

                        // Display emotional analysis if available
                        if (data.emotion_analysis) {
                            showEmotionalAnalysis(data.emotion_analysis);
                        }

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
                        if (data.emotion_analysis) {
                            log(`Emotional context: ${data.emotion_analysis.emotional_reasoning}`);
                        }
                    }
                    break;

                default:
                    log(`Unknown message type: ${data.type}`);
            }
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
        
        // FIXED: Audio context handling
        let audioContext = null;
        let audioQueue = [];
        let isPlayingAudio = false;
        
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
                    responseElement.innerHTML += '<br><strong>Complete:</strong> ' + text;
                } else {
                    responseElement.innerHTML += text + ' ';
                }
                responseElement.scrollTop = responseElement.scrollHeight;
            }
        }
        
        async function startConversation() {
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
                log(`Audio context created with sample rate: ${audioContext.sampleRate}`);
                
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

                    // ULTRA-FAST volume update (reduced computation)
                    updateVolumeMeter(inputData);

                    // OPTIMIZED: Only add significant audio data
                    const rms = Math.sqrt(inputData.reduce((sum, val) => sum + val * val, 0) / inputData.length);
                    if (rms > SILENCE_THRESHOLD) {
                        continuousAudioBuffer.push(...inputData);
                    }

                    const now = Date.now();
                    const hasSpeech = rms > SILENCE_THRESHOLD;

                    if (hasSpeech) {
                        if (!isSpeechActive) {
                            speechStartTime = now;
                            isSpeechActive = true;
                            silenceStartTime = null;
                            updateVadStatus('speech');
                        }
                        lastSpeechTime = now;
                    } else {
                        if (isSpeechActive && !silenceStartTime) {
                            silenceStartTime = now;
                            updateVadStatus('silence');
                        }
                    }

                    // ULTRA-AGGRESSIVE: Send smaller, faster chunks
                    if (isSpeechActive && silenceStartTime &&
                        (now - silenceStartTime >= END_OF_SPEECH_SILENCE) &&
                        (lastSpeechTime - speechStartTime >= MIN_SPEECH_DURATION)) {

                        // ULTRA-OPTIMIZED: Send SMALLER audio chunks for faster processing
                        const maxSamples = SAMPLE_RATE * 3;  // Max 3 seconds of audio
                        let audioToSend = continuousAudioBuffer;
                        if (audioToSend.length > maxSamples) {
                            // Keep only the most recent 3 seconds
                            audioToSend = audioToSend.slice(-maxSamples);
                            log(`Trimmed audio to ${maxSamples} samples (3s) for ultra-fast processing`);
                        }

                        log(`Processing ULTRA-FAST utterance: ${audioToSend.length} samples, ${(lastSpeechTime - speechStartTime)}ms duration`);
                        sendCompleteUtterance(new Float32Array(audioToSend));

                        // Reset
                        continuousAudioBuffer = [];
                        isSpeechActive = false;
                        speechStartTime = null;
                        lastSpeechTime = null;  
                        silenceStartTime = null;
                        pendingResponse = true;
                    }

                    // ULTRA-OPTIMIZED: Much smaller max buffer (5 seconds vs 30 seconds)
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
            
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
            
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            
            document.getElementById('streamBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('speechToSpeechBtn').disabled = false;
            updateConnectionStatus(true, false);
            updateStatus('Conversation ended. Ready to start a new conversation.', 'info');
            updateVadStatus('waiting');

            // Reset speech-to-speech mode
            if (speechToSpeechActive) {
                speechToSpeechActive = false;
                currentConversationId = null;

                // Hide speech-to-speech displays
                hideProcessingStatus();
                document.getElementById('currentTranscription').style.display = 'none';
                document.getElementById('currentResponse').style.display = 'none';
                document.getElementById('audioPlayback').style.display = 'none';

                // Show regular conversation area
                document.getElementById('speechToSpeechConversation').style.display = 'none';
                document.getElementById('conversation').style.display = 'block';

                log('Speech-to-Speech mode deactivated');
            }
            
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
                    mode: speechToSpeechActive ? 'speech_to_speech' : 'conversation',
                    prompt: '',  // No custom prompts - using hardcoded optimal prompt
                    chunk_id: chunkCounter++,
                    timestamp: Date.now()
                };

                // Add speech-to-speech specific parameters
                if (speechToSpeechActive) {
                    message.conversation_id = currentConversationId;
                    message.voice = selectedVoice === 'auto' ? null : selectedVoice;  // null for auto-selection
                    message.speed = selectedSpeed;
                }
                
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
            updateStatus('Ready to connect for conversation with VAD');
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
            model_info['unified_manager']['voxtral_initialized'] and
            model_info['unified_manager']['kokoro_initialized']
        )
        
        voxtral_model = get_voxtral_model()
        model_info = voxtral_model.get_model_info()

        # Get speech-to-speech pipeline info if enabled
        speech_to_speech_info = None
        if config.speech_to_speech.enabled:
            try:
                pipeline = get_speech_to_speech_pipeline()
                speech_to_speech_info = pipeline.get_pipeline_info()
            except Exception as e:
                speech_to_speech_info = {"error": str(e), "enabled": False}

        return JSONResponse({
            "status": "healthy" if is_healthy else "initializing",
            "timestamp": time.time(),
            "unified_system": {
                "initialized": unified_manager.is_initialized,
                "voxtral_ready": model_info['unified_manager']['voxtral_initialized'],
                "kokoro_ready": model_info['unified_manager']['kokoro_initialized'],
                "memory_manager_ready": model_info['unified_manager']['memory_manager_initialized']
            },
            "memory_stats": memory_stats.get("memory_stats", {}),
            "performance_stats": {
                "total_operations": performance_summary["statistics"]["total_operations"],
                "average_latency_ms": performance_summary["statistics"]["average_latency_ms"],
                "operations_within_target": performance_summary["statistics"]["operations_within_target"]
            },
            "model": model_info,
            "speech_to_speech": speech_to_speech_info,
            "config": {
                "sample_rate": config.audio.sample_rate,
                "tcp_ports": config.server.tcp_ports,
                "latency_target": config.streaming.latency_target_ms,
                "mode": "conversational_optimized_with_kokoro_tts",
                "integration_type": "kokoro_tts",
                "speech_to_speech_enabled": config.speech_to_speech.enabled,
                "speech_to_speech_latency_target": config.speech_to_speech.latency_target_ms,
                "mode": "conversational_optimized_with_vad_and_speech_to_speech" if config.speech_to_speech.enabled else "conversational_optimized_with_vad"
            }
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "timestamp": time.time(),
            "error": str(e),
            "integration_type": "kokoro_tts"
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
                                
                                # Generate TTS for this chunk immediately
                                try:
                                    tts_result = await unified_manager.kokoro_model.synthesize_speech_chunk(
                                        text=text_chunk['text'],
                                        chunk_id=f"tts_{chunk_id}_{chunk_counter}"
                                    )
                                    
                                    if tts_result['success'] and len(tts_result['audio_data']) > 0:
                                        # Send audio chunk immediately
                                        audio_bytes = tts_result['audio_data'].astype(np.float32).tobytes()
                                        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                                        
                                        await websocket.send_json({
                                            "type": "audio_chunk_stream",
                                            "chunk_id": f"{chunk_id}_{chunk_counter}",
                                            "audio_data": audio_b64,
                                            "sample_rate": tts_result['sample_rate'],
                                            "synthesis_time_ms": tts_result.get('synthesis_time_ms', 0),
                                            "is_final": text_chunk.get('is_final', False)
                                        })
                                        streaming_logger.debug(f"🎵 Audio chunk {chunk_counter} sent instantly")
                                        
                                except Exception as tts_error:
                                    streaming_logger.error(f"❌ TTS error for chunk {chunk_counter}: {tts_error}")
                                
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
                streaming_logger.info(f"   Kokoro: {model_info['unified_manager']['kokoro_initialized']}")
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
