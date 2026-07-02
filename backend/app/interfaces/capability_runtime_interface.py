"""
capability_runtime_interface.py — Interface Contract for Kanishk's Capability Runtime

This file defines the API contract that Mitra's Companion layer expects
from Kanishk's Capability Runtime.

Mitra will consume the runtime ONLY through this interface.
Kanishk implements these endpoints. We do NOT duplicate the implementation.

Runtime responsibilities (Kanishk):
- Capability discovery (what capabilities are available and healthy)
- Scheduling (time-based and trigger-based execution)
- Execution (safe, isolated execution of capability actions)
- Monitoring (execution status, retries, timeouts)
- Recovery (failed execution retry logic)
- Reporting (execution audit trail)

Our responsibilities (Raj / Mitra product layer):
- Define the interface contract (this file)
- Call the runtime via HTTP when executing capabilities
- Handle the response and surface it to the user
- Never implement execution logic ourselves
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Runtime base URL — set by Kanishk when deployed
CAPABILITY_RUNTIME_BASE_URL = os.getenv("CAPABILITY_RUNTIME_URL", "http://localhost:8100")
CAPABILITY_RUNTIME_API_KEY = os.getenv("CAPABILITY_RUNTIME_API_KEY", "")


class CapabilityRuntimeInterface:
    """
    HTTP client for Kanishk's Capability Runtime.

    Contract (endpoints the runtime MUST expose):

    POST /runtime/execute
        Request:  { capability, intent, params, trace_id, user_id }
        Response: { run_id, status, result, error, executed_at }

    GET  /runtime/status/{run_id}
        Response: { run_id, status, result, error, retries, executed_at }

    GET  /runtime/capabilities
        Response: [{ name, status, version, supported_intents }]

    POST /runtime/schedule
        Request:  { capability, intent, params, scheduled_at, user_id }
        Response: { schedule_id, status, scheduled_at }

    DELETE /runtime/schedule/{schedule_id}
        Response: { schedule_id, status: "cancelled" }
    """

    def __init__(self) -> None:
        self.base_url = CAPABILITY_RUNTIME_BASE_URL.rstrip("/")
        self.api_key = CAPABILITY_RUNTIME_API_KEY

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    async def execute(
        self,
        capability: str,
        intent: str,
        params: Dict[str, Any],
        user_id: str,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a capability action via Kanishk's runtime.

        Expected response shape:
        {
            "run_id":      "run_abc123",
            "status":      "success" | "error" | "pending",
            "result":      { ... capability-specific result ... },
            "error":       null | "error message",
            "executed_at": "2026-07-02T11:00:00Z"
        }
        """
        import httpx
        payload = {
            "capability": capability,
            "intent":     intent,
            "params":     params,
            "user_id":    user_id,
            "trace_id":   trace_id,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/runtime/execute",
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("CapabilityRuntime.execute failed: %s", exc)
            return {"status": "error", "error": str(exc), "result": {}}

    async def get_status(self, run_id: str) -> Dict[str, Any]:
        """Check the status of a running or completed capability execution."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/runtime/status/{run_id}",
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("CapabilityRuntime.get_status failed: %s", exc)
            return {"run_id": run_id, "status": "unknown", "error": str(exc)}

    async def list_available(self) -> list:
        """Discover all capabilities registered in the runtime."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/runtime/capabilities",
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("CapabilityRuntime.list_available failed: %s", exc)
            return []

    async def schedule(
        self,
        capability: str,
        intent: str,
        params: Dict[str, Any],
        user_id: str,
        scheduled_at: str,
    ) -> Dict[str, Any]:
        """Schedule a future capability execution."""
        import httpx
        payload = {
            "capability":   capability,
            "intent":       intent,
            "params":       params,
            "user_id":      user_id,
            "scheduled_at": scheduled_at,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/runtime/schedule",
                    json=payload,
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("CapabilityRuntime.schedule failed: %s", exc)
            return {"status": "error", "error": str(exc)}

    async def cancel_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Cancel a scheduled capability execution."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(
                    f"{self.base_url}/runtime/schedule/{schedule_id}",
                    headers=self._headers,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.warning("CapabilityRuntime.cancel_schedule failed: %s", exc)
            return {"schedule_id": schedule_id, "status": "error", "error": str(exc)}


# Singleton — used by ExecutionService when Kanishk's runtime is live
capability_runtime = CapabilityRuntimeInterface()
