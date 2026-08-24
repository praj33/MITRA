"""
notification_capability.py — Mitra Notification Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class NotificationCapability(BaseCapability):
    @property
    def name(self) -> str: return "notification"
    @property
    def description(self) -> str: return "Send notifications via available channels."
    @property
    def supported_intents(self) -> List[str]:
        return ["notification", "send_notification", "notify", "instagram", "device"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            action_params = {
                "intent": intent,
                "raw_message": params.get("message", ""),
                "channel": "telegram",
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("telegram", action_params)
            summary = result.get("summary") or result.get("message") or "Notification sent."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
            )
        except Exception as exc:
            logger.warning("NotificationCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
