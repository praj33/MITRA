"""
Bucket Adapter
--------------
Connects Mitra with Bucket (Audit Trail & Compliance platform).
This adapter wraps the existing BucketService for ecosystem integration.
Protocol: Internal adapter (same database).
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict

from app.ecosystem.base_adapter import (
    AdapterCapability,
    BaseBHIVAdapter,
    IntegrationManifest,
    IntegrationProtocol,
    IntegrationRequest,
    IntegrationResponse,
)


class BucketAdapter(BaseBHIVAdapter):

    @property
    def product_name(self) -> str:
        return "Bucket"

    def _create_manifest(self) -> IntegrationManifest:
        return IntegrationManifest(
            product_name=self.product_name,
            protocol=IntegrationProtocol.ADAPTER,
            base_url="internal://bucket-service",
            capabilities=[
                AdapterCapability.QUERY,
                AdapterCapability.EXECUTE,
                AdapterCapability.SYNC,
            ],
            auth_type="internal",
            timeout_seconds=10,
            retry_count=1,
            rate_limit_per_minute=1000,
            event_topics=[
                "audit.logged",
                "trace.created",
                "compliance.verified",
            ],
        )

    async def query(self, request: IntegrationRequest) -> IntegrationResponse:
        start = time.time()
        try:
            from app.services.bucket_service import BucketService
            bucket = BucketService()

            trace_id = request.payload.get("trace_id", "")
            stages = bucket.load_trace(trace_id) if hasattr(bucket, "load_trace") else []

            latency = (time.time() - start) * 1000
            self._record_success(latency)
            return IntegrationResponse(
                success=True,
                data={"trace_id": trace_id, "stages": stages, "stage_count": len(stages)},
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
            from app.services.bucket_service import BucketService
            bucket = BucketService()

            trace_id = request.payload.get("trace_id", request.trace_id)
            stage = request.payload.get("stage", "ecosystem_event")
            data = request.payload.get("data", {})

            bucket.log_event(trace_id, stage, data)

            latency = (time.time() - start) * 1000
            self._record_success(latency)
            return IntegrationResponse(
                success=True,
                data={"trace_id": trace_id, "stage": stage, "logged": True},
                trace_id=trace_id,
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
