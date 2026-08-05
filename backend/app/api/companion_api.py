"""
companion_api.py — Mitra Companion REST API

Primary conversation endpoint + session/memory management.
All requests pass through the CompanionOrchestrator.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.companion.companion_orchestrator import companion_orchestrator
from app.companion.companion_memory import companion_memory
from app.companion.companion_session import session_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ── Request / Response Models ──────────────────────────────────────────────

class CompanionChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    platform: str = "web"
    device: str = "browser"


class CompanionMemoryUpdateRequest(BaseModel):
    key: str
    value: str
    source: str = "user"


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/api/companion/chat")
async def companion_chat(
    request: CompanionChatRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    """
    Primary companion conversation endpoint.
    Accepts a user message, routes through CompanionOrchestrator,
    returns companion response + optional capability result.
    """
    _ = x_api_key
    user_id = request.user_id or x_user_id or "anonymous"
    if not request.message or not request.message.strip():
        return JSONResponse(status_code=400, content={"error": "message is required"})

    try:
        response = await companion_orchestrator.process(
            user_id=user_id,
            message=request.message.strip(),
            platform=request.platform,
            device=request.device,
        )
        return JSONResponse(status_code=200, content=response.to_dict())
    except Exception as exc:
        logger.exception("Companion chat failed for user_id=%s: %s", user_id, exc)
        return JSONResponse(status_code=500, content={"error": "Companion pipeline failed."})


@router.get("/api/companion/greeting/{user_id}")
async def companion_greeting(
    user_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Return a personalized greeting for the user."""
    _ = x_api_key
    try:
        greeting = await companion_orchestrator.get_greeting(user_id)
        return {"greeting": greeting, "user_id": user_id}
    except Exception as exc:
        logger.exception("Greeting failed: %s", exc)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.get("/api/companion/session/{user_id}")
