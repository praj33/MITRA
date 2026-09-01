"""
TANTRA API Endpoints
====================
Exposes TANTRA runtime status, execution history, governance, and registry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/tantra", tags=["TANTRA Runtime"])


def _get_runtime():
    from app.mitra_system_registry import mitra_registry
    return mitra_registry.tantra_runtime


@router.get("/status")
async def tantra_status():
    """TANTRA runtime status — the sole execution engine."""
    runtime = _get_runtime()
    return runtime.get_status()


@router.get("/execution/{trace_id}")
async def get_execution(trace_id: str):
    """Get execution record by trace_id."""
    runtime = _get_runtime()
    record = runtime.get_execution_record(trace_id)
    if not record:
        return {"error": "Execution not found", "trace_id": trace_id}
    return record.to_dict()


@router.get("/governance")
async def governance_health():
    """Runtime governance health report."""
    runtime = _get_runtime()
    return runtime.governance.get_health_report()


@router.get("/registry")
async def registry_snapshot():
    """Constitutional registry snapshot."""
    runtime = _get_runtime()
    return runtime.registry.snapshot()


@router.get("/registry/health")
async def registry_health():
    """Constitutional registry health."""
    runtime = _get_runtime()
    return runtime.registry.get_health()


@router.get("/executions")
async def list_executions(limit: int = Query(default=50, le=200)):
    """List recent executions."""
    runtime = _get_runtime()
    records = list(runtime._execution_records.values())[-limit:]
    return {
        "count": len(records),
        "executions": [r.to_dict() for r in records],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/cancel/{trace_id}")
async def cancel_execution(trace_id: str, reason: str = Query(default="user_requested")):
    """Cancel an in-progress execution."""
    runtime = _get_runtime()
    token = runtime.governance.get_cancellation_token(trace_id)
    if token:
        token.cancel(reason)
        return {"status": "cancelled", "trace_id": trace_id, "reason": reason}
    # Create a new cancellation token
    token = runtime.governance.create_cancellation_token(trace_id)
    token.cancel(reason)
    return {"status": "cancelled", "trace_id": trace_id, "reason": reason}
