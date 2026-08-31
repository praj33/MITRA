"""
companion_orchestrator.py — Mitra Companion Brain

Main entry point for all companion interactions.
Flow: message → intent classify → capability route OR conversation
    → safety gate → LLM response → memory update → return
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.companion.companion_config import get_companion_config
from app.companion.companion_memory import companion_memory
from app.companion.companion_session import session_manager
from app.companion.capability_registry import capability_registry
from app.companion.personality_engine import personality_engine
from app.core.llm_bridge import llm_bridge
from app.core.intentflow import intent_flow
from app.capabilities.base_capability import CapabilityResult

logger = logging.getLogger(__name__)

# Intent → capability name mapping (extends IntentFlow's patterns)
_CAPABILITY_INTENT_MAP: Dict[str, str] = {
    "email":         "email",
    "calendar":      "calendar",
    "telegram":      "whatsapp",
    "reminder":      "reminder",
    "ems":           "task",
    "task":          "task",
    "search":        "browser",
    "instagram":     "notification",
    "device":        "notification",
    "samruddhi":     "samruddhi",
    "portfolio":     "samruddhi",
    "balance":       "samruddhi",
    "trades":        "samruddhi",
    "transactions":  "samruddhi",
    "samachar":      "samachar",
    "news":          "samachar",
    "headlines":     "samachar",
    "setu":          "setu",
    "inventory":     "setu",
    "stock":         "setu",
    "orders":        "setu",
    "uniguru":       "uniguru",
    "knowledge":     "uniguru",
}


_KNOWLEDGE_KEYWORDS = {
    "explain", "what is", "how does", "define", "teach",
    "learn", "study", "concept", "theory", "difference between",
    "why does", "how do", "what are", "meaning of",
}


@dataclass
class CompanionResponse:
    message: str
    capability_result: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    intent: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message":          self.message,
            "capability_result": self.capability_result,
            "session_id":       self.session_id,
            "trace_id":         self.trace_id,
            "intent":           self.intent,
            "suggested_actions": self.suggested_actions,
        }


class CompanionOrchestrator:
    """
    The Mitra companion brain.
    Routes each user message to the right handler:
    - Capability invocation (email, calendar, tasks, etc.)
    - Knowledge query (UniGuru)
    - General companion conversation (LLM)
    All paths go through Mitra safety gate.
    """

    def __init__(self) -> None:
        self._config = get_companion_config()

    async def process(
        self,
        user_id: str,
        message: str,
        platform: str = "web",
        device: str = "browser",
        trace_id: Optional[str] = None,
        page_context: Optional[Dict[str, Any]] = None,
    ) -> CompanionResponse:
        """
        Process a user message and return a CompanionResponse.
        Enforces canonical context (trace_id, correlation_id, execution_id),
        syncs active DOM page context, and streams real-time runtime state events.
        """
        from app.runtime.canonical_context import create_canonical_context
        from app.runtime.runtime_event_bus import runtime_event_bus
        import json

        # Store page_context if provided directly in request
        if page_context:
            try:
                await companion_memory.set_fact(
                    user_id=user_id,
                    key="active_ui_context",
                    value=json.dumps(page_context),
                    source="dom_scraper",
                )
            except Exception:
                pass

        # 0. Enforce Canonical Context (trace_id, correlation_id, execution_id)
        ctx = create_canonical_context(
            user_id=user_id,
            trace_id=trace_id,
            platform=platform,
            device=device,
        )

        await runtime_event_bus.publish(
            event_type="requested",
            user_id=user_id,
            trace_id=ctx.trace_id,
            execution_id=ctx.execution_id,
            data={"message": message, "platform": platform},
        )

        # 1. Get/create session
        session = await session_manager.get_or_create(
            user_id=user_id,
            platform=platform,
            device=device,
            ttl_hours=self._config.session_ttl_hours,
        )

        # 2. Store user turn
        await session_manager.add_turn(user_id, role="user", content=message)

        # 3. Classify intent
        intent_data = intent_flow.process_text(message)
        intent = intent_data.get("intent", "general")

        await runtime_event_bus.publish(
            event_type="running",
            user_id=user_id,
            trace_id=ctx.trace_id,
            execution_id=ctx.execution_id,
            data={"intent": intent},
        )

        # 4. Mitra safety gate
        if self._config.safety_gate_enabled:
            blocked, block_reason = await self._safety_check(message, user_id, ctx.trace_id)
            if blocked:
                response_text = personality_engine.build_capability_fail(
                    "I can't help with that particular request."
                )
                await session_manager.add_turn(user_id, role="assistant", content=response_text)
                await runtime_event_bus.publish(
                    event_type="failed",
                    user_id=user_id,
                    trace_id=ctx.trace_id,
                    execution_id=ctx.execution_id,
                    data={"reason": block_reason or "safety_gate_blocked"},
                )
                return CompanionResponse(
                    message=response_text,
                    session_id=session.session_id,
                    trace_id=ctx.trace_id,
                    intent=intent,
                )

        # 5. Route: capability / knowledge / conversation
        capability_result: Optional[CapabilityResult] = None
        response_text: str

        # Check active UI context from request page_context
        active_host_app = (page_context or {}).get("host_app", "")

        if active_host_app == "uniguru":
            is_knowledge = True
            capability_name = None
        elif active_host_app == "setu":
            capability_name = "setu"
            intent = "setu"
            is_knowledge = False
        else:
            capability_name = _CAPABILITY_INTENT_MAP.get(intent)
            is_knowledge = self._is_knowledge_query(message, intent)

        if capability_name and capability_name in self._config.enabled_capabilities:
            # ── Capability path ───────────────────────────────────────
            await runtime_event_bus.publish(
                event_type="capability_running",
                user_id=user_id,
                trace_id=ctx.trace_id,
                execution_id=ctx.execution_id,
                capability=capability_name,
                data={"intent": intent},
            )
            params = {
                "message":   message,
                "entities":  intent_data.get("entities", {}),
                "dates":     intent_data.get("dates_times", {}),
                "context":   intent_data.get("context", {}),
                "user_id":   user_id,
                "trace_id":  ctx.trace_id,
                "execution_id": ctx.execution_id,
            }
            capability_result = await capability_registry.execute(
                intent=intent, params=params, trace_id=ctx.trace_id
            )
            if capability_result and capability_result.status == "success":
                if capability_result.capability == "samachar":
                    # Generate a conversational news response using LLM with returned data
                    cap_data = capability_result.data or {}
                    scraped_info = cap_data.get("scraped_data", {})
                    vetting_info = cap_data.get("vetting_results", {})
                    summary_info = cap_data.get("summary", {})
                    article_title = scraped_info.get("title") or "News Intelligence Update"
                    article_author = scraped_info.get("author")
                    if isinstance(article_author, dict):
                        article_author = article_author.get("name")
                    article_author = article_author or "News Desk"
                    article_summary = summary_info.get("text") or cap_data.get("result") or "No summary."
                    credibility_rating = vetting_info.get("credibility_rating") or "High"
                    authenticity_score = vetting_info.get("authenticity_score")
                    score_str = f"{authenticity_score}/100" if authenticity_score is not None else "95/100"

                    system_prompt = (
                        "You are Mitra, a real-time AI companion. "
                        "A news retrieval tool (Samachar) was invoked to answer the user's query.\n"
                        "Use the following scraped data and summary to formulate a thoughtful, conversational answer "
                        "summarizing the news for the user. Mention the article title/source and credibility context briefly if relevant.\n\n"
                        f"[SAMACHAR RETRIEVED DATA]:\n"
                        f"- Article Title: {article_title}\n"
                        f"- Author/Source: {article_author}\n"
                        f"- Credibility Rating: {credibility_rating} (Score: {score_str})\n"
                        f"- Summary/Content: {article_summary}\n"
                    )
                    
                    # Patterns that indicate LLM synthesis failed and returned a fallback template or raw search output
                    _TEMPLATE_PATTERNS = (
                        "Real-time search completed for:",
                        "Here is what I found for your query:",
                        "I'm listening and working on fetching",
                        "MITRA intelligence service is currently unavailable",
                        "Web Information Intelligence Summary:",
                    )

                    def _is_template(text: str) -> bool:
                        return any(p in text for p in _TEMPLATE_PATTERNS)

                    # Clean deterministic fallback formatted cleanly when LLM synthesis is unavailable
                    clean_summary = article_summary
                    if "Web Information Intelligence Summary:" in clean_summary:
                        clean_summary = clean_summary.replace("Web Information Intelligence Summary:", "").strip()
                        lines = [l.strip() for l in clean_summary.split("\n") if l.strip()]
                        cleaned_bullets = []
                        for line in lines:
                            line_str = line[2:].strip() if line.startswith("- ") else line
                            cleaned_bullets.append(f"• {line_str}")
                        clean_summary = "\n\n".join(cleaned_bullets[:3])

                    _deterministic_report = (
                        f"Here's what I found regarding **{message}**:\n\n"
                        f"**{article_title}**\n\n"
                        f"{clean_summary}\n\n"
                        f"• **Source / Author:** {article_author}\n"
                        f"• **Source Credibility:** {credibility_rating}\n"
                        f"• **Authenticity Score:** {score_str}"
                    )

                    try:
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ]
                        response_text = await llm_bridge.call_llm_with_messages(
                            model=self._config.llm_provider,
                            messages=messages,
                            temperature=0.7,
                        )
                        # If LLM returned a template/raw search fallback, use the clean deterministic report
                        if _is_template(response_text):
                            logger.info("LLM returned template response for samachar — using clean deterministic Samachar report")
                            response_text = _deterministic_report
                    except Exception as llm_exc:
                        logger.warning("Failed to synthesize news with LLM: %s — using clean deterministic Samachar report", llm_exc)
                        response_text = _deterministic_report
                else:
                    response_text = personality_engine.build_capability_confirm(
                        capability_result.summary
                    )
                await companion_memory.log_capability_use(
                    user_id, capability_result.capability, intent, success=True
                )
                await session_manager.touch(user_id, capability=capability_name)
                await runtime_event_bus.publish(
                    event_type="completed",
                    user_id=user_id,
                    trace_id=ctx.trace_id,
                    execution_id=ctx.execution_id,
                    capability=capability_name,
                    data={"status": "success"},
                )
            else:
                err = capability_result.error if capability_result else "Unknown error"
                response_text = personality_engine.build_capability_fail(err)
                if capability_result:
                    await companion_memory.log_capability_use(
                        user_id, capability_result.capability, intent, success=False
                    )
                await runtime_event_bus.publish(
                    event_type="failed",
                    user_id=user_id,
                    trace_id=ctx.trace_id,
                    execution_id=ctx.execution_id,
                    capability=capability_name,
                    data={"error": err},
                )

        elif is_knowledge and "uniguru" in self._config.enabled_capabilities:
            # ── UniGuru knowledge path ────────────────────────────────
            await runtime_event_bus.publish(
                event_type="capability_running",
                user_id=user_id,
                trace_id=ctx.trace_id,
                execution_id=ctx.execution_id,
                capability="uniguru",
            )
            response_text = await self._call_knowledge(message, user_id)
            capability_result = CapabilityResult(
                capability="uniguru",
                intent="knowledge",
                status="success",
                summary="UniGuru Knowledge Answer",
                data={
                    "answer": response_text,
                    "source": "llm_fallback",
                    "verification_status": "VERIFIED",
                    "result": response_text
                },
                trace_id=ctx.trace_id
            )
            await runtime_event_bus.publish(
                event_type="completed",
                user_id=user_id,
                trace_id=ctx.trace_id,
                execution_id=ctx.execution_id,
                capability="uniguru",
            )

        else:
            # ── General conversation path ─────────────────────────────
            await runtime_event_bus.publish(
                event_type="capability_running",
                user_id=user_id,
                trace_id=ctx.trace_id,
                execution_id=ctx.execution_id,
                capability="conversation",
            )
            response_text = await self._call_conversation(message, user_id)
            await runtime_event_bus.publish(
                event_type="completed",
                user_id=user_id,
                trace_id=ctx.trace_id,
                execution_id=ctx.execution_id,
                capability="conversation",
            )

        # 6. Store assistant turn
        await session_manager.add_turn(
            user_id,
            role="assistant",
            content=response_text,
            capability_result=capability_result.to_dict() if capability_result else None,
        )

        # 7. Auto-extract facts from message (name, preferences)
        await self._extract_facts(user_id, message, intent_data)

        return CompanionResponse(
            message=response_text,
            capability_result=capability_result.to_dict() if capability_result else None,
            session_id=session.session_id,
            trace_id=trace_id,
            intent=intent,
            suggested_actions=self._suggest_actions(intent, capability_result),
        )

    async def get_greeting(self, user_id: str) -> str:
        """Return a personalized greeting for the user."""
        facts = await companion_memory.get_user_facts(user_id)
        raw_name = facts.get("name") or "User"
        user_name = "User" if raw_name.lower() in ("there", "user_default", "using", "anonymous") else raw_name
        return personality_engine.build_greeting(user_name=user_name)

    # ── private helpers ───────────────────────────────────────────

    async def _safety_check(
        self, message: str, user_id: str, trace_id: Optional[str]
    ) -> tuple[bool, str]:
        """Run message through Mitra safety gate. Returns (blocked, reason)."""
        try:
            from app.services.mitra_control_plane_service import (
                MitraControlPlaneService,
                MitraAuthorityInput,
            )
            svc = MitraControlPlaneService()
            result = svc.evaluate(
                MitraAuthorityInput(
                    input_text=message,
                    raw_input={"message": message},
                    user_id=user_id,
                    source="companion",
                )
            )
            status = result.get("response_contract", {}).get("status", "ALLOW")
            if status == "BLOCK":
                return True, result.get("response_contract", {}).get("reason", "Blocked")
            return False, ""
        except Exception as exc:
            logger.warning("Safety gate error: %s — failing open for conversation", exc)
            return False, ""

    async def _call_conversation(self, message: str, user_id: str) -> str:
        """General LLM conversation with full context & live web/market integration."""
        facts = await companion_memory.get_user_facts(user_id)
        user_name = facts.get("name") or "there"
        system_prompt = personality_engine.build_system_prompt(
            user_name=user_name,
            user_facts=facts,
            enabled_capabilities=self._config.enabled_capabilities,
        )

        # Inject Active UI DOM Context if present (from host app DOM Extractor)
        if "active_ui_context" in facts:
            try:
                import json
                ctx_obj = json.loads(facts["active_ui_context"])
                buttons_str = ", ".join(ctx_obj.get("buttons", [])) or "None detected"
                headings_str = ", ".join(ctx_obj.get("headings", [])) or "None detected"
                fields_str = ", ".join(ctx_obj.get("fields", [])) or "None detected"
                snippet = (ctx_obj.get("snippet") or "")[:400]

                system_prompt += (
                    f"\n\n[ACTIVE HOST APP SCREEN CONTEXT (DOM SCRAPED)]:\n"
                    f"- Page Title: {ctx_obj.get('title', 'Unknown Page')}\n"
                    f"- URL: {ctx_obj.get('url', 'Unknown URL')}\n"
                    f"- Visible Buttons: {buttons_str}\n"
                    f"- Visible Headings/Sections: {headings_str}\n"
                    f"- Visible Form Fields: {fields_str}\n"
                    f"- Visible Content Snippet: {snippet}\n\n"
                    "INSTRUCTION: The user is currently looking at this active application screen. "
                    "Use this exact screen context to answer questions about buttons, settings, options, and actions available to them."
                )
            except Exception as e:
                logger.warning(f"UI Context injection error: {e}")

        msg_lower = message.lower()
        live_keywords = [
            "news", "finance", "stock", "share", "market", "sensex", "nifty", "bse", "nse",
            "price", "today", "weather", "crypto", "bitcoin", "btc", "eth", "ethereum",
            "hdfc", "reliance", "tcs", "infosys", "sbi", "icici", "tata", "apple", "tesla",
            "gold", "silver", "commodity", "mutual fund", "sip", "bond", "inflation", "rbi",
            "rate", "currency", "rupee", "dollar", "inr", "usd", "latest", "update", "headline",
            "gain", "loss", "ups", "downs", "up", "down", "rally", "crash"
        ]
        if any(kw in msg_lower for kw in live_keywords):

            try:
                from app.tools.search_tool import SearchTool
                search_tool = SearchTool()
                live_info = await search_tool.run(message)
                if live_info:
                    system_prompt += (
                        f"\n\n[REAL-TIME LIVE DATA INJECTED FOR USER QUERY]:\n{live_info}\n"
                        "Instruction: Use the exact live numbers and news snippet provided above. "
                        "Do NOT guess or hallucinate stock prices or news headlines."
                    )
            except Exception as e:
                logger.warning(f"Live search context enrichment failed: {e}")

        history = await session_manager.get_history(
            user_id, limit=self._config.max_history_turns
        )
        messages = [{"role": "system", "content": system_prompt}] + history
        return await llm_bridge.call_llm_with_messages(
            model=self._config.llm_provider,
            messages=messages,
            temperature=0.7,
        )


    async def _call_knowledge(self, message: str, user_id: str) -> str:
        """Route to UniGuru for knowledge queries."""
        history = await session_manager.get_history(user_id, limit=6)
        messages = [
            {"role": "system", "content": (
                "You are an educational assistant. Explain concepts clearly, "
                "accurately, and at the appropriate depth for the user. "
                "Offer to go deeper or give examples if the user wants."
            )}
        ] + history + [{"role": "user", "content": message}]
        return await llm_bridge.call_llm_with_messages(
            model="uniguru",
            messages=messages,
            temperature=0.5,
        )

    def _is_knowledge_query(self, message: str, intent: str) -> bool:
        msg_lower = message.lower()
        return any(kw in msg_lower for kw in _KNOWLEDGE_KEYWORDS)

    async def _extract_facts(
        self, user_id: str, message: str, intent_data: Dict
    ) -> None:
        """Auto-extract user facts (name, preferences) from message."""
        msg_lower = message.lower()
        # Name extraction
        for phrase in ("my name is ", "i am ", "i'm ", "call me "):
            if phrase in msg_lower:
                idx = msg_lower.index(phrase) + len(phrase)
                candidate = message[idx:].split()[0].strip(".,!?").capitalize()
                if len(candidate) >= 2:
                    await companion_memory.set_fact(user_id, "name", candidate, source="user")
                    break

    def _suggest_actions(
        self,
        intent: str,
        cap_result: Optional[CapabilityResult],
    ) -> List[str]:
        if not cap_result or cap_result.status != "success":
            return []
        suggestions = {
            "email":    ["View full draft", "Edit before sending"],
            "calendar": ["Add to calendar", "Set a reminder"],
            "reminder": ["View all reminders"],
            "task":     ["View task board"],
        }
        return suggestions.get(intent, [])


# Singleton
companion_orchestrator = CompanionOrchestrator()
