"""
companion_memory.py — Mitra Companion Memory Layer

Per-user persistent memory backed by MongoDB (via BucketService).
Stores: user facts, conversation summaries, capability history.
Falls back to in-memory if MongoDB is unavailable.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MEMORY_COLLECTION = "mitra_companion_memory"


@dataclass
class UserFact:
    key: str
    value: Any
    source: str = "user"      # user | inferred | capability
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ConversationSummary:
    session_id: str
    summary: str
    capabilities_used: List[str]
    created_at: str
    turn_count: int = 0


@dataclass
class UserMemory:
    user_id: str
    facts: Dict[str, UserFact] = field(default_factory=dict)
    conversation_summaries: List[ConversationSummary] = field(default_factory=list)
    capability_history: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def get_fact(self, key: str) -> Optional[Any]:
        f = self.facts.get(key)
        return f.value if f else None

    def set_fact(self, key: str, value: Any, source: str = "user") -> None:
        self.facts[key] = UserFact(key=key, value=value, source=source)

    def to_context_dict(self) -> Dict[str, Any]:
        """Compact representation for LLM context injection."""
        return {
            k: v.value
            for k, v in self.facts.items()
            if v.value
        }


class CompanionMemory:
    """
    Reads and writes per-user memory.
    Primary: MongoDB via BucketService.
    Fallback: in-process dict cache.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, UserMemory] = {}
        self._mongo_available = False
        self._mongo_col = None
        self._init_mongo()

    def _init_mongo(self) -> None:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            return
        try:
            from pymongo import MongoClient  # type: ignore
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db_name = os.getenv("MONGODB_DB", "mitra")
            self._mongo_col = client[db_name][_MEMORY_COLLECTION]
            self._mongo_available = True
            logger.info("CompanionMemory: MongoDB connected (%s)", _MEMORY_COLLECTION)
        except Exception as exc:
            logger.warning("CompanionMemory: MongoDB unavailable (%s), using cache.", exc)

    async def get(self, user_id: str) -> UserMemory:
        """Retrieve full UserMemory for a user."""
        if user_id in self._cache:
            return self._cache[user_id]

        if self._mongo_available and self._mongo_col is not None:
            try:
                import asyncio
                doc = await asyncio.to_thread(self._mongo_col.find_one, {"user_id": user_id})
                if doc:
                    mem = self._deserialize(doc)
                    self._cache[user_id] = mem
                    return mem
            except Exception as exc:
                logger.warning("CompanionMemory.get failed: %s", exc)

        # New user — empty memory
        mem = UserMemory(user_id=user_id)
        self._cache[user_id] = mem
        return mem

    async def set_fact(self, user_id: str, key: str, value: Any, source: str = "user") -> None:
        """Update a single fact for the user."""
        mem = await self.get(user_id)
        mem.set_fact(key, value, source)
        await self._save(mem)

    async def delete_fact(self, user_id: str, key: str) -> None:
        """Remove a stored fact for the user."""
        mem = await self.get(user_id)
        if key in mem.facts:
            del mem.facts[key]
            await self._save(mem)

    async def add_conversation_summary(
        self,
        user_id: str,
        session_id: str,
        summary: str,
        capabilities_used: List[str],
        turn_count: int = 0,
    ) -> None:
        mem = await self.get(user_id)
        entry = ConversationSummary(
            session_id=session_id,
            summary=summary,
            capabilities_used=capabilities_used,
            created_at=datetime.now(timezone.utc).isoformat(),
            turn_count=turn_count,
        )
        mem.conversation_summaries.append(entry)
        # Keep last 50 summaries
        if len(mem.conversation_summaries) > 50:
            mem.conversation_summaries = mem.conversation_summaries[-50:]
        await self._save(mem)

    async def log_capability_use(
        self, user_id: str, capability: str, intent: str, success: bool
    ) -> None:
        mem = await self.get(user_id)
        mem.capability_history.append({
            "capability": capability,
            "intent": intent,
            "success": success,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        if len(mem.capability_history) > 200:
            mem.capability_history = mem.capability_history[-200:]
        await self._save(mem)

    async def get_user_facts(self, user_id: str) -> Dict[str, Any]:
        mem = await self.get(user_id)
        return mem.to_context_dict()

    async def get_recent_summaries(self, user_id: str, limit: int = 5) -> List[str]:
        mem = await self.get(user_id)
        recent = mem.conversation_summaries[-limit:]
        return [s.summary for s in reversed(recent)]

    # ── serialization ──────────────────────────────────────────────

    async def _save(self, mem: UserMemory) -> None:
        self._cache[mem.user_id] = mem
        if not self._mongo_available or self._mongo_col is None:
            return
        try:
            import asyncio
            doc = self._serialize(mem)
            await asyncio.to_thread(
                self._mongo_col.replace_one,
                {"user_id": mem.user_id}, doc, True
            )
        except Exception as exc:
            logger.warning("CompanionMemory._save failed: %s", exc)

    @staticmethod
    def _serialize(mem: UserMemory) -> Dict:
        return {
            "user_id": mem.user_id,
            "facts": {
                k: {"key": v.key, "value": v.value, "source": v.source, "updated_at": v.updated_at}
                for k, v in mem.facts.items()
            },
            "conversation_summaries": [
                {"session_id": s.session_id, "summary": s.summary,
                 "capabilities_used": s.capabilities_used,
                 "created_at": s.created_at, "turn_count": s.turn_count}
                for s in mem.conversation_summaries
            ],
            "capability_history": mem.capability_history,
            "preferences": mem.preferences,
        }

    @staticmethod
    def _deserialize(doc: Dict) -> UserMemory:
        facts = {
            k: UserFact(key=v["key"], value=v["value"], source=v.get("source", "user"),
                        updated_at=v.get("updated_at", ""))
            for k, v in doc.get("facts", {}).items()
        }
        summaries = [
            ConversationSummary(
                session_id=s["session_id"], summary=s["summary"],
                capabilities_used=s.get("capabilities_used", []),
                created_at=s.get("created_at", ""),
                turn_count=s.get("turn_count", 0),
            )
            for s in doc.get("conversation_summaries", [])
        ]
        return UserMemory(
            user_id=doc["user_id"],
            facts=facts,
            conversation_summaries=summaries,
            capability_history=doc.get("capability_history", []),
            preferences=doc.get("preferences", {}),
        )


# Singleton
companion_memory = CompanionMemory()
