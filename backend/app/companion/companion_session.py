"""
companion_session.py — Mitra Companion Session Manager

Manages persistent sessions per user_id + platform.
Sessions persist across devices via MongoDB.
Falls back to in-memory if MongoDB unavailable.
"""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_SESSION_COLLECTION = "mitra_companion_sessions"
_HISTORY_COLLECTION = "mitra_conversation_history"


@dataclass
class CompanionSession:
    session_id: str
    user_id: str
    platform: str = "web"
    device: str = "browser"
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_active: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turn_count: int = 0
    capabilities_used: List[str] = field(default_factory=list)

    def touch(self) -> None:
        self.last_active = datetime.now(timezone.utc).isoformat()
        self.turn_count += 1

    def is_expired(self, ttl_hours: int = 24) -> bool:
        try:
            last = datetime.fromisoformat(self.last_active.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) - last > timedelta(hours=ttl_hours)
        except Exception:
            return False

    def to_dict(self) -> Dict:
        return {
            "session_id":        self.session_id,
            "user_id":           self.user_id,
            "platform":          self.platform,
            "device":            self.device,
            "started_at":        self.started_at,
            "last_active":       self.last_active,
            "turn_count":        self.turn_count,
            "capabilities_used": self.capabilities_used,
        }


@dataclass
class MessageTurn:
    role: str          # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    capability_result: Optional[Dict] = None   # attached if capability was invoked


class SessionManager:
    """
    Creates, retrieves, and updates companion sessions.
    Conversation history stored per session for LLM context injection.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, CompanionSession] = {}
        self._histories: Dict[str, List[MessageTurn]] = {}
        self._mongo_available = False
        self._session_col = None
        self._history_col = None
        self._init_mongo()

    def _init_mongo(self) -> None:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            return
        try:
            from pymongo import MongoClient  # type: ignore
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db_name = os.getenv("MONGODB_DB", "mitra")
            self._session_col = client[db_name][_SESSION_COLLECTION]
            self._history_col = client[db_name][_HISTORY_COLLECTION]
            self._mongo_available = True
            logger.info("SessionManager: MongoDB connected")
        except Exception as exc:
            logger.warning("SessionManager: MongoDB unavailable (%s), using cache.", exc)

    async def get_or_create(
        self,
        user_id: str,
        platform: str = "web",
        device: str = "browser",
        ttl_hours: int = 24,
    ) -> CompanionSession:
        """Get existing active session or create a new one."""
        # Check cache
        session = self._sessions.get(user_id)
        if session and not session.is_expired(ttl_hours):
            return session

        # Check MongoDB
        if self._mongo_available and self._session_col is not None:
            try:
                doc = self._session_col.find_one({"user_id": user_id})
                if doc:
                    session = self._from_doc(doc)
                    if not session.is_expired(ttl_hours):
                        self._sessions[user_id] = session
                        return session
            except Exception as exc:
                logger.warning("SessionManager.get failed: %s", exc)

        # Create new session
        session = CompanionSession(
            session_id=f"sess_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            platform=platform,
            device=device,
        )
        self._sessions[user_id] = session
        await self._save_session(session)
        return session

    async def touch(self, user_id: str, capability: Optional[str] = None) -> None:
        session = self._sessions.get(user_id)
        if session:
            session.touch()
            if capability and capability not in session.capabilities_used:
                session.capabilities_used.append(capability)
            await self._save_session(session)

    async def add_turn(
        self,
        user_id: str,
        role: str,
        content: str,
        capability_result: Optional[Dict] = None,
    ) -> None:
        session = self._sessions.get(user_id)
        if not session:
            return
        turn = MessageTurn(role=role, content=content, capability_result=capability_result)
        history = self._histories.setdefault(session.session_id, [])
        history.append(turn)
        # Keep last 100 turns in memory
        if len(history) > 100:
            self._histories[session.session_id] = history[-100:]
        await self._save_turn(session.session_id, turn)

    async def get_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Returns last N turns as OpenAI-compatible message dicts.
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        session = self._sessions.get(user_id)
        if not session:
            return []
        history = self._histories.get(session.session_id, [])

        # Try MongoDB if cache empty
        if not history and self._mongo_available and self._history_col is not None:
            try:
                docs = list(
                    self._history_col.find({"session_id": session.session_id})
                    .sort("timestamp", -1)
                    .limit(limit)
                )
                history = [
                    MessageTurn(
                        role=d["role"],
                        content=d["content"],
                        timestamp=d.get("timestamp", ""),
                        capability_result=d.get("capability_result"),
                    )
                    for d in reversed(docs)
                ]
                self._histories[session.session_id] = history
            except Exception as exc:
                logger.warning("SessionManager.get_history failed: %s", exc)

        recent = history[-limit:]
        return [
            {"role": t.role, "content": t.content}
            for t in recent
        ]

    async def clear_session(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)
        session_id = None
        if self._mongo_available and self._session_col is not None:
            try:
                doc = self._session_col.find_one({"user_id": user_id})
                if doc:
                    session_id = doc.get("session_id")
                self._session_col.delete_one({"user_id": user_id})
                if session_id and self._history_col is not None:
                    self._history_col.delete_many({"session_id": session_id})
            except Exception as exc:
                logger.warning("SessionManager.clear failed: %s", exc)

    # ── persistence ─────────────────────────────────────────────────

    async def _save_session(self, session: CompanionSession) -> None:
        if not self._mongo_available or self._session_col is None:
            return
        try:
            self._session_col.replace_one(
                {"user_id": session.user_id}, session.to_dict(), upsert=True
            )
        except Exception as exc:
            logger.warning("SessionManager._save_session failed: %s", exc)

    async def _save_turn(self, session_id: str, turn: MessageTurn) -> None:
        if not self._mongo_available or self._history_col is None:
            return
        try:
            self._history_col.insert_one({
                "session_id":        session_id,
                "role":              turn.role,
                "content":           turn.content,
                "timestamp":         turn.timestamp,
                "capability_result": turn.capability_result,
            })
        except Exception as exc:
            logger.warning("SessionManager._save_turn failed: %s", exc)

    @staticmethod
    def _from_doc(doc: Dict) -> CompanionSession:
        return CompanionSession(
            session_id=doc["session_id"],
            user_id=doc["user_id"],
            platform=doc.get("platform", "web"),
            device=doc.get("device", "browser"),
            started_at=doc.get("started_at", ""),
            last_active=doc.get("last_active", ""),
            turn_count=doc.get("turn_count", 0),
            capabilities_used=doc.get("capabilities_used", []),
        )


# Singleton
session_manager = SessionManager()
