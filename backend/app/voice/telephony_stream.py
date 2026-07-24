"""
Telephony Stream - Real-time audio streaming for telephony calls

Handles bidirectional audio streaming for telephony integrations including:
- Twilio, Vonage, and other telephony providers
- WebRTC-based voice connections
- Audio chunk processing and buffering
"""

import asyncio
import base64
import json
import uuid
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from datetime import datetime
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamState(Enum):
    """Telephony stream states"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PROCESSING = "processing"
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AudioFormat(Enum):
    """Supported audio formats"""
    PCM_16BIT = "pcm_16bit"
    WAV = "wav"
    MP3 = "mp3"
    OPUS = "opus"
    G711 = "g711"


class TelephonyStream:
    """
    Manages real-time audio streaming for telephony calls.
    Supports both inbound and outbound voice connections.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        audio_format: AudioFormat = AudioFormat.PCM_16BIT,
        buffer_size: int = 1024,
        max_chunk_duration_ms: int = 100
    ):
        self.stream_id = str(uuid.uuid4())
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_format = audio_format
        self.buffer_size = buffer_size
        self.max_chunk_duration_ms = max_chunk_duration_ms
        
        self.state = StreamState.IDLE
        self.session_id: Optional[str] = None
        self.caller_id: Optional[str] = None
        self.callee_id: Optional[str] = None
        
        # Audio buffers
        self._input_buffer: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._output_buffer: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # Callbacks
        self._on_audio_received: Optional[Callable] = None
        self._on_audio_sent: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        # Statistics
        self._bytes_received = 0
        self._bytes_sent = 0
        self._chunks_received = 0
        self._chunks_sent = 0
        self._start_time: Optional[datetime] = None
        self._last_activity: Optional[datetime] = None
        
        logger.info(f"[TelephonyStream {self.stream_id}] Initialized")
    
    async def connect(
        self,
        session_id: str,
        caller_id: str = None,
        callee_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Establish a telephony stream connection.
        
        Args:
            session_id: Unique session identifier
            caller_id: Phone number or identifier of caller
            callee_id: Phone number or identifier of callee
            metadata: Additional session metadata
            
        Returns:
            Connection result with stream details
        """
        try:
            self.session_id = session_id
            self.caller_id = caller_id
            self.callee_id = callee_id
            
            await self._set_state(StreamState.CONNECTING)
            
            # Initialize provider-specific connection here
            # (Twilio, Vonage, etc.)
            
            self._start_time = datetime.utcnow()
            self._last_activity = datetime.utcnow()
            
            await self._set_state(StreamState.CONNECTED)
            
            logger.info(
                f"[TelephonyStream {self.stream_id}] Connected - "
                f"session={session_id}, caller={caller_id}, callee={callee_id}"
            )
            
            return {
                "status": "connected",
                "stream_id": self.stream_id,
                "session_id": session_id,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "audio_format": self.audio_format.value,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TelephonyStream {self.stream_id}] Connection failed: {e}")
            await self._set_state(StreamState.ERROR)
            return {
                "status": "error",
                "error": str(e),
                "stream_id": self.stream_id
            }
    
    async def disconnect(self, reason: str = "normal") -> Dict[str, Any]:
        """
        Disconnect the telephony stream.
        
        Args:
            reason: Reason for disconnection
            
        Returns:
            Disconnection result with statistics
        """
        try:
            await self._set_state(StreamState.DISCONNECTED)
            
            duration = None
            if self._start_time:
                duration = (datetime.utcnow() - self._start_time).total_seconds()
            
            stats = self.get_stats()
            
            logger.info(
                f"[TelephonyStream {self.stream_id}] Disconnected - "
                f"reason={reason}, duration={duration}s"
            )
            
            return {
                "status": "disconnected",
                "stream_id": self.stream_id,
                "session_id": self.session_id,
                "reason": reason,
                "duration_seconds": duration,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"[TelephonyStream {self.stream_id}] Disconnect error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def receive_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process incoming audio data.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Processing result
        """
        if self.state not in [StreamState.CONNECTED, StreamState.PROCESSING]:
            return {
                "status": "ignored",
                "reason": f"Stream not in receiving state: {self.state.value}"
            }
        
        try:
            await self._set_state(StreamState.PROCESSING)
            
            # Update statistics
            self._bytes_received += len(audio_data)
            self._chunks_received += 1
            self._last_activity = datetime.utcnow()
            
            # Add to input buffer
            await self._input_buffer.put(audio_data)
            
            # Trigger callback if registered
            if self._on_audio_received:
                await self._on_audio_received(audio_data, self.session_id)
            
            return {
                "status": "received",
                "bytes": len(audio_data),
                "chunk_id": self._chunks_received,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.QueueFull:
            logger.warning(f"[TelephonyStream {self.stream_id}] Input buffer full, dropping chunk")
            return {
                "status": "dropped",
                "reason": "buffer_full"
            }
        except Exception as e:
            logger.error(f"[TelephonyStream {self.stream_id}] Audio receive error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Send audio data to the caller.
        
        Args:
            audio_data: Audio bytes to send
            
        Returns:
            Send result
        """
        if self.state not in [StreamState.CONNECTED, StreamState.PROCESSING]:
            return {
                "status": "ignored",
                "reason": f"Stream not in sending state: {self.state.value}"
            }
        
        try:
            # Update statistics
            self._bytes_sent += len(audio_data)
            self._chunks_sent += 1
            self._last_activity = datetime.utcnow()
            
            # Add to output buffer
            await self._output_buffer.put(audio_data)
            
            # Trigger callback if registered
            if self._on_audio_sent:
                await self._on_audio_sent(audio_data, self.session_id)
            
            return {
                "status": "sent",
                "bytes": len(audio_data),
                "chunk_id": self._chunks_sent,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except asyncio.QueueFull:
            logger.warning(f"[TelephonyStream {self.stream_id}] Output buffer full")
            return {
                "status": "dropped",
                "reason": "buffer_full"
            }
        except Exception as e:
            logger.error(f"[TelephonyStream {self.stream_id}] Audio send error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_text_as_speech(
        self,
        text: str,
        language: str = "en",
        voice: str = None,
        prosody_style: str = None
    ) -> Dict[str, Any]:
        """
        Convert text to speech and send as audio.
        
        Args:
            text: Text to convert to speech
            language: Language code
            voice: Voice identifier
            prosody_style: Prosody style (fast, slow, etc.)
            
        Returns:
            Result of TTS generation and sending
        """
        try:
            from app.audio.tts_service import get_tts_service
            
            tts_service = get_tts_service()
            
            # Generate speech
            result = tts_service.synthesize(
                text=text,
                language=language,
                voice=voice,
                prosody_style=prosody_style
            )
            
            if result.get("status") != "success":
                return {
                    "status": "error",
                    "error": result.get("error", "TTS synthesis failed")
                }
            
            # Decode and send audio
            audio_base64 = result.get("audio_base64")
            if audio_base64:
                audio_bytes = base64.b64decode(audio_base64)
                send_result = await self.send_audio(audio_bytes)
                
                return {
                    "status": "success",
                    "tts_result": result,
                    "send_result": send_result
                }
            
            return {
                "status": "error",
                "error": "No audio generated"
            }
            
        except Exception as e:
            logger.error(f"[TelephonyStream {self.stream_id}] TTS send error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def stream_audio_generator(self) -> AsyncGenerator[bytes, None]:
        """
        Generate audio chunks for streaming playback.
        
        Yields:
            Audio bytes chunks
        """
        while self.state in [StreamState.CONNECTED, StreamState.PROCESSING]:
            try:
                audio_chunk = await asyncio.wait_for(
                    self._output_buffer.get(),
                    timeout=0.1
                )
                yield audio_chunk
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[TelephonyStream {self.stream_id}] Stream generator error: {e}")
                break
    
    def get_input_buffer(self) -> asyncio.Queue:
        """Get the input audio buffer"""
        return self._input_buffer
    
    def get_output_buffer(self) -> asyncio.Queue:
        """Get the output audio buffer"""
        return self._output_buffer
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        duration = None
        if self._start_time:
            duration = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "state": self.state.value,
            "bytes_received": self._bytes_received,
            "bytes_sent": self._bytes_sent,
            "chunks_received": self._chunks_received,
            "chunks_sent": self._chunks_sent,
            "duration_seconds": duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "audio_format": self.audio_format.value
        }
    
    async def _set_state(self, new_state: StreamState):
        """Update stream state and trigger callback"""
        old_state = self.state
        self.state = new_state
        
        if old_state != new_state:
            logger.info(
                f"[TelephonyStream {self.stream_id}] State change: "
                f"{old_state.value} -> {new_state.value}"
            )
            
            if self._on_state_change:
                await self._on_state_change(old_state, new_state, self.session_id)
    
    def set_callbacks(
        self,
        on_audio_received: Callable = None,
        on_audio_sent: Callable = None,
        on_state_change: Callable = None,
        on_error: Callable = None
    ):
        """Set stream event callbacks"""
        self._on_audio_received = on_audio_received
        self._on_audio_sent = on_audio_sent
        self._on_state_change = on_state_change
        self._on_error = on_error
    
    @property
    def is_connected(self) -> bool:
        """Check if stream is connected"""
        return self.state in [StreamState.CONNECTED, StreamState.PROCESSING]
    
    @property
    def is_active(self) -> bool:
        """Check if stream is active (connected or processing)"""
        return self.state in [
            StreamState.CONNECTING,
            StreamState.CONNECTED,
            StreamState.PROCESSING,
            StreamState.PAUSED
        ]

    # =========================================================
    # WebSocket Support for Twilio/VoIP
    # =========================================================

    async def handle_websocket(
        self,
        websocket: WebSocket,
        session_id: str,
        caller_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Handle WebSocket connection for live audio streaming.
        This integrates with Twilio's Media Stream.
        
        Args:
            websocket: FastAPI WebSocket connection
            session_id: Session identifier
            caller_id: Caller phone number/ID
            metadata: Additional metadata
        """
        from app.voice.voice_session_manager import get_voice_session_manager
        from app.voice.language_auto import get_language_auto
        from app.voice.failure_handler import get_failure_handler
        
        session_manager = get_voice_session_manager()
        lang_auto = get_language_auto()
        failure_handler = get_failure_handler()
        
        # Connect the stream
        await self.connect(
            session_id=session_id,
            caller_id=caller_id,
            callee_id=metadata.get("callee_id", "assistant") if metadata else "assistant",
            metadata=metadata
        )
        
        # Create/update voice session
        try:
            voice_session = await session_manager.create_session(
                session_type="inbound",
                caller_id=caller_id or "unknown",
                callee_id="assistant",
                caller_number=caller_id,
                provider=metadata.get("provider", "twilio") if metadata else "twilio",
                context=metadata or {}
            )
            await session_manager.attach_stream(voice_session.session_id, self)
            await session_manager.start_session(voice_session.session_id)
        except Exception as e:
            logger.error(f"[TelephonyStream] Session creation error: {e}")
        
        # Process incoming messages and generate responses
        audio_buffer = b""
        transcription_text = ""
        
        try:
            while self.is_active:
                try:
                    # Receive audio/text from WebSocket
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=1.0
                    )
                    
                    data = json.loads(message)
                    event = data.get("event", "")
                    
                    if event == "media":
                        # Receive audio chunk from Twilio
                        media = data.get("media", {})
                        audio_b64 = media.get("blob", "")
                        
                        if audio_b64:
                            audio_chunk = base64.b64decode(audio_b64)
                            audio_buffer += audio_chunk
                            
                            # Process audio when enough accumulated (e.g., 1 second)
                            if len(audio_buffer) >= self.sample_rate * self.channels * 2:  # 1 sec of 16-bit audio
                                await self.receive_audio(audio_buffer)
                                
                                # Here you would send to STT service
                                # For now, accumulate for transcription
                                audio_buffer = b""
                    
                    elif event == "start":
                        # Call started
                        start_data = data.get("start", {})
                        logger.info(f"[TelephonyStream] Stream started - {start_data}")
                        
                    elif event == "stop":
                        # Call ended
                        logger.info("[TelephonyStream] Stream stopped")
                        break
                        
                    elif event == "dtmf":
                        # DTMF tone received
                        dtmf = data.get("dtmf", {})
                        digit = dtmf.get("digit", "")
                        logger.info(f"[TelephonyStream] DTMF received - {digit}")
                        
                except asyncio.TimeoutError:
                    # No message received, check if we should send pending audio
                    continue
                    
                except WebSocketDisconnect:
                    logger.info("[TelephonyStream] WebSocket disconnected")
                    break
                
                # Check if there's TTS audio to send back
                while not self._output_buffer.empty():
                    try:
                        audio_to_send = self._output_buffer.get_nowait()
                        
                        # Encode to base64 for Twilio
                        audio_b64 = base64.b64encode(audio_to_send).decode("utf-8")
                        
                        # Send as media message
                        response = {
                            "event": "media",
                            "media": {
                                "blob": audio_b64
                            }
                        }
                        await websocket.send_json(response)
                        
                    except asyncio.QueueEmpty:
                        break
                    except Exception as e:
                        logger.error(f"[TelephonyStream] Send error: {e}")
        
        except Exception as e:
            logger.error(f"[TelephonyStream] WebSocket handling error: {e}")
            await failure_handler.handle_failure(
                failure_type="websocket_error",
                message=str(e),
                severity="high",
                session_id=session_id
            )
        
        finally:
            # Cleanup
            await self.disconnect(reason="websocket_closed")
            
            # End voice session
            if voice_session:
                await session_manager.end_session(voice_session.session_id, reason="call_ended")

    async def send_tts_to_websocket(
        self,
        websocket: WebSocket,
        text: str,
        language: str = "en",
        voice: str = None
    ):
        """
        Convert text to speech and send directly via WebSocket.
        
        Args:
            websocket: WebSocket to send audio to
            text: Text to synthesize
            language: Language code
            voice: Voice ID
        """
        try:
            from app.audio.tts_service import get_tts_service
            
            tts_service = get_tts_service()
            
            # Generate TTS
            result = tts_service.synthesize(
                text=text,
                language=language,
                voice=voice
            )
            
            if result.get("status") == "success":
                audio_b64 = result.get("audio_base64")
                
                if audio_b64:
                    # Convert to Twilio format (8kHz mono if needed)
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_converted = self._convert_audio_for_twilio(audio_bytes)
                    audio_b64_converted = base64.b64encode(audio_converted).decode("utf-8")
                    
                    # Send media event with audio
                    response = {
                        "event": "media",
                        "media": {
                            "blob": audio_b64_converted
                        }
                    }
                    await websocket.send_json(response)
                    
                    logger.info(f"[TelephonyStream] TTS sent - text length: {len(text)}")
                    return {"success": True}
            
            return {"success": False, "error": result.get("error")}
            
        except Exception as e:
            logger.error(f"[TelephonyStream] TTS WebSocket send error: {e}")
            return {"success": False, "error": str(e)}

    def _convert_audio_for_twilio(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio to Twilio Media Stream format (PCM 8kHz mono).
        
        Twilio Media Stream expects:
        - Format: RAW (not WAV)
        - Sample rate: 8000 Hz
        - Channels: 1 (mono)
        - Bit depth: 16-bit signed little-endian
        
        Args:
            audio_bytes: Input audio bytes
            
        Returns:
            Converted audio bytes
        """
        try:
            import io
            import wave
            
            # Try to read as WAV first
            try:
                with wave.open(io.BytesIO(audio_bytes), 'rb') as wav:
                    original_rate = wav.getframerate()
                    original_channels = wav.getnchannels()
                    
                    # Read all frames
                    frames = wav.readframes(wav.getnframes())
                    
                    # Convert to mono if stereo
                    if original_channels == 2:
                        import audioop
                        frames = audioop.tomono(frames, 2, 1, 1)
                    
                    # Convert sample rate if needed
                    if original_rate != 8000:
                        try:
                            frames = audioop.ratecv(
                                frames, 2, 1, original_rate, 8000, None
                            )[0]
                        except:
                            # If ratecv fails, keep original
                            pass
                    
                    return frames
            
            except:
                # Not a WAV file, assume it's already raw PCM
                # Try to convert if it seems like audio
                if len(audio_bytes) > 0:
                    # Return as-is for now (could add resampling)
                    return audio_bytes
                return audio_bytes
                
        except Exception as e:
            logger.warning(f"[TelephonyStream] Audio conversion error: {e}")
            return audio_bytes

    async def execute_tts_and_send(
        self,
        websocket: WebSocket,
        text: str,
        language: str = "en",
        voice: str = None,
        stream_sid: str = None
    ):
        """
        Execute TTS and send to WebSocket with proper Twilio format.
        Also handles Mark messages for flow control.
        
        Args:
            websocket: WebSocket connection
            text: Text to speak
            language: Language code
            voice: Voice ID
            stream_sid: Stream ID for marking
        """
        try:
            from app.audio.tts_service import get_tts_service
            
            tts_service = get_tts_service()
            
            # Generate TTS
            result = tts_service.synthesize(
                text=text,
                language=language,
                voice=voice
            )
            
            if result.get("status") != "success":
                logger.error(f"[TelephonyStream] TTS failed: {result.get('error')}")
                return {"success": False, "error": result.get("error")}
            
            audio_b64 = result.get("audio_base64")
            if not audio_b64:
                return {"success": False, "error": "No audio generated"}
            
            # Decode and convert
            audio_bytes = base64.b64decode(audio_b64)
            audio_converted = self._convert_audio_for_twilio(audio_bytes)
            
            # Send Mark (flow control)
            if stream_sid:
                await websocket.send_json({
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "response_start"}
                })
            
            # Send audio in chunks (Twilio expects chunks)
            chunk_size = 160 * 5  # ~20ms chunks at 8kHz
            for i in range(0, len(audio_converted), chunk_size):
                chunk = audio_converted[i:i + chunk_size]
                chunk_b64 = base64.b64encode(chunk).decode("utf-8")
                
                await websocket.send_json({
                    "event": "media",
                    "media": {"blob": chunk_b64}
                })
            
            # Send Mark after completion
            if stream_sid:
                await websocket.send_json({
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "response_end"}
                })
            
            logger.info(f"[TelephonyStream] TTS executed and sent - text: {len(text)} chars")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"[TelephonyStream] TTS execution error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_telephony_stream_instance: Optional[TelephonyStream] = None


def get_telephony_stream() -> TelephonyStream:
    """Get or create the global TelephonyStream instance"""
    global _telephony_stream_instance
    if _telephony_stream_instance is None:
        _telephony_stream_instance = TelephonyStream()
    return _telephony_stream_instance


def create_telephony_stream(**kwargs) -> TelephonyStream:
    """Create a new TelephonyStream instance"""
    return TelephonyStream(**kwargs)
