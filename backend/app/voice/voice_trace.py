"""
Voice Trace Logging - MongoDB-based trace storage

Stores voice conversation traces in MongoDB for:
- Debugging and troubleshooting
- Performance analysis
- Quality monitoring
- Audit trail
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field, asdict

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VoiceTrace:
    """Voice trace data model - stores each conversation turn"""
    trace_id: str
    session_id: str
    channel: str  # "phone" or "whatsapp"
    language: str
    
    # Conversation data
    user_transcript: str = ""
    assistant_response: str = ""
    tts_path: str = ""
    
    # Timing (in milliseconds)
    stt_time_ms: int = 0
    llm_time_ms: int = 0
    tts_time_ms: int = 0
    total_latency_ms: int = 0
    
    # Status
    failure: bool = False
    failure_reason: str = ""
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    turn_number: int = 0
    
    # Additional context
    caller_id: str = ""
    callee_id: str = ""
    platform_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB"""
        data = asdict(self)
        # Convert datetime to ISO string
        data["timestamp"] = self.timestamp.isoformat()
        return data


class VoiceTraceLogger:
    """
    Logs voice conversation traces to MongoDB.
    Replaces/augments the bucket service for voice-specific traces.
    """
    
    def __init__(
        self,
        mongo_uri: str = None,
        database_name: str = "ai_assistant",
        collection_name: str = "voice_traces"
    ):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self.collection_name = collection_name
        
        self._client = None
        self._db = None
        self._collection = None
        self._connected = False
        
        # In-memory fallback if MongoDB unavailable
        self._memory_store: List[Dict[str, Any]] = []
        
        logger.info(f"[VoiceTraceLogger] Initialized - DB: {database_name}")
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            self._client = AsyncIOMotorClient(self.mongo_uri)
            self._db = self._client[self.database_name]
            self._collection = self._db[self.collection_name]
            
            # Create indexes
            await self._collection.create_index("trace_id")
            await self._collection.create_index("session_id")
            await self._collection.create_index("timestamp")
            await self._collection.create_index([("session_id", 1), ("timestamp", 1)])
            
            self._connected = True
            logger.info("[VoiceTraceLogger] Connected to MongoDB")
            
        except Exception as e:
            logger.warning(f"[VoiceTraceLogger] MongoDB connection failed: {e}")
            logger.info("[VoiceTraceLogger] Using in-memory storage")
            self._connected = False
    
    async def log_turn(
        self,
        trace_id: str,
        session_id: str,
        channel: str,
        language: str,
        user_transcript: str = "",
        assistant_response: str = "",
        tts_path: str = "",
        stt_time_ms: int = 0,
        llm_time_ms: int = 0,
        tts_time_ms: int = 0,
        failure: bool = False,
        failure_reason: str = "",
        caller_id: str = "",
        callee_id: str = "",
        metadata: Dict[str, Any] = None,
        turn_number: int = 0
    ) -> str:
        """
        Log a conversation turn to MongoDB.
        
        Args:
            trace_id: Continous trace ID for the call
            session_id: Session identifier
            channel: "phone" or "whatsapp"
            language: Detected language
            user_transcript: What the user said
            assistant_response: AI response text
            tts_path: Path/URL to generated TTS
            stt_time_ms: STT processing time
            llm_time_ms: LLM processing time
            tts_time_ms: TTS generation time
            failure: Whether this turn had a failure
            failure_reason: Reason for failure
            caller_id: Caller's phone number
            callee_id: Callee's identifier
            metadata: Additional platform metadata
            turn_number: Turn number in conversation
            
        Returns:
            Logged trace ID
        """
        total_latency = stt_time_ms + llm_time_ms + tts_time_ms
        
        trace = VoiceTrace(
            trace_id=trace_id,
            session_id=session_id,
            channel=channel,
            language=language,
            user_transcript=user_transcript,
            assistant_response=assistant_response,
            tts_path=tts_path,
            stt_time_ms=stt_time_ms,
            llm_time_ms=llm_time_ms,
            tts_time_ms=tts_time_ms,
            total_latency_ms=total_latency,
            failure=failure,
            failure_reason=failure_reason,
            caller_id=caller_id,
            callee_id=callee_id,
            platform_metadata=metadata or {},
            turn_number=turn_number
        )
        
        trace_dict = trace.to_dict()
        
        if self._connected:
            try:
                await self._collection.insert_one(trace_dict)
                logger.debug(f"[VoiceTraceLogger] Turn logged - trace: {trace_id}, turn: {turn_number}")
            except Exception as e:
                logger.error(f"[VoiceTraceLogger] Insert error: {e}")
                self._memory_store.append(trace_dict)
        else:
            # Fallback to memory
            self._memory_store.append(trace_dict)
            logger.debug(f"[VoiceTraceLogger] Turn logged (memory) - trace: {trace_id}")
        
        return trace_id
    
    async def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all turns for a trace ID"""
        if self._connected:
            try:
                cursor = self._collection.find({"trace_id": trace_id}).sort("turn_number", 1)
                return await cursor.to_list(length=100)
            except Exception as e:
                logger.error(f"[VoiceTraceLogger] Query error: {e}")
        
        # Fallback to memory
        return [t for t in self._memory_store if t.get("trace_id") == trace_id]
    
    async def get_session_traces(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all traces for a session"""
        if self._connected:
            try:
                cursor = self._collection.find({"session_id": session_id}).sort("timestamp", -1)
                return await cursor.to_list(length=100)
            except Exception as e:
                logger.error(f"[VoiceTraceLogger] Query error: {e}")
        
        return [t for t in self._memory_store if t.get("session_id") == session_id]
    
    async def get_latency_stats(
        self,
        channel: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get latency statistics"""
        query = {}
        
        if channel:
            query["channel"] = channel
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date.isoformat()
            if end_date:
                query["timestamp"]["$lte"] = end_date.isoformat()
        
        if self._connected:
            try:
                pipeline = [
                    {"$match": query},
                    {"$group": {
                        "_id": None,
                        "avg_stt": {"$avg": "$stt_time_ms"},
                        "avg_llm": {"$avg": "$llm_time_ms"},
                        "avg_tts": {"$avg": "$tts_time_ms"},
                        "avg_total": {"$avg": "$total_latency_ms"},
                        "count": {"$sum": 1},
                        "failures": {"$sum": {"$cond": ["$failure", 1, 0]}}
                    }}
                ]
                result = await self._collection.aggregate(pipeline).to_list(1)
                if result:
                    return result[0]
            except Exception as e:
                logger.error(f"[VoiceTraceLogger] Stats error: {e}")
        
        return {"count": len(self._memory_store), "avg_total": 0}
    
    async def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent traces"""
        if self._connected:
            try:
                cursor = self._collection.find().sort("timestamp", -1).limit(limit)
                return await cursor.to_list(length=limit)
            except Exception as e:
                logger.error(f"[VoiceTraceLogger] Query error: {e}")
        
        return sorted(self._memory_store, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]


# Global instance
_voice_trace_logger: Optional[VoiceTraceLogger] = None


def get_voice_trace_logger() -> VoiceTraceLogger:
    """Get or create global VoiceTraceLogger instance"""
    global _voice_trace_logger
    if _voice_trace_logger is None:
        _voice_trace_logger = VoiceTraceLogger()
    return _voice_trace_logger


def create_voice_trace_logger(**kwargs) -> VoiceTraceLogger:
    """Create a new VoiceTraceLogger instance"""
    return VoiceTraceLogger(**kwargs)
