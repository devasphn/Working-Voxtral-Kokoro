"""
TCP server for real-time audio streaming (alternative to WebSocket)
Handles raw TCP connections for low-level audio streaming
"""
import asyncio
import json
import base64
import numpy as np
import struct
import logging
import time
from typing import Dict, Any, Set
import traceback

from src.models.voxtral_model import voxtral_model
from src.models.audio_processor import AudioProcessor
from src.utils.config import config
from src.utils.logging_config import logger

class TCPStreamingServer:
    """TCP server for real-time audio streaming"""
    
    def __init__(self):
        self.clients: Set[asyncio.StreamWriter] = set()
        self.audio_processor = AudioProcessor()
        self.host = config.server.host
        self.port = config.server.tcp_ports[1]  # Use second TCP port (8766)
        
        logger.info(f"TCP server configured for {self.host}:{self.port}")
    
    async def send_response(self, writer: asyncio.StreamWriter, response_data: Dict[str, Any]):
        """Send response back to TCP client"""
        try:
            # Convert response to JSON
            response_json = json.dumps(response_data)
            response_bytes = response_json.encode('utf-8')
            
            # Send length prefix (4 bytes) + data
            length_prefix = struct.pack('!I', len(response_bytes))
            writer.write(length_prefix + response_bytes)
            await writer.drain()
            
        except Exception as e:
            logger.error(f"Error sending TCP response: {e}")
    
    async def read_message(self, reader: asyncio.StreamReader) -> Dict[str, Any]:
        """Read a message from TCP client"""
        try:
            # Read length prefix (4 bytes)
            length_data = await reader.readexactly(4)
            message_length = struct.unpack('!I', length_data)[0]
            
            # Read the actual message
            message_data = await reader.readexactly(message_length)
            message_json = message_data.decode('utf-8')
            
            return json.loads(message_json)
            
        except asyncio.IncompleteReadError:
            logger.debug("Client disconnected during read")
            raise ConnectionResetError("Client disconnected")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from TCP client: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading TCP message: {e}")
            raise
    
    async def handle_audio_stream(self, writer: asyncio.StreamWriter, data: Dict[str, Any]):
        """Process streaming audio data from TCP client"""
        try:
            start_time = time.time()
            
            # Extract audio data
            audio_b64 = data.get("audio_data")
            if not audio_b64:
                await self.send_response(writer, {
                    "type": "error",
                    "message": "No audio data provided"
                })
                return
            
            # Decode audio
            audio_bytes = base64.b64decode(audio_b64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Validate and preprocess
            if not self.audio_processor.validate_audio_format(audio_array):
                await self.send_response(writer, {
                    "type": "error",
                    "message": "Invalid audio format"
                })
                return
            
            audio_tensor = self.audio_processor.preprocess_audio(audio_array)
            
            # Get processing parameters
            mode = data.get("mode", "transcribe")
            prompt = data.get("prompt", "")
            
            # Process with Voxtral
            if mode == "transcribe":
                response_text = await voxtral_model.transcribe_audio(audio_tensor)
            elif mode == "understand":
                if not prompt:
                    prompt = "Describe what you hear in this audio."
                response_text = await voxtral_model.understand_audio(audio_tensor, prompt)
            else:
                response_text = await voxtral_model.process_audio_stream(audio_tensor, prompt)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Send response
            await self.send_response(writer, {
                "type": "response",
                "mode": mode,
                "text": response_text,
                "processing_time_ms": round(processing_time, 1),
                "audio_duration_ms": len(audio_array) / config.audio.sample_rate * 1000,
                "timestamp": time.time()
            })
            
            logger.debug(f"TCP audio processed in {processing_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"Error processing TCP audio stream: {e}")
            await self.send_response(writer, {
                "type": "error",
                "message": f"Processing error: {str(e)}"
            })
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle individual TCP client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"TCP client connected: {client_addr}")
        
        self.clients.add(writer)
        
        try:
            # Send welcome message
            await self.send_response(writer, {
                "type": "connection",
                "status": "connected", 
                "message": "Connected to Voxtral TCP streaming server",
                "protocol": "tcp",
                "server_config": {
                    "sample_rate": config.audio.sample_rate,
                    "chunk_size": config.audio.chunk_size,
                    "format": config.audio.format
                }
            })
            
            # Handle client messages
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.read_message(reader), 
                        timeout=config.streaming.timeout_seconds
                    )
                    
                    msg_type = message.get("type")
                    
                    if msg_type == "audio":
                        await self.handle_audio_stream(writer, message)
                        
                    elif msg_type == "ping":
                        await self.send_response(writer, {
                            "type": "pong",
                            "timestamp": time.time()
                        })
                        
                    elif msg_type == "status":
                        model_info = voxtral_model.get_model_info()
                        await self.send_response(writer, {
                            "type": "status",
                            "model_info": model_info,
                            "connected_clients": len(self.clients)
                        })
                        
                    else:
                        await self.send_response(writer, {
                            "type": "error",
                            "message": f"Unknown message type: {msg_type}"
                        })
                        
                except asyncio.TimeoutError:
                    logger.debug(f"TCP client timeout: {client_addr}")
                    break
                    
        except ConnectionResetError:
            logger.debug(f"TCP client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"TCP client error {client_addr}: {e}")
            logger.debug(traceback.format_exc())
        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            logger.info(f"TCP client {client_addr} connection closed")
    
    async def start_server(self):
        """Start the TCP streaming server"""
        logger.info(f"Starting TCP server on {self.host}:{self.port}")
        
        # Initialize Voxtral model if needed
        if not voxtral_model.is_initialized:
            await voxtral_model.initialize()
        
        # Start TCP server
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"TCP server running on {self.host}:{self.port}")
        
        # Keep server running
        async with server:
            await server.serve_forever()

async def main():
    """Main entry point for TCP server"""
    server = TCPStreamingServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("TCP server shutdown requested")
    except Exception as e:
        logger.error(f"TCP server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
