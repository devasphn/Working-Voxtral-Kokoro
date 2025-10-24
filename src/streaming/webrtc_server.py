"""
WebRTC Server for Voxtral Conversational AI
Handles real-time audio streaming via WebRTC instead of WebSockets
Optimized for AWS EC2 deployment with low-latency peer-to-peer communication
"""

import asyncio
import logging
import json
import time
import base64
from typing import Dict, Set, Optional
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack
import av
import numpy as np

# Configure logging
webrtc_logger = logging.getLogger("webrtc_streaming")
webrtc_logger.setLevel(logging.DEBUG)

# Constants
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
AUDIO_FORMAT = "float32"

class AudioTrack(MediaStreamTrack):
    """Custom audio track for receiving audio from WebRTC peer"""
    
    kind = "audio"
    
    def __init__(self):
        super().__init__()
        self.audio_buffer = asyncio.Queue()
        self.sample_rate = 16000
        
    async def recv(self):
        """Receive audio frame from peer"""
        frame = await self.audio_buffer.get()
        return frame
    
    async def put_frame(self, frame):
        """Put audio frame into buffer"""
        await self.audio_buffer.put(frame)


class WebRTCConnectionManager:
    """Manages WebRTC peer connections with audio streaming and data channels"""

    def __init__(self):
        self.connections: Dict[str, RTCPeerConnection] = {}
        self.audio_tracks: Dict[str, AudioTrack] = {}
        self.data_channels: Dict[str, any] = {}
        self.client_ids: Set[str] = set()
        self.audio_buffers: Dict[str, asyncio.Queue] = {}

    async def create_peer_connection(self, client_id: str) -> RTCPeerConnection:
        """Create new WebRTC peer connection with audio and data channels"""
        pc = RTCPeerConnection()

        # Create audio track for receiving audio
        audio_track = AudioTrack()
        self.audio_tracks[client_id] = audio_track
        self.audio_buffers[client_id] = asyncio.Queue()

        @pc.on("track")
        async def on_track(track):
            webrtc_logger.info(f"🎯 [WebRTC] Track received from {client_id}: {track.kind}")

            if track.kind == "audio":
                # Process incoming audio stream
                asyncio.create_task(self._process_audio_stream(client_id, track))

        @pc.on("datachannel")
        async def on_datachannel(channel):
            webrtc_logger.info(f"🎯 [WebRTC] Data channel opened for {client_id}")
            self.data_channels[client_id] = channel

            @channel.on("message")
            async def on_message(message):
                webrtc_logger.debug(f"📨 [WebRTC] Message from {client_id}: {message[:50]}...")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            webrtc_logger.info(f"🎯 [WebRTC] Connection state for {client_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await self.close_connection(client_id)

        self.connections[client_id] = pc
        self.client_ids.add(client_id)
        webrtc_logger.info(f"✅ [WebRTC] Created connection for {client_id}")

        return pc

    async def _process_audio_stream(self, client_id: str, track):
        """Process incoming audio stream from WebRTC track"""
        try:
            while True:
                frame = await track.recv()
                # Convert frame to numpy array
                audio_data = frame.to_ndarray()
                # Put into buffer for processing
                await self.audio_buffers[client_id].put(audio_data)
        except Exception as e:
            webrtc_logger.error(f"❌ [WebRTC] Error processing audio from {client_id}: {e}")
    
    async def close_connection(self, client_id: str):
        """Close WebRTC peer connection"""
        if client_id in self.connections:
            pc = self.connections[client_id]
            await pc.close()
            del self.connections[client_id]

        if client_id in self.audio_tracks:
            del self.audio_tracks[client_id]

        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]

        if client_id in self.data_channels:
            del self.data_channels[client_id]

        if client_id in self.client_ids:
            self.client_ids.remove(client_id)

        webrtc_logger.info(f"✅ [WebRTC] Closed connection for {client_id}")

    async def get_audio_track(self, client_id: str) -> Optional[AudioTrack]:
        """Get audio track for client"""
        return self.audio_tracks.get(client_id)

    async def get_audio_buffer(self, client_id: str) -> Optional[asyncio.Queue]:
        """Get audio buffer for client"""
        return self.audio_buffers.get(client_id)

    async def send_message(self, client_id: str, message: dict):
        """Send message to client via data channel"""
        if client_id in self.data_channels:
            channel = self.data_channels[client_id]
            try:
                channel.send(json.dumps(message))
                webrtc_logger.debug(f"📨 [WebRTC] Sent message to {client_id}")
            except Exception as e:
                webrtc_logger.error(f"❌ [WebRTC] Error sending message to {client_id}: {e}")

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)

    def get_connection_info(self, client_id: str) -> dict:
        """Get connection information"""
        if client_id not in self.connections:
            return {}

        pc = self.connections[client_id]
        return {
            "client_id": client_id,
            "connection_state": pc.connectionState,
            "ice_connection_state": pc.iceConnectionState,
            "ice_gathering_state": pc.iceGatheringState,
            "signaling_state": pc.signalingState,
            "has_data_channel": client_id in self.data_channels,
            "has_audio_track": client_id in self.audio_tracks
        }


