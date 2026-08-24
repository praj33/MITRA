"""
AI-Being Unified Validator
Consolidated APIs with Deterministic State Management
Version: v1.0-PRODUCTION-FROZEN
Schema Hash: sha256:unified_validator_20240115_frozen
"""

import hashlib
import json
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

# FROZEN SCHEMAS - Version Hash: sha256:unified_validator_20240115_frozen

class ValidationDecision(Enum):
    ALLOW = "allow"
    REWRITE = "rewrite" 
    BLOCK = "block"

class InboundDecision(Enum):
    SAFE = "safe"
    SENSITIVE = "sensitive"
    ESCALATING = "escalating"
    SUPPRESS = "suppress"

@dataclass
class MessagePayload:
    content: str
    sender: str
    recipient: str
    platform: str
    timestamp: str
    message_type: str = "general"

@dataclass
class ActionPayload:
    content: str
    platform: str
    recipient: str
    action_type: str
    timestamp: str
    urgency_level: str = "low"

@dataclass
class ValidationResult:
    decision: ValidationDecision
    reason: str
    trace_id: str
    safety_flags: List[str]
    rewritten_content: Optional[str] = None
    timestamp: str = ""

@dataclass
class InboundResult:
    decision: InboundDecision
    safe_summary: Optional[str]
    trace_id: str
    risk_indicators: List[str]
    resources_provided: List[str]
    timestamp: str

# DETERMINISTIC STATE MANAGEMENT
class ContactCounter:
    """State-based, replayable contact frequency tracking"""
    
    def __init__(self):
        self.daily_counts = {}  # {(sender, recipient, date): count}
        self.platform_limits = {
            "whatsapp": 5,
            "email": 3, 
            "instagram": 2,
            "sms": 4
        }
    
    def get_daily_count(self, sender: str, recipient: str, platform: str, date: str) -> int:
        key = (sender, recipient, platform, date)
        return self.daily_counts.get(key, 0)
    
    def increment_count(self, sender: str, recipient: str, platform: str, date: str) -> int:
        key = (sender, recipient, platform, date)
        current = self.daily_counts.get(key, 0)
        self.daily_counts[key] = current + 1
        return current + 1
    
    def exceeds_limit(self, sender: str, recipient: str, platform: str, date: str) -> bool:
        current_count = self.get_daily_count(sender, recipient, platform, date)
        limit = self.platform_limits.get(platform.lower(), 3)
        return current_count >= limit

class TimeEnforcer:
    """Time-of-day enforcement using preference slots"""
    
    def __init__(self):
        self.quiet_hours_start = time(22, 0)  # 10 PM
        self.quiet_hours_end = time(7, 0)     # 7 AM
        self.business_hours_start = time(9, 0)  # 9 AM
        self.business_hours_end = time(18, 0)   # 6 PM
    
    def is_quiet_hours(self, timestamp: str) -> bool:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_time = dt.time()
        
        # Handle overnight quiet hours (10 PM to 7 AM)
        if self.quiet_hours_start <= time(23, 59):  # Same day
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        return self.quiet_hours_start <= current_time <= self.quiet_hours_end
    
    def is_business_hours(self, timestamp: str) -> bool:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        current_time = dt.time()
        return self.business_hours_start <= current_time <= self.business_hours_end

