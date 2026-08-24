"""
notifications_api.py — MITRA Notifications API

Shared notification system across all BHIV products.
Part of the Canonical MITRA API (Phase 1).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.services.jwt_service import verify_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

# In-memory notification store (MongoDB in production)
_notifications: Dict[str, List[Dict[str, Any]]] = {}


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    body: str
    type: str = "info"  # info, success, warning, error, capability
    product_id: str = "mitra"
    action_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


@router.post("/")
async def create_notification(payload: NotificationCreate):
    """Push a notification to a user (from any BHIV product)."""
    notif = {
        "id": f"notif_{uuid4().hex[:12]}",
        "user_id": payload.user_id,
        "title": payload.title,
        "body": payload.body,
        "type": payload.type,
        "product_id": payload.product_id,
        "action_url": payload.action_url,
        "metadata": payload.metadata,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notifications.setdefault(payload.user_id, []).append(notif)
    return {"status": "created", "notification": notif}


@router.get("/{user_id}")
async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
):
    """Fetch notifications for a user."""
    all_notifs = _notifications.get(user_id, [])
    if unread_only:
        all_notifs = [n for n in all_notifs if not n.get("read")]
    # Most recent first
    recent = sorted(all_notifs, key=lambda n: n["created_at"], reverse=True)[:limit]
    return {
        "user_id": user_id,
        "notifications": recent,
        "total": len(all_notifs),
        "unread_count": sum(1 for n in _notifications.get(user_id, []) if not n.get("read")),
    }


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: str):
    """Mark a notification as read."""
    for user_notifs in _notifications.values():
        for notif in user_notifs:
            if notif["id"] == notification_id:
                notif["read"] = True
                return {"status": "ok", "notification": notif}
    return {"status": "not_found"}


@router.post("/{user_id}/mark-all-read")
async def mark_all_read(user_id: str):
    """Mark all notifications as read for a user."""
    count = 0
    for notif in _notifications.get(user_id, []):
        if not notif.get("read"):
            notif["read"] = True
            count += 1
    return {"status": "ok", "marked_read": count}
