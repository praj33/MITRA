"""
backend/app/services/webhook_dedup_service.py — Webhook Event Deduplication Service

Prevents replay attacks, duplicate deliveries, and at-least-once provider retries
from causing redundant assistant executions.

SECURITY INVARIANTS:
1. SCOPED IDENTITY: Deduplication key is strictly scoped by provider and event ID
   (e.g., whatsapp:wamid.HBg... or email:msg_12345).
2. NEVER SENDER ID ALONE: sender_id must never be used as a deduplication key.
3. ATOMIC REGISTRATION: Database insertion uses unique indexing to ensure race-free
   idempotency under concurrent webhook deliveries.
"""
from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from typing import Dict, Set
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

_IN_MEMORY_DEDUP: Set[str] = set()
_LOCK = threading.Lock()


def _get_db():
    try:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        return client[db_name]
    except Exception as exc:
        logger.debug("MongoDB connection unavailable in WebhookDedupService: %s", exc)
        return None


class WebhookDedupService:
    """
    Manages atomic deduplication of incoming webhook events across providers.
    """

    def __init__(self):
        self.collection_name = "webhook_event_dedup"
        self._ensure_indexes()

    def _ensure_indexes(self):
        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].create_index("dedup_key", unique=True)
                # TTL index to clean up deduplication records after 72 hours
                db[self.collection_name].create_index("created_at", expireAfterSeconds=259200)
            except Exception as exc:
                logger.debug("Error creating indexes for webhook_event_dedup: %s", exc)

    def check_and_record(self, provider: str, event_id: str) -> bool:
        """
        Check if an event has already been processed.
        Returns:
            True: Event is NEW and has been recorded.
            False: Event is a DUPLICATE (already processed).
        """
        if not provider or not event_id:
            logger.warning("WebhookDedupService called with empty provider or event_id.")
            return False

        clean_provider = provider.strip().lower()
        clean_event_id = event_id.strip()
        dedup_key = f"{clean_provider}:{clean_event_id}"
        now_iso = datetime.utcnow().isoformat()

        # 1. Check in-memory registry under lock
        with _LOCK:
            if dedup_key in _IN_MEMORY_DEDUP:
                logger.warning("Duplicate webhook detected in-memory: %s", dedup_key)
                return False

        # 2. Check MongoDB collection
        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].insert_one({
                    "dedup_key": dedup_key,
                    "provider": clean_provider,
                    "event_id": clean_event_id,
                    "created_at": datetime.utcnow(),
                    "created_at_iso": now_iso,
                    "status": "received",
                })
                # Successfully inserted into MongoDB; also track in-memory
                with _LOCK:
                    _IN_MEMORY_DEDUP.add(dedup_key)
                return True
            except DuplicateKeyError:
                logger.warning("Duplicate webhook detected in MongoDB: %s", dedup_key)
                with _LOCK:
                    _IN_MEMORY_DEDUP.add(dedup_key)
                return False
            except Exception as exc:
                logger.error("MongoDB error in WebhookDedupService: %s", exc)
                # Fall back to in-memory check
                with _LOCK:
                    if dedup_key in _IN_MEMORY_DEDUP:
                        return False
                    _IN_MEMORY_DEDUP.add(dedup_key)
                    return True
        else:
            with _LOCK:
                _IN_MEMORY_DEDUP.add(dedup_key)
            return True

    def clear_for_testing(self) -> None:
        """Clear deduplication records for tests."""
        with _LOCK:
            _IN_MEMORY_DEDUP.clear()
        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].delete_many({})
            except Exception:
                pass


# Global singleton instance
webhook_dedup_service = WebhookDedupService()