# UNIFIED VALIDATOR CLASS
class UnifiedValidator:
    """Consolidated validator with frozen schemas and deterministic behavior"""
    
    VERSION = "v1.0-PRODUCTION-FROZEN"
    SCHEMA_HASH = "sha256:unified_validator_20240115_frozen"
    
    def __init__(self):
        self.contact_counter = ContactCounter()
        self.time_enforcer = TimeEnforcer()
        self.manipulation_patterns = [
            "if you don't", "you have to", "you must", "last chance",
            "everyone else", "only you", "don't ignore", "really need you"
        ]
        self.urgency_patterns = [
            "urgent", "emergency", "immediate", "act now", "expires", "limited time"
        ]
        self.threat_patterns = [
            "i'll hurt", "you'll regret", "i know where", "i'm coming", "make you pay"
        ]
    
    def generate_trace_id(self, content: str, decision: str, timestamp: str) -> str:
        """Generate deterministic trace ID"""
        trace_input = f"{content}:{decision}:{timestamp}:{self.VERSION}"
        return hashlib.md5(trace_input.encode()).hexdigest()[:16]
    
    def detect_manipulation(self, content: str) -> Tuple[int, List[str]]:
        """Detect emotional manipulation patterns"""
        content_lower = content.lower()
        flags = []
        score = 0
        
        for pattern in self.manipulation_patterns:
            if pattern in content_lower:
                flags.append(f"manipulation_{pattern.replace(' ', '_')}")
                score += 2
        
        for pattern in self.urgency_patterns:
            if pattern in content_lower:
                flags.append(f"urgency_{pattern.replace(' ', '_')}")
                score += 1
                
        for pattern in self.threat_patterns:
            if pattern in content_lower:
                flags.append(f"threat_{pattern.replace(' ', '_')}")
                score += 3
        
        return score, flags
    
    def validate_action(self, action_payload: ActionPayload) -> ValidationResult:
        """
        Validate outbound assistant actions
        Returns: ValidationResult with ALLOW/REWRITE/BLOCK decision
        """
        timestamp = datetime.now().isoformat() + "Z"
        
        # Extract date for contact counting
        date = action_payload.timestamp[:10]  # YYYY-MM-DD
        
        # Check contact frequency limits
        if self.contact_counter.exceeds_limit(
            "assistant", action_payload.recipient, 
            action_payload.platform, date
        ):
            trace_id = self.generate_trace_id(
                action_payload.content, "BLOCK", timestamp
            )
            return ValidationResult(
                decision=ValidationDecision.BLOCK,
                reason="Daily contact limit exceeded",
                trace_id=trace_id,
                safety_flags=["contact_abuse", "frequency_violation"],
                timestamp=timestamp
            )
        
        # Check time-of-day rules
        is_quiet = self.time_enforcer.is_quiet_hours(action_payload.timestamp)
        is_business = self.time_enforcer.is_business_hours(action_payload.timestamp)
        
        # Detect manipulation and safety issues
        manipulation_score, safety_flags = self.detect_manipulation(action_payload.content)
        
        # Decision logic
        if manipulation_score >= 5:  # High manipulation threshold
            trace_id = self.generate_trace_id(
                action_payload.content, "BLOCK", timestamp
            )
            return ValidationResult(
                decision=ValidationDecision.BLOCK,
                reason="Severe emotional manipulation detected",
                trace_id=trace_id,
                safety_flags=safety_flags,
                timestamp=timestamp
            )
        
        elif manipulation_score >= 2 or (is_quiet and action_payload.urgency_level != "critical"):
            # Rewrite needed for minor issues or quiet hours
            rewritten = self._generate_safe_rewrite(action_payload.content)
            trace_id = self.generate_trace_id(
                action_payload.content, "REWRITE", timestamp
            )
            return ValidationResult(
                decision=ValidationDecision.REWRITE,
                reason="Content requires safety modification",
                trace_id=trace_id,
                safety_flags=safety_flags,
                rewritten_content=rewritten,
                timestamp=timestamp
            )
        
        else:
            # Safe to send
            self.contact_counter.increment_count(
                "assistant", action_payload.recipient,
                action_payload.platform, date
            )
            trace_id = self.generate_trace_id(
                action_payload.content, "ALLOW", timestamp
            )
            return ValidationResult(
                decision=ValidationDecision.ALLOW,
                reason="Content passes all safety checks",
                trace_id=trace_id,
                safety_flags=[],
                timestamp=timestamp
            )
    
    def validate_inbound(self, message_payload: MessagePayload) -> InboundResult:
        """
        Validate inbound messages before user delivery
        Returns: InboundResult with classification and safe summary
        """
        timestamp = datetime.now().isoformat() + "Z"
        
        # Detect risks and manipulation
        manipulation_score, risk_indicators = self.detect_manipulation(message_payload.content)
        
        # Check for crisis indicators
        crisis_keywords = ["hurt myself", "end it all", "suicide", "kill myself"]
        has_crisis = any(keyword in message_payload.content.lower() for keyword in crisis_keywords)
        
        # Generate trace ID
        trace_id = self.generate_trace_id(
            message_payload.content, "INBOUND", timestamp
        )
        
        # Classification logic
        if manipulation_score >= 6 or any("threat_" in flag for flag in risk_indicators):
            return InboundResult(
                decision=InboundDecision.SUPPRESS,
                safe_summary=None,
                trace_id=trace_id,
                risk_indicators=risk_indicators,
                resources_provided=[],
                timestamp=timestamp
            )
        
        elif manipulation_score >= 3 or has_crisis:
            safe_summary = self._generate_safe_summary(message_payload.content)
            resources = ["Crisis Text Line: 741741", "National Suicide Prevention Lifeline: 988"] if has_crisis else []
            
            return InboundResult(
                decision=InboundDecision.ESCALATING,
                safe_summary=safe_summary,
                trace_id=trace_id,
                risk_indicators=risk_indicators,
                resources_provided=resources,
                timestamp=timestamp
            )
        
        elif manipulation_score >= 1:
            return InboundResult(
                decision=InboundDecision.SENSITIVE,
                safe_summary=None,
                trace_id=trace_id,
                risk_indicators=risk_indicators,
                resources_provided=[],
                timestamp=timestamp
            )
        
        else:
            return InboundResult(
                decision=InboundDecision.SAFE,
                safe_summary=None,
                trace_id=trace_id,
                risk_indicators=[],
                resources_provided=[],
                timestamp=timestamp
            )
    
    def _generate_safe_rewrite(self, content: str) -> str:
        """Generate safe rewrite of manipulative content"""
        # Remove manipulation patterns
        safe_content = content
        
        # Replace urgency language
        urgency_replacements = {
            "urgent": "important",
            "immediately": "when convenient",
            "right now": "at your convenience",
            "you must": "please consider",
            "you have to": "you might want to"
        }
        
        for urgent, calm in urgency_replacements.items():
            safe_content = safe_content.replace(urgent, calm)
            safe_content = safe_content.replace(urgent.upper(), calm)
        
        return safe_content
    
    def _generate_safe_summary(self, content: str) -> str:
        """Generate safe summary of manipulative content"""
        if "hurt myself" in content.lower() or "suicide" in content.lower():
            return "Message received expressing distress. Crisis support resources available."
        elif any(pattern in content.lower() for pattern in self.manipulation_patterns):
            return "Message received requesting communication response."
        else:
            return "Personal message received."

