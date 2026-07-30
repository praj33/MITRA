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
    ) -> CompanionResponse:
        """
        Process a user message and return a CompanionResponse.
        """
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

        # 4. Mitra safety gate
        if self._config.safety_gate_enabled:
            blocked, block_reason = await self._safety_check(message, user_id, trace_id)
            if blocked:
                response_text = personality_engine.build_capability_fail(
                    "I can't help with that particular request."
                )
                await session_manager.add_turn(user_id, role="assistant", content=response_text)
                return CompanionResponse(
                    message=response_text,
                    session_id=session.session_id,
                    trace_id=trace_id,
                    intent=intent,
                )

        # 5. Route: capability / knowledge / conversation
        capability_result: Optional[CapabilityResult] = None
        response_text: str

        capability_name = _CAPABILITY_INTENT_MAP.get(intent)
        is_knowledge = self._is_knowledge_query(message, intent)

        if capability_name and capability_name in self._config.enabled_capabilities:
            # ── Capability path ───────────────────────────────────────
            params = {
                "message":   message,
                "entities":  intent_data.get("entities", {}),
                "dates":     intent_data.get("dates_times", {}),
                "context":   intent_data.get("context", {}),
                "user_id":   user_id,
            }
            capability_result = await capability_registry.execute(
                intent=intent, params=params, trace_id=trace_id
            )
            if capability_result and capability_result.status == "success":
                response_text = personality_engine.build_capability_confirm(
                    capability_result.summary
                )
                await companion_memory.log_capability_use(
                    user_id, capability_result.capability, intent, success=True
                )
                await session_manager.touch(user_id, capability=capability_name)
            else:
                err = capability_result.error if capability_result else "Unknown error"
                response_text = personality_engine.build_capability_fail(err)
                if capability_result:
                    await companion_memory.log_capability_use(
                        user_id, capability_result.capability, intent, success=False
                    )

        elif is_knowledge and "uniguru" in self._config.enabled_capabilities:
            # ── UniGuru knowledge path ────────────────────────────────
            response_text = await self._call_knowledge(message, user_id)

        else:
            # ── General conversation path ─────────────────────────────
            response_text = await self._call_conversation(message, user_id)

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
        """General LLM conversation with full context."""
        facts = await companion_memory.get_user_facts(user_id)
        user_name = facts.get("name") or "there"
        system_prompt = personality_engine.build_system_prompt(
            user_name=user_name,
            user_facts=facts,
            enabled_capabilities=self._config.enabled_capabilities,
        )
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
