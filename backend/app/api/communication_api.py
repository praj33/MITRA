"""
backend/app/api/communication_api.py — Unified Communication Confirmation REST API

Provides dedicated, authenticated endpoints for approving and cancelling pending communication actions:
- POST /api/communication/actions/{pending_action_id}/confirm
- POST /api/communication/actions/{pending_action_id}/cancel
- GET  /api/communication/actions/{pending_action_id}

Zero LLM reinterpretation: Executes the exact staged action stored in the database.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.auth_dependencies import get_current_user
from app.services.communication_service import communication_service
from app.services.pending_action_service import pending_action_service

logger = logging.getLogger(__name__)

router = APIRouter()


class CommunicationConfirmRequest(BaseModel):
    """
    Optional payload for confirmation.
    The pending action stored server-side is strictly authoritative:
    recipient, content, subject, and channel cannot be overridden by client.
    """
    client_timestamp: Optional[str] = None


@router.post("/api/communication/actions/{pending_action_id}/confirm")
async def confirm_communication_action(
    pending_action_id: str,
    request_body: Optional[CommunicationConfirmRequest] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
):
    """
    Securely confirm and execute an exact pending communication action.
    - Identity is derived strictly from verified JWT (current_user["user_id"])
    - Reconstructs and executes the exact stored action
    - Enforces atomic state transition (replay and race condition protection)
    - Verifies action integrity hash against tampering
    """
    auth_user_id = current_user["user_id"]
    if not auth_user_id or not str(auth_user_id).strip():
        raise HTTPException(
            status_code=401,
            detail={"error": "Authenticated user_id required to confirm communication actions.", "error_code": "AUTH_REQUIRED"}
        )

    clean_uid = str(auth_user_id).strip()
    result = communication_service.confirm_pending_action(
        pending_action_id=pending_action_id,
        user_id=clean_uid,
        trace_id=x_trace_id,
    )

    res_dict = result.to_dict()

    # Map error states to appropriate HTTP status codes while preserving full normalized body
    status_code = 200
    if result.status == "failed":
        if result.error_code == "ACTION_NOT_FOUND":
            status_code = 404
        elif result.error_code in ("AUTH_REQUIRED", "ACCOUNT_NOT_AUTHORIZED"):
            status_code = 403
        elif result.error_code == "ACTION_EXPIRED":
            status_code = 410
        elif result.error_code == "CONCURRENT_EXECUTION_BLOCKED":
            status_code = 409
        elif result.error_code in ("INTEGRITY_CHECK_FAILED", "ACTION_CANCELLED"):
            status_code = 400
        else:
            status_code = 400

    return JSONResponse(status_code=status_code, content=res_dict)


@router.post("/api/communication/actions/{pending_action_id}/cancel")
async def cancel_communication_action(
    pending_action_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
):
    """
    Cancel a pending communication action.
    Once cancelled, an action cannot be confirmed or executed.
    """
    auth_user_id = current_user["user_id"]
    if not auth_user_id or not str(auth_user_id).strip():
        raise HTTPException(
            status_code=401,
            detail={"error": "Authenticated user_id required to cancel communication actions.", "error_code": "AUTH_REQUIRED"}
        )

    clean_uid = str(auth_user_id).strip()
    res = communication_service.cancel_pending_action(
        pending_action_id=pending_action_id,
        user_id=clean_uid,
        trace_id=x_trace_id,
    )

    status_code = 200
    if res.get("status") == "error":
        err_code = res.get("error_code")
        if err_code == "ACTION_NOT_FOUND":
            status_code = 404
        elif err_code == "ACTION_EXPIRED":
            status_code = 410
        elif err_code == "AUTH_REQUIRED":
            status_code = 403
        else:
            status_code = 400

    return JSONResponse(status_code=status_code, content=res)


@router.get("/api/communication/actions/{pending_action_id}")
async def get_communication_action(
    pending_action_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Inspect a pending communication action by ID for the authenticated user.
    Never returns secrets, tokens, or credentials.
    """
    auth_user_id = current_user["user_id"]
    if not auth_user_id or not str(auth_user_id).strip():
        raise HTTPException(status_code=401, detail="Authentication required.")

    clean_uid = str(auth_user_id).strip()
    action = pending_action_service.get_pending_action(
        pending_action_id=pending_action_id,
        user_id=clean_uid,
    )

    if not action:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Pending action '{pending_action_id}' not found.", "error_code": "ACTION_NOT_FOUND"}
        )

    return JSONResponse(status_code=200, content=action.to_dict())


@router.get("/api/communication/drafts/{draft_id}")
async def get_draft_endpoint(
    draft_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
):
    """
    GET /api/communication/drafts/{draft_id}
    Retrieves draft details for the authenticated user and their bound Gmail account.
    Enforces user authentication, account ownership, and cross-user isolation.
    """
    auth_user_id = current_user.get("user_id")
    if not auth_user_id or not str(auth_user_id).strip() or str(auth_user_id).strip().lower() in ("user_default", "default", "none", "null", "anonymous"):
        raise HTTPException(status_code=401, detail="Authentication required.")

    clean_uid = str(auth_user_id).strip()
    res = communication_service.get_draft(draft_id=draft_id, user_id=clean_uid, trace_id=x_trace_id)

    if res.get("status") == "success":
        return JSONResponse(status_code=200, content=res)

    err_code = res.get("error_code", "DRAFT_FETCH_FAILED")
    status_code = 404 if err_code == "GMAIL_NOT_FOUND" else (401 if err_code == "AUTH_REQUIRED" else 400)
    return JSONResponse(status_code=status_code, content=res)