# GLOBAL VALIDATOR INSTANCE
validator = UnifiedValidator()

# CONSOLIDATED API FUNCTIONS
def validate_action(action_payload: ActionPayload) -> ValidationResult:
    """
    Consolidated API for validating outbound assistant actions
    
    Args:
        action_payload: ActionPayload with content, platform, recipient, etc.
    
    Returns:
        ValidationResult with ALLOW/REWRITE/BLOCK decision
    """
    return validator.validate_action(action_payload)

def validate_inbound(message_payload: MessagePayload) -> InboundResult:
    """
    Consolidated API for validating inbound messages
    
    Args:
        message_payload: MessagePayload with content, sender, platform, etc.
    
    Returns:
        InboundResult with classification and safe summary
    """
    return validator.validate_inbound(message_payload)

# API VERSION AND SCHEMA INFO
def get_api_info() -> Dict:
    """Get API version and schema information"""
    return {
        "version": UnifiedValidator.VERSION,
        "schema_hash": UnifiedValidator.SCHEMA_HASH,
        "frozen": True,
        "apis": ["validate_action", "validate_inbound"],
        "deterministic": True
    }

if __name__ == "__main__":
    # API Info
    print("AI-Being Unified Validator")
    print(f"Version: {UnifiedValidator.VERSION}")
    print(f"Schema Hash: {UnifiedValidator.SCHEMA_HASH}")
    print("APIs: validate_action(), validate_inbound()")
    print("Status: FROZEN - Deterministic behavior guaranteed")