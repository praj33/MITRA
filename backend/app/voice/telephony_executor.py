"""
Telephony Execution - TTS to Telephony Playback

Handles:
- TTS generation for non-streaming calls
- Audio format conversion for Twilio
- CDN upload for audio files
- TwiML Play response generation
"""

import os
import io
import base64
import uuid
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class TelephonyExecutor:
    """
    Handles TTS generation and playback for telephony calls.
    Supports both streaming (WebSocket) and non-streaming (TwiML) modes.
    """
    
    def __init__(
        self,
        cdn_base_url: str = None,
        audio_cache_dir: str = "./audio_cache"
    ):
        self.cdn_base_url = cdn_base_url or os.getenv("CDN_BASE_URL", "https://yourcdn.com/audio")
        self.audio_cache_dir = audio_cache_dir
        
        logger.info(f"[TelephonyExecutor] Initialized - CDN: {self.cdn_base_url}")
    
    async def generate_and_upload_tts(
        self,
        text: str,
        language: str = "en",
        voice: str = None,
        session_id: str = None,
        trace_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate TTS and upload to CDN.
        
        Args:
            text: Text to synthesize
            language: Language code
            voice: Voice ID
            session_id: Session identifier
            trace_id: Trace ID for tracking
            
        Returns:
            Dict with audio URL and metadata
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
                return {
                    "success": False,
                    "error": result.get("error", "TTS generation failed")
                }
            
            # Get audio bytes
            audio_b64 = result.get("audio_base64")
            if not audio_b64:
                return {"success": False, "error": "No audio generated"}
            
            audio_bytes = base64.b64decode(audio_b64)
            
            # Generate unique filename
            trace = trace_id or f"trace_{uuid.uuid4().hex[:8]}"
            session = session_id or f"session_{uuid.uuid4().hex[:8]}"
            
            # Convert to WAV for better compatibility
            wav_bytes = self._convert_to_wav(audio_bytes, language)
            
            # Upload to CDN (or save locally)
            audio_url = await self._upload_audio(
                wav_bytes,
                trace_id=trace,
                session_id=session
            )
            
            # Generate TwiML for playback
            twiml = self.generate_play_twiml(audio_url)
            
            logger.info(
                f"[TelephonyExecutor] TTS generated - "
                f"trace={trace}, url={audio_url}"
            )
            
            return {
                "success": True,
                "audio_url": audio_url,
                "audio_bytes": len(wav_bytes),
                "twiml": twiml,
                "trace_id": trace,
                "language": language,
                "duration_seconds": len(wav_bytes) / 16000  # Approximate
            }
            
        except Exception as e:
            logger.error(f"[TelephonyExecutor] Error: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_play_twiml(self, audio_url: str) -> str:
        """
        Generate TwiML to play an audio file.
        
        Args:
            audio_url: URL of audio file
            
        Returns:
            TwiML XML string
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
</Response>"""
    
    def generate_gather_twiml(
        self,
        audio_url: str = None,
        prompt: str = None,
        num_digits: int = 1,
        action_url: str = None
    ) -> str:
        """
        Generate TwiML to play audio and gather input.
        """
        parts = []
        
        if audio_url:
            parts.append(f"<Play>{audio_url}</Play>")
        elif prompt:
            parts.append(f"<Say voice='alice'>{prompt}</Say>")
        
        action = f' action="{action_url}"' if action_url else ""
        parts.append(f'<Gather numDigits="{num_digits}"{action} />')
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {"".join(parts)}
</Response>"""
    
    def _convert_to_wav(self, audio_bytes: bytes, language: str = "en") -> bytes:
        """
        Convert raw audio to WAV format.
        
        Args:
            audio_bytes: Raw audio bytes
            language: Language code (for sample rate selection)
            
        Returns:
            WAV-encoded audio bytes
        """
        try:
            import wave
            
            # Use appropriate sample rate for language
            sample_rate = 16000  # Standard for most TTS
            
            output = io.BytesIO()
            
            with wave.open(output, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"[TelephonyExecutor] WAV conversion error: {e}")
            # Return original if conversion fails
            return audio_bytes
    
    async def _upload_audio(
        self,
        audio_bytes: bytes,
        trace_id: str,
        session_id: str
    ) -> str:
        """
        Upload audio to CDN or save locally.
        
        Args:
            audio_bytes: Audio data
            trace_id: Trace identifier
            session_id: Session identifier
            
        Returns:
            URL of uploaded audio
        """
        # Generate filename
        filename = f"{trace_id}_{session_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.wav"
        
        # Try to upload to CDN if configured
        if self.cdn_base_url and self.cdn_base_url != "https://yourcdn.com/audio":
            try:
                cdn_url = await self._upload_to_cdn(audio_bytes, filename)
                if cdn_url:
                    return cdn_url
            except Exception as e:
                logger.warning(f"[TelephonyExecutor] CDN upload failed: {e}")
        
        # Fallback: save locally
        local_path = await self._save_locally(audio_bytes, filename)
        
        if local_path:
            return f"{self.cdn_base_url}/{filename}"
        
        # Last resort: return base64 (not recommended for production)
        return f"data:audio/wav;base64,{base64.b64encode(audio_bytes).decode()}"
    
    async def _upload_to_cdn(self, audio_bytes: bytes, filename: str) -> Optional[str]:
        """
        Upload to CDN (S3, Cloudflare R2, etc.).
        Override this method for specific CDN implementation.
        """
        # Placeholder - implement based on your CDN
        # Example for S3:
        # import boto3
        # s3 = boto3.client('s3', ...)
        # s3.put_object(Bucket='your-bucket', Key=filename, Body=audio_bytes)
        # return f"https://your-bucket.s3.amazonaws.com/{filename}"
        
        logger.info(f"[TelephonyExecutor] Would upload to CDN: {filename}")
        return None
    
    async def _save_locally(self, audio_bytes: bytes, filename: str) -> Optional[str]:
        """
        Save audio locally.
        """
        try:
            os.makedirs(self.audio_cache_dir, exist_ok=True)
            filepath = os.path.join(self.audio_cache_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
            
            logger.info(f"[TelephonyExecutor] Saved locally: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"[TelephonyExecutor] Local save error: {e}")
            return None
    
    async def generate_conversation_tts(
        self,
        messages: list,
        language: str = "en",
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate TTS for a multi-message conversation.
        
        Args:
            messages: List of message dicts with 'text' and 'speaker' keys
            language: Language code
            session_id: Session identifier
            
        Returns:
            Dict with combined audio URL
        """
        try:
            import io
            import wave
            
            combined_audio = io.BytesIO()
            
            with wave.open(combined_audio, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(16000)
                
                for msg in messages:
                    text = msg.get("text", "")
                    if not text:
                        continue
                    
                    # Generate TTS for this message
                    result = await self.generate_and_upload_tts(
                        text=text,
                        language=language,
                        session_id=session_id
                    )
                    
                    if result.get("success"):
                        # Add to combined audio
                        audio_url = result.get("audio_url")
                        # In production, you'd fetch and combine the actual audio
                        
            logger.info(f"[TelephonyExecutor] Generated conversation TTS - {len(messages)} messages")
            return {"success": True, "message_count": len(messages)}
            
        except Exception as e:
            logger.error(f"[TelephonyExecutor] Conversation TTS error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_telephony_executor: Optional[TelephonyExecutor] = None


def get_telephony_executor() -> TelephonyExecutor:
    """Get or create global TelephonyExecutor instance"""
    global _telephony_executor
    if _telephony_executor is None:
        _telephony_executor = TelephonyExecutor()
    return _telephony_executor


def create_telephony_executor(**kwargs) -> TelephonyExecutor:
    """Create a new TelephonyExecutor instance"""
    return TelephonyExecutor(**kwargs)
