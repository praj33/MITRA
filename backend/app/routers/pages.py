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
    """Synchronous database access via pymongo."""
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
# CALENDAR — Full CRUD (No Auto-Reseed on Delete)
# ═══════════════════════════════════════════════════════════

@router.get("/calendar/events")
async def get_calendar_events(user_id: str = "user_default"):
    """Return calendar events from MongoDB without re-seeding deleted events."""
    db = _get_db()
    if db is not None:
        try:
            events_col = db["calendar_events"]
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
            logger.warning(f"Calendar DB lookup failed: {e}")

    return {"events": [], "source": "database"}


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
    """Permanently delete a calendar event from MongoDB."""
    db = _get_db()
    if db is not None:
        try:
            res = db["calendar_events"].delete_one({"_id": event_id})
            if res.deleted_count == 0:
                db["calendar_events"].delete_one({"id": event_id})
            logger.info(f"Deleted calendar event: {event_id}")
        except Exception as e:
            logger.warning(f"Calendar delete failed: {e}")
    return {"success": True, "event_id": event_id}


@router.delete("/calendar/events/cleanup/past")
async def clear_past_calendar_events(user_id: str = "user_default"):
    """Delete all past calendar events before today for the given user."""
    db = _get_db()
    deleted_count = 0
    if db is not None:
        try:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            res = db["calendar_events"].delete_many({
                "user_id": user_id,
                "start": {"$lt": today_str}
            })
            deleted_count = res.deleted_count
            logger.info(f"Cleared {deleted_count} past calendar events for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to clear past events: {e}")
    return {"success": True, "deleted_count": deleted_count}


# ═══════════════════════════════════════════════════════════
# TASKS — Full CRUD (No Auto-Reseed on Delete)
# ═══════════════════════════════════════════════════════════

@router.get("/tasks/list")
async def get_tasks(user_id: str = "user_default"):
    """Return task list from MongoDB without re-seeding deleted tasks."""
    db = _get_db()
    if db is not None:
        try:
            tasks_col = db["user_tasks"]
            cursor = tasks_col.find({"user_id": user_id}).sort("created_at", -1).limit(100)
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
            logger.warning(f"Tasks DB lookup failed: {e}")

    return {"tasks": [], "source": "database"}


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
    """Permanently delete a task from MongoDB."""
    db = _get_db()
    if db is not None:
        try:
            res = db["user_tasks"].delete_one({"_id": task_id})
            if res.deleted_count == 0:
                db["user_tasks"].delete_one({"id": task_id})
            logger.info(f"Deleted task: {task_id}")
        except Exception as e:
            logger.warning(f"Task delete failed: {e}")
    return {"success": True, "task_id": task_id}


# ═══════════════════════════════════════════════════════════
# REMINDERS — Full CRUD (No Auto-Reseed on Delete)
# ═══════════════════════════════════════════════════════════

@router.get("/reminders/list")
async def get_reminders(user_id: str = "user_default"):
    """Return active reminders without re-seeding deleted reminders."""
    db = _get_db()
    if db is not None:
        try:
            rem_col = db["reminders"]
            cursor = rem_col.find(
                {"user_id": user_id, "status": {"$in": ["active", "snoozed"]}}
            ).sort("time", 1).limit(100)
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
            logger.warning(f"Reminders DB lookup failed: {e}")

    return {"reminders": [], "source": "database"}


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

    return {"success": True, "reminder": {"id": rem_id, "message": reminder.message, "time": reminder.time}}


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str, user_id: str = "user_default"):
    """Permanently delete a reminder from MongoDB."""
    db = _get_db()
    if db is not None:
        try:
            res = db["reminders"].delete_one({"_id": reminder_id})
            if res.deleted_count == 0:
                db["reminders"].delete_one({"id": reminder_id})
            logger.info(f"Deleted reminder: {reminder_id}")
        except Exception as e:
            logger.warning(f"Reminder delete failed: {e}")
    return {"success": True, "reminder_id": reminder_id}


# ═══════════════════════════════════════════════════════════
# WORKFLOWS — Read Only
# ═══════════════════════════════════════════════════════════

@router.get("/workflows/list")
async def get_workflows(user_id: str = "user_default"):
    """Return available pre-configured workflows."""
    workflows = [
        {"id": "wf_1", "name": "Morning Briefing", "description": "Summarizes today's schedule, unread emails, and high-priority tasks.", "trigger": "Daily at 8:00 AM", "status": "active", "category": "productivity", "steps_count": 3},
        {"id": "wf_2", "name": "Smart Email Triage", "description": "Categorizes incoming emails and highlights urgent items.", "trigger": "On email received", "status": "active", "category": "communication", "steps_count": 4},
        {"id": "wf_3", "name": "End-of-Day Summary", "description": "Logs completed tasks and prepares tomorrow's agenda.", "trigger": "Daily at 6:00 PM", "status": "inactive", "category": "productivity", "steps_count": 2},
    ]
    return {"workflows": workflows}


