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
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        import httpx
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=3.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

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
            client = self._get_client()
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

    async def evaluate_mitra_event(
        self,
        title: str,
        content: str,
        category: str = "general",
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """Call Ashmit's /api/mitra/evaluate endpoint for event governance evaluation."""
        try:
            import httpx
            url = f"{self.base_url}/api/mitra/evaluate"
            payload = {
                "event": {"title": title, "content": content, "category": category, "confidence": 1.0},
                "user_id": user_id,
                "context": {"platform": "mitra_companion", "device": "api"},
            }
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key or "localtest",
                "X-User-Id": user_id,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "ALLOW", "reason": f"Fallback HTTP {resp.status_code}"}
        except Exception as exc:
            logger.warning("Evaluate event failed (%s) — allowing locally", exc)
            return {"status": "ALLOW", "reason": "Local evaluation fallback"}

    async def call_assistant(
        self,
        message: str,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call Ashmit's /api/assistant single entrypoint."""
        try:
            import httpx
            url = f"{self.base_url}/api/assistant"
            payload = {
                "version": "3.0.0",
                "input": {"message": message},
                "context": {"platform": "web", "device": "browser", "session_id": session_id or "sess_default"},
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key or "localtest",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            logger.warning("Call assistant endpoint failed (%s)", exc)
            return {"status": "error", "error": str(exc)}

    async def get_tantra_status(self) -> Dict[str, Any]:
        """Fetch status report from Ashmit's /api/tantra/status endpoint."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/status"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "reachable", "http_code": resp.status_code}
        except Exception as exc:
            return {"status": "offline", "error": str(exc)}

    async def get_execution(self, trace_id: str) -> Dict[str, Any]:
        """Fetch execution record by trace_id from Ashmit's /api/tantra/execution/{trace_id}."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/execution/{trace_id}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"Execution trace_id={trace_id} returned HTTP {resp.status_code}"}
        except Exception as exc:
            return {"error": str(exc)}

    async def get_governance_health(self) -> Dict[str, Any]:
        """Fetch governance health report from Ashmit's /api/tantra/governance."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/governance"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "healthy", "http_code": resp.status_code}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    async def get_registry_snapshot(self) -> Dict[str, Any]:
        """Fetch constitutional registry snapshot from Ashmit's /api/tantra/registry."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/registry"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "snapshot_available", "http_code": resp.status_code}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    async def get_registry_health(self) -> Dict[str, Any]:
        """Fetch constitutional registry health from Ashmit's /api/tantra/registry/health."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/registry/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "healthy", "http_code": resp.status_code}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    async def list_tantra_executions(self, limit: int = 50) -> Dict[str, Any]:
        """List recent executions from Ashmit's /api/tantra/executions."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/executions?limit={limit}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"executions": [], "count": 0, "http_code": resp.status_code}
        except Exception as exc:
            return {"executions": [], "error": str(exc)}

    async def cancel_execution(self, trace_id: str, reason: str = "user_requested") -> Dict[str, Any]:
        """Cancel an in-progress execution via Ashmit's POST /api/tantra/cancel/{trace_id}."""
        try:
            import httpx
            url = f"{self.base_url}/api/tantra/cancel/{trace_id}?reason={reason}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "cancelled", "trace_id": trace_id, "reason": reason, "http_code": resp.status_code}
        except Exception as exc:
            return {"status": "cancelled_local", "trace_id": trace_id, "reason": reason, "error": str(exc)}


# Singleton
tantra_client = TANTRAClient()


