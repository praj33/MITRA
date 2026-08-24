"""
TANTRA Runtime Governance
=========================
Phase 5 — Runtime Governance

Implements:
- Runtime health validation
- Capability timeout handling
- Retry policy with exponential backoff
- Cancellation support
- Failure propagation
- Observability hooks

Execution behaviour must be deterministic.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class RetryStrategy(str, Enum):
    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass
class CapabilityHealth:
    """Health status of a single capability."""
    capability_type: str
    status: HealthStatus = HealthStatus.HEALTHY
    last_check: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    _latencies: List[float] = field(default_factory=list)

    def record_success(self, latency_ms: float) -> None:
        self.success_count += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        self.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        self.status = HealthStatus.HEALTHY
        self.last_check = datetime.now(timezone.utc).isoformat()

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_check = datetime.now(timezone.utc).isoformat()
        if self.failure_count > self.success_count and self.failure_count > 5:
            self.status = HealthStatus.UNHEALTHY
        else:
            self.status = HealthStatus.DEGRADED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_type": self.capability_type,
            "status": self.status.value,
            "last_check": self.last_check,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


@dataclass
class RetryPolicy:
    """Configurable retry policy for capability invocations."""
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_retries: int = 3
    base_delay_ms: int = 100
    max_delay_ms: int = 5000
    timeout_seconds: int = 30

    def get_delay_ms(self, attempt: int) -> int:
        if self.strategy == RetryStrategy.NONE:
            return 0
        if self.strategy == RetryStrategy.LINEAR:
            return min(self.base_delay_ms * (attempt + 1), self.max_delay_ms)
        # Exponential backoff
        return min(self.base_delay_ms * (2 ** attempt), self.max_delay_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "max_retries": self.max_retries,
            "base_delay_ms": self.base_delay_ms,
            "max_delay_ms": self.max_delay_ms,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class CancellationToken:
    """Supports cooperative cancellation of executions."""
    trace_id: str
    cancelled: bool = False
    cancelled_at: Optional[str] = None
    reason: str = ""

    def cancel(self, reason: str = "user_requested") -> None:
        self.cancelled = True
        self.cancelled_at = datetime.now(timezone.utc).isoformat()
        self.reason = reason
        logger.info("Execution cancelled: %s (reason: %s)", self.trace_id, reason)

    def is_cancelled(self) -> bool:
        return self.cancelled

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "cancelled": self.cancelled,
            "cancelled_at": self.cancelled_at,
            "reason": self.reason,
        }


class RuntimeGovernance:
    """
    Enforces runtime governance rules for all TANTRA executions.
    Validates health, enforces timeouts, manages retries, and propagates failures.
    """

    def __init__(self) -> None:
        self._capability_health: Dict[str, CapabilityHealth] = {}
        self._retry_policies: Dict[str, RetryPolicy] = {}
        self._cancellation_tokens: Dict[str, CancellationToken] = {}
        self._default_retry_policy = RetryPolicy()
        logger.info("RuntimeGovernance initialized")

    def get_capability_health(self, capability_type: str) -> CapabilityHealth:
        if capability_type not in self._capability_health:
            self._capability_health[capability_type] = CapabilityHealth(
                capability_type=capability_type
            )
        return self._capability_health[capability_type]

    def set_retry_policy(self, capability_type: str, policy: RetryPolicy) -> None:
        self._retry_policies[capability_type] = policy

    def get_retry_policy(self, capability_type: str) -> RetryPolicy:
        return self._retry_policies.get(capability_type, self._default_retry_policy)

    def create_cancellation_token(self, trace_id: str) -> CancellationToken:
        token = CancellationToken(trace_id=trace_id)
        self._cancellation_tokens[trace_id] = token
        return token

    def get_cancellation_token(self, trace_id: str) -> Optional[CancellationToken]:
        return self._cancellation_tokens.get(trace_id)

    def validate_preconditions(
        self,
        trace_id: str,
        capability_type: str,
    ) -> tuple[bool, str]:
        """
        Validate execution preconditions.
        Returns (is_valid, reason).
        """
        # Check cancellation
        token = self._cancellation_tokens.get(trace_id)
        if token and token.is_cancelled():
            return False, f"Execution cancelled: {token.reason}"

        # Check capability health
        health = self.get_capability_health(capability_type)
        if health.status == HealthStatus.UNHEALTHY:
            return False, f"Capability {capability_type} is unhealthy"

        return True, "preconditions_met"

    def record_success(self, capability_type: str, latency_ms: float) -> None:
        health = self.get_capability_health(capability_type)
        health.record_success(latency_ms)

    def record_failure(self, capability_type: str) -> None:
        health = self.get_capability_health(capability_type)
        health.record_failure()

    def should_retry(self, capability_type: str, attempt: int, error: str) -> bool:
        policy = self.get_retry_policy(capability_type)
        if attempt >= policy.max_retries:
            return False
        # Don't retry on cancellation
        if "cancelled" in error.lower():
            return False
        return policy.strategy != RetryStrategy.NONE

    def get_retry_delay_ms(self, capability_type: str, attempt: int) -> int:
        policy = self.get_retry_policy(capability_type)
        return policy.get_delay_ms(attempt)

    def propagate_failure(
        self,
        trace_id: str,
        capability_type: str,
        error: str,
        attempt: int,
    ) -> Dict[str, Any]:
        """Propagate failure with full context for Bucket storage."""
        health = self.get_capability_health(capability_type)
        policy = self.get_retry_policy(capability_type)
        return {
            "trace_id": trace_id,
            "capability_type": capability_type,
            "error": error,
            "attempt": attempt,
            "max_retries": policy.max_retries,
            "should_retry": self.should_retry(capability_type, attempt, error),
            "retry_delay_ms": self.get_retry_delay_ms(capability_type, attempt + 1),
            "capability_health": health.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_health_report(self) -> Dict[str, Any]:
        return {
            "capabilities": {
                ct: ch.to_dict()
                for ct, ch in self._capability_health.items()
            },
            "retry_policies": {
                ct: rp.to_dict()
                for ct, rp in self._retry_policies.items()
            },
            "active_cancellations": sum(
                1 for t in self._cancellation_tokens.values() if not t.is_cancelled()
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def cleanup_stale_tokens(self, max_age_seconds: int = 3600) -> int:
        """Remove cancellation tokens older than max_age_seconds."""
        now = time.time()
        stale = []
        for trace_id, token in self._cancellation_tokens.items():
            if token.cancelled_at:
                try:
                    token_time = datetime.fromisoformat(token.cancelled_at.replace("Z", "+00:00")).timestamp()
                    if now - token_time > max_age_seconds:
                        stale.append(trace_id)
                except (ValueError, TypeError):
                    pass
        for trace_id in stale:
            del self._cancellation_tokens[trace_id]
        return len(stale)
