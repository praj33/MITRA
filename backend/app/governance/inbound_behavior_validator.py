#!/usr/bin/env python3
"""
INBOUND BEHAVIOR VALIDATOR - Extension for Inbound Content
Extends existing validator to handle inbound content with new decision types
"""

import re
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import base validator components
from behavior_validator import BehaviorValidator, RiskCategory, ReasonCode

# ============================================================================
# INBOUND-SPECIFIC ENUMS AND DATA STRUCTURES
# ============================================================================

class InboundDecision(str, Enum):
    """Inbound-specific decision enum for content handling"""
    DELIVER = "deliver"          # Safe content, deliver normally
    SUMMARIZE = "summarize"      # Potentially overwhelming, provide summary
    DELAY = "delay"              # Suspicious timing, delay delivery
    SILENCE = "silence"          # Block delivery, don't notify sender
    ESCALATE = "escalate"        # Critical threat, escalate to human review

class InboundRiskCategory(str, Enum):
    """Inbound-specific risk categories"""
    PANIC_LANGUAGE = "panic_language"
    MANIPULATIVE_URGENCY = "manipulative_urgency"
    REPEATED_HARASSMENT = "repeated_harassment"
    EMOTIONAL_PRESSURE = "emotional_pressure"
    INFORMATION_OVERLOAD = "information_overload"
    CLEAN_INBOUND = "clean_inbound"

@dataclass
class InboundValidationResult:
    """Inbound validation result with direction flag"""
    direction: str  # "inbound" flag
    decision: InboundDecision
    risk_category: InboundRiskCategory
    confidence: float
    reason_code: ReasonCode
    trace_id: str
    matched_patterns: List[str]
    explanation: str
    original_content: str
    safe_summary: str = ""
    delay_duration: int = 0  # seconds to delay
    
    def to_dict(self) -> Dict:
        return {
            "direction": self.direction,
            "decision": self.decision.value,
            "risk_category": self.risk_category.value,
            "confidence": self.confidence,
            "reason_code": self.reason_code.value,
            "trace_id": self.trace_id,
            "matched_patterns": self.matched_patterns,
            "explanation": self.explanation,
            "original_content": self.original_content,
            "safe_summary": self.safe_summary,
            "delay_duration": self.delay_duration
        }

# ============================================================================
# INBOUND PATTERN LIBRARY
# ============================================================================

class InboundPatternLibrary:
    """Pattern library for inbound content risks"""
    
    # Patterns that trigger ESCALATE (critical threats)
    ESCALATE_PATTERNS = {
        InboundRiskCategory.PANIC_LANGUAGE: [
            (r'\bEMERGENCY\b.*\bACT NOW\b', 95, "Emergency manipulation"),
            (r'\bURGENT\b.*\bDELETE\b.*\bACCOUNT\b', 90, "Account deletion threat"),
            (r'\bSECURITY BREACH\b.*\bIMMEDIATE\b', 92, "False security alert"),
            (r'\bEMERGENCY\b.*\bSECURITY BREACH\b', 90, "Emergency security alert"),
            (r'\bSECURITY BREACH DETECTED\b', 88, "Security breach panic"),
            (r'\bHACKED\b.*\bCLICK HERE\b', 88, "Phishing with panic"),
            (r'\bVIRUS DETECTED\b.*\bDOWNLOAD\b', 85, "Malware panic"),
        ],
        
        InboundRiskCategory.REPEATED_HARASSMENT: [
            (r'\bI KNOW WHERE YOU LIVE\b', 98, "Direct threat"),
            (r'\bYOU CAN\'T HIDE FROM ME\b', 95, "Stalking threat"),
            (r'\bI\'LL FIND YOU\b', 92, "Pursuit threat"),
            (r'\bYOU\'LL PAY FOR THIS\b', 90, "Revenge threat"),
        ]
    }
    
    # Patterns that trigger SILENCE (block without notification)
    SILENCE_PATTERNS = {
        InboundRiskCategory.REPEATED_HARASSMENT: [
            (r'\bSTUPID\b.*\bIDIOT\b', 75, "Personal insults"),
            (r'\bFAT\b.*\bUGLY\b', 78, "Appearance harassment"),
            (r'\bKILL YOURSELF\b', 95, "Self-harm encouragement"),
            (r'\bNOBODY LIKES YOU\b', 70, "Social isolation attack"),
        ],
        
        InboundRiskCategory.EMOTIONAL_PRESSURE: [
            (r'\bIF YOU DON\'T RESPOND\b.*\bHURT MYSELF\b', 90, "Self-harm manipulation"),
            (r'\bYOU\'RE MAKING ME\b.*\bSUICIDAL\b', 88, "Emotional blackmail"),
            (r'\bI\'LL DIE IF YOU\b.*\bIGNORE ME\b', 85, "Death manipulation"),
        ]
    }
    
    # Patterns that trigger DELAY (suspicious timing)
    DELAY_PATTERNS = {
        InboundRiskCategory.MANIPULATIVE_URGENCY: [
            (r'\bEXPIRES IN\b.*\b\d+\s*MINUTES?\b', 80, "False deadline"),
            (r'\bLIMITED TIME\b.*\bOFFER\b', 75, "Scarcity manipulation"),
            (r'\bACT FAST\b.*\bBEFORE\b.*\bTOO LATE\b', 78, "Pressure tactics"),
            (r'\bONLY\s*\d+\s*LEFT\b', 72, "Artificial scarcity"),
            (r'\bONLY\s*\d+\s*SPOTS?\s*LEFT\b', 75, "Spot scarcity"),
            (r'\bREGISTER NOW\b.*\bBEFORE\b', 70, "Registration pressure"),
        ]
    }
    
    # Patterns that trigger SUMMARIZE (information overload)
    SUMMARIZE_PATTERNS = {
        InboundRiskCategory.INFORMATION_OVERLOAD: [
            (r'.{200,}', 60, "Long content"),  # Content over 200 chars
            (r'(\n.*){4,}', 65, "Multi-paragraph"),  # 4+ lines
            (r'(\b\d+\b.*){10,}', 70, "Number-heavy content"),  # 10+ numbers
        ]
    }

