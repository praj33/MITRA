"""
notes_capability.py — Mitra Notes Capability
Stores notes in MongoDB via BucketService.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

_NOTES_COLLECTION = "mitra_notes"

class NotesCapability(BaseCapability):
    def __init__(self):
        self._col = None
        self._init_mongo()

    def _init_mongo(self):
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            return
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db = client[os.getenv("MONGODB_DB", "mitra")]
            self._col = db[_NOTES_COLLECTION]
        except Exception as exc:
            logger.warning("NotesCapability: MongoDB unavailable: %s", exc)

    @property
    def name(self) -> str:
        return "notes"

    @property
    def description(self) -> str:
        return "Create, retrieve, and search notes."

    @property
    def supported_intents(self) -> List[str]:
        return ["notes", "create_note", "read_note", "search_notes", "list_notes"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "anonymous")
            message = params.get("message", "")
            if intent in ("create_note", "notes"):
                note = {
                    "user_id": user_id,
                    "content": message,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "trace_id": trace_id,
                }
                if self._col is not None:
                    self._col.insert_one(note)
                return CapabilityResult(
                    capability=self.name, intent=intent, status="success",
                    summary="Note saved.", data={"content": message}, trace_id=trace_id,
                )
            elif intent in ("list_notes", "read_note"):
                notes = []
                if self._col is not None:
                    notes = list(self._col.find({"user_id": user_id}).sort("created_at", -1).limit(10))
                    notes = [{"content": n["content"], "created_at": n["created_at"]} for n in notes]
                return CapabilityResult(
                    capability=self.name, intent=intent, status="success",
                    summary=f"{len(notes)} notes found.", data={"notes": notes}, trace_id=trace_id,
                )
            return CapabilityResult.error_result(self.name, intent, f"Unknown intent: {intent}", trace_id)
        except Exception as exc:
            logger.warning("NotesCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