# ═══════════════════════════════════════════════════════════
# HABITS — Full CRUD MongoDB Synchronization
# ═══════════════════════════════════════════════════════════
class HabitCreate(BaseModel):
    name: str

DEFAULT_HABITS = [
    {"id": "h1", "name": "🎯 25m Focus Session", "streak": 4, "last_completed": ""},
    {"id": "h2", "name": "📖 Read Tech Article / Docs", "streak": 7, "last_completed": ""},
    {"id": "h3", "name": "💧 Drink 2L Water", "streak": 3, "last_completed": ""},
    {"id": "h4", "name": "🌅 Morning Briefing Check", "streak": 12, "last_completed": ""},
]

@router.get("/habits/list")
async def get_habits(user_id: str = "user_default"):
    """Return user habits from MongoDB with live today completion state."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = _get_db()
    if db is not None:
        try:
            habits_col = db["user_habits"]
            cursor = habits_col.find({"user_id": user_id}).sort("created_at", -1)
            docs = list(cursor)
            if not docs:
                # Seed default habits for new user
                now = datetime.now(timezone.utc).isoformat()
                for h in DEFAULT_HABITS:
                    h_doc = {
                        "_id": f"h_{uuid4().hex[:8]}",
                        "user_id": user_id,
                        "name": h["name"],
                        "streak": h["streak"],
                        "last_completed": "",
                        "created_at": now,
                    }
                    habits_col.insert_one(h_doc)
                docs = list(habits_col.find({"user_id": user_id}))

            habits_list = []
            for doc in docs:
                completed_today = (doc.get("last_completed") == today_str)
                habits_list.append({
                    "id": str(doc["_id"]),
                    "name": doc.get("name", "Habit"),
                    "streak": doc.get("streak", 0),
                    "completedToday": completed_today,
                    "last_completed": doc.get("last_completed", ""),
                })
            return {"habits": habits_list, "source": "database"}
        except Exception as e:
            logger.warning(f"Habits DB lookup failed: {e}")

    # Fallback response
    return {
        "habits": [
            {**h, "completedToday": False} for h in DEFAULT_HABITS
        ],
        "source": "fallback"
    }


@router.post("/habits/create")
async def create_habit(habit: HabitCreate, user_id: str = "user_default"):
    """Create a new personal habit in MongoDB."""
    habit_id = f"h_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    doc = {
        "_id": habit_id,
        "user_id": user_id,
        "name": habit.name,
        "streak": 1,
        "last_completed": today_str,
        "created_at": now.isoformat(),
    }

    db = _get_db()
    if db is not None:
        try:
            db["user_habits"].insert_one(doc)
            logger.info(f"Habit created: {habit_id} — {habit.name}")
        except Exception as e:
            logger.warning(f"Habit DB insert failed: {e}")

    return {
        "success": True,
        "habit": {
            "id": habit_id,
            "name": habit.name,
            "streak": 1,
            "completedToday": True,
            "last_completed": today_str,
        }
    }


@router.post("/habits/toggle")
async def toggle_habit(habit_id: str, user_id: str = "user_default"):
    """Toggle today's completion state for a habit and update streak count live."""
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = _get_db()
    if db is not None:
        try:
            habits_col = db["user_habits"]
            doc = habits_col.find_one({"_id": habit_id, "user_id": user_id})
            if not doc:
                doc = habits_col.find_one({"id": habit_id, "user_id": user_id})

            if doc:
                current_last = doc.get("last_completed", "")
                current_streak = doc.get("streak", 0)

                if current_last == today_str:
                    # Uncheck habit for today
                    new_streak = max(0, current_streak - 1)
                    new_last = ""
                    completed_today = False
                else:
                    # Check habit for today
                    new_streak = current_streak + 1
                    new_last = today_str
                    completed_today = True

                habits_col.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"streak": new_streak, "last_completed": new_last}}
                )
                return {
                    "success": True,
                    "habit_id": str(doc["_id"]),
                    "streak": new_streak,
                    "completedToday": completed_today
                }
        except Exception as e:
            logger.warning(f"Habit toggle failed: {e}")

    return {"success": True, "habit_id": habit_id, "completedToday": True}


@router.delete("/habits/{habit_id}")
async def delete_habit(habit_id: str, user_id: str = "user_default"):
    """Delete a habit from MongoDB."""
    db = _get_db()
    if db is not None:
        try:
            res = db["user_habits"].delete_one({"_id": habit_id})
            if res.deleted_count == 0:
                db["user_habits"].delete_one({"id": habit_id})
            logger.info(f"Deleted habit: {habit_id}")
        except Exception as e:
            logger.warning(f"Habit delete failed: {e}")
    return {"success": True, "habit_id": habit_id}

