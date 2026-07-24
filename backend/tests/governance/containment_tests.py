"""
containment_tests.py - Test failure containment and cascading prevention
"""

import pytest
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class FailureTier(int, Enum):
    CATASTROPHIC = 0
    CRITICAL = 1
    DEGRADED = 2
    INFORMATIONAL = 3

class Decision(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"

@dataclass
class ValidationResult:
    decision: Decision
    reason: str
    tier: Optional[FailureTier] = None

class CircuitBreaker:
    def __init__(self, threshold=3):
        self.failure_count = 0
        self.threshold = threshold
        self.state = "CLOSED"
    
    def call(self, func):
        if self.state == "OPEN":
            raise Exception("Circuit breaker open")
        
        try:
            result = func()
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.state = "OPEN"
            raise

class FailureAwareValidator:
    """Validator with failure tier awareness"""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(threshold=3)
        self.degraded_mode = False
    
    def validate(self, content: str, simulate_failure: Optional[FailureTier] = None):
        """Validate with failure simulation"""
        
        # Simulate failures for testing
        if simulate_failure == FailureTier.CATASTROPHIC:
            raise Exception("TIER 0: Pattern library corrupted")
        elif simulate_failure == FailureTier.CRITICAL:
            raise Exception("TIER 1: Pattern matching failed")
        elif simulate_failure == FailureTier.DEGRADED:
            # Degraded mode: continue with reduced functionality
            self.degraded_mode = True
            return ValidationResult(
                decision=Decision.ALLOW,
                reason="Degraded mode - non-critical feature failed",
                tier=FailureTier.DEGRADED
            )
        
        # Normal validation
        if "threat" in content.lower():
            return ValidationResult(decision=Decision.BLOCK, reason="Threat detected")
        return ValidationResult(decision=Decision.ALLOW, reason="Clean content")
    
    def validate_with_containment(self, content: str, simulate_failure: Optional[FailureTier] = None):
        """Validate with failure containment"""
        try:
            return self.circuit_breaker.call(lambda: self.validate(content, simulate_failure))
        except Exception as e:
            # Fail closed on critical errors
            if "TIER 0" in str(e) or "TIER 1" in str(e):
                return ValidationResult(
                    decision=Decision.BLOCK,
                    reason=f"Validation error - blocked for safety: {str(e)}",
                    tier=FailureTier.CRITICAL
                )
            # Fail open on degraded errors
            return ValidationResult(
                decision=Decision.ALLOW,
                reason="Degraded validation",
                tier=FailureTier.DEGRADED
            )


# ============================================================================
# TIER 0: CATASTROPHIC FAILURE TESTS
# ============================================================================

def test_tier0_blocks_all_requests():
    """Test: Tier 0 failure blocks all requests"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CATASTROPHIC)
    
    assert result.decision == Decision.BLOCK
    assert "TIER 0" in result.reason or result.tier == FailureTier.CRITICAL


# ============================================================================
# TIER 1: CRITICAL FAILURE TESTS
# ============================================================================

def test_tier1_fails_closed():
    """Test: Tier 1 failure fails closed (blocks request)"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    assert result.decision == Decision.BLOCK
    assert result.tier == FailureTier.CRITICAL

def test_tier1_logs_error():
    """Test: Tier 1 failure logs error"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    assert "error" in result.reason.lower() or "failed" in result.reason.lower()


# ============================================================================
# TIER 2: DEGRADED FAILURE TESTS
# ============================================================================

def test_tier2_fails_open():
    """Test: Tier 2 failure fails open (allows request)"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.DEGRADED)
    
    assert result.decision == Decision.ALLOW
    assert result.tier == FailureTier.DEGRADED

def test_tier2_continues_with_warning():
    """Test: Tier 2 failure continues with warning"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.DEGRADED)
    
    assert "degraded" in result.reason.lower()


# ============================================================================
# CASCADING FAILURE PREVENTION TESTS
# ============================================================================

def test_circuit_breaker_opens_after_threshold():
    """Test: Circuit breaker opens after failure threshold"""
    validator = FailureAwareValidator()
    
    # Trigger 3 failures
    for i in range(3):
        try:
            validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
        except:
            pass
    
    # Circuit should be open
    assert validator.circuit_breaker.state == "OPEN"

def test_circuit_breaker_prevents_cascade():
    """Test: Circuit breaker prevents cascading failures"""
    validator = FailureAwareValidator()
    
    # Trigger 3 failures to open circuit
    for i in range(3):
        validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    # Next call should fail fast (circuit open)
    with pytest.raises(Exception, match="Circuit breaker open"):
        validator.circuit_breaker.call(lambda: validator.validate("Hello"))

def test_failure_isolation():
    """Test: Failure in one request doesn't affect others"""
    validator = FailureAwareValidator()
    
    # First request fails
    result1 = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    assert result1.decision == Decision.BLOCK
    
    # Second request succeeds (isolated)
    result2 = validator.validate_with_containment("Hello", simulate_failure=None)
    assert result2.decision == Decision.ALLOW


# ============================================================================
# GRACEFUL DEGRADATION TESTS
# ============================================================================

def test_degraded_mode_continues():
    """Test: Degraded mode continues with reduced functionality"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.DEGRADED)
    
    assert result.decision == Decision.ALLOW
    assert validator.degraded_mode == True

def test_degraded_mode_still_validates():
    """Test: Degraded mode still performs core validation"""
    validator = FailureAwareValidator()
    
    # Enter degraded mode
    validator.validate_with_containment("Hello", simulate_failure=FailureTier.DEGRADED)
    
    # Core validation still works
    result = validator.validate("threat detected")
    assert result.decision == Decision.BLOCK


# ============================================================================
# FAIL CLOSED VS FAIL OPEN TESTS
# ============================================================================

def test_safety_failures_fail_closed():
    """Test: Safety-critical failures fail closed"""
    validator = FailureAwareValidator()
    
    # Tier 0 and Tier 1 should fail closed
    result0 = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CATASTROPHIC)
    result1 = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    assert result0.decision == Decision.BLOCK
    assert result1.decision == Decision.BLOCK

def test_non_safety_failures_fail_open():
    """Test: Non-safety failures fail open"""
    validator = FailureAwareValidator()
    
    # Tier 2 should fail open
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.DEGRADED)
    
    assert result.decision == Decision.ALLOW


# ============================================================================
# RECOVERY TESTS
# ============================================================================

def test_automatic_recovery_after_success():
    """Test: Circuit breaker resets after successful call"""
    validator = FailureAwareValidator()
    
    # Trigger 2 failures (below threshold)
    for i in range(2):
        validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    # Successful call resets counter
    validator.validate_with_containment("Hello", simulate_failure=None)
    
    assert validator.circuit_breaker.failure_count == 0

def test_fallback_to_safe_default():
    """Test: Fallback to safe default on error"""
    validator = FailureAwareValidator()
    
    result = validator.validate_with_containment("Hello", simulate_failure=FailureTier.CRITICAL)
    
    # Should block (safe default)
    assert result.decision == Decision.BLOCK


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
