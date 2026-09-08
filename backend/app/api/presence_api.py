"""
presence_api.py — MITRA User Presence API

Tracks user online/away/offline status across all BHIV products.
Part of the Canonical MITRA API (Phase 2 Hardened).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends

from app.core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/presence", tags=["Presence"])

# In-memory presence store (MongoDB in production)
_presence: Dict[str, Dict[str, Any]] = {}

# Heartbeat timeout: if no heartbeat in 60s, user is "away"; 5min = "offline"
_AWAY_SECONDS = 60
_OFFLINE_SECONDS = 300


def _get_status(last_seen: datetime) -> str:
    """Derive status from last heartbeat timestamp."""
    now = datetime.now(timezone.utc)
    delta = (now - last_seen).total_seconds()
    if delta < _AWAY_SECONDS:
        return "online"
    elif delta < _OFFLINE_SECONDS:
        return "away"
    return "offline"


@router.post("/heartbeat")
async def heartbeat(
    product_id: str = "mitra",
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Companion sends heartbeat every 30s to keep presence alive.
    Requires authenticated user context.
    """
    user_id = current_user["user_id"]
    now = datetime.now(timezone.utc)
    _presence[user_id] = {
        "user_id": user_id,
        "status": "online",
        "product_id": product_id,
        "last_seen": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    return {"status": "ok", "user_id": user_id, "presence": "online"}


@router.get("/me")
async def get_my_presence(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get current authenticated user's presence status."""
    user_id = current_user["user_id"]
    entry = _presence.get(user_id)
    if not entry:
        return {
            "user_id": user_id,
            "status": "offline",
            "product_id": None,
            "last_seen": None,
        }

    last_seen = datetime.fromisoformat(entry["last_seen"])
    status = _get_status(last_seen)
    return {
        "user_id": user_id,
        "status": status,
        "product_id": entry.get("product_id"),
        "last_seen": entry["last_seen"],
    }


@router.get("/{user_id}")
async def get_presence(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a user's current presence status (isolated to authenticated user)."""
    auth_user_id = current_user["user_id"]
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot access another user's presence state")

    return await get_my_presence(current_user=current_user)


@router.get("")
@router.get("/")
async def list_online_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List currently online users (requires authentication)."""
    now = datetime.now(timezone.utc)
    online = []
    for uid, entry in _presence.items():
        last_seen = datetime.fromisoformat(entry["last_seen"])
        status = _get_status(last_seen)
        if status in ("online", "away"):
            online.append({
                "user_id": uid,
                "status": status,
                "product_id": entry.get("product_id"),
                "last_seen": entry["last_seen"],
            })
    return {"users": online, "count": len(online)}
