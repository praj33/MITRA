"""
ambiguity_handling_tests.py - Test epistemic discipline under uncertainty
"""

import pytest
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class EpistemicState(str, Enum):
    KNOWN = "known"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"
    UNKNOWN = "unknown"

class Decision(str, Enum):
    BLOCK = "block"
    ESCALATE = "escalate"
    ALLOW_WITH_FLAG = "allow_with_flag"
    ALLOW = "allow"

@dataclass
class ValidationResult:
    decision: Decision
    confidence: float
    epistemic_state: EpistemicState
    evidence: List[str]
    uncertainty_flags: List[str]

class EpistemicValidator:
    """Validator with epistemic discipline"""
    
    def classify_epistemic_state(self, confidence: float) -> EpistemicState:
        if confidence >= 100:
            return EpistemicState.KNOWN
        elif confidence >= 70:
            return EpistemicState.LIKELY
        elif confidence >= 30:
            return EpistemicState.UNCERTAIN
        else:
            return EpistemicState.UNKNOWN
    
    def validate(self, content: str, metadata: dict = None) -> ValidationResult:
        """Validate with epistemic discipline"""
        evidence = []
        confidence = 0.0
        
        # Content analysis only (metadata ignored)
        if "kill" in content.lower():
            evidence.append("threat_language")
            confidence = 100.0
        elif "you have to" in content.lower() and "last chance" in content.lower():
            evidence.append("manipulation_patterns")
            confidence = 85.0
        elif "need you" in content.lower():
            evidence.append("weak_dependency_signal")
            confidence = 50.0
        else:
            confidence = 0.0
        
        epistemic_state = self.classify_epistemic_state(confidence)
        
        # Decision based on epistemic state
        if epistemic_state == EpistemicState.KNOWN and confidence >= 90:
            decision = Decision.BLOCK
            uncertainty_flags = []
        elif epistemic_state == EpistemicState.LIKELY:
            decision = Decision.ESCALATE
            uncertainty_flags = ["requires_human_review"]
        elif epistemic_state == EpistemicState.UNCERTAIN:
            decision = Decision.ALLOW_WITH_FLAG
            uncertainty_flags = ["ambiguous_intent", "insufficient_evidence"]
        else:
            decision = Decision.ALLOW
            uncertainty_flags = []
        
        return ValidationResult(
            decision=decision,
            confidence=confidence,
            epistemic_state=epistemic_state,
            evidence=evidence,
            uncertainty_flags=uncertainty_flags
        )


# ============================================================================
# EPISTEMIC STATE TESTS
# ============================================================================

def test_known_state_high_confidence():
    """Test: High confidence (100%) → KNOWN state"""
    validator = EpistemicValidator()
    result = validator.validate("I will kill you")
    
    assert result.epistemic_state == EpistemicState.KNOWN
    assert result.confidence == 100.0
    assert result.decision == Decision.BLOCK

def test_likely_state_medium_confidence():
    """Test: Medium confidence (85%) → LIKELY state"""
    validator = EpistemicValidator()
    result = validator.validate("You have to respond or this is your last chance")
    
    assert result.epistemic_state == EpistemicState.LIKELY
    assert result.confidence == 85.0
    assert result.decision == Decision.ESCALATE

def test_uncertain_state_low_confidence():
    """Test: Low confidence (50%) → UNCERTAIN state"""
    validator = EpistemicValidator()
    result = validator.validate("I really need you")
    
    assert result.epistemic_state == EpistemicState.UNCERTAIN
    assert result.confidence == 50.0
    assert result.decision == Decision.ALLOW_WITH_FLAG

def test_unknown_state_no_evidence():
    """Test: No evidence (0%) → UNKNOWN state"""
    validator = EpistemicValidator()
    result = validator.validate("Hello there")
    
    assert result.epistemic_state == EpistemicState.UNKNOWN
    assert result.confidence == 0.0
    assert result.decision == Decision.ALLOW


# ============================================================================
# AMBIGUITY HANDLING TESTS
# ============================================================================

