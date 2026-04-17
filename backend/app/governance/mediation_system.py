"""
Inbound & Outbound Mediation System (Embedded in Mitra)
Validates all content before UI render or execution.
Enforces quiet hours, contact limits, and emotional escalation rules.
"""

import hashlib
import json
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict


class MediationDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REWRITE = "rewrite"
    DELAY = "delay"


@dataclass
class InboundMessage:
    content: str
    sender: str
    recipient: str
    platform: str
    timestamp: str
    message_type: str = "general"


@dataclass
class OutboundAction:
    content: str
    recipient: str
    platform: str
    action_type: str
    timestamp: str
    urgency_level: str = "low"


@dataclass
class MediationResult:
    decision: MediationDecision
    reason: str
    trace_id: str
    safety_flags: List[str]
    rewritten_content: Optional[str] = None
    delay_until: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "safety_flags": self.safety_flags,
            "rewritten_content": self.rewritten_content,
            "delay_until": self.delay_until,
            "timestamp": self.timestamp,
        }


class MediationSystem:
    """Complete inbound/outbound mediation with enforcement rules"""

    def __init__(self):
        # Contact tracking for repeat limits
        self.contact_counts = {}  # {(sender, recipient, date): count}
        self.platform_limits = {
            "whatsapp": 5,
            "email": 3,
            "instagram": 2,
            "sms": 4,
        }

        # Quiet hours enforcement
        self.quiet_start = time(22, 0)  # 10 PM
        self.quiet_end = time(7, 0)     # 7 AM

        # Emotional escalation patterns
        self.manipulation_patterns = [
            "you have to", "if you don't", "last chance", "only you",
            "everyone else", "don't ignore", "really need you", "you must",
        ]

        self.escalation_patterns = [
            "getting angry", "fed up", "tired of waiting", "final warning",
            "won't ask again", "this is it", "had enough",
        ]

        # Trace ID continuity
        self.trace_counter = 1000

    def generate_trace_id(self, content: str, direction: str) -> str:
        self.trace_counter += 1
        trace_input = f"{content}:{direction}:{self.trace_counter}"
        return f"med_{hashlib.md5(trace_input.encode()).hexdigest()[:12]}"

    def is_quiet_hours(self, timestamp: str) -> bool:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            current_time = dt.time()
            return current_time >= self.quiet_start or current_time <= self.quiet_end
        except Exception:
            return False

    def get_contact_count(self, sender: str, recipient: str, date: str) -> int:
        key = (sender, recipient, date)
        return self.contact_counts.get(key, 0)

    def increment_contact_count(self, sender: str, recipient: str, date: str) -> int:
        key = (sender, recipient, date)
        current = self.contact_counts.get(key, 0)
        self.contact_counts[key] = current + 1
        return current + 1

    def detect_manipulation(self, content: str) -> Tuple[int, List[str]]:
        content_lower = content.lower()
        flags = []
        score = 0

        for pattern in self.manipulation_patterns:
            if pattern in content_lower:
                flags.append(f"manipulation_{pattern.replace(' ', '_')}")
                score += 2

        for pattern in self.escalation_patterns:
            if pattern in content_lower:
                flags.append(f"escalation_{pattern.replace(' ', '_')}")
                score += 3

        threat_words = ["hurt", "regret", "sorry", "pay", "consequences"]
        for word in threat_words:
            if word in content_lower and any(bad in content_lower for bad in ["you'll", "make you", "i'll make"]):
                flags.append(f"threat_{word}")
                score += 4

        return score, flags

    def validate_inbound(self, message: InboundMessage) -> MediationResult:
        """Validate inbound message before UI render"""
        timestamp = datetime.now().isoformat() + "Z"
        trace_id = self.generate_trace_id(message.content, "inbound")

        manipulation_score, safety_flags = self.detect_manipulation(message.content)

        date = message.timestamp[:10]
        contact_count = self.get_contact_count(message.sender, message.recipient, date)
        platform_limit = self.platform_limits.get(message.platform.lower(), 3)

        if contact_count >= platform_limit:
            safety_flags.append("contact_limit_exceeded")
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason=f"Daily contact limit exceeded ({contact_count}/{platform_limit})",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp,
            )

        if manipulation_score >= 6:
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason="Severe emotional manipulation or threats detected",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp,
            )

        elif manipulation_score >= 3:
            safe_summary = self._generate_safe_summary(message.content)
            return MediationResult(
                decision=MediationDecision.REWRITE,
                reason="Emotional manipulation detected - safe summary generated",
                trace_id=trace_id,
                safety_flags=safety_flags,
                rewritten_content=safe_summary,
                timestamp=timestamp,
            )

        elif self.is_quiet_hours(message.timestamp) and message.message_type != "emergency":
            delay_until = message.timestamp[:10] + "T07:00:00Z"
            return MediationResult(
                decision=MediationDecision.DELAY,
                reason="Quiet hours - message delayed until morning",
                trace_id=trace_id,
                safety_flags=["quiet_hours"],
                delay_until=delay_until,
                timestamp=timestamp,
            )

        else:
            self.increment_contact_count(message.sender, message.recipient, date)
            return MediationResult(
                decision=MediationDecision.ALLOW,
                reason="Message passes all safety checks",
                trace_id=trace_id,
                safety_flags=[],
                timestamp=timestamp,
            )

    def validate_outbound(self, action: OutboundAction) -> MediationResult:
        """Validate outbound action before execution"""
        timestamp = datetime.now().isoformat() + "Z"
        trace_id = self.generate_trace_id(action.content, "outbound")

        manipulation_score, safety_flags = self.detect_manipulation(action.content)

        date = action.timestamp[:10]
        contact_count = self.get_contact_count("assistant", action.recipient, date)
        platform_limit = self.platform_limits.get(action.platform.lower(), 3)

        if contact_count >= platform_limit:
            safety_flags.append("outbound_limit_exceeded")
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason=f"Daily outbound limit exceeded ({contact_count}/{platform_limit})",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp,
            )

        if manipulation_score >= 4:
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason="Outbound content contains manipulation patterns",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp,
            )

        elif manipulation_score >= 2:
            safe_content = self._generate_safe_rewrite(action.content)
            return MediationResult(
                decision=MediationDecision.REWRITE,
                reason="Minor manipulation detected - content rewritten",
                trace_id=trace_id,
                safety_flags=safety_flags,
                rewritten_content=safe_content,
                timestamp=timestamp,
            )

        elif self.is_quiet_hours(action.timestamp) and action.urgency_level != "critical":
            delay_until = action.timestamp[:10] + "T07:00:00Z"
            return MediationResult(
                decision=MediationDecision.DELAY,
                reason="Quiet hours - action delayed until morning",
                trace_id=trace_id,
                safety_flags=["quiet_hours"],
                delay_until=delay_until,
                timestamp=timestamp,
            )

        else:
            self.increment_contact_count("assistant", action.recipient, date)
            return MediationResult(
                decision=MediationDecision.ALLOW,
                reason="Action passes all safety checks",
                trace_id=trace_id,
                safety_flags=[],
                timestamp=timestamp,
            )

    def _generate_safe_summary(self, content: str) -> str:
        if any(word in content.lower() for word in ["hurt", "kill", "die", "suicide"]):
            return "Message expressing distress received. Crisis support resources available."
        elif any(pattern in content.lower() for pattern in self.manipulation_patterns):
            return "Message requesting communication response received."
        else:
            return "Personal message received."

    def _generate_safe_rewrite(self, content: str) -> str:
        safe_content = content
        replacements = {
            "you have to": "please consider",
            "you must": "you might want to",
            "if you don't": "if you choose not to",
            "last chance": "opportunity",
            "really need you": "would appreciate your help",
        }
        for manipulative, safe in replacements.items():
            safe_content = safe_content.replace(manipulative, safe)
            safe_content = safe_content.replace(manipulative.title(), safe.title())
        return safe_content
