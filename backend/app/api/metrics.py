"""
MITRA Metrics & Observability Endpoint
--------------------------------------
Provides basic system metrics and observability data.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.core.logging import get_logger
from app.mitra_system_registry import mitra_registry

logger = get_logger(__name__)

router = APIRouter()

# Simple in-memory metrics
_start_time = time.time()
_request_count = 0
_error_count = 0
_enforcement_blocks = 0
_enforcement_allows = 0
_enforcement_rewrites = 0


def increment_request_count():
    """Increment request counter."""
    global _request_count
    _request_count += 1


def increment_error_count():
    """Increment error counter."""
    global _error_count
    _error_count += 1


def increment_enforcement_counter(decision: str):
    """Increment enforcement decision counter."""
    global _enforcement_blocks, _enforcement_allows, _enforcement_rewrites
    if decision == "BLOCK":
        _enforcement_blocks += 1
    elif decision == "ALLOW":
        _enforcement_allows += 1
    elif decision == "REWRITE":
        _enforcement_rewrites += 1


@router.get("/api/metrics")
async def get_metrics():
    """
    Get basic system metrics.

    Returns:
        System metrics including uptime, request counts, and enforcement stats.
    """
    uptime_seconds = time.time() - _start_time
    uptime_hours = uptime_seconds / 3600

    return {
        "status": "ok",
        "version": "3.0.0",
        "uptime": {
            "seconds": round(uptime_seconds, 2),
            "hours": round(uptime_hours, 2),
        },
        "requests": {
            "total": _request_count,
            "errors": _error_count,
            "success_rate": round(
                ((_request_count - _error_count) / max(_request_count, 1)) * 100, 2
            ),
        },
        "enforcement": {
            "allows": _enforcement_allows,
            "blocks": _enforcement_blocks,
            "rewrites": _enforcement_rewrites,
            "total": _enforcement_allows + _enforcement_blocks + _enforcement_rewrites,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/metrics/system")
async def get_system_metrics():
    """
    Get detailed system metrics including service status.

    Returns:
        Detailed system metrics with service health.
    """
    registry_snapshot = mitra_registry.snapshot()

    return {
        "status": "ok",
        "version": "3.0.0",
        "services": registry_snapshot,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/metrics/enforcement")
async def get_enforcement_metrics():
    """
    Get enforcement-specific metrics.

    Returns:
        Enforcement decision distribution and rates.
    """
    total_enforcement = _enforcement_allows + _enforcement_blocks + _enforcement_rewrites

    return {
        "status": "ok",
        "enforcement": {
            "allows": _enforcement_allows,
            "blocks": _enforcement_blocks,
            "rewrites": _enforcement_rewrites,
            "total": total_enforcement,
            "allow_rate": round(
                (_enforcement_allows / max(total_enforcement, 1)) * 100, 2
            ),
            "block_rate": round(
                (_enforcement_blocks / max(total_enforcement, 1)) * 100, 2
            ),
            "rewrite_rate": round(
                (_enforcement_rewrites / max(total_enforcement, 1)) * 100, 2
            ),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/metrics/reset")
async def reset_metrics():
    """
    Reset all metrics counters.

    Returns:
        Confirmation of reset.
    """
    global _start_time, _request_count, _error_count
    global _enforcement_blocks, _enforcement_allows, _enforcement_rewrites

    _start_time = time.time()
    _request_count = 0
    _error_count = 0
    _enforcement_blocks = 0
    _enforcement_allows = 0
    _enforcement_rewrites = 0

    return {
        "status": "ok",
        "message": "Metrics counters reset",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