def test_ambiguity_defaults_to_allow():
    """Test: Ambiguous content defaults to ALLOW"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    assert result.decision in [Decision.ALLOW_WITH_FLAG, Decision.ALLOW]
    assert "ambiguous_intent" in result.uncertainty_flags or result.decision == Decision.ALLOW

def test_no_inference_from_metadata():
    """Test: Metadata does not influence decision"""
    validator = EpistemicValidator()
    
    # Same content, different metadata
    result1 = validator.validate("Hello", metadata={"region": "high_risk"})
    result2 = validator.validate("Hello", metadata={"region": "low_risk"})
    
    # Decisions must be identical (metadata ignored)
    assert result1.decision == result2.decision
    assert result1.confidence == result2.confidence

def test_uncertainty_propagates():
    """Test: Uncertainty flags propagate to output"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    assert result.epistemic_state == EpistemicState.UNCERTAIN
    assert len(result.uncertainty_flags) > 0
    assert "ambiguous_intent" in result.uncertainty_flags or "insufficient_evidence" in result.uncertainty_flags

def test_no_confidence_inflation():
    """Test: Confidence scores not inflated"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    # 50% confidence should stay 50%, not round to 100%
    assert result.confidence == 50.0
    assert result.epistemic_state == EpistemicState.UNCERTAIN


# ============================================================================
# EPISTEMIC COLLAPSE PREVENTION TESTS
# ============================================================================

def test_no_collapse_inference_without_evidence():
    """Test: Do not infer threat without direct evidence"""
    validator = EpistemicValidator()
    
    # No threat language, should not infer threat
    result = validator.validate("I'm frustrated with you")
    
    assert result.decision != Decision.BLOCK
    assert "threat_language" not in result.evidence

def test_no_collapse_context_overweighting():
    """Test: Context does not override content analysis"""
    validator = EpistemicValidator()
    
    # Clean content with "suspicious" metadata
    result = validator.validate("Hello", metadata={"sender": "suspicious_user"})
    
    assert result.decision == Decision.ALLOW
    assert result.confidence == 0.0

def test_no_collapse_ambiguity_resolution():
    """Test: Ambiguity preserved, not resolved"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    # Should stay UNCERTAIN, not collapse to KNOWN
    assert result.epistemic_state == EpistemicState.UNCERTAIN
    assert result.confidence < 70.0

def test_no_collapse_absence_of_evidence():
    """Test: Absence of evidence ≠ evidence of absence"""
    validator = EpistemicValidator()
    
    # No threat signals, but also no safety signals
    result = validator.validate("...")
    
    # Should be UNKNOWN, not KNOWN_SAFE
    assert result.epistemic_state == EpistemicState.UNKNOWN
    assert result.decision == Decision.ALLOW


# ============================================================================
# EVIDENCE REQUIREMENT TESTS
# ============================================================================

def test_threat_requires_direct_evidence():
    """Test: Threat detection requires direct threat language"""
    validator = EpistemicValidator()
    
    # Indirect/implied threat (insufficient)
    result = validator.validate("You'll regret this")
    
    assert result.decision != Decision.BLOCK
    assert result.confidence < 90.0

def test_manipulation_requires_multiple_patterns():
    """Test: Manipulation requires multiple patterns"""
    validator = EpistemicValidator()
    
    # Single pattern (insufficient for BLOCK)
    result = validator.validate("You have to respond")
    
    assert result.decision != Decision.BLOCK

def test_high_confidence_requires_strong_evidence():
    """Test: High confidence requires strong evidence"""
    validator = EpistemicValidator()
    
    # Weak signal should not produce high confidence
    result = validator.validate("I need you")
    
    assert result.confidence < 70.0
    assert result.epistemic_state != EpistemicState.KNOWN


# ============================================================================
# UNCERTAINTY PROPAGATION TESTS
# ============================================================================

def test_uncertainty_flags_present():
    """Test: Uncertain results include uncertainty flags"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    assert len(result.uncertainty_flags) > 0

def test_confidence_score_preserved():
    """Test: Exact confidence score preserved"""
    validator = EpistemicValidator()
    result = validator.validate("I need you")
    
    # Should be exactly 50.0, not rounded
    assert result.confidence == 50.0

def test_evidence_list_included():
    """Test: Evidence list included in output"""
    validator = EpistemicValidator()
    result = validator.validate("I will kill you")
    
    assert len(result.evidence) > 0
    assert "threat_language" in result.evidence


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
