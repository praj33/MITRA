"""
UCCIS Adapter
-------------
Connects Mitra with UCCIS (Unified Citizen Communication & Information System).
Protocol: REST API with webhook support.
"""
from __future__ import annotations

import os
import time

import httpx

from app.ecosystem.base_adapter import (
    AdapterCapability,
    BaseBHIVAdapter,
    IntegrationManifest,
    IntegrationProtocol,
    IntegrationRequest,
    IntegrationResponse,
)


class UCCISAdapter(BaseBHIVAdapter):

    @property
    def product_name(self) -> str:
        return "UCCIS"

    def _create_manifest(self) -> IntegrationManifest:
        return IntegrationManifest(
            product_name=self.product_name,
            protocol=IntegrationProtocol.REST,
            base_url=os.getenv("UCCIS_API_URL", "https://uccis.bhiv.example.com/api/v1"),
            capabilities=[
                AdapterCapability.QUERY,
                AdapterCapability.EXECUTE,
                AdapterCapability.NOTIFY,
                AdapterCapability.STREAM,
            ],
            auth_type="bearer",
            timeout_seconds=30,
            retry_count=3,
            rate_limit_per_minute=150,
            event_topics=[
                "communication.sent",
                "notification.delivered",
                "citizen.registered",
                "service.requested",
            ],
        )

    async def query(self, request: IntegrationRequest) -> IntegrationResponse:
        start = time.time()
        try:
            base_url = self._manifest.base_url
            headers = {
                "Authorization": f"Bearer {os.getenv('UCCIS_API_KEY', '')}",
                "X-Trace-ID": request.trace_id,
                "X-Source": "mitra",
            }
            async with httpx.AsyncClient(timeout=self._manifest.timeout_seconds) as client:
                resp = await client.get(
                    f"{base_url}/{request.action}",
                    params=request.payload,
                    headers=headers,
                )
                latency = (time.time() - start) * 1000
                if resp.status_code < 400:
                    self._record_success(latency)
                    return IntegrationResponse(
                        success=True,
                        data=resp.json(),
                        trace_id=request.trace_id,
                        source_product=self.product_name,
                        latency_ms=latency,
                    )
                else:
                    error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    self._record_error(error)
                    return IntegrationResponse(
                        success=False,
                        error=error,
                        trace_id=request.trace_id,
                        source_product=self.product_name,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_error(str(e))
            return IntegrationResponse(
                success=False,
                error=str(e),
                trace_id=request.trace_id,
                source_product=self.product_name,
                latency_ms=latency,
            )

    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        start = time.time()
        try:
            base_url = self._manifest.base_url
            headers = {
                "Authorization": f"Bearer {os.getenv('UCCIS_API_KEY', '')}",
                "X-Trace-ID": request.trace_id,
                "X-Source": "mitra",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=self._manifest.timeout_seconds) as client:
                resp = await client.post(
                    f"{base_url}/{request.action}",
                    json=request.payload,
                    headers=headers,
                )
                latency = (time.time() - start) * 1000
                if resp.status_code < 400:
                    self._record_success(latency)
                    return IntegrationResponse(
                        success=True,
                        data=resp.json(),
                        trace_id=request.trace_id,
                        source_product=self.product_name,
                        latency_ms=latency,
                    )
                else:
                    error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    self._record_error(error)
                    return IntegrationResponse(
                        success=False,
                        error=error,
                        trace_id=request.trace_id,
                        source_product=self.product_name,
                        latency_ms=latency,
                    )
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record_error(str(e))
            return IntegrationResponse(
                success=False,
                error=str(e),
                trace_id=request.trace_id,
                source_product=self.product_name,
                latency_ms=latency,
            )
