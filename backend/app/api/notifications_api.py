"""
notifications_api.py — MITRA Notifications API

Shared notification system across all BHIV products.
Part of the Canonical MITRA API (Phase 2 Hardened).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

# In-memory notification store (MongoDB in production)
_notifications: Dict[str, List[Dict[str, Any]]] = {}


class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    body: str
    type: str = "info"  # info, success, warning, error, capability
    product_id: str = "mitra"
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


@router.post("/")
async def create_notification(
    payload: NotificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Push a notification to a user."""
    auth_user_id = payload.user_id or current_user["user_id"]
    notif = {
        "id": f"notif_{uuid4().hex[:12]}",
        "user_id": auth_user_id,
        "title": payload.title,
        "body": payload.body,
        "type": payload.type,
        "product_id": payload.product_id,
        "action_url": payload.action_url,
        "metadata": payload.metadata,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notifications.setdefault(auth_user_id, []).append(notif)
    return {"status": "created", "notification": notif}


@router.get("")
@router.get("/")
@router.get("/me")
async def get_my_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch notifications for current authenticated user."""
    auth_user_id = current_user["user_id"]
    all_notifs = _notifications.get(auth_user_id, [])
    if unread_only:
        all_notifs = [n for n in all_notifs if not n.get("read")]
    recent = sorted(all_notifs, key=lambda n: n["created_at"], reverse=True)[:limit]
    return {
        "user_id": auth_user_id,
        "notifications": recent,
        "total": len(all_notifs),
        "unread_count": sum(1 for n in _notifications.get(auth_user_id, []) if not n.get("read")),
    }


@router.get("/{user_id}")
async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch notifications for a user (strictly isolated to authenticated user)."""
    auth_user_id = current_user["user_id"]
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot access another user's notifications")

    return await get_my_notifications(unread_only=unread_only, limit=limit, current_user=current_user)


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark a notification as read for authenticated user."""
    auth_user_id = current_user["user_id"]
    user_notifs = _notifications.get(auth_user_id, [])
    for notif in user_notifs:
        if notif["id"] == notification_id:
            notif["read"] = True
            return {"status": "ok", "notification": notif}

    raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/mark-all-read")
async def mark_all_read_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark all notifications as read for current authenticated user."""
    auth_user_id = current_user["user_id"]
    count = 0
    for notif in _notifications.get(auth_user_id, []):
        if not notif.get("read"):
            notif["read"] = True
            count += 1
    return {"status": "ok", "marked_read": count}


@router.post("/{user_id}/mark-all-read")
async def mark_all_read(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Mark all notifications as read for a user (strictly isolated)."""
    auth_user_id = current_user["user_id"]
    if user_id != auth_user_id:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot modify another user's notifications")

    return await mark_all_read_me(current_user=current_user)
