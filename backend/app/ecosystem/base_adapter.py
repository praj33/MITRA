"""
Base Adapter for BHIV Ecosystem Integration
-------------------------------------------
All BHIV product adapters inherit from this base class.
Defines the canonical contract for Mitra <-> BHIV product communication.
"""
from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AdapterStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class IntegrationProtocol(str, Enum):
    REST = "rest"
    WEBHOOK = "webhook"
    EVENT = "event"
    GRPC = "grpc"
    ADAPTER = "adapter"


class AdapterCapability(str, Enum):
    QUERY = "query"
    EXECUTE = "execute"
    STREAM = "stream"
    SYNC = "sync"
    NOTIFY = "notify"


class AdapterHealth:
    """Health status for a BHIV product adapter."""

    def __init__(self, product: str):
        self.product = product
        self.status = AdapterStatus.UNKNOWN
        self.last_check: Optional[str] = None
        self.last_success: Optional[str] = None
        self.last_error: Optional[str] = None
        self.error_count: int = 0
        self.success_count: int = 0
        self.avg_latency_ms: float = 0.0
        self._latencies: List[float] = []

    def record_success(self, latency_ms: float):
        self.status = AdapterStatus.HEALTHY
        self.last_success = datetime.utcnow().isoformat() + "Z"
        self.last_check = self.last_success
        self.success_count += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        self.avg_latency_ms = sum(self._latencies) / len(self._latencies)

    def record_error(self, error: str):
        self.last_error = error
        self.last_check = datetime.utcnow().isoformat() + "Z"
        self.error_count += 1
        if self.error_count > self.success_count and self.error_count > 5:
            self.status = AdapterStatus.UNHEALTHY
        else:
            self.status = AdapterStatus.DEGRADED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product": self.product,
            "status": self.status.value,
            "last_check": self.last_check,
            "last_success": self.last_success,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


class IntegrationManifest:
    """
    Canonical manifest defining how Mitra integrates with a BHIV product.
    This is the published contract - no internal product modifications needed.
    """

    def __init__(
        self,
        product_name: str,
        protocol: IntegrationProtocol,
        base_url: Optional[str] = None,
        capabilities: Optional[List[AdapterCapability]] = None,
        auth_type: str = "api_key",
        timeout_seconds: int = 30,
        retry_count: int = 3,
        rate_limit_per_minute: int = 60,
        event_topics: Optional[List[str]] = None,
    ):
        self.product_name = product_name
        self.protocol = protocol
        self.base_url = base_url
        self.capabilities = capabilities or []
        self.auth_type = auth_type
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.rate_limit_per_minute = rate_limit_per_minute
        self.event_topics = event_topics or []
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.version = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_name": self.product_name,
            "protocol": self.protocol.value,
            "base_url": self.base_url,
            "capabilities": [c.value for c in self.capabilities],
            "auth_type": self.auth_type,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "event_topics": self.event_topics,
            "version": self.version,
            "created_at": self.created_at,
        }


class IntegrationRequest:
    """Canonical request format for BHIV product integration."""

    def __init__(
        self,
        action: str,
        payload: Dict[str, Any],
        trace_id: str,
        source_product: str = "mitra",
        target_product: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        authority_token: Optional[str] = None,
    ):
        self.action = action
        self.payload = payload
        self.trace_id = trace_id
        self.source_product = source_product
        self.target_product = target_product
        self.user_id = user_id
        self.session_id = session_id
        self.authority_token = authority_token
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "source_product": self.source_product,
            "target_product": self.target_product,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "authority_token": self.authority_token,
            "timestamp": self.timestamp,
        }


class IntegrationResponse:
    """Canonical response format from BHIV product integration."""

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        trace_id: str = "",
        source_product: str = "",
        latency_ms: float = 0.0,
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.trace_id = trace_id
        self.source_product = source_product
        self.latency_ms = latency_ms
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "trace_id": self.trace_id,
            "source_product": self.source_product,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp,
        }


class BaseBHIVAdapter(ABC):
    """
    Abstract base class for all BHIV product adapters.

    Every BHIV product adapter must:
    1. Define its manifest (published contract)
    2. Implement query/execute methods
    3. Provide health check
    4. Respect authority boundaries
    5. Log all operations for replay
    """

    def __init__(self):
        self._health = AdapterHealth(self.product_name)
        self._manifest = self._create_manifest()

    @property
    @abstractmethod
    def product_name(self) -> str:
        """Name of the BHIV product this adapter connects to."""
        ...

    @abstractmethod
    def _create_manifest(self) -> IntegrationManifest:
        """Define the canonical integration manifest for this product."""
        ...

    @abstractmethod
    async def query(self, request: IntegrationRequest) -> IntegrationResponse:
        """Query data from the BHIV product."""
        ...

    @abstractmethod
    async def execute(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute an action on the BHIV product."""
        ...

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health status."""
        return self._health.to_dict()

    @property
    def manifest(self) -> Dict[str, Any]:
        return self._manifest.to_dict()

    def _record_success(self, latency_ms: float):
        self._health.record_success(latency_ms)

    def _record_error(self, error: str):
        self._health.record_error(error)

    @staticmethod
    def generate_integration_trace_id(source: str, target: str, action: str) -> str:
        """Generate deterministic trace ID for integration operations."""
        payload = f"{source}:{target}:{action}:{time.time()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]
