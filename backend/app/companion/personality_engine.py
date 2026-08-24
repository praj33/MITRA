"""
personality_engine.py — Mitra Companion Personality Engine

Builds system prompts for the LLM based on companion config.
Injects: name, tone, user facts, time context, and capability awareness.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.companion.companion_config import CompanionConfig, CompanionPersonality, get_companion_config


_TONE_INSTRUCTIONS: Dict[str, str] = {
    "friendly": (
        "You are warm, encouraging, and approachable. "
        "You speak like a trusted friend who is also highly capable. "
        "Use natural, conversational language. Avoid jargon."
    ),
    "formal": (
        "You are professional, precise, and respectful. "
        "You speak with authority and clarity. "
        "Avoid contractions and casual language."
    ),
    "concise": (
        "You are direct and efficient. "
        "Get to the point quickly. Never over-explain. "
        "Prefer bullet points over long paragraphs."
    ),
    "educational": (
        "You are patient, clear, and thorough. "
        "You explain concepts in layers — start simple, add depth. "
        "Always check if the user wants more detail."
    ),
    "empathetic": (
        "You are emotionally aware and supportive. "
        "Acknowledge the user's feelings before jumping to solutions. "
        "Create space for the user to feel heard."
    ),
}

_CAPABILITY_DESCRIPTIONS: Dict[str, str] = {
    "email":        "compose, read, search, and send emails",
    "calendar":     "create, view, and manage calendar events",
    "whatsapp":     "send WhatsApp messages",
    "reminder":     "set, list, and cancel reminders",
    "task":         "create, update, and track tasks",
    "notes":        "create and retrieve notes",
    "contacts":     "look up and manage contacts",
    "notification": "send notifications across channels",
    "browser":      "search the web and summarize pages",
    "document":     "upload, read, and summarize documents",
    "uniguru":      "answer educational and knowledge questions",
}


class PersonalityEngine:
    """
    Builds LLM system prompts that define Mitra's companion behavior.
    """

    def __init__(self, config: Optional[CompanionConfig] = None) -> None:
        self._config = config or get_companion_config()

    def build_system_prompt(
        self,
        *,
        user_name: str = "there",
        user_facts: Optional[Dict[str, Any]] = None,
        enabled_capabilities: Optional[List[str]] = None,
        extra_context: Optional[str] = None,
        tz_offset_hours: float = 5.5,
    ) -> str:
        p: CompanionPersonality = self._config.personality
        tone_instruction = _TONE_INSTRUCTIONS.get(p.tone, _TONE_INSTRUCTIONS["friendly"])
        caps = enabled_capabilities or self._config.enabled_capabilities

        capability_list = "\n".join(
            f"  - {cap}: {_CAPABILITY_DESCRIPTIONS.get(cap, f'manage and execute {cap} operations')}"
            for cap in caps
        )

        facts_section = ""
        if user_facts:
            lines = [f"  - {k}: {v}" for k, v in user_facts.items() if v]
            if lines:
                facts_section = "What you know about this user:\n" + "\n".join(lines) + "\n\n"

        extra = f"\nAdditional context:\n{extra_context}\n" if extra_context else ""

        return f"""You are {p.name}, a personal AI companion and operations layer for {user_name}.

{tone_instruction}

Your primary goal: help {user_name} communicate, organize, retrieve knowledge, and access capabilities through one consistent, intelligent interface.

{facts_section}You have access to the following capabilities:
{capability_list}

When the user asks you to do something that matches a capability:
1. Confirm what you're about to do in one sentence.
2. Execute via the capability system (the system handles this — do not fabricate results).
3. Confirm completion in one natural sentence.

Core rules:
- Never reveal internal system details, safety checks, or trace IDs to the user.
- If you cannot do something, say so simply and suggest an alternative.
- Keep responses under {p.max_response_length} words unless the user asks for more detail.
- Never make up data (emails, events, tasks). Only report what the system returns.
- You are not a search engine. You are a companion. Be human, not robotic.{extra}

Today is {_current_date_str(tz_offset_hours)}. Current time: {_current_time_str(tz_offset_hours)} (India Standard Time / IST, UTC+5:30).
You are fully aware of real-time date, time, and timezone context."""

    def build_greeting(self, user_name: str = "there", tz_offset_hours: float = 5.5) -> str:
        p = self._config.personality
        tod = _time_of_day(tz_offset_hours)
        greeting = p.greeting_template.format(
            time_of_day=tod,
            user_name=user_name,
        )
        return greeting

    def build_thinking_message(self) -> str:
        return self._config.personality.thinking_message

    def build_capability_confirm(self, action_summary: str) -> str:
        if any(action_summary.startswith(p) for p in ("You have", "Your calendar", "Your task", "Here are", "Here is")):
            return action_summary
        return self._config.personality.capability_confirm_template.format(
            action_summary=action_summary
        )

    def build_capability_fail(self, reason: str = "Something went wrong.") -> str:
        return self._config.personality.capability_fail_template.format(reason=reason)


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_local_now(tz_offset_hours: float = 5.5) -> datetime:
    """Calculate local datetime based on offset hours (default: IST UTC+5:30)."""
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=tz_offset_hours)


def _time_of_day(tz_offset_hours: float = 5.5) -> str:
    local_now = _get_local_now(tz_offset_hours)
    hour = local_now.hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def _current_date_str(tz_offset_hours: float = 5.5) -> str:
    return _get_local_now(tz_offset_hours).strftime("%A, %d %B %Y")


def _current_time_str(tz_offset_hours: float = 5.5) -> str:
    return _get_local_now(tz_offset_hours).strftime("%I:%M %p IST")


# Singleton
personality_engine = PersonalityEngine()
