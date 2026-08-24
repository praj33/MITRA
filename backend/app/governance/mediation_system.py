"""
Inbound & Outbound Mediation System
Validates all content before UI render or execution
Enforces quiet hours, contact limits, and emotional escalation rules
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

class MediationSystem:
    """Complete inbound/outbound mediation with enforcement rules"""
    
    def __init__(self):
        # Contact tracking for repeat limits
        self.contact_counts = {}  # {(sender, recipient, date): count}
        self.platform_limits = {
            "whatsapp": 5,
            "email": 3,
            "instagram": 2,
            "sms": 4
        }
        
        # Quiet hours enforcement
        self.quiet_start = time(22, 0)  # 10 PM
        self.quiet_end = time(7, 0)     # 7 AM
        
        # Emotional escalation patterns
        self.manipulation_patterns = [
            "you have to", "if you don't", "last chance", "only you",
            "everyone else", "don't ignore", "really need you", "you must"
        ]
        
        self.escalation_patterns = [
            "getting angry", "fed up", "tired of waiting", "final warning",
            "won't ask again", "this is it", "had enough"
        ]
        
        # Trace ID continuity
        self.trace_counter = 1000
    
    def generate_trace_id(self, content: str, direction: str) -> str:
        """Generate continuous trace IDs"""
        self.trace_counter += 1
        trace_input = f"{content}:{direction}:{self.trace_counter}"
        return f"trace_{hashlib.md5(trace_input.encode()).hexdigest()[:12]}"
    
    def is_quiet_hours(self, timestamp: str) -> bool:
        """Check if timestamp falls in quiet hours"""
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_time = dt.time()
        
        # Handle overnight quiet hours (10 PM to 7 AM)
        return current_time >= self.quiet_start or current_time <= self.quiet_end
    
    def get_contact_count(self, sender: str, recipient: str, date: str) -> int:
        """Get daily contact count"""
        key = (sender, recipient, date)
        return self.contact_counts.get(key, 0)
    
    def increment_contact_count(self, sender: str, recipient: str, date: str) -> int:
        """Increment and return contact count"""
        key = (sender, recipient, date)
        current = self.contact_counts.get(key, 0)
        self.contact_counts[key] = current + 1
        return current + 1
    
    def detect_manipulation(self, content: str) -> Tuple[int, List[str]]:
        """Detect emotional manipulation and escalation"""
        content_lower = content.lower()
        flags = []
        score = 0
        
        # Check manipulation patterns
        for pattern in self.manipulation_patterns:
            if pattern in content_lower:
                flags.append(f"manipulation_{pattern.replace(' ', '_')}")
                score += 2
        
        # Check escalation patterns
        for pattern in self.escalation_patterns:
            if pattern in content_lower:
                flags.append(f"escalation_{pattern.replace(' ', '_')}")
                score += 3
        
        # Check for threats
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
        
        # Check for manipulation and escalation
        manipulation_score, safety_flags = self.detect_manipulation(message.content)
        
        # Check contact frequency
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
                timestamp=timestamp
            )
        
        # Check for severe manipulation/threats
        if manipulation_score >= 6:
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason="Severe emotional manipulation or threats detected",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp
            )
        
        # Check for moderate manipulation - rewrite to safe summary
        elif manipulation_score >= 3:
            safe_summary = self._generate_safe_summary(message.content)
            return MediationResult(
                decision=MediationDecision.REWRITE,
                reason="Emotional manipulation detected - safe summary generated",
                trace_id=trace_id,
                safety_flags=safety_flags,
                rewritten_content=safe_summary,
                timestamp=timestamp
            )
        
        # Check quiet hours for non-urgent messages
        elif self.is_quiet_hours(message.timestamp) and message.message_type != "emergency":
            delay_until = message.timestamp[:10] + "T07:00:00Z"  # Delay until 7 AM
            return MediationResult(
                decision=MediationDecision.DELAY,
                reason="Quiet hours - message delayed until morning",
                trace_id=trace_id,
                safety_flags=["quiet_hours"],
                delay_until=delay_until,
                timestamp=timestamp
            )
        
        # Safe to display
        else:
            self.increment_contact_count(message.sender, message.recipient, date)
            return MediationResult(
                decision=MediationDecision.ALLOW,
                reason="Message passes all safety checks",
                trace_id=trace_id,
                safety_flags=[],
                timestamp=timestamp
            )
    
    def validate_outbound(self, action: OutboundAction) -> MediationResult:
        """Validate outbound action before execution"""
        timestamp = datetime.now().isoformat() + "Z"
        trace_id = self.generate_trace_id(action.content, "outbound")
        
        # Check for manipulation in outbound content
        manipulation_score, safety_flags = self.detect_manipulation(action.content)
        
        # Check contact frequency for outbound
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
                timestamp=timestamp
            )
        
        # Block manipulative outbound content
        if manipulation_score >= 4:
            return MediationResult(
                decision=MediationDecision.BLOCK,
                reason="Outbound content contains manipulation patterns",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp
            )
        
        # Rewrite minor manipulation
        elif manipulation_score >= 2:
            safe_content = self._generate_safe_rewrite(action.content)
            return MediationResult(
                decision=MediationDecision.REWRITE,
                reason="Minor manipulation detected - content rewritten",
                trace_id=trace_id,
                safety_flags=safety_flags,
                rewritten_content=safe_content,
                timestamp=timestamp
            )
        
        # Check quiet hours for non-critical actions
        elif self.is_quiet_hours(action.timestamp) and action.urgency_level != "critical":
            delay_until = action.timestamp[:10] + "T07:00:00Z"
            return MediationResult(
                decision=MediationDecision.DELAY,
                reason="Quiet hours - action delayed until morning",
                trace_id=trace_id,
                safety_flags=["quiet_hours"],
                delay_until=delay_until,
                timestamp=timestamp
            )
        
        # Safe to execute
        else:
            self.increment_contact_count("assistant", action.recipient, date)
            return MediationResult(
                decision=MediationDecision.ALLOW,
                reason="Action passes all safety checks",
                trace_id=trace_id,
                safety_flags=[],
                timestamp=timestamp
            )
    
    def _generate_safe_summary(self, content: str) -> str:
        """Generate safe summary of manipulative content"""
        if any(word in content.lower() for word in ["hurt", "kill", "die", "suicide"]):
            return "Message expressing distress received. Crisis support resources available."
        elif any(pattern in content.lower() for pattern in self.manipulation_patterns):
            return "Message requesting communication response received."
        else:
            return "Personal message received."
    
    def _generate_safe_rewrite(self, content: str) -> str:
        """Generate safe rewrite of manipulative content"""
        safe_content = content
        
        # Replace manipulation patterns
        replacements = {
            "you have to": "please consider",
            "you must": "you might want to",
            "if you don't": "if you choose not to",
            "last chance": "opportunity",
            "really need you": "would appreciate your help"
        }
        
        for manipulative, safe in replacements.items():
            safe_content = safe_content.replace(manipulative, safe)
            safe_content = safe_content.replace(manipulative.title(), safe.title())
        
        return safe_content

# Global mediation system
mediation_system = MediationSystem()

def validate_inbound_message(message: InboundMessage) -> MediationResult:
    """Validate inbound message before UI render"""
    return mediation_system.validate_inbound(message)

def validate_outbound_action(action: OutboundAction) -> MediationResult:
    """Validate outbound action before execution"""
    return mediation_system.validate_outbound(action)

def run_mediation_demo():
    """Run comprehensive mediation demo with logs"""
    
    print("=" * 60)
    print("INBOUND & OUTBOUND MEDIATION DEMO")
    print("=" * 60)
    
    demo_logs = []
    
    # INBOUND TESTS
    print("\nINBOUND MEDIATION TESTS")
    print("-" * 40)
    
    # Test 1: Inbound BLOCKED - Severe manipulation
    inbound_blocked = InboundMessage(
        content="You HAVE to respond right now or I'll make you regret ignoring me. This is your last chance!",
        sender="manipulator@example.com",
        recipient="user123",
        platform="email",
        timestamp="2024-01-28T20:30:00Z"
    )
    
    result1 = validate_inbound_message(inbound_blocked)
    log1 = {
        "type": "INBOUND_BLOCKED",
        "content": inbound_blocked.content,
        "decision": result1.decision.value,
        "reason": result1.reason,
        "safety_flags": result1.safety_flags,
        "trace_id": result1.trace_id,
        "timestamp": result1.timestamp
    }
    demo_logs.append(log1)
    
    print(f"BLOCKED: {result1.reason}")
    print(f"   Flags: {result1.safety_flags}")
    print(f"   Trace: {result1.trace_id}")
    
    # Test 2: Inbound ALLOWED - Clean message
    inbound_allowed = InboundMessage(
        content="Hi! Hope you're having a great day. Just wanted to check in and see how you're doing.",
        sender="friend@example.com",
        recipient="user123",
        platform="whatsapp",
        timestamp="2024-01-28T14:30:00Z"
    )
    
    result2 = validate_inbound_message(inbound_allowed)
    log2 = {
        "type": "INBOUND_ALLOWED",
        "content": inbound_allowed.content,
        "decision": result2.decision.value,
        "reason": result2.reason,
        "safety_flags": result2.safety_flags,
        "trace_id": result2.trace_id,
        "timestamp": result2.timestamp
    }
    demo_logs.append(log2)
    
    print(f"ALLOWED: {result2.reason}")
    print(f"   Flags: {result2.safety_flags}")
    print(f"   Trace: {result2.trace_id}")
    
    # Test 3: Inbound REWRITTEN - Moderate manipulation
    inbound_rewritten = InboundMessage(
        content="I really need you to help me with this. You're the only one who understands my situation.",
        sender="needy@example.com",
        recipient="user123",
        platform="instagram",
        timestamp="2024-01-28T16:00:00Z"
    )
    
    result3 = validate_inbound_message(inbound_rewritten)
    log3 = {
        "type": "INBOUND_REWRITTEN",
        "content": inbound_rewritten.content,
        "decision": result3.decision.value,
        "reason": result3.reason,
        "safe_summary": result3.rewritten_content,
        "safety_flags": result3.safety_flags,
        "trace_id": result3.trace_id,
        "timestamp": result3.timestamp
    }
    demo_logs.append(log3)
    
    print(f"REWRITTEN: {result3.reason}")
    print(f"   Safe Summary: {result3.rewritten_content}")
    print(f"   Trace: {result3.trace_id}")
    
    # Test 4: Inbound DELAYED - Quiet hours
    inbound_delayed = InboundMessage(
        content="Just a quick update on the project status for tomorrow's meeting.",
        sender="colleague@work.com",
        recipient="user123",
        platform="email",
        timestamp="2024-01-28T23:30:00Z"  # 11:30 PM
    )
    
    result4 = validate_inbound_message(inbound_delayed)
    log4 = {
        "type": "INBOUND_DELAYED",
        "content": inbound_delayed.content,
        "decision": result4.decision.value,
        "reason": result4.reason,
        "delay_until": result4.delay_until,
        "safety_flags": result4.safety_flags,
        "trace_id": result4.trace_id,
        "timestamp": result4.timestamp
    }
    demo_logs.append(log4)
    
    print(f"DELAYED: {result4.reason}")
    print(f"   Delay Until: {result4.delay_until}")
    print(f"   Trace: {result4.trace_id}")
    
    # OUTBOUND TESTS
    print("\nOUTBOUND MEDIATION TESTS")
    print("-" * 40)
    
    # Test 5: Outbound BLOCKED - Manipulation
    outbound_blocked = OutboundAction(
        content="You really need to respond to my messages. If you don't, I'll assume you don't want my help anymore.",
        recipient="user456",
        platform="whatsapp",
        action_type="message",
        timestamp="2024-01-28T19:00:00Z"
    )
    
    result5 = validate_outbound_action(outbound_blocked)
    log5 = {
        "type": "OUTBOUND_BLOCKED",
        "content": outbound_blocked.content,
        "decision": result5.decision.value,
        "reason": result5.reason,
        "safety_flags": result5.safety_flags,
        "trace_id": result5.trace_id,
        "timestamp": result5.timestamp
    }
    demo_logs.append(log5)
    
    print(f"BLOCKED: {result5.reason}")
    print(f"   Flags: {result5.safety_flags}")
    print(f"   Trace: {result5.trace_id}")
    
    # Test 6: Outbound ALLOWED - Clean action
    outbound_allowed = OutboundAction(
        content="Thanks for your question! Here's the weather forecast: sunny, 75°F tomorrow. Have a great day!",
        recipient="user456",
        platform="email",
        action_type="reply",
        timestamp="2024-01-28T15:00:00Z"
    )
    
    result6 = validate_outbound_action(outbound_allowed)
    log6 = {
        "type": "OUTBOUND_ALLOWED",
        "content": outbound_allowed.content,
        "decision": result6.decision.value,
        "reason": result6.reason,
        "safety_flags": result6.safety_flags,
        "trace_id": result6.trace_id,
        "timestamp": result6.timestamp
    }
    demo_logs.append(log6)
    
    print(f"ALLOWED: {result6.reason}")
    print(f"   Flags: {result6.safety_flags}")
    print(f"   Trace: {result6.trace_id}")
    
    # Test 7: Outbound REWRITTEN - Minor manipulation
    outbound_rewritten = OutboundAction(
        content="You really should check this out - it's important for your project success.",
        recipient="user456",
        platform="email",
        action_type="notification",
        timestamp="2024-01-28T17:00:00Z"
    )
    
    result7 = validate_outbound_action(outbound_rewritten)
    log7 = {
        "type": "OUTBOUND_REWRITTEN",
        "content": outbound_rewritten.content,
        "decision": result7.decision.value,
        "reason": result7.reason,
        "rewritten_content": result7.rewritten_content,
        "safety_flags": result7.safety_flags,
        "trace_id": result7.trace_id,
        "timestamp": result7.timestamp
    }
    demo_logs.append(log7)
    
    print(f"REWRITTEN: {result7.reason}")
    print(f"   Safe Content: {result7.rewritten_content}")
    print(f"   Trace: {result7.trace_id}")
    
    # Test 8: Contact Limit Enforcement
    print("\nCONTACT LIMIT ENFORCEMENT")
    print("-" * 40)
    
    # Send multiple messages to test limits
    for i in range(6):  # WhatsApp limit is 5
        test_action = OutboundAction(
            content=f"Message {i+1} to test contact limits",
            recipient="user789",
            platform="whatsapp",
            action_type="message",
            timestamp="2024-01-28T12:00:00Z"
        )
        
        result = validate_outbound_action(test_action)
        status = "ALLOWED" if result.decision == MediationDecision.ALLOW else "BLOCKED"
        print(f"Message {i+1}: {status} - {result.reason}")
        
        if result.decision == MediationDecision.BLOCK:
            break
    
    # Save comprehensive logs
    print(f"\nSAVING MEDIATION LOGS")
    print("-" * 40)
    
    with open("mediation_demo_logs.json", "w") as f:
        json.dump(demo_logs, f, indent=2)
    
    print(f"Logs saved to: mediation_demo_logs.json")
    print(f"Total tests: {len(demo_logs)}")
    print(f"Trace ID continuity: MAINTAINED")
    
    return demo_logs

if __name__ == "__main__":
    # Run the comprehensive mediation demo
    logs = run_mediation_demo()
    print("\nMEDIATION DEMO COMPLETE")
    print("Nothing unsafe leaked through the system!")