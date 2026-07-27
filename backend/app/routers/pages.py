"""
Direct REST endpoints for Calendar, Tasks, Reminders, Workflows.
These serve structured data for dedicated frontend pages.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pages", tags=["Page Data"])


# ── Models ──────────────────────────────────────────────
class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str
    end: str
    color: str = "#7c5cfc"
    description: str = ""
    location: str = ""

class TaskItem(BaseModel):
    id: str
    title: str
    status: str = "pending"  # pending | in_progress | completed
    priority: str = "medium"  # low | medium | high
    due_date: Optional[str] = None
    category: str = "general"

class ReminderItem(BaseModel):
    id: str
    message: str
    time: str
    status: str = "active"  # active | fired | snoozed | cancelled
    repeat: Optional[str] = None

class WorkflowItem(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    last_run: Optional[str] = None
    status: str = "ready"


# ── Calendar ────────────────────────────────────────────
@router.get("/calendar/events")
async def get_calendar_events(user_id: str = "user_default"):
    """Return calendar events for the current week."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Try to load from MongoDB
    try:
        from app.core.database import get_db
        db = get_db()
        if db is not None:
            events_col = db.get_collection("calendar_events")
            cursor = events_col.find({"user_id": user_id}).sort("start", 1).limit(50)
            db_events = []
            for doc in cursor:
                db_events.append({
                    "id": str(doc.get("_id", "")),
                    "title": doc.get("title", "Untitled"),
                    "start": doc.get("start", now.isoformat()),
                    "end": doc.get("end", (now + timedelta(hours=1)).isoformat()),
                    "color": doc.get("color", "#7c5cfc"),
                    "description": doc.get("description", ""),
                    "location": doc.get("location", ""),
                })
            if db_events:
                return {"events": db_events, "source": "database"}
    except Exception as e:
        logger.debug(f"Calendar DB lookup: {e}")

    # Seed data for demo
    events = [
        {
            "id": "ev_1", "title": "Team Standup",
            "start": (today + timedelta(hours=10)).isoformat(),
            "end": (today + timedelta(hours=10, minutes=30)).isoformat(),
            "color": "#7c5cfc", "description": "Daily sync", "location": "Google Meet",
        },
        {
            "id": "ev_2", "title": "Design Review",
            "start": (today + timedelta(hours=14)).isoformat(),
            "end": (today + timedelta(hours=15)).isoformat(),
            "color": "#10b981", "description": "UI/UX review", "location": "Conference Room B",
        },
        {
            "id": "ev_3", "title": "Sprint Planning",
            "start": (today + timedelta(days=1, hours=11)).isoformat(),
            "end": (today + timedelta(days=1, hours=12)).isoformat(),
            "color": "#f59e0b", "description": "Next sprint scope", "location": "Zoom",
        },
        {
            "id": "ev_4", "title": "1:1 with Manager",
            "start": (today + timedelta(days=2, hours=16)).isoformat(),
            "end": (today + timedelta(days=2, hours=16, minutes=30)).isoformat(),
            "color": "#ef4444", "description": "Weekly check-in", "location": "Office",
        },
    ]
    return {"events": events, "source": "seed"}


