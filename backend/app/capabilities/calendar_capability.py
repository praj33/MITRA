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


def _get_user_events_from_db(user_id: str) -> List[Dict[str, Any]]:
    """Fetch calendar events for user from MongoDB."""
    try:
        from pymongo import MongoClient
        import os
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]
        docs = list(db["calendar_events"].find({"$or": [{"user_id": user_id}, {"user_id": "user_default"}]}).sort("created_at", -1).limit(20))
        for doc in docs:
            doc["id"] = str(doc.get("_id"))
            doc.pop("_id", None)
        return docs
    except Exception as e:
        logger.warning(f"Failed to fetch calendar events from DB: {e}")
        return []


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
            message = params.get("message", "").strip()
            msg_lower = message.lower()
            dates = params.get("dates", {})
            date_str = dates.get("resolved_date", "")
            time_str = dates.get("time", "")

            # Differentiate READ / CHECK queries from CREATE actions
            read_keywords = (
                "check", "what", "show", "view", "list", "get", "see",
                "do i have", "any event", "my schedule", "my calendar", "upcoming"
            )
            create_keywords = ("create", "add", "schedule", "book", "set")

            is_read_query = any(k in msg_lower for k in read_keywords) and not any(msg_lower.startswith(k) for k in create_keywords)

            if is_read_query or intent in ("list_events", "check_availability"):
                events = _get_user_events_from_db(user_id)
                if events:
                    event_list_str = ", ".join([f"'{e.get('title')}'" for e in events[:5]])
                    summary = f"You have {len(events)} event(s) on your calendar: {event_list_str}."
                else:
                    summary = "Your calendar is clear! You have no upcoming events scheduled."

                return CapabilityResult(
                    capability=self.name,
                    intent="list_events",
                    status="success",
                    summary=summary,
                    data={"events": events, "count": len(events)},
                    trace_id=trace_id,
                    actions=[{"label": "Add to calendar", "action": "Add to calendar"}],
                )

            # Otherwise: CREATE EVENT action
            title = message
            for prefix in ("create a calendar event", "create calendar event", "create event",
                          "add event", "schedule a meeting", "schedule meeting", "schedule", "add to calendar", "calendar event"):
                if msg_lower.startswith(prefix):
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
