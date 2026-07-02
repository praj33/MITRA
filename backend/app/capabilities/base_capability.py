"""
base_capability.py — Mitra Base Capability Interface

Every capability in the Capability Hub must extend BaseCapability.
This enforces a uniform interface so CapabilityRegistry can
attach/detach capabilities dynamically at runtime.

Kanishk's Capability Runtime will consume this interface to
discover, schedule, and execute capabilities.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

CapabilityStatus = Literal["success", "error", "pending", "not_found"]


@dataclass
class CapabilityResult:
    """Structured result returned by every capability execution."""
    capability: str
    intent: str
    status: CapabilityStatus
    summary: str                          # human-readable one-line summary
    data: Dict[str, Any] = field(default_factory=dict)   # capability-specific payload
    actions: List[Dict[str, str]] = field(default_factory=list)  # follow-up actions
    error: Optional[str] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability":  self.capability,
            "intent":      self.intent,
            "status":      self.status,
            "summary":     self.summary,
            "data":        self.data,
            "actions":     self.actions,
            "error":       self.error,
            "trace_id":    self.trace_id,
        }

    @classmethod
    def error_result(
        cls,
        capability: str,
        intent: str,
        error: str,
        trace_id: Optional[str] = None,
    ) -> "CapabilityResult":
        return cls(
            capability=capability,
            intent=intent,
            status="error",
            summary=f"Could not complete {intent}.",
            error=error,
            trace_id=trace_id,
        )


class BaseCapability(ABC):
    """
    Abstract base for all Mitra capabilities.

    Subclasses must implement:
        - name: str property
        - description: str property
        - supported_intents: list[str] property
        - execute(intent, params, trace_id) -> CapabilityResult
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique capability identifier e.g. 'email', 'calendar'"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-sentence description of what this capability does."""
        ...

    @property
    @abstractmethod
    def supported_intents(self) -> List[str]:
        """
        List of intents this capability handles.
        e.g. ['draft_email', 'send_email', 'read_emails']
        """
        ...

    @abstractmethod
    async def execute(
        self,
        intent: str,
        params: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> CapabilityResult:
        """
        Execute the capability for the given intent.

        Args:
            intent:   The classified intent string.
            params:   Extracted parameters from the user message.
            trace_id: Mitra safety trace ID for this request.

        Returns:
            CapabilityResult with structured output.
        """
        ...

    def can_handle(self, intent: str) -> bool:
        """Check if this capability can handle the given intent."""
        return intent in self.supported_intents

    def __repr__(self) -> str:
        return f"<Capability: {self.name} | intents={self.supported_intents}>"
