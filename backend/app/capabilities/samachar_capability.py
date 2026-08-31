"""
samachar_capability.py — Registered Samachar News & Retrieval Capability
Provides structured media & news intelligence retrieval for MITRA.
"""
from __future__ import annotations
import logging
from typing import Any, Dict
from app.capabilities.base_capability import BaseCapability, CapabilityResult
from app.tools.search_tool import SearchTool

logger = logging.getLogger(__name__)

class SamacharCapability(BaseCapability):
    """
    Samachar capability participant contract.
    Retrieves current news, headlines, and structured media context.
    """
    def __init__(self) -> None:
        super().__init__()
        self.search_tool = SearchTool()

    @property
    def name(self) -> str:
        return "samachar"

    @property
    def description(self) -> str:
        return "Retrieves structured news, headlines, articles, and media intelligence."

    @property
    def supported_intents(self) -> list[str]:
        return ["news", "samachar", "headlines", "articles", "press", "media"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: str | None = None) -> CapabilityResult:
        query = params.get("message") or params.get("query") or "latest news"
        user_id = params.get("user_id", "anonymous")
        t_id = trace_id or params.get("trace_id", "trc_unknown")

        logger.info("Executing Samachar capability for query='%s' user_id=%s trace_id=%s", query, user_id, trace_id)

        try:
            raw_result = await self.search_tool.run(query)
            data = {
                "capability": "samachar",
                "version": "1.0.0",
                "query": query,
                "result": raw_result,
                "retrieved_at": self.now_iso(),
            }
            return CapabilityResult.ok(
                data=data,
                message=f"Retrieved news intelligence for '{query}'.",
            )
        except Exception as exc:
            logger.error("Samachar capability failed: %s", exc)
            return CapabilityResult.fail(
                error=f"Samachar retrieval failed: {str(exc)}",
            )