# Global WebRTC connection manager
webrtc_manager = WebRTCConnectionManager()


async def handle_webrtc_offer(client_id: str, offer_data: dict) -> dict:
    """
    Handle WebRTC offer from client
    AWS EC2 optimized for low-latency peer-to-peer communication

    Args:
        client_id: Unique client identifier
        offer_data: WebRTC offer SDP

    Returns:
        WebRTC answer SDP
    """
    try:
        # Create peer connection
        pc = await webrtc_manager.create_peer_connection(client_id)

        # Create data channel for sending responses
        data_channel = pc.createDataChannel("voxtral-responses")
        webrtc_logger.info(f"🎯 [WebRTC] Created data channel for {client_id}")

        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
        await pc.setRemoteDescription(offer)

        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        webrtc_logger.info(f"✅ [WebRTC] Created answer for {client_id}")

        return {
            "type": "answer",
            "sdp": pc.localDescription.sdp
        }

    except Exception as e:
        webrtc_logger.error(f"❌ [WebRTC] Error handling offer for {client_id}: {e}")
        raise


async def handle_ice_candidate(client_id: str, candidate_data: dict):
    """
    Handle ICE candidate from client
    Enables NAT traversal for peer-to-peer connection

    Args:
        client_id: Unique client identifier
        candidate_data: ICE candidate data
    """
    try:
        if client_id not in webrtc_manager.connections:
            webrtc_logger.warning(f"⚠️ [WebRTC] Connection not found for {client_id}")
            return

        pc = webrtc_manager.connections[client_id]

        # Add ICE candidate
        candidate = RTCIceCandidate(
            candidate=candidate_data.get("candidate"),
            sdpMLineIndex=candidate_data.get("sdpMLineIndex"),
            sdpMid=candidate_data.get("sdpMid")
        )
        await pc.addIceCandidate(candidate)

        webrtc_logger.debug(f"🎯 [WebRTC] Added ICE candidate for {client_id}")

    except Exception as e:
        webrtc_logger.error(f"❌ [WebRTC] Error handling ICE candidate for {client_id}: {e}")


async def get_audio_from_webrtc(client_id: str) -> Optional[np.ndarray]:
    """
    Get audio data from WebRTC connection
    Retrieves audio from the peer's media stream

    Args:
        client_id: Unique client identifier

    Returns:
        Audio data as numpy array or None
    """
    try:
        audio_buffer = await webrtc_manager.get_audio_buffer(client_id)
        if audio_buffer:
            audio_data = await asyncio.wait_for(audio_buffer.get(), timeout=5.0)
            return audio_data
    except asyncio.TimeoutError:
        webrtc_logger.warning(f"⏱️ [WebRTC] Timeout waiting for audio from {client_id}")
    except Exception as e:
        webrtc_logger.error(f"❌ [WebRTC] Error getting audio from {client_id}: {e}")

    return None


async def close_webrtc_connection(client_id: str):
    """Close WebRTC connection for client"""
    await webrtc_manager.close_connection(client_id)


def get_webrtc_stats(client_id: str) -> dict:
    """Get WebRTC connection statistics"""
    return webrtc_manager.get_connection_info(client_id)


def get_webrtc_connection_count() -> int:
    """Get number of active WebRTC connections"""
    return webrtc_manager.get_connection_count()