# ============================================================================
# INBOUND BEHAVIOR VALIDATOR
# ============================================================================

class InboundBehaviorValidator:
    """Extended validator for inbound content"""
    
    def __init__(self):
        self.pattern_lib = InboundPatternLibrary()
        self.base_validator = BehaviorValidator()  # Reuse existing validator
    
    def validate_inbound_content(self, 
                                content: str,
                                sender_id: str = "unknown",
                                content_type: str = "message",
                                frequency_data: Optional[Dict] = None) -> InboundValidationResult:
        """
        Validate inbound content with direction=inbound flag
        
        Args:
            content: Inbound content to validate
            sender_id: ID of content sender
            content_type: Type of content (message, email, notification, etc.)
            frequency_data: Frequency information for harassment detection
            
        Returns:
            InboundValidationResult with appropriate decision
        """
        
        text = content.lower()
        trace_id = self._generate_trace_id(content, "inbound")
        
        # Check for critical threats first (ESCALATE)
        for risk_category, patterns in self.pattern_lib.ESCALATE_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self._calculate_confidence(matches, content)
                return InboundValidationResult(
                    direction="inbound",
                    decision=InboundDecision.ESCALATE,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=ReasonCode.AGGRESSIVE_BEHAVIOR_DETECTED,
                    trace_id=trace_id,
                    matched_patterns=[match[2] for match in matches],
                    explanation=f"Critical threat detected: {risk_category.value}",
                    original_content=content
                )
        
        # Check for harassment patterns (SILENCE)
        for risk_category, patterns in self.pattern_lib.SILENCE_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self._calculate_confidence(matches, content)
                return InboundValidationResult(
                    direction="inbound",
                    decision=InboundDecision.SILENCE,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=ReasonCode.BOUNDARY_VIOLATION_DETECTED,
                    trace_id=trace_id,
                    matched_patterns=[match[2] for match in matches],
                    explanation=f"Harassment detected: {risk_category.value}",
                    original_content=content
                )
        
        # Check frequency-based harassment
        if frequency_data and self._is_harassment_frequency(frequency_data):
            return InboundValidationResult(
                direction="inbound",
                decision=InboundDecision.SILENCE,
                risk_category=InboundRiskCategory.REPEATED_HARASSMENT,
                confidence=85.0,
                reason_code=ReasonCode.BOUNDARY_VIOLATION_DETECTED,
                trace_id=trace_id,
                matched_patterns=["High frequency messaging"],
                explanation="Repeated harassment detected via frequency analysis",
                original_content=content
            )
        
        # Check for urgency manipulation (DELAY)
        for risk_category, patterns in self.pattern_lib.DELAY_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self._calculate_confidence(matches, content)
                delay_duration = self._calculate_delay_duration(confidence)
                return InboundValidationResult(
                    direction="inbound",
                    decision=InboundDecision.DELAY,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=ReasonCode.EMOTIONAL_MANIPULATION_DETECTED,
                    trace_id=trace_id,
                    matched_patterns=[match[2] for match in matches],
                    explanation=f"Manipulative urgency detected: {risk_category.value}",
                    original_content=content,
                    delay_duration=delay_duration
                )
        
        # Check for information overload (SUMMARIZE)
        for risk_category, patterns in self.pattern_lib.SUMMARIZE_PATTERNS.items():
            matches = self._find_matches(text, patterns)
            if matches:
                confidence = self._calculate_confidence(matches, content)
                summary = self._generate_summary(content)
                return InboundValidationResult(
                    direction="inbound",
                    decision=InboundDecision.SUMMARIZE,
                    risk_category=risk_category,
                    confidence=confidence,
                    reason_code=ReasonCode.CLEAN_CONTENT,
                    trace_id=trace_id,
                    matched_patterns=[match[2] for match in matches],
                    explanation=f"Information overload detected: {risk_category.value}",
                    original_content=content,
                    safe_summary=summary
                )
        
        # Default: DELIVER (safe content)
        return InboundValidationResult(
            direction="inbound",
            decision=InboundDecision.DELIVER,
            risk_category=InboundRiskCategory.CLEAN_INBOUND,
            confidence=0.0,
            reason_code=ReasonCode.CLEAN_CONTENT,
            trace_id=trace_id,
            matched_patterns=[],
            explanation="Safe inbound content",
            original_content=content
        )
    
    def _find_matches(self, text: str, patterns: List[Tuple[str, float, str]]) -> List[Tuple[float, str, str]]:
        """Find pattern matches in text"""
        matches = []
        for pattern, confidence, description in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append((confidence, pattern, description))
        return matches
    
    def _calculate_confidence(self, matches: List[Tuple[float, str, str]], content: str) -> float:
        """Calculate confidence score"""
        if not matches:
            return 0.0
        
        confidences = [match[0] for match in matches]
        base_confidence = sum(confidences) / len(confidences)
        
        # Boost for multiple matches
        if len(matches) > 1:
            base_confidence += min(len(matches) * 5, 15)
        
        return min(base_confidence, 100.0)
    
    def _generate_trace_id(self, content: str, direction: str) -> str:
        """Generate deterministic trace ID for inbound content"""
        version = "v1.0-INBOUND"
        hash_input = f"{content}:{direction}:{version}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"inbound_{hash_value}"
    
    def _is_harassment_frequency(self, frequency_data: Dict) -> bool:
        """Check if frequency indicates harassment"""
        messages_per_hour = frequency_data.get("messages_per_hour", 0)
        messages_after_block = frequency_data.get("messages_after_block", 0)
        
        return messages_per_hour > 10 or messages_after_block > 0
    
    def _calculate_delay_duration(self, confidence: float) -> int:
        """Calculate delay duration based on confidence"""
        if confidence > 90:
            return 3600  # 1 hour
        elif confidence > 80:
            return 1800  # 30 minutes
        elif confidence > 70:
            return 900   # 15 minutes
        else:
            return 300   # 5 minutes
    
    def _generate_summary(self, content: str) -> str:
        """Generate safe summary of long content"""
        # Simple summarization - take first 100 chars + "..."
        if len(content) > 100:
            return content[:100] + "... [Content summarized for readability]"
        return content