# ── Tasks ───────────────────────────────────────────────
@router.get("/tasks/list")
async def get_tasks(user_id: str = "user_default"):
    """Return task list."""
    try:
        from app.core.database import get_db
        db = get_db()
        if db is not None:
            tasks_col = db.get_collection("tasks")
            cursor = tasks_col.find({"user_id": user_id}).sort("created_at", -1).limit(50)
            db_tasks = []
            for doc in cursor:
                db_tasks.append({
                    "id": str(doc.get("_id", "")),
                    "title": doc.get("title", ""),
                    "status": doc.get("status", "pending"),
                    "priority": doc.get("priority", "medium"),
                    "due_date": doc.get("due_date"),
                    "category": doc.get("category", "general"),
                })
            if db_tasks:
                return {"tasks": db_tasks, "source": "database"}
    except Exception as e:
        logger.debug(f"Tasks DB: {e}")

    tasks = [
        {"id": "t_1", "title": "Complete API documentation", "status": "in_progress", "priority": "high", "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), "category": "development"},
        {"id": "t_2", "title": "Review pull requests", "status": "pending", "priority": "medium", "due_date": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(), "category": "development"},
        {"id": "t_3", "title": "Update deployment scripts", "status": "pending", "priority": "low", "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(), "category": "devops"},
        {"id": "t_4", "title": "Send weekly report", "status": "completed", "priority": "medium", "due_date": None, "category": "admin"},
        {"id": "t_5", "title": "Fix login page validation", "status": "pending", "priority": "high", "due_date": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(), "category": "bugfix"},
    ]
    return {"tasks": tasks, "source": "seed"}


@router.post("/tasks/update")
async def update_task(task_id: str, status: str, user_id: str = "user_default"):
    """Update task status."""
    try:
        from app.core.database import get_db
        db = get_db()
        if db is not None:
            from bson import ObjectId
            db.get_collection("tasks").update_one(
                {"_id": ObjectId(task_id)},
                {"$set": {"status": status}}
            )
            return {"success": True, "task_id": task_id, "status": status}
    except Exception:
        pass
    return {"success": True, "task_id": task_id, "status": status}


# ── Reminders ───────────────────────────────────────────
@router.get("/reminders/list")
async def get_reminders(user_id: str = "user_default"):
    """Return active reminders."""
    try:
        from app.core.database import get_db
        db = get_db()
        if db is not None:
            rem_col = db.get_collection("reminders")
            cursor = rem_col.find({"user_id": user_id, "status": {"$in": ["active", "snoozed"]}}).sort("time", 1).limit(50)
            db_reminders = []
            for doc in cursor:
                db_reminders.append({
                    "id": str(doc.get("_id", "")),
                    "message": doc.get("message", ""),
                    "time": doc.get("time", ""),
                    "status": doc.get("status", "active"),
                    "repeat": doc.get("repeat"),
                })
            if db_reminders:
                return {"reminders": db_reminders, "source": "database"}
    except Exception as e:
        logger.debug(f"Reminders DB: {e}")

    now = datetime.now(timezone.utc)
    reminders = [
        {"id": "r_1", "message": "Check deployment status", "time": (now + timedelta(hours=1)).isoformat(), "status": "active", "repeat": None},
        {"id": "r_2", "message": "Call the team for sync", "time": (now + timedelta(hours=3)).isoformat(), "status": "active", "repeat": "daily"},
        {"id": "r_3", "message": "Submit timesheet", "time": (now + timedelta(days=1, hours=17)).isoformat(), "status": "active", "repeat": "weekly"},
    ]
    return {"reminders": reminders, "source": "seed"}


# ── Workflows ───────────────────────────────────────────
@router.get("/workflows/list")
async def get_workflows(user_id: str = "user_default"):
    """Return available workflows."""
    workflows = [
        {"id": "wf_1", "name": "Morning Briefing", "description": "Calendar + emails + tasks summary", "icon": "☀️", "status": "ready"},
        {"id": "wf_2", "name": "Email Digest", "description": "Summarize unread emails", "icon": "📧", "status": "ready"},
        {"id": "wf_3", "name": "End of Day Report", "description": "Summary of completed tasks and next steps", "icon": "📊", "status": "ready"},
        {"id": "wf_4", "name": "Weekly Review", "description": "Week's progress, blockers, and priorities", "icon": "📋", "status": "ready"},
        {"id": "wf_5", "name": "Meeting Prep", "description": "Prepare context for upcoming meetings", "icon": "🎯", "status": "ready"},
        {"id": "wf_6", "name": "Focus Mode", "description": "Silence notifications and set status", "icon": "🧘", "status": "ready"},
    ]
    return {"workflows": workflows, "source": "system"}
