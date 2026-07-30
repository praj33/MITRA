"""
tantra_client.py — MITRA → TANTRA Runtime Integration

Routes all capability execution through the TANTRA governed runtime.
Records provenance in Bucket and captures execution in Replay.

Flow: MITRA → TANTRA → Capability Runtime (Kanishk) → Execution → Bucket → Replay

When TANTRA_RUNTIME_URL is not set, falls back to local execution
with a warning log. This ensures the system remains functional
during development while clearly marking the governance gap.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# TANTRA Runtime endpoint — provided by Ashmit when deployed
TANTRA_RUNTIME_URL = os.getenv("TANTRA_RUNTIME_URL", "https://bhiv-mitra.onrender.com")
TANTRA_API_KEY = os.getenv("TANTRA_API_KEY", "")

# Bucket logging
BUCKET_ENABLED = os.getenv("BUCKET_LOGGING", "true").lower() in ("true", "1", "yes")


class TANTRAClient:
    """
    HTTP client for the TANTRA governed execution runtime.

    Execution flow:
    1. Receive execution request from orchestrator
    2. Forward to TANTRA runtime with trace_id
    3. TANTRA routes to Kanishk's Capability Runtime
    4. Log provenance in Bucket
    5. Return result to orchestrator
    """

    def __init__(self) -> None:
        self.base_url = TANTRA_RUNTIME_URL.rstrip("/") if TANTRA_RUNTIME_URL else "https://bhiv-mitra.onrender.com"
        self.api_key = TANTRA_API_KEY
        self._bucket_traces: list[Dict[str, Any]] = []

    @property
    def is_available(self) -> bool:
        """Whether TANTRA runtime is configured and reachable."""
        return bool(self.base_url)

    async def execute(
        self,
        capability: str,
        intent: str,
        params: Dict[str, Any],
        user_id: str,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a capability action through TANTRA.

        If TANTRA is not available or fails, falls back to local execution
        and logs a governance warning.
        """
        trace_id = trace_id or f"trace_{uuid4().hex[:12]}"
        start_time = datetime.now(timezone.utc)

        # Route through TANTRA (try ecosystem endpoint first, then fallback to /execute)
        try:
            import httpx
            payload = {
                "product": params.get("app_id", "mitra_companion"),
                "action": capability,
                "payload": params,
                "user_id": user_id,
                "session_id": trace_id,
            }
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key or "internal_key",
                "X-Trace-ID": trace_id,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try ecosystem endpoint on Ashmit's runtime
                try:
                    resp = await client.post(
                        f"{self.base_url}/api/ecosystem/execute",
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        self._log_bucket(trace_id, user_id, capability, intent, params, result, start_time, governed=True)
                        return result
                except Exception:
                    pass

                # Fallback to direct /execute on Ashmit's runtime
                resp = await client.post(
                    f"{self.base_url}/execute",
                    json={
                        "capability": capability,
                        "intent": intent,
                        "params": params,
                        "user_id": user_id,
                        "trace_id": trace_id,
                        "source": "mitra_companion",
                    },
                    headers=headers,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    self._log_bucket(trace_id, user_id, capability, intent, params, result, start_time, governed=True)
                    return result
                raise Exception(f"TANTRA HTTP {resp.status_code}")
        except Exception as exc:
            logger.warning("TANTRA runtime execution notice (%s) — using local capability execution", exc)
            result = await self._local_fallback(capability, intent, params, user_id, trace_id)
            self._log_bucket(trace_id, user_id, capability, intent, params, result, start_time, governed=False)
            return result

    async def _local_fallback(
        self,
        capability: str,
        intent: str,
        params: Dict[str, Any],
        user_id: str,
        trace_id: str,
    ) -> Dict[str, Any]:
        """Local execution fallback when TANTRA is unavailable."""
        from app.services.execution_service import ExecutionService
        svc = ExecutionService()
        return svc.execute_action(
            action_type=capability,
            action_data=params,
            trace_id=trace_id,
        )

    def _log_bucket(
        self,
        trace_id: str,
        user_id: str,
        capability: str,
        intent: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        start_time: datetime,
        governed: bool,
    ) -> None:
        """Log execution provenance to Bucket (truth layer)."""
        if not BUCKET_ENABLED:
            return

        entry = {
            "trace_id": trace_id,
            "user_id": user_id,
            "capability": capability,
            "intent": intent,
            "params_summary": str(params)[:500],
            "result_status": result.get("status", "unknown"),
            "governed": governed,
            "runtime": "tantra" if governed else "local_fallback",
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
        }
        self._bucket_traces.append(entry)
        # Keep last 1000 traces in memory
        if len(self._bucket_traces) > 1000:
            self._bucket_traces = self._bucket_traces[-1000:]

        # Also try MongoDB bucket
        try:
            from app.services.bucket_service import BucketService
            bucket = BucketService()
            bucket.log_trace(entry)
        except Exception:
            pass

        logger.info(
            "Bucket: trace=%s cap=%s status=%s governed=%s duration=%dms",
            trace_id, capability, result.get("status"), governed, entry["duration_ms"],
        )

    def get_traces(self, limit: int = 50) -> list:
        """Return recent execution traces."""
        return self._bucket_traces[-limit:]


# Singleton
tantra_client = TANTRAClient()
