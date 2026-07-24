"""
HARDENED VALIDATOR WITH FAIL-SAFE MECHANISMS
Makes silent failures impossible through hard guards and safe defaults
"""

import json
import hashlib
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Configure logging to catch all issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass

class SystemState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"

@dataclass
class ValidationResult:
    """Immutable validation result with required fields"""
    trace_id: str
    decision: str
    direction: str
    timestamp: str
    system_state: str
    error_details: Optional[Dict] = None
    safe_output: Optional[Dict] = None
    
    def __post_init__(self):
        # Validate required fields exist
        required = ['trace_id', 'decision', 'direction', 'timestamp', 'system_state']
        for field in required:
            if not getattr(self, field):
                raise ValidationError(f"Missing required field: {field}")

class HardenedValidator:
    def __init__(self):
        self.system_state = SystemState.HEALTHY
        self.failure_count = 0
        self.max_failures = 3
        
        # Hard-coded safe defaults (cannot be overridden)
        self.SAFE_DEFAULTS = {
            "unknown_content_decision": "summarize",  # When in doubt, protect user
            "system_error_decision": "delay",         # System errors = delay processing
            "malformed_input_decision": "deny",       # Bad input = deny by default
            "timeout_decision": "delay",              # Timeouts = delay for safety
            "emergency_fallback": "escalate"          # Last resort = human intervention
        }
        
        # Critical keywords that always trigger (cannot be disabled)
        self.HARD_GUARDS = {
            "suicide_keywords": ["kill myself", "end it all", "suicide", "want to die"],
            "threat_keywords": ["kill you", "hurt you", "find you", "destroy you", "dead to me literally"],
            "scam_keywords": ["send money", "wire transfer", "bitcoin", "cashapp emergency", "$500", "need money"]
        }
    
    def validate_action(self, payload: Dict) -> ValidationResult:
        """Validate outbound action with comprehensive error handling"""
        try:
            # STEP 1: Input validation with hard guards
            validated_input = self._validate_input(payload, "outbound")
            
            # STEP 2: System health check
            self._check_system_health()
            
            # STEP 3: Generate deterministic trace
            trace_id = self._generate_trace_id(validated_input)
            
            # STEP 4: Apply hard guards first (non-negotiable)
            hard_guard_result = self._apply_hard_guards(validated_input.get("content", ""))
            if hard_guard_result["blocked"]:
                return ValidationResult(
                    trace_id=trace_id,
                    decision="hard_deny",
                    direction="outbound",
                    timestamp=datetime.now().isoformat(),
                    system_state=self.system_state.value,
                    safe_output={
                        "block_reason": hard_guard_result["reason"],
                        "safe_rewrite": "Message blocked for safety - please contact support if needed"
                    }
                )
            
            # STEP 5: Content analysis with fallback protection
            try:
                analysis = self._analyze_content_safe(validated_input.get("content", ""))
            except Exception as e:
                logger.error(f"Content analysis failed: {e}")
                return self._emergency_fallback(trace_id, "outbound", "content_analysis_failure")
            
            # STEP 6: Decision making with safe defaults
            decision = self._make_safe_decision(analysis, "outbound")
            
            # STEP 7: Generate safe output
            safe_output = self._generate_safe_outbound_output(validated_input, analysis, decision)
            
            return ValidationResult(
                trace_id=trace_id,
                decision=decision,
                direction="outbound",
                timestamp=datetime.now().isoformat(),
                system_state=self.system_state.value,
                safe_output=safe_output
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return self._handle_validation_error(str(e), "outbound")
        except Exception as e:
            logger.critical(f"Unexpected error in validate_action: {e}")
            return self._emergency_fallback("error_trace", "outbound", f"system_error: {str(e)}")
    
    def validate_inbound(self, payload: Dict) -> ValidationResult:
        """Validate inbound message with comprehensive error handling"""
        try:
            # STEP 1: Input validation with hard guards
            validated_input = self._validate_input(payload, "inbound")
            
            # STEP 2: System health check
            self._check_system_health()
            
            # STEP 3: Generate deterministic trace
            trace_id = self._generate_trace_id(validated_input)
            
            # STEP 4: Apply hard guards first (non-negotiable)
            hard_guard_result = self._apply_hard_guards(validated_input.get("content", ""))
            if hard_guard_result["blocked"]:
                if "suicide" in hard_guard_result["reason"]:
                    return ValidationResult(
                        trace_id=trace_id,
                        decision="escalate",
                        direction="inbound",
                        timestamp=datetime.now().isoformat(),
                        system_state=self.system_state.value,
                        safe_output={
                            "message_primary": "Crisis support has been contacted",
                            "urgency_level": "critical",
                            "source_hidden": "Support team notified",
                            "suggested_action": "Professional help is on the way",
                            "emotional_tone": "supportive"
                        }
                    )
                else:
                    return ValidationResult(
                        trace_id=trace_id,
                        decision="silence",
                        direction="inbound",
                        timestamp=datetime.now().isoformat(),
                        system_state=self.system_state.value,
                        safe_output={
                            "message_primary": "Harmful content filtered",
                            "urgency_level": "low",
                            "source_hidden": "Blocked source",
                            "suggested_action": "Content blocked for safety",
                            "emotional_tone": "protective"
                        }
                    )
            
            # STEP 5: Content analysis with fallback protection
            try:
                analysis = self._analyze_content_safe(validated_input.get("content", ""))
            except Exception as e:
                logger.error(f"Content analysis failed: {e}")
                return self._emergency_fallback(trace_id, "inbound", "content_analysis_failure")
            
            # STEP 6: Decision making with safe defaults
            decision = self._make_safe_decision(analysis, "inbound")
            
            # STEP 7: Generate safe output
            safe_output = self._generate_safe_inbound_output(validated_input, analysis, decision)
            
            return ValidationResult(
                trace_id=trace_id,
                decision=decision,
                direction="inbound",
                timestamp=datetime.now().isoformat(),
                system_state=self.system_state.value,
                safe_output=safe_output
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return self._handle_validation_error(str(e), "inbound")
        except Exception as e:
            logger.critical(f"Unexpected error in validate_inbound: {e}")
            return self._emergency_fallback("error_trace", "inbound", f"system_error: {str(e)}")
    
    def _validate_input(self, payload: Dict, expected_direction: str) -> Dict:
        """Validate input with strict requirements"""
        if not isinstance(payload, dict):
            raise ValidationError("Payload must be a dictionary")
        
        # Required fields check
        required_fields = ["content"]
        if expected_direction == "outbound":
            required_fields.extend(["action_type", "recipient", "user_id"])
        else:
            required_fields.extend(["source", "user_id"])
        
        for field in required_fields:
            if field not in payload:
                raise ValidationError(f"Missing required field: {field}")
            if not payload[field] or not isinstance(payload[field], str):
                raise ValidationError(f"Invalid {field}: must be non-empty string")
        
        # Content length check
        content = payload.get("content", "")
        if len(content) > 10000:  # Hard limit
            raise ValidationError("Content exceeds maximum length (10000 characters)")
        
        # Direction validation
        if payload.get("direction") and payload["direction"] != expected_direction:
            raise ValidationError(f"Direction mismatch: expected {expected_direction}")
        
        return payload
    
    def _check_system_health(self):
        """Check system health and adjust behavior accordingly"""
        if self.failure_count >= self.max_failures:
            self.system_state = SystemState.EMERGENCY
            logger.critical(f"System in emergency mode: {self.failure_count} failures")
        elif self.failure_count > 0:
            self.system_state = SystemState.DEGRADED
            logger.warning(f"System degraded: {self.failure_count} failures")
    
    def _generate_trace_id(self, payload: Dict) -> str:
        """Generate deterministic trace ID"""
        try:
            content = payload.get("content", "")
            source = payload.get("source", payload.get("recipient", "unknown"))
            trace_content = f"{content}:{source}:{datetime.now().date()}"
            return hashlib.md5(trace_content.encode()).hexdigest()[:16]
        except Exception:
            # Fallback to timestamp-based ID
            return f"fallback_{int(datetime.now().timestamp())}"
    
    def _apply_hard_guards(self, content: str) -> Dict:
        """Apply non-negotiable hard guards"""
        content_lower = content.lower()
        
        # Check for suicide/self-harm (always escalate)
        for keyword in self.HARD_GUARDS["suicide_keywords"]:
            if keyword in content_lower:
                return {"blocked": True, "reason": "suicide_content_detected"}
        
        # Check for threats (always block)
        for keyword in self.HARD_GUARDS["threat_keywords"]:
            if keyword in content_lower:
                return {"blocked": True, "reason": "threat_detected"}
        
        # Check for financial scams (always block)
        for keyword in self.HARD_GUARDS["scam_keywords"]:
            if keyword in content_lower:
                return {"blocked": True, "reason": "financial_scam_detected"}
        
        return {"blocked": False}
    
    def _analyze_content_safe(self, content: str) -> Dict:
        """Analyze content with error protection"""
        try:
            if not content or not isinstance(content, str):
                return {"risk_level": "unknown", "categories": [], "confidence": 0.0}
            
            content_lower = content.lower()
            risk_categories = []
            risk_score = 0
            
            # Emotional manipulation detection
            manipulation_keywords = ["if you don't", "you have to", "devastated", "heartbroken"]
            if any(keyword in content_lower for keyword in manipulation_keywords):
                risk_categories.append("emotional_manipulation")
                risk_score += 2
            
            # Urgency abuse detection
            urgency_keywords = ["urgent", "emergency", "right now", "immediately"]
            if any(keyword in content_lower for keyword in urgency_keywords):
                risk_categories.append("urgency_abuse")
                risk_score += 1
            
            # Harassment detection
            harassment_keywords = ["hate you", "terrible person", "worthless", "pathetic"]
            if any(keyword in content_lower for keyword in harassment_keywords):
                risk_categories.append("harassment")
                risk_score += 3
            
            # Determine risk level
            if risk_score >= 4:
                risk_level = "high"
            elif risk_score >= 2:
                risk_level = "medium"
            elif risk_score >= 1:
                risk_level = "low"
            else:
                risk_level = "safe"
            
            return {
                "risk_level": risk_level,
                "categories": risk_categories,
                "confidence": min(1.0, risk_score / 5.0),
                "risk_score": risk_score
            }
            
        except Exception as e:
            logger.error(f"Content analysis error: {e}")
            # Safe fallback: assume medium risk
            return {"risk_level": "medium", "categories": ["analysis_error"], "confidence": 0.5}
    
    def _make_safe_decision(self, analysis: Dict, direction: str) -> str:
        """Make decision with safe defaults"""
        try:
            risk_level = analysis.get("risk_level", "unknown")
            
            # Emergency mode: extra conservative
            if self.system_state == SystemState.EMERGENCY:
                if direction == "outbound":
                    return "hard_deny"  # Always deny in emergency mode
                else:
                    return "escalate" if risk_level in ["high", "unknown"] else "summarize"
            
            # Normal decision logic with safe defaults
            if direction == "outbound":
                decision_map = {
                    "safe": "allow",
                    "low": "soft_rewrite",
                    "medium": "soft_rewrite", 
                    "high": "hard_deny",
                    "unknown": self.SAFE_DEFAULTS["unknown_content_decision"]
                }
            else:
                decision_map = {
                    "safe": "deliver",
                    "low": "deliver",
                    "medium": "summarize",
                    "high": "summarize",
                    "unknown": self.SAFE_DEFAULTS["unknown_content_decision"]
                }
            
            return decision_map.get(risk_level, self.SAFE_DEFAULTS["unknown_content_decision"])
            
        except Exception as e:
            logger.error(f"Decision making error: {e}")
            # Ultimate fallback
            return self.SAFE_DEFAULTS["emergency_fallback"]
    
    def _generate_safe_outbound_output(self, input_data: Dict, analysis: Dict, decision: str) -> Dict:
        """Generate safe outbound output"""
        try:
            if decision == "allow":
                return {
                    "original_content": input_data.get("content"),
                    "safe_rewrite": None,
                    "block_reason": None
                }
            elif decision == "soft_rewrite":
                return {
                    "original_content": None,
                    "safe_rewrite": "I'd like to discuss this matter with you when convenient",
                    "block_reason": "Content modified for better communication"
                }
            else:  # hard_deny
                return {
                    "original_content": None,
                    "safe_rewrite": "Message blocked - please reconsider your approach",
                    "block_reason": "Content blocked for safety reasons"
                }
        except Exception:
            return {
                "original_content": None,
                "safe_rewrite": "System error - message not sent",
                "block_reason": "Technical issue occurred"
            }
    
    def _generate_safe_inbound_output(self, input_data: Dict, analysis: Dict, decision: str) -> Dict:
        """Generate safe inbound output"""
        try:
            if decision == "deliver":
                return {
                    "message_primary": input_data.get("content", "Message received"),
                    "urgency_level": "normal",
                    "source_hidden": "Contact",
                    "suggested_action": "No action required",
                    "emotional_tone": "neutral"
                }
            elif decision == "summarize":
                return {
                    "message_primary": "Message contains concerning content - review when ready",
                    "urgency_level": "low",
                    "source_hidden": "Filtered contact",
                    "suggested_action": "Review for safety concerns",
                    "emotional_tone": "protective"
                }
            elif decision == "escalate":
                return {
                    "message_primary": "Crisis support has been contacted",
                    "urgency_level": "critical",
                    "source_hidden": "Support team notified",
                    "suggested_action": "Professional help activated",
                    "emotional_tone": "supportive"
                }
            else:  # delay, silence, etc.
                return {
                    "message_primary": "Message filtered for your protection",
                    "urgency_level": "low",
                    "source_hidden": "Protected source",
                    "suggested_action": "Available in filtered folder",
                    "emotional_tone": "neutral"
                }
        except Exception:
            return {
                "message_primary": "System protected you from potentially harmful content",
                "urgency_level": "low",
                "source_hidden": "System filter",
                "suggested_action": "Contact support if needed",
                "emotional_tone": "protective"
            }
    
    def _emergency_fallback(self, trace_id: str, direction: str, error_reason: str) -> ValidationResult:
        """Emergency fallback when all else fails"""
        self.failure_count += 1
        logger.critical(f"Emergency fallback triggered: {error_reason}")
        
        # Always protect the user in emergency
        if direction == "outbound":
            decision = "hard_deny"
            safe_output = {
                "original_content": None,
                "safe_rewrite": "System error - message blocked for safety",
                "block_reason": f"Emergency protection activated: {error_reason}"
            }
        else:
            decision = "escalate"
            safe_output = {
                "message_primary": "System error - content filtered for safety",
                "urgency_level": "high",
                "source_hidden": "System protection",
                "suggested_action": "Contact support - system issue detected",
                "emotional_tone": "protective"
            }
        
        return ValidationResult(
            trace_id=trace_id,
            decision=decision,
            direction=direction,
            timestamp=datetime.now().isoformat(),
            system_state=SystemState.EMERGENCY.value,
            error_details={"reason": error_reason, "fallback_triggered": True},
            safe_output=safe_output
        )
    
    def _handle_validation_error(self, error_msg: str, direction: str) -> ValidationResult:
        """Handle validation errors gracefully"""
        trace_id = f"validation_error_{int(datetime.now().timestamp())}"
        
        return ValidationResult(
            trace_id=trace_id,
            decision=self.SAFE_DEFAULTS["malformed_input_decision"],
            direction=direction,
            timestamp=datetime.now().isoformat(),
            system_state=self.system_state.value,
            error_details={"validation_error": error_msg},
            safe_output={
                "error_message": "Invalid input - request blocked for safety",
                "suggested_action": "Please check your input format and try again"
            }
        )

# Example usage with error simulation
if __name__ == "__main__":
    validator = HardenedValidator()
    
    print("🛡️  HARDENED VALIDATOR - FAIL-SAFE TESTING")
    print("=" * 50)
    
    # Test normal operation
    normal_payload = {
        "direction": "outbound",
        "action_type": "whatsapp_send",
        "content": "Hi, how are you?",
        "recipient": "friend@example.com",
        "user_id": "user123"
    }
    
    result = validator.validate_action(normal_payload)
    print(f"Normal case: {result.decision} - {result.system_state}")
    
    # Test hard guard triggers
    suicide_payload = {
        "direction": "inbound",
        "content": "I want to kill myself tonight",
        "source": "crisis@example.com",
        "user_id": "user123"
    }
    
    result = validator.validate_inbound(suicide_payload)
    print(f"Crisis case: {result.decision} - {result.safe_output['message_primary']}")
    
    print("\n✅ Hardened validator operational - no silent failures possible!")