"""
jwt_service.py — MITRA Canonical JWT Service

Cross-compatible with the frontend authController.js JWT pattern.
Uses the same JWT_SECRET env var so tokens work across the entire BHIV ecosystem.

Payload shape: { id: user_id, email: email, name: name, iat: ..., exp: ... }
Expiry: 7 days (matches frontend authController.js)
"""
from __future__ import annotations

import os
import time
import hmac
import hashlib
import base64
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "mitra_default_dev_secret_change_in_production")
JWT_EXPIRY_SECONDS = int(os.getenv("JWT_EXPIRY_SECONDS", str(7 * 24 * 3600)))  # 7 days


# ── Pure-Python JWT (HS256) ──────────────────────────────────────────────────
# No external dependency required. Compatible with jsonwebtoken (Node.js).

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_access_token(
    user_id: str,
    email: str = "",
    name: str = "",
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.

    Payload matches frontend authController.js pattern:
    { id: user_id, email, name, iat, exp }
    """
    now = int(time.time())
    payload: Dict[str, Any] = {
        "id": user_id,
        "email": email,
        "name": name,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    if extra_claims:
        payload.update(extra_claims)

    # Header
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())

    # Signature
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.

    Returns the payload dict if valid, None if invalid/expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(
            JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            logger.warning("JWT signature verification failed")
            return None

        # Decode payload
        payload = json.loads(_b64url_decode(payload_b64))

        # Check expiry
        exp = payload.get("exp", 0)
        if exp and int(time.time()) > exp:
            logger.info("JWT token expired for user %s", payload.get("id"))
            return None

        return payload

    except Exception as exc:
        logger.warning("JWT verification error: %s", exc)
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from a valid JWT token."""
    payload = verify_access_token(token)
    if payload:
        return payload.get("id")
    return None


# ── FastAPI Dependency ───────────────────────────────────────────────────────

async def get_current_user(authorization: str = "") -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for extracting the current user from the Authorization header.

    Usage:
        @app.get("/protected")
        async def protected(user = Depends(get_current_user)):
            ...
    """
    if not authorization:
        return None

    # Support both "Bearer <token>" and raw token
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    return verify_access_token(token)
