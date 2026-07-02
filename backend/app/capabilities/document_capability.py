"""
document_capability.py — Mitra Document Capability
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

_DOCS_COLLECTION = "mitra_documents"

class DocumentCapability(BaseCapability):
    def __init__(self):
        self._col = None
        mongo_uri = os.getenv("MONGODB_URI")
        if mongo_uri:
            try:
                from pymongo import MongoClient
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                self._col = client[os.getenv("MONGODB_DB", "mitra")][_DOCS_COLLECTION]
            except Exception as exc:
                logger.warning("DocumentCapability: MongoDB unavailable: %s", exc)

    @property
    def name(self) -> str: return "document"
    @property
    def description(self) -> str: return "Upload, read, and summarize documents."
    @property
    def supported_intents(self) -> List[str]:
        return ["document", "upload_document", "read_document", "summarize_document", "search_document"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "anonymous")
            message = params.get("message", "")
            if intent in ("list_documents", "document"):
                docs = []
                if self._col is not None:
                    docs = list(self._col.find({"user_id": user_id}).sort("uploaded_at", -1).limit(10))
                    docs = [{"title": d.get("title", "Untitled"), "uploaded_at": d.get("uploaded_at")} for d in docs]
                return CapabilityResult(
                    capability=self.name, intent=intent, status="success",
                    summary=f"{len(docs)} document(s) found.", data={"documents": docs}, trace_id=trace_id,
                )
            return CapabilityResult.error_result(self.name, intent, f"Intent not fully implemented: {intent}", trace_id)
        except Exception as exc:
            logger.warning("DocumentCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
