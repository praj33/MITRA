from __future__ import annotations

from typing import Any, Dict

from fastapi import Request

from app.inbound.email_inbound_handler import handle_email_webhook as _handle_email_webhook


async def handle_email_webhook(request: Request) -> Dict[str, Any]:
    """
    Memory-layer shim that delegates to the primary Email webhook handler.
    """
    return await _handle_email_webhook(request)