# ============================================================================
# PUBLIC API FUNCTION
# ============================================================================

def validate_inbound_behavior(content: str, 
                            sender_id: str = "unknown",
                            content_type: str = "message",
                            frequency_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Public API function for inbound content validation
    
    Args:
        content: Inbound content to validate
        sender_id: ID of content sender
        content_type: Type of content (message, email, notification, etc.)
        frequency_data: Frequency information for harassment detection
        
    Returns:
        Dictionary with validation results
    """
    validator = InboundBehaviorValidator()
    result = validator.validate_inbound_content(
        content=content,
        sender_id=sender_id,
        content_type=content_type,
        frequency_data=frequency_data
    )
    
    return result.to_dict()

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("INBOUND BEHAVIOR VALIDATOR - TEST MODE")
    print("=" * 60)
    
    test_cases = [
        # DELIVER cases
        ("Hello! Hope you're having a great day.", "deliver"),
        ("Meeting scheduled for 3pm tomorrow.", "deliver"),
        
        # SUMMARIZE cases
        ("This is a very long message with lots of details about the project timeline, requirements, specifications, deliverables, milestones, dependencies, resources, budget constraints, risk factors, and success criteria that might overwhelm the recipient.", "summarize"),
        
        # DELAY cases
        ("URGENT: Limited time offer expires in 5 minutes! Act fast!", "delay"),
        ("Only 2 spots left! Register now before it's too late!", "delay"),
        
        # SILENCE cases
        ("You're such a stupid idiot, nobody likes you.", "silence"),
        ("If you don't respond I'll hurt myself.", "silence"),
        
        # ESCALATE cases
        ("EMERGENCY: Security breach detected! Click here immediately!", "escalate"),
        ("I know where you live and I'm coming for you.", "escalate"),
    ]
    
    validator = InboundBehaviorValidator()
    
    for content, expected in test_cases:
        result = validator.validate_inbound_content(content)
        actual = result.decision.value
        status = "PASS" if actual == expected else "FAIL"
        
        print(f"\n{status}: '{content[:40]}...'")
        print(f"  Expected: {expected}")
        print(f"  Actual: {actual}")
        print(f"  Risk: {result.risk_category.value}")
        print(f"  Confidence: {result.confidence:.1f}%")
        print(f"  Trace ID: {result.trace_id}")
        
        if result.delay_duration > 0:
            print(f"  Delay: {result.delay_duration} seconds")
        if result.safe_summary:
            print(f"  Summary: {result.safe_summary[:50]}...")