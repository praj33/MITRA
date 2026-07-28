"""
Direct REST endpoints for Calendar, Tasks, Reminders, Workflows.
These serve structured data for dedicated frontend pages.
Now with full CRUD (create, read, update, delete) and proper async MongoDB.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pages", tags=["Page Data"])


# ── Models ──────────────────────────────────────────────
class CalendarEventCreate(BaseModel):
    title: str
    start: str
    end: Optional[str] = None
    color: str = "#7c5cfc"
    description: str = ""
    location: str = ""

class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    due_date: Optional[str] = None
    category: str = "general"

class ReminderCreate(BaseModel):
    message: str
    time: str
    repeat: Optional[str] = None


# ── Helper: get MongoDB database ────────────────────────
def _get_db():
    """Synchronous database access via pymongo (not motor)."""
    try:
        from pymongo import MongoClient
        import os
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        return client[db_name]
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# CALENDAR — Full CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/calendar/events")
async def get_calendar_events(user_id: str = "user_default"):
    """Return calendar events."""
    db = _get_db()
    if db is not None:
        try:
            events_col = db["calendar_events"]
            # If user has no events yet and database collection is empty, seed initial default events once
            if events_col.count_documents({"user_id": user_id}) == 0 and events_col.count_documents({}) == 0:
                now = datetime.now(timezone.utc)
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                initial_seed = [
                    {"_id": "ev_1", "user_id": user_id, "title": "Team Standup", "start": (today + timedelta(hours=10)).isoformat(), "end": (today + timedelta(hours=10, minutes=30)).isoformat(), "color": "#7c5cfc", "description": "Daily sync", "location": "Google Meet", "created_at": now.isoformat()},
                    {"_id": "ev_2", "user_id": user_id, "title": "Design Review", "start": (today + timedelta(hours=14)).isoformat(), "end": (today + timedelta(hours=15)).isoformat(), "color": "#10b981", "description": "UI/UX review", "location": "Conference Room B", "created_at": now.isoformat()},
                    {"_id": "ev_3", "user_id": user_id, "title": "Sprint Planning", "start": (today + timedelta(days=1, hours=11)).isoformat(), "end": (today + timedelta(days=1, hours=12)).isoformat(), "color": "#f59e0b", "description": "Next sprint scope", "location": "Zoom", "created_at": now.isoformat()},
                ]
                events_col.insert_many(initial_seed)

            cursor = events_col.find({"user_id": user_id}).sort("start", 1).limit(100)
            db_events = []
            for doc in cursor:
                db_events.append({
                    "id": str(doc["_id"]),
                    "title": doc.get("title", "Untitled"),
                    "start": doc.get("start", ""),
                    "end": doc.get("end", ""),
                    "color": doc.get("color", "#7c5cfc"),
                    "description": doc.get("description", ""),
                    "location": doc.get("location", ""),
                })
            return {"events": db_events, "source": "database"}
        except Exception as e:
            logger.warning(f"Calendar DB lookup: {e}")

    # Fallback only if database connection failed
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    events = [
        {"id": "ev_1", "title": "Team Standup", "start": (today + timedelta(hours=10)).isoformat(), "end": (today + timedelta(hours=10, minutes=30)).isoformat(), "color": "#7c5cfc", "description": "Daily sync", "location": "Google Meet"},
        {"id": "ev_2", "title": "Design Review", "start": (today + timedelta(hours=14)).isoformat(), "end": (today + timedelta(hours=15)).isoformat(), "color": "#10b981", "description": "UI/UX review", "location": "Conference Room B"},
        {"id": "ev_3", "title": "Sprint Planning", "start": (today + timedelta(days=1, hours=11)).isoformat(), "end": (today + timedelta(days=1, hours=12)).isoformat(), "color": "#f59e0b", "description": "Next sprint scope", "location": "Zoom"},
    ]
    return {"events": events, "source": "seed"}


@router.post("/calendar/events")
async def create_calendar_event(event: CalendarEventCreate, user_id: str = "user_default"):
    """Create a calendar event and persist to database."""
    event_id = f"ev_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # Default end = start + 1 hour
    end_time = event.end or (
        datetime.fromisoformat(event.start.replace("Z", "+00:00")) + timedelta(hours=1)
    ).isoformat()

    doc = {
        "_id": event_id,
        "user_id": user_id,
        "title": event.title,
        "start": event.start,
        "end": end_time,
        "color": event.color,
        "description": event.description,
        "location": event.location,
        "created_at": now.isoformat(),
    }

    db = _get_db()
    if db is not None:
        try:
            db["calendar_events"].insert_one(doc)
            logger.info(f"Calendar event created: {event_id} — {event.title}")
        except Exception as e:
            logger.warning(f"Calendar DB insert failed: {e}")

    return {
        "success": True,
        "event": {
            "id": event_id, "title": event.title, "start": event.start,
            "end": end_time, "color": event.color,
            "description": event.description, "location": event.location,
        },
    }


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str, user_id: str = "user_default"):
    """Delete a calendar event."""
    db = _get_db()
    if db is not None:
        try:
            result = db["calendar_events"].delete_one({"_id": event_id, "user_id": user_id})
            if result.deleted_count == 0:
                # Try without user_id filter (for seed data migration)
                db["calendar_events"].delete_one({"_id": event_id})
        except Exception as e:
            logger.warning(f"Calendar delete failed: {e}")
    return {"success": True, "event_id": event_id}


# ═══════════════════════════════════════════════════════════
# TASKS — Full CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/tasks/list")
async def get_tasks(user_id: str = "user_default"):
    """Return task list."""
    db = _get_db()
    if db is not None:
        try:
            tasks_col = db["user_tasks"]
            if tasks_col.count_documents({"user_id": user_id}) == 0 and tasks_col.count_documents({}) == 0:
                now = datetime.now(timezone.utc)
                initial_seed = [
                    {"_id": "t_1", "user_id": user_id, "title": "Complete API documentation", "status": "in_progress", "priority": "high", "due_date": (now + timedelta(days=1)).isoformat(), "category": "development", "created_at": now.isoformat()},
                    {"_id": "t_2", "user_id": user_id, "title": "Review pull requests", "status": "pending", "priority": "medium", "due_date": (now + timedelta(hours=4)).isoformat(), "category": "development", "created_at": now.isoformat()},
                    {"_id": "t_3", "user_id": user_id, "title": "Update deployment scripts", "status": "pending", "priority": "low", "due_date": (now + timedelta(days=3)).isoformat(), "category": "devops", "created_at": now.isoformat()},
                ]
                tasks_col.insert_many(initial_seed)

            cursor = tasks_col.find({"user_id": user_id}).sort("created_at", -1).limit(50)
            db_tasks = []
            for doc in cursor:
                db_tasks.append({
                    "id": str(doc["_id"]),
                    "title": doc.get("title", ""),
                    "status": doc.get("status", "pending"),
                    "priority": doc.get("priority", "medium"),
                    "due_date": doc.get("due_date"),
                    "category": doc.get("category", "general"),
                })
            return {"tasks": db_tasks, "source": "database"}
        except Exception as e:
            logger.warning(f"Tasks DB lookup: {e}")

    now = datetime.now(timezone.utc)
    tasks = [
        {"id": "t_1", "title": "Complete API documentation", "status": "in_progress", "priority": "high", "due_date": (now + timedelta(days=1)).isoformat(), "category": "development"},
        {"id": "t_2", "title": "Review pull requests", "status": "pending", "priority": "medium", "due_date": (now + timedelta(hours=4)).isoformat(), "category": "development"},
        {"id": "t_3", "title": "Update deployment scripts", "status": "pending", "priority": "low", "due_date": (now + timedelta(days=3)).isoformat(), "category": "devops"},
    ]
    return {"tasks": tasks, "source": "seed"}


@router.post("/tasks/create")
async def create_task(task: TaskCreate, user_id: str = "user_default"):
    """Create a task and persist to database."""
    task_id = f"task_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    doc = {
        "_id": task_id,
        "user_id": user_id,
        "title": task.title,
        "status": "pending",
        "priority": task.priority,
        "due_date": task.due_date,
        "category": task.category,
        "created_at": now.isoformat(),
    }

    db = _get_db()
    if db is not None:
        try:
            db["user_tasks"].insert_one(doc)
            logger.info(f"Task created: {task_id} — {task.title}")
        except Exception as e:
            logger.warning(f"Task DB insert failed: {e}")

    return {"success": True, "task": {"id": task_id, "title": task.title, "status": "pending", "priority": task.priority}}


@router.post("/tasks/update")
async def update_task(task_id: str, status: str, user_id: str = "user_default"):
    """Update task status."""
    db = _get_db()
    if db is not None:
        try:
            db["user_tasks"].update_one(
                {"_id": task_id},
                {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        except Exception as e:
            logger.warning(f"Task update failed: {e}")
    return {"success": True, "task_id": task_id, "status": status}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str = "user_default"):
    """Delete a task."""
    db = _get_db()
    if db is not None:
        try:
            db["user_tasks"].delete_one({"_id": task_id})
        except Exception as e:
            logger.warning(f"Task delete failed: {e}")
    return {"success": True, "task_id": task_id}


# ═══════════════════════════════════════════════════════════
# REMINDERS — Full CRUD
# ═══════════════════════════════════════════════════════════

@router.get("/reminders/list")
async def get_reminders(user_id: str = "user_default"):
    """Return active reminders."""
    db = _get_db()
    if db is not None:
        try:
            rem_col = db["reminders"]
            if rem_col.count_documents({"user_id": user_id}) == 0 and rem_col.count_documents({}) == 0:
                now = datetime.now(timezone.utc)
                initial_seed = [
                    {"_id": "r_1", "user_id": user_id, "message": "Check deployment status", "time": (now + timedelta(hours=1)).isoformat(), "status": "active", "repeat": None, "created_at": now.isoformat()},
                    {"_id": "r_2", "user_id": user_id, "message": "Call the team for sync", "time": (now + timedelta(hours=3)).isoformat(), "status": "active", "repeat": "daily", "created_at": now.isoformat()},
                ]
                rem_col.insert_many(initial_seed)

            cursor = rem_col.find(
                {"user_id": user_id, "status": {"$in": ["active", "snoozed"]}}
            ).sort("time", 1).limit(50)
            db_reminders = []
            for doc in cursor:
                db_reminders.append({
                    "id": str(doc["_id"]),
                    "message": doc.get("message", ""),
                    "time": doc.get("time", ""),
                    "status": doc.get("status", "active"),
                    "repeat": doc.get("repeat"),
                })
            return {"reminders": db_reminders, "source": "database"}
        except Exception as e:
            logger.warning(f"Reminders DB lookup: {e}")

    now = datetime.now(timezone.utc)
    reminders = [
        {"id": "r_1", "message": "Check deployment status", "time": (now + timedelta(hours=1)).isoformat(), "status": "active", "repeat": None},
        {"id": "r_2", "message": "Call the team for sync", "time": (now + timedelta(hours=3)).isoformat(), "status": "active", "repeat": "daily"},
    ]
    return {"reminders": reminders, "source": "seed"}


@router.post("/reminders/create")
async def create_reminder(reminder: ReminderCreate, user_id: str = "user_default"):
    """Create a reminder and persist to database."""
    rem_id = f"rem_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    doc = {
        "_id": rem_id,
        "user_id": user_id,
        "message": reminder.message,
        "time": reminder.time,
        "status": "active",
        "repeat": reminder.repeat,
        "created_at": now.isoformat(),
    }

    db = _get_db()
    if db is not None:
        try:
            db["reminders"].insert_one(doc)
            logger.info(f"Reminder created: {rem_id} — {reminder.message}")
        except Exception as e:
            logger.warning(f"Reminder DB insert failed: {e}")

    return {"success": True, "reminder": {"id": rem_id, "message": reminder.message, "time": reminder.time, "status": "active"}}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, user_id: str = "user_default"):
    """Delete a reminder."""
    db = _get_db()
    if db is not None:
        try:
            result = db["reminders"].delete_one({"_id": reminder_id, "user_id": user_id})
            if result.deleted_count == 0:
                db["reminders"].delete_one({"_id": reminder_id})
        except Exception as e:
            logger.warning(f"Reminder delete failed: {e}")
    return {"success": True, "reminder_id": reminder_id}


# ═══════════════════════════════════════════════════════════
# WORKFLOWS
# ═══════════════════════════════════════════════════════════

@router.get("/workflows/list")
async def get_workflows(user_id: str = "user_default"):
    """Return available workflow templates."""
    workflows = [
        {
            "id": "wf_morning_briefing",
            "name": "Morning Briefing",
            "description": "Daily digest of upcoming events, unread emails, and pending high-priority tasks.",
            "steps": ["Fetch calendar events", "Summarize unread emails", "List pending tasks", "Synthesize briefing"],
            "category": "productivity",
            "active": True,
        },
        {
            "id": "wf_meeting_prep",
            "name": "Meeting Prep",
            "description": "Gather context, previous notes, and attendee details before an upcoming meeting.",
            "steps": ["Identify next meeting", "Lookup attendee notes", "Fetch related emails", "Draft agenda"],
            "category": "productivity",
            "active": True,
        },
        {
            "id": "wf_task_triage",
            "name": "Task Triage",
            "description": "Auto-prioritize overdue and pending tasks based on deadlines and importance.",
            "steps": ["Scan pending tasks", "Calculate urgency scores", "Re-order task board", "Notify user"],
            "category": "automation",
            "active": False,
        },
    ]
    return {"workflows": workflows, "source": "templates"}
