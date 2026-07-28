"""
calendar_capability.py — Mitra Calendar Capability

Creates, views, and manages calendar events.
Events are PERSISTED to MongoDB so they show in the calendar panel.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging

logger = logging.getLogger(__name__)


def _save_event_to_db(user_id: str, title: str, date_str: str, time_str: str, trace_id: str) -> Optional[str]:
    """Save calendar event to MongoDB. Returns event_id or None."""
    try:
        from pymongo import MongoClient
        import os
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]

        now = datetime.now(timezone.utc)
        event_id = f"ev_{uuid4().hex[:8]}"

        # Parse date/time
        try:
            if date_str and "T" in date_str:
                start = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif date_str:
                start = datetime.fromisoformat(date_str)
            else:
                start = now + timedelta(hours=1)
        except Exception:
            start = now + timedelta(hours=1)

        end = start + timedelta(hours=1)

        doc = {
            "_id": event_id,
            "user_id": user_id,
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "color": "#7c5cfc",
            "description": f"Created via Mitra companion",
            "location": "",
            "trace_id": trace_id,
            "created_at": now.isoformat(),
        }

        db["calendar_events"].insert_one(doc)
        logger.info(f"Calendar event saved to DB: {event_id} — {title}")
        return event_id
    except Exception as e:
        logger.warning(f"Failed to save calendar event to DB: {e}")
        return None


class CalendarCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return "Create, view, and manage calendar events and meetings."

    @property
    def supported_intents(self) -> List[str]:
        return ["calendar", "create_event", "update_event", "list_events", "check_availability", "schedule_meeting"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "user_default")
            message = params.get("message", "")
            dates = params.get("dates", {})
            date_str = dates.get("resolved_date", "")
            time_str = dates.get("time", "")

            # Extract title from message
            title = message
            for prefix in ("create a calendar event", "create calendar event", "create event",
                          "add event", "schedule", "add to calendar", "calendar event"):
                if message.lower().startswith(prefix):
                    title = message[len(prefix):].strip().strip(":.,-") or message
                    break

            if not title or len(title) < 2:
                title = "New Event"

            # Save to MongoDB
            event_id = _save_event_to_db(user_id, title, date_str, time_str, trace_id or "")

            summary = f"Calendar event created: {title}"
            if date_str:
                summary += f" on {date_str}"

            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary,
                data={
                    "event_id": event_id,
                    "title": title,
                    "date": date_str,
                    "time": time_str,
                    "persisted": event_id is not None,
                },
                trace_id=trace_id,
                actions=[
                    {"label": "Add to calendar", "action": "Add to calendar"},
                    {"label": "Set a reminder", "action": "Set a reminder"},
                ],
            )
        except Exception as exc:
            logger.warning("CalendarCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
