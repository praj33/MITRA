"""
reminder_capability.py — Mitra Reminder Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class ReminderCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "reminder"

    @property
    def description(self) -> str:
        return "Set, list, and cancel reminders."

    @property
    def supported_intents(self) -> List[str]:
        return ["reminder", "create_reminder", "list_reminders", "cancel_reminder", "set_alert"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            dates = params.get("dates", {})
            action_params = {
                "intent": intent,
                "raw_message": params.get("message", ""),
                "remind_at": dates.get("resolved_date") or dates.get("time", ""),
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("reminder", action_params)
            summary = result.get("summary") or result.get("message") or "Reminder set."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
                actions=[{"label": "View Reminders", "action": "list_reminders"}],
            )
        except Exception as exc:
            logger.warning("ReminderCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
