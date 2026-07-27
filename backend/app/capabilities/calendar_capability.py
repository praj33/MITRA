"""
calendar_capability.py — Mitra Calendar Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class CalendarCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return "Create, view, and manage calendar events and meetings."

    @property
    def supported_intents(self) -> List[str]:
        return ["calendar", "create_event", "update_event", "list_events", "check_availability", "schedule_meeting"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            dates = params.get("dates", {})
            action_params = {
                "intent": intent,
                "raw_message": params.get("message", ""),
                "date": dates.get("resolved_date", ""),
                "time": dates.get("time", ""),
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("calendar", action_params)
            summary = result.get("summary") or result.get("message") or "Calendar action completed."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
                actions=[{"label": "Add to calendar", "action": "Add to calendar"}, {"label": "Set a reminder", "action": "Set a reminder"}],
            )
        except Exception as exc:
            logger.warning("CalendarCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
