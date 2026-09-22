"""
jwt_service.py — MITRA Canonical JWT Service Wrapper

DEPRECATION NOTICE:
This module wraps app.core.security for backward compatibility.
All JWT operations are delegated to app.core.security to ensure ONE authoritative JWT implementation.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.core.security import (
    create_access_token as security_create_token,
    verify_token_string,
    get_jwt_secret,
)

logger = logging.getLogger(__name__)


def create_access_token(
    user_id: str,
    email: str = "",
    name: str = "",
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token using the canonical security module.
    """
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "sub": user_id,
        "id": user_id,
        "email": email,
        "name": name,
    }
    if extra_claims:
        payload.update(extra_claims)

    return security_create_token(data=payload)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token using the canonical security module.
    Returns the payload dict if valid, None if invalid/expired.
    """
    try:
        token_data = verify_token_string(token)
        return {
            "id": token_data.user_id,
            "user_id": token_data.user_id,
            "sub": token_data.username,
            "email": token_data.email or "",
            "name": token_data.name or "",
        }
    except Exception as exc:
        logger.warning("JWT verification failed in jwt_service wrapper: %s", exc)
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from a valid JWT token using canonical security."""
    try:
        token_data = verify_token_string(token)
        return token_data.user_id
    except Exception:
        return None


async def get_current_user(authorization: str = "") -> Optional[Dict[str, Any]]:
    """
    Legacy wrapper for extracting current user payload from Authorization header.
    """
    if not authorization:
        return None

    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    return verify_access_token(token)
