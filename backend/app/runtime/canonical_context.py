"""
canonical_context.py — MITRA Canonical Runtime Identity & Context Model
Enforces unified trace_id, correlation_id, execution_id, and provenance metadata across execution pathways.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class CanonicalContext:
    trace_id: str = field(default_factory=lambda: f"trc_{uuid.uuid4().hex[:12]}")
    correlation_id: str = field(default_factory=lambda: f"cor_{uuid.uuid4().hex[:12]}")
    execution_id: str = field(default_factory=lambda: f"exc_{uuid.uuid4().hex[:12]}")
    user_id: str = "anonymous"
    platform: str = "web"
    device: str = "browser"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "platform": self.platform,
            "device": self.device,
            "created_at": self.created_at,
            "provenance": self.provenance,
        }

def create_canonical_context(
    user_id: str = "anonymous",
    trace_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    platform: str = "web",
    device: str = "browser",
    provenance: Optional[Dict[str, Any]] = None,
) -> CanonicalContext:
    """Factory helper to ensure all 3 IDs are valid and non-empty."""
    t_id = trace_id or f"trc_{uuid.uuid4().hex[:12]}"
    c_id = correlation_id or t_id
    e_id = execution_id or f"exc_{uuid.uuid4().hex[:12]}"
    
    prov = provenance or {}
    prov.setdefault("source", "mitra_companion")
    prov.setdefault("version", "5.0.0")

    return CanonicalContext(
        trace_id=t_id,
        correlation_id=c_id,
        execution_id=e_id,
        user_id=user_id,
        platform=platform,
        device=device,
        provenance=prov,
    )
