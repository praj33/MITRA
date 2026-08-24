"""
Voice Session Manager - Manages voice call sessions

Handles:
- Voice call session lifecycle (create, update, terminate)
- Session state management and persistence
- Multi-party call handling
- Session metadata and history tracking
"""

import asyncio
import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.voice.telephony_stream import TelephonyStream, StreamState

logger = get_logger(__name__)


class SessionStatus(Enum):
    """Voice session status"""
    INITIATING = "initiating"
    RINGING = "ringing"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    TRANSFERRING = "transferring"
    ENDED = "ended"
    FAILED = "failed"
    TIMEOUT = "timeout"


class SessionType(Enum):
    """Type of voice session"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    CONFERENCE = "conference"
    TRANSFER = "transfer"
    CALLBACK = "callback"


@dataclass
class VoiceSession:
    """Voice session data model"""
    session_id: str
    session_type: SessionType
    status: SessionStatus
    
    # Participants
    caller_id: str
    callee_id: str
    caller_number: Optional[str] = None
    callee_number: Optional[str] = None
    
    # Technical details
    stream_id: Optional[str] = None
    provider: str = "unknown"  # twilio, vonage, etc.
    sip_uri: Optional[str] = None
    
    # Language settings
    detected_language: str = "en"
    preferred_language: str = "en"
    tts_voice: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Context and history
    context: Dict[str, Any] = field(default_factory=dict)
    transcript: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Call flow
    redirect_count: int = 0
    transfer_count: int = 0
    escalation_count: int = 0
    
    # Quality metrics
    audio_quality_score: Optional[float] = None
    asr_confidence: Optional[float] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    # Conversation memory for full duplex
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "status": self.status.value,
            "caller_id": self.caller_id,
            "callee_id": self.callee_id,
            "caller_number": self.caller_number,
            "callee_number": self.callee_number,
            "stream_id": self.stream_id,
            "provider": self.provider,
            "sip_uri": self.sip_uri,
            "detected_language": self.detected_language,
            "preferred_language": self.preferred_language,
            "tts_voice": self.tts_voice,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "context": self.context,
            "transcript": self.transcript,
            "events": self.events,
            "redirect_count": self.redirect_count,
            "transfer_count": self.transfer_count,
            "escalation_count": self.escalation_count,
            "audio_quality_score": self.audio_quality_score,
            "asr_confidence": self.asr_confidence,
            "tags": self.tags,
            "notes": self.notes
        }


class VoiceSessionManager:
    """
    Manages voice call sessions throughout their lifecycle.
    Handles session creation, state transitions, and cleanup.
    Supports both in-memory and Redis-backed storage.
    """
    
    def __init__(
        self,
        session_timeout_minutes: int = 30,
        max_sessions: int = 1000,
        enable_persistence: bool = False,
        redis_url: str = None
    ):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.max_sessions = max_sessions
        self.enable_persistence = enable_persistence
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Active sessions storage
        self._sessions: Dict[str, VoiceSession] = {}
        self._streams: Dict[str, TelephonyStream] = {}
        
        # Session locking
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Redis client for persistence
        self._redis = None
        self._use_redis = False
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics
        self._total_sessions = 0
        self._active_count = 0
        
        logger.info("[VoiceSessionManager] Initialized")
    
    async def _init_redis(self):
        """Initialize Redis connection if available"""
        if self.enable_persistence:
            try:
                import redis.asyncio as redis
                self._redis = await redis.from_url(self.redis_url)
                self._use_redis = True
                logger.info("[VoiceSessionManager] Redis connected for session storage")
            except Exception as e:
                logger.warning(f"[VoiceSessionManager] Redis unavailable: {e}")
                self._use_redis = False
    
    async def _save_to_redis(self, session: VoiceSession):
        """Save session to Redis for persistence"""
        if not self._use_redis or not self._redis:
            return
        
        try:
            import json
            key = f"voice_session:{session.session_id}"
            data = json.dumps(session.to_dict())
            await self._redis.setex(key, self.session_timeout.seconds, data)
        except Exception as e:
            logger.error(f"[VoiceSessionManager] Redis save error: {e}")
    
    async def _load_from_redis(self, session_id: str) -> Optional[VoiceSession]:
        """Load session from Redis"""
        if not self._use_redis or not self._redis:
            return None
        
        try:
            import json
            key = f"voice_session:{session_id}"
            data = await self._redis.get(key)
            if data:
                session_data = json.loads(data)
                # Reconstruct session (simplified)
                return session_data
        except Exception as e:
            logger.error(f"[VoiceSessionManager] Redis load error: {e}")
        
        return None
    
    async def start(self):
        """Start the session manager"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("[VoiceSessionManager] Started")
    
    async def stop(self):
        """Stop the session manager"""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # End all active sessions
        for session in list(self._sessions.values()):
            if session.status == SessionStatus.ACTIVE:
                await self.end_session(session.session_id, reason="manager_shutdown")
        
        logger.info("[VoiceSessionManager] Stopped")
    
    async def create_session(
        self,
        session_type: SessionType,
        caller_id: str,
        callee_id: str,
        caller_number: str = None,
        callee_number: str = None,
        provider: str = "unknown",
        context: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> VoiceSession:
        """
        Create a new voice session.
        
        Args:
            session_type: Type of session (inbound, outbound, etc.)
            caller_id: Identifier for caller
            callee_id: Identifier for callee
            caller_number: Phone number of caller
            callee_number: Phone number of callee
            provider: Telephony provider
            context: Initial context
            metadata: Additional metadata
            
        Returns:
            Created VoiceSession
        """
        # Check session limit
        if len(self._sessions) >= self.max_sessions:
            raise RuntimeError(f"Maximum sessions ({self.max_sessions}) reached")
        
        session_id = f"voice_{uuid.uuid4().hex[:12]}"
        
        # Create session
        session = VoiceSession(
            session_id=session_id,
            session_type=session_type,
            status=SessionStatus.INITIATING,
            caller_id=caller_id,
            callee_id=callee_id,
            caller_number=caller_number,
            callee_number=callee_number,
            provider=provider,
            context=context or {},
            created_at=datetime.utcnow()
        )
        
        # Add metadata if provided
        if metadata:
            session.tags = metadata.get("tags", [])
            session.preferred_language = metadata.get("language", "en")
            session.tts_voice = metadata.get("voice")
        
        # Initialize lock
        self._locks[session_id] = asyncio.Lock()
        
        # Store session
        self._sessions[session_id] = session
        self._total_sessions += 1
        self._active_count += 1
        
        # Log creation
        logger.info(
            f"[VoiceSessionManager] Session created - "
            f"id={session_id}, type={session_type.value}, "
            f"caller={caller_id}, callee={callee_id}"
        )
        
        # Record event
        await self._record_event(session_id, "session_created", {
            "session_type": session_type.value,
            "provider": provider
        })
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    async def update_session(
        self,
        session_id: str,
        **updates
    ) -> Optional[VoiceSession]:
        """
        Update session fields.
        
        Args:
            session_id: Session to update
            **updates: Fields to update
            
        Returns:
            Updated session or None
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            # Log update
            logger.debug(f"[VoiceSessionManager] Session updated - {session_id}: {updates}")
        
        return session
    
    async def start_session(self, session_id: str) -> Optional[VoiceSession]:
        """
        Mark session as started/active.
        
        Args:
            session_id: Session to start
            
        Returns:
            Updated session
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            session.status = SessionStatus.ACTIVE
            session.started_at = datetime.utcnow()
        
        await self._record_event(session_id, "session_started", {
            "started_at": session.started_at.isoformat()
        })
        
        logger.info(f"[VoiceSessionManager] Session started - {session_id}")
        
        return session
    
    async def end_session(
        self,
        session_id: str,
        reason: str = "normal",
        status: SessionStatus = SessionStatus.ENDED
    ) -> Optional[VoiceSession]:
        """
        End a voice session.
        
        Args:
            session_id: Session to end
            reason: Reason for ending
            status: Final status
            
        Returns:
            Final session state
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            session.status = status
            session.ended_at = datetime.utcnow()
            
            if session.started_at:
                session.duration_seconds = (
                    session.ended_at - session.started_at
                ).total_seconds()
        
        # Clean up stream
        if session.stream_id and session.stream_id in self._streams:
            stream = self._streams[session.stream_id]
            await stream.disconnect(reason=reason)
            del self._streams[session.stream_id]
        
        self._active_count -= 1
        
        # Record event
        await self._record_event(session_id, "session_ended", {
            "reason": reason,
            "status": status.value,
            "duration_seconds": session.duration_seconds
        })
        
        logger.info(
            f"[VoiceSessionManager] Session ended - "
            f"{session_id}, reason={reason}, duration={session.duration_seconds}s"
        )
        
        return session
    
    async def add_transcript_entry(
        self,
        session_id: str,
        speaker: str,
        text: str,
        language: str = None,
        confidence: float = None,
        timestamp: datetime = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add an entry to the session transcript.
        
        Args:
            session_id: Session ID
            speaker: Speaker identifier (caller/assistant)
            text: Transcribed text
            language: Detected language
            confidence: ASR confidence score
            timestamp: Entry timestamp
            
        Returns:
            Transcript entry
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        entry = {
            "id": len(session.transcript) + 1,
            "speaker": speaker,
            "text": text,
            "timestamp": (timestamp or datetime.utcnow()).isoformat()
        }
        
        if language:
            entry["language"] = language
        if confidence is not None:
            entry["confidence"] = confidence
            # Update session ASR confidence
            if session.asr_confidence is None:
                session.asr_confidence = confidence
            else:
                session.asr_confidence = (session.asr_confidence + confidence) / 2
        
        session.transcript.append(entry)
        
        # Also add to conversation history for full duplex
        await self.add_conversation_turn(
            session_id=session_id,
            speaker=speaker,
            text=text,
            language=language
        )
        
        return entry
    
    async def add_conversation_turn(
        self,
        session_id: str,
        speaker: str,
        text: str,
        language: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a turn to the conversation history for full duplex memory.
        
        This maintains the full conversation context for the LLM.
        
        Args:
            session_id: Session ID
            speaker: Speaker (user/assistant)
            text: Message text
            language: Language of the message
            metadata: Additional metadata (intent, entities, etc.)
            
        Returns:
            Conversation turn entry
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        turn = {
            "turn": len(session.conversation_history) + 1,
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if language:
            turn["language"] = language
            # Update session language if user speaks different language
            if speaker == "user" and session.detected_language != language:
                session.detected_language = language
        
        if metadata:
            turn["metadata"] = metadata
        
        session.conversation_history.append(turn)
        
        logger.debug(
            f"[VoiceSessionManager] Conversation turn added - "
            f"session={session_id}, turn={turn['turn']}, speaker={speaker}"
        )
        
        return turn
    
    def get_conversation_history(
        self,
        session_id: str,
        max_turns: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for the LLM.
        
        Args:
            session_id: Session ID
            max_turns: Maximum number of recent turns to return (None = all)
            
        Returns:
            List of conversation turns
        """
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        history = session.conversation_history
        
        if max_turns and len(history) > max_turns:
            return history[-max_turns:]
        
        return history
    
    def get_conversation_for_llm(
        self,
        session_id: str,
        include_metadata: bool = False
    ) -> str:
        """
        Get formatted conversation history for LLM context.
        
        Args:
            session_id: Session ID
            include_metadata: Whether to include metadata
            
        Returns:
            Formatted string for LLM prompt
        """
        history = self.get_conversation_history(session_id)
        
        if not history:
            return ""
        
        formatted = []
        for turn in history:
            speaker = "User" if turn["speaker"] == "user" else "Assistant"
            text = turn["text"]
            formatted.append(f"{speaker}: {text}")
            
            if include_metadata and "metadata" in turn:
                formatted.append(f"  [Context: {turn['metadata']}]")
        
        return "\n".join(formatted)
    
    def get_conversation_count(self, session_id: str) -> int:
        """Get number of conversation turns"""
        session = self._sessions.get(session_id)
        if not session:
            return 0
        return len(session.conversation_history)
    
    async def transfer_session(
        self,
        session_id: str,
        target_callee_id: str,
        target_number: str = None,
        reason: str = None
    ) -> Optional[VoiceSession]:
        """
        Transfer session to another participant.
        
        Args:
            session_id: Session to transfer
            target_callee_id: New callee ID
            target_number: New callee number
            reason: Transfer reason
            
        Returns:
            Updated session
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            old_callee = session.callee_id
            session.callee_id = target_callee_id
            if target_number:
                session.callee_number = target_number
            session.status = SessionStatus.TRANSFERRING
            session.transfer_count += 1
        
        await self._record_event(session_id, "session_transferred", {
            "old_callee": old_callee,
            "new_callee": target_callee_id,
            "reason": reason
        })
        
        logger.info(
            f"[VoiceSessionManager] Session transferred - "
            f"{session_id}: {old_callee} -> {target_callee_id}"
        )
        
        return session
    
    async def hold_session(self, session_id: str) -> Optional[VoiceSession]:
        """Put session on hold"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            session.status = SessionStatus.ON_HOLD
        
        await self._record_event(session_id, "session_held", {})
        
        return session
    
    async def resume_session(self, session_id: str) -> Optional[VoiceSession]:
        """Resume session from hold"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        async with self._locks.get(session_id, asyncio.Lock()):
            session.status = SessionStatus.ACTIVE
        
        await self._record_event(session_id, "session_resumed", {})
        
        return session
    
    async def attach_stream(
        self,
        session_id: str,
        stream: TelephonyStream
    ) -> Optional[VoiceSession]:
        """
        Attach a telephony stream to a session.
        
        Args:
            session_id: Session ID
            stream: TelephonyStream to attach
            
        Returns:
            Updated session
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        session.stream_id = stream.stream_id
        self._streams[stream.stream_id] = stream
        
        logger.info(f"[VoiceSessionManager] Stream attached - {session_id}: {stream.stream_id}")
        
        return session
    
    def get_active_sessions(self) -> List[VoiceSession]:
        """Get all active sessions"""
        return [
            s for s in self._sessions.values()
            if s.status in [SessionStatus.ACTIVE, SessionStatus.ON_HOLD, SessionStatus.TRANSFERRING]
        ]
    
    def get_sessions_by_status(self, status: SessionStatus) -> List[VoiceSession]:
        """Get sessions by status"""
        return [s for s in self._sessions.values() if s.status == status]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session manager statistics"""
        return {
            "total_sessions": self._total_sessions,
            "active_sessions": self._active_count,
            "by_status": {
                status.value: len(self.get_sessions_by_status(status))
                for status in SessionStatus
            },
            "by_type": {
                stype.value: len([s for s in self._sessions.values() if s.session_type == stype])
                for stype in SessionType
            },
            "total_duration": sum(
                s.duration_seconds or 0
                for s in self._sessions.values()
                if s.duration_seconds
            )
        }
    
    async def _record_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Record session event"""
        session = await self.get_session(session_id)
        if not session:
            return
        
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        session.events.append(event)
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                expired = []
                
                for session_id, session in self._sessions.items():
                    if session.status in [SessionStatus.ACTIVE, SessionStatus.ON_HOLD]:
                        # Check for timeout
                        last_activity = session.started_at or session.created_at
                        if now - last_activity > self.session_timeout:
                            expired.append(session_id)
                
                # End expired sessions
                for session_id in expired:
                    logger.warning(f"[VoiceSessionManager] Session timeout - {session_id}")
                    await self.end_session(
                        session_id,
                        reason="timeout",
                        status=SessionStatus.TIMEOUT
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[VoiceSessionManager] Cleanup error: {e}")


# Global instance
_session_manager_instance: Optional[VoiceSessionManager] = None


def get_voice_session_manager() -> VoiceSessionManager:
    """Get or create the global VoiceSessionManager instance"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = VoiceSessionManager()
    return _session_manager_instance


def create_voice_session_manager(**kwargs) -> VoiceSessionManager:
    """Create a new VoiceSessionManager instance"""
    return VoiceSessionManager(**kwargs)
