"""
task_capability.py — Mitra Task Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class TaskCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "task"

    @property
    def description(self) -> str:
        return "Create, update, and track tasks and to-dos."

    @property
    def supported_intents(self) -> List[str]:
        return ["ems", "task", "create_task", "update_task", "list_tasks", "assign_task", "todo"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            action_params = {
                "intent": intent,
                "raw_message": params.get("message", ""),
                "priority": params.get("context", {}).get("priority", "medium"),
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("ems", action_params)
            summary = result.get("summary") or result.get("message") or "Task created."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
                actions=[{"label": "View Tasks", "action": "list_tasks"}],
            )
        except Exception as exc:
            logger.warning("TaskCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
