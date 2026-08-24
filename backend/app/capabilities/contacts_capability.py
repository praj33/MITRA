"""
contacts_capability.py — Mitra Contacts Capability
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

_CONTACTS_COLLECTION = "mitra_contacts"

class ContactsCapability(BaseCapability):
    def __init__(self):
        self._col = None
        mongo_uri = os.getenv("MONGODB_URI")
        if mongo_uri:
            try:
                from pymongo import MongoClient
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                self._col = client[os.getenv("MONGODB_DB", "mitra")][_CONTACTS_COLLECTION]
            except Exception as exc:
                logger.warning("ContactsCapability: MongoDB unavailable: %s", exc)

    @property
    def name(self) -> str: return "contacts"
    @property
    def description(self) -> str: return "Find, add, and manage contacts."
    @property
    def supported_intents(self) -> List[str]:
        return ["contacts", "find_contact", "add_contact", "update_contact", "search_contacts"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            message = params.get("message", "")
            user_id = params.get("user_id", "anonymous")
            if intent in ("find_contact", "search_contacts", "contacts"):
                results = []
                if self._col is not None:
                    results = list(self._col.find({"user_id": user_id, "$text": {"$search": message}}).limit(5))
                    results = [{"name": c.get("name"), "email": c.get("email"), "phone": c.get("phone")} for c in results]
                return CapabilityResult(
                    capability=self.name, intent=intent, status="success",
                    summary=f"{len(results)} contact(s) found.", data={"contacts": results}, trace_id=trace_id,
                )
            return CapabilityResult.error_result(self.name, intent, f"Intent not handled: {intent}", trace_id)
        except Exception as exc:
            logger.warning("ContactsCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
