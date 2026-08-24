"""
browser_capability.py — Mitra Browser / Web Search Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

class BrowserCapability(BaseCapability):
    @property
    def name(self) -> str: return "browser"
    @property
    def description(self) -> str: return "Search the web and summarize pages."
    @property
    def supported_intents(self) -> List[str]:
        return ["search", "browser", "search_web", "open_url", "summarize_page", "web_search"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            action_params = {
                "intent": intent,
                "query": params.get("message", ""),
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("search", action_params)
            summary = result.get("summary") or result.get("message") or "Search completed."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
            )
        except Exception as exc:
            logger.warning("BrowserCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
