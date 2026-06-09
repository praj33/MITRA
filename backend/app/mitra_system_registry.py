from __future__ import annotations

from typing import Any, Dict

from app.services.audio_service import AudioService
from app.services.bucket_service import BucketService
from app.services.enforcement_service import EnforcementService
from app.services.execution_service import ExecutionService


class MitraSystemRegistry:
    """Shared services used by the single Mitra control plane."""

    def __init__(self) -> None:
        self.enforcement_service = EnforcementService()
        self.execution_service = ExecutionService()
        self.bucket_service = BucketService()
        self.audio_service = AudioService()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "policy_runtime": {
                "service": "mitra_policy_runtime",
                "status": "embedded",
                "owner": "app.services.mitra_control_plane_service.MitraControlPlaneService",
            },
            "rl_runtime": {
                "service": "mitra_rl_runtime",
                "status": "embedded",
                "owner": "app.services.mitra_control_plane_service.MitraControlPlaneService",
            },
            "enforcement": self.enforcement_service.get_status(),
            "execution": self.execution_service.get_status(),
            "bucket": self.bucket_service.get_status(),
            "audio": self.audio_service.get_tts_status()
            if hasattr(self.audio_service, "get_tts_status")
            else {"service": "audio_service", "status": "active"},
        }


mitra_registry = MitraSystemRegistry()
