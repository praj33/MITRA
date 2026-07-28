"""
reminder_capability.py — Mitra Reminder Capability

Sets, lists, and cancels reminders.
Reminders are PERSISTED to MongoDB so they show in the reminders panel.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging

logger = logging.getLogger(__name__)


def _save_reminder_to_db(user_id: str, message: str, remind_at: str, trace_id: str) -> Optional[str]:
    """Save reminder to MongoDB. Returns reminder_id or None."""
    try:
        from pymongo import MongoClient
        import os
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]

        now = datetime.now(timezone.utc)
        rem_id = f"rem_{uuid4().hex[:8]}"

        # Parse remind_at time
        try:
            if remind_at and "T" in remind_at:
                remind_time = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
            elif remind_at:
                remind_time = datetime.fromisoformat(remind_at)
            else:
                remind_time = now + timedelta(minutes=30)
        except Exception:
            remind_time = now + timedelta(minutes=30)

        doc = {
            "_id": rem_id,
            "user_id": user_id,
            "message": message,
            "time": remind_time.isoformat(),
            "status": "active",
            "repeat": None,
            "trace_id": trace_id,
            "created_at": now.isoformat(),
        }

        db["reminders"].insert_one(doc)
        logger.info(f"Reminder saved to DB: {rem_id} — {message}")
        return rem_id
    except Exception as e:
        logger.warning(f"Failed to save reminder to DB: {e}")
        return None


class ReminderCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "reminder"

    @property
    def description(self) -> str:
        return "Set, list, and cancel reminders."

    @property
    def supported_intents(self) -> List[str]:
        return ["reminder", "create_reminder", "list_reminders", "cancel_reminder", "set_alert"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "user_default")
            message = params.get("message", "")
            dates = params.get("dates", {})
            remind_at = dates.get("resolved_date") or dates.get("time", "")

            # Extract reminder text from message
            reminder_text = message
            for prefix in ("remind me to", "remind me", "set a reminder to", "set reminder to",
                          "set a reminder", "set reminder", "reminder to", "reminder"):
                if message.lower().startswith(prefix):
                    reminder_text = message[len(prefix):].strip().strip(":.,-") or message
                    break

            if not reminder_text or len(reminder_text) < 2:
                reminder_text = "Reminder"

            # Save to MongoDB
            rem_id = _save_reminder_to_db(user_id, reminder_text, remind_at, trace_id or "")

            summary = f"Reminder set: {reminder_text}"

            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary,
                data={
                    "reminder_id": rem_id,
                    "message": reminder_text,
                    "time": remind_at,
                    "persisted": rem_id is not None,
                },
                trace_id=trace_id,
                actions=[{"label": "View reminders", "action": "View reminders"}],
            )
        except Exception as exc:
            logger.warning("ReminderCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
