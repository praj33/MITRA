from __future__ import annotations

"""
Mitra System Registry
Centralized registry for all core runtime modules.

Goal:
- Provide a single, deterministic place where system services are constructed.
- Governance (policy, mediation, enforcement adapter) is now EMBEDDED directly
  in MitraControlPlaneService — not registered here.
- Safety and Intelligence wrappers are REMOVED — replaced by embedded governance.
"""

from typing import Dict, Any

from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService
from app.services.bucket_service import BucketService
from app.services.audio_service import AudioService


class MitraSystemRegistry:
    def __init__(self) -> None:
        # Core services — governance is embedded directly in the control plane
        self.enforcement_service = EnforcementService()
        self.execution_service = ExecutionService()
        self.bucket_service = BucketService()
        self.audio_service = AudioService()

    def snapshot(self) -> Dict[str, Any]:
        """
        Lightweight status snapshot of all registered modules.
        Used by health monitors and BHIV Core gateway.
        """
        return {
            "enforcement": self.enforcement_service.get_status(),
            "execution": self.execution_service.get_status(),
            "bucket": self.bucket_service.get_status()
            if hasattr(self.bucket_service, "get_status")
            else {"service": "bucket_service", "status": "unknown"},
            "audio": self.audio_service.get_tts_status()
            if hasattr(self.audio_service, "get_tts_status")
            else {"service": "audio_service", "status": "active"},
            "governance": {
                "service": "governance_embedded",
                "status": "active",
                "note": "PolicyRuntime, Mediation, EnforcementAdapter embedded in MitraControlPlaneService",
            },
        }


# Global registry instance used across the runtime.
mitra_registry = MitraSystemRegistry()