async def get_session(
    user_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Get current session info for the user."""
    _ = x_api_key
    session = await session_manager.get_or_create(user_id)
    return session.to_dict()


@router.get("/api/companion/history/{user_id}")
async def get_history(
    user_id: str,
    limit: int = 20,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Get conversation history for the user."""
    _ = x_api_key
    history = await session_manager.get_history(user_id, limit=limit)
    return {"user_id": user_id, "history": history, "count": len(history)}


@router.get("/api/companion/memory/{user_id}")
async def get_memory(
    user_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Get stored user facts and memory."""
    _ = x_api_key
    facts = await companion_memory.get_user_facts(user_id)
    summaries = await companion_memory.get_recent_summaries(user_id)
    return {"user_id": user_id, "facts": facts, "recent_summaries": summaries}


@router.post("/api/companion/memory/{user_id}")
async def update_memory(
    user_id: str,
    request: CompanionMemoryUpdateRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Update a single user memory fact."""
    _ = x_api_key
    await companion_memory.set_fact(user_id, request.key, request.value, request.source)
    return {"user_id": user_id, "key": request.key, "status": "updated"}


@router.delete("/api/companion/session/{user_id}")
async def clear_session(
    user_id: str,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Clear the session for the user (start fresh)."""
    _ = x_api_key
    await session_manager.clear_session(user_id)
    return {"user_id": user_id, "status": "session_cleared"}


@router.get("/api/companion/capabilities")
async def list_capabilities(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """List all registered capabilities."""
    _ = x_api_key
    from app.companion.capability_registry import capability_registry
    return {"capabilities": capability_registry.list_capabilities()}


# ── Canonical BHIV Orchestration Models ────────────────────────────────────

class CompanionAuthRequest(BaseModel):
    app_id: str
    user_id: str
    auth_token: Optional[str] = None


class CompanionStateSyncRequest(BaseModel):
    user_id: str
    app_id: str
    active_section: Optional[str] = "chat"
    theme: Optional[str] = "dark"
    meta: Optional[dict] = None


class CompanionExecuteRequest(BaseModel):
    capability: str
    intent: str
    params: dict = {}
    user_id: str = "anonymous"
    trace_id: Optional[str] = None


# ── Canonical BHIV Orchestration Endpoints ─────────────────────────────────

@router.post("/api/companion/auth")
async def companion_auth(request: CompanionAuthRequest):
    """Canonical authentication handshake for BHIV products."""
    from datetime import datetime, timezone
    session = await session_manager.get_or_create(request.user_id)
    return {
        "status": "authenticated",
        "app_id": request.app_id,
        "user_id": request.user_id,
        "session_id": session.session_id,
        "authenticated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/api/companion/state")
async def sync_state(request: CompanionStateSyncRequest):
    """Sync UI/session state across BHIV applications."""
    from datetime import datetime, timezone
    await companion_memory.set_fact(
        user_id=request.user_id,
        key=f"app_state_{request.app_id}",
        value=str({
            "active_section": request.active_section,
            "theme": request.theme,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }),
        source=request.app_id,
    )
    return {"status": "synced", "user_id": request.user_id, "app_id": request.app_id}


@router.get("/api/companion/state/{user_id}")
async def get_state(user_id: str, app_id: Optional[str] = "universal_app"):
    """Fetch stored UI/session state for a user across apps."""
    facts = await companion_memory.get_user_facts(user_id)
    state_value = facts.get(f"app_state_{app_id}")
    return {"user_id": user_id, "app_id": app_id, "state": state_value}


@router.post("/api/companion/execute")
async def execute_capability(request: CompanionExecuteRequest):
    """Execute a capability action via TANTRA runtime client."""
    from app.services.tantra_client import tantra_client
    result = await tantra_client.execute(
        capability=request.capability,
        intent=request.intent,
        params=request.params,
        user_id=request.user_id,
        trace_id=request.trace_id,
    )
    return {"status": "executed", "request": request.dict(), "result": result}


# ── TANTRA Runtime Governed Proxy Endpoints ─────────────────────────────────

@router.get("/api/tantra/status")
async def tantra_status_proxy():
    """Proxy for Ashmit TANTRA Runtime status."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.get_tantra_status()


@router.get("/api/tantra/execution/{trace_id}")
async def tantra_get_execution_proxy(trace_id: str):
    """Fetch execution trace from TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.get_execution(trace_id)


@router.get("/api/tantra/governance")
async def tantra_governance_proxy():
    """Fetch governance health from TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.get_governance_health()


@router.get("/api/tantra/registry")
async def tantra_registry_proxy():
    """Fetch constitutional registry snapshot from TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.get_registry_snapshot()


@router.get("/api/tantra/registry/health")
async def tantra_registry_health_proxy():
    """Fetch constitutional registry health from TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.get_registry_health()


@router.get("/api/tantra/executions")
async def tantra_list_executions_proxy(limit: int = 50):
    """List recent executions from TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.list_tantra_executions(limit=limit)


@router.post("/api/tantra/cancel/{trace_id}")
async def tantra_cancel_execution_proxy(trace_id: str, reason: str = "user_requested"):
    """Cancel an in-progress execution on TANTRA Runtime."""
    from app.services.tantra_client import tantra_client
    return await tantra_client.cancel_execution(trace_id=trace_id, reason=reason)


# ── Smart Proactive Daily Briefing Endpoint ──────────────────────────────────

@router.get("/api/companion/briefing/{user_id}")
async def get_daily_briefing(user_id: str):
    """
    Generate a smart, proactive daily briefing aggregating:
    - Today's calendar events
    - Active pending tasks & high priority items
    - Active reminders
    - User profile details & contextual time-of-day greeting
    """
    from datetime import datetime, timezone
    from app.capabilities.task_capability import task_capability
    from app.capabilities.calendar_capability import calendar_capability
    from app.capabilities.reminder_capability import reminder_capability

    try:
        facts = await companion_memory.get_user_facts(user_id)
        user_name = facts.get("user_name") or facts.get("name") or "Friend"

        now = datetime.now(timezone.utc)
        hour = now.hour
        if 5 <= hour < 12:
            greeting = f"Good morning, {user_name}!"
            period = "morning"
        elif 12 <= hour < 18:
            greeting = f"Good afternoon, {user_name}!"
            period = "afternoon"
        else:
            greeting = f"Good evening, {user_name}!"
            period = "evening"

        tasks_res = await task_capability.execute("get_tasks", {"user_id": user_id})
        events_res = await calendar_capability.execute("get_events", {"user_id": user_id})
        reminders_res = await reminder_capability.execute("get_reminders", {"user_id": user_id})

        all_tasks = tasks_res.get("tasks", []) if isinstance(tasks_res, dict) else []
        all_events = events_res.get("events", []) if isinstance(events_res, dict) else []
        all_reminders = reminders_res.get("reminders", []) if isinstance(reminders_res, dict) else []

        pending_tasks = [t for t in all_tasks if t.get("status") in ("pending", "in_progress")]
        high_priority_tasks = [t for t in pending_tasks if t.get("priority") == "high"]

        today_str = now.strftime("%Y-%m-%d")
        today_events = [e for e in all_events if str(e.get("start", "")).startswith(today_str)]

        active_reminders = [r for r in all_reminders if r.get("status") == "active"]

        insights = []
        if today_events:
            insights.append(f"You have {len(today_events)} event(s) on your schedule today.")
        else:
            insights.append("Your calendar is clear for today.")

        if pending_tasks:
            insights.append(f"{len(pending_tasks)} pending task(s) awaiting your attention.")
        else:
            insights.append("All tasks are up to date!")

        if active_reminders:
            insights.append(f"{len(active_reminders)} active reminder(s) scheduled.")

        return {
            "user_id": user_id,
            "user_name": user_name,
            "greeting": greeting,
            "period": period,
            "date_display": now.strftime("%A, %B %d, %Y"),
            "today_events_count": len(today_events),
            "today_events": today_events[:3],
            "pending_tasks_count": len(pending_tasks),
            "high_priority_count": len(high_priority_tasks),
            "active_reminders_count": len(active_reminders),
            "summary_text": " ".join(insights),
            "quick_actions": [
                {"id": "schedule", "label": "📅 Plan Today", "prompt": "Help me plan my schedule for today"},
                {"id": "tasks", "label": "⚡ Review Tasks", "prompt": "Show me my pending tasks"},
                {"id": "focus", "label": "⏱️ Focus Mode", "prompt": "Let's start a 25-minute focus session"}
            ]
        }
    except Exception as e:
        logger.error(f"Error generating briefing for {user_id}: {e}")
        return {
            "user_id": user_id,
            "greeting": "Hello!",
            "date_display": datetime.now().strftime("%A, %B %d"),
            "summary_text": "Mitra is ready to assist you today.",
            "today_events_count": 0,
            "pending_tasks_count": 0,
            "active_reminders_count": 0,
            "quick_actions": []
        }


