"""
illegal_transition_tests.py - Test suite for forbidden state transitions
Verifies state machine rejects all illegal transitions
"""

import pytest
from enum import Enum

class State(Enum):
    RECEIVED = 0
    SAFETY_VALIDATING = 1
    SAFETY_BLOCKED = 2
    SAFETY_REWRITTEN = 3
    SAFETY_APPROVED = 4
    INTELLIGENCE_PROCESSING = 5
    ENFORCEMENT_VALIDATING = 6
    ENFORCEMENT_BLOCKED = 7
    ENFORCEMENT_APPROVED = 8
    EXECUTING = 9
    COMPLETED = 10
    FAILED = 11

class IllegalTransitionError(Exception):
    """Raised when illegal state transition attempted"""
    pass

class StateMachine:
    """Deterministic state machine with transition validation"""
    
    ALLOWED_TRANSITIONS = {
        State.RECEIVED: [State.SAFETY_VALIDATING, State.FAILED],
        State.SAFETY_VALIDATING: [State.SAFETY_BLOCKED, State.SAFETY_REWRITTEN, State.SAFETY_APPROVED, State.FAILED],
        State.SAFETY_BLOCKED: [],
        State.SAFETY_REWRITTEN: [State.INTELLIGENCE_PROCESSING, State.FAILED],
        State.SAFETY_APPROVED: [State.INTELLIGENCE_PROCESSING, State.FAILED],
        State.INTELLIGENCE_PROCESSING: [State.ENFORCEMENT_VALIDATING, State.FAILED],
        State.ENFORCEMENT_VALIDATING: [State.ENFORCEMENT_BLOCKED, State.ENFORCEMENT_APPROVED, State.FAILED],
        State.ENFORCEMENT_BLOCKED: [],
        State.ENFORCEMENT_APPROVED: [State.EXECUTING, State.FAILED],
        State.EXECUTING: [State.COMPLETED, State.FAILED],
        State.COMPLETED: [],
        State.FAILED: []
    }
    
    def __init__(self):
        self.current_state = State.RECEIVED
        self.history = [State.RECEIVED]
    
    def transition(self, to_state: State):
        """Attempt state transition with validation"""
        if to_state not in self.ALLOWED_TRANSITIONS[self.current_state]:
            raise IllegalTransitionError(
                f"Illegal transition: {self.current_state.name} -> {to_state.name}"
            )
        self.current_state = to_state
        self.history.append(to_state)
    
    def reset(self):
        """Reset to initial state"""
        self.current_state = State.RECEIVED
        self.history = [State.RECEIVED]


# ============================================================================
# BYPASS TESTS - Intelligence without Safety
# ============================================================================

def test_bypass_direct_intelligence():
    """Test: RECEIVED -> INTELLIGENCE_PROCESSING (bypass)"""
    sm = StateMachine()
    with pytest.raises(IllegalTransitionError, match="RECEIVED -> INTELLIGENCE_PROCESSING"):
        sm.transition(State.INTELLIGENCE_PROCESSING)

def test_bypass_direct_execution():
    """Test: RECEIVED -> EXECUTING (bypass)"""
    sm = StateMachine()
    with pytest.raises(IllegalTransitionError, match="RECEIVED -> EXECUTING"):
        sm.transition(State.EXECUTING)

def test_bypass_during_safety_validation():
    """Test: SAFETY_VALIDATING -> EXECUTING (bypass)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    with pytest.raises(IllegalTransitionError, match="SAFETY_VALIDATING -> EXECUTING"):
        sm.transition(State.EXECUTING)


# ============================================================================
# ESCALATION TESTS - Skip Enforcement
# ============================================================================

def test_escalation_skip_enforcement():
    """Test: INTELLIGENCE_PROCESSING -> EXECUTING (skip enforcement)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    with pytest.raises(IllegalTransitionError, match="INTELLIGENCE_PROCESSING -> EXECUTING"):
        sm.transition(State.EXECUTING)

def test_escalation_direct_completion():
    """Test: INTELLIGENCE_PROCESSING -> COMPLETED (skip enforcement)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    with pytest.raises(IllegalTransitionError, match="INTELLIGENCE_PROCESSING -> COMPLETED"):
        sm.transition(State.COMPLETED)


# ============================================================================
# LOOP TESTS - Backward Transitions
# ============================================================================

def test_loop_intelligence_to_safety():
    """Test: INTELLIGENCE_PROCESSING -> SAFETY_VALIDATING (backward)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    with pytest.raises(IllegalTransitionError, match="INTELLIGENCE_PROCESSING -> SAFETY_VALIDATING"):
        sm.transition(State.SAFETY_VALIDATING)

def test_loop_enforcement_to_intelligence():
    """Test: ENFORCEMENT_VALIDATING -> INTELLIGENCE_PROCESSING (backward)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    with pytest.raises(IllegalTransitionError, match="ENFORCEMENT_VALIDATING -> INTELLIGENCE_PROCESSING"):
        sm.transition(State.INTELLIGENCE_PROCESSING)

def test_loop_executing_to_enforcement():
    """Test: EXECUTING -> ENFORCEMENT_VALIDATING (backward)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_APPROVED)
    sm.transition(State.EXECUTING)
    with pytest.raises(IllegalTransitionError, match="EXECUTING -> ENFORCEMENT_VALIDATING"):
        sm.transition(State.ENFORCEMENT_VALIDATING)


# ============================================================================
# RESURRECTION TESTS - Terminal State Exits
# ============================================================================

def test_resurrection_safety_blocked():
    """Test: SAFETY_BLOCKED -> * (terminal exit)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_BLOCKED)
    
    # Try all possible transitions
    for state in State:
        if state != State.SAFETY_BLOCKED:
            with pytest.raises(IllegalTransitionError):
                sm.transition(state)

def test_resurrection_enforcement_blocked():
    """Test: ENFORCEMENT_BLOCKED -> * (terminal exit)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_BLOCKED)
    
    with pytest.raises(IllegalTransitionError):
        sm.transition(State.EXECUTING)

def test_resurrection_completed():
    """Test: COMPLETED -> * (terminal exit)"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_APPROVED)
    sm.transition(State.EXECUTING)
    sm.transition(State.COMPLETED)
    
    with pytest.raises(IllegalTransitionError):
        sm.transition(State.RECEIVED)

def test_resurrection_failed():
    """Test: FAILED -> * (terminal exit)"""
    sm = StateMachine()
    sm.transition(State.FAILED)
    
    with pytest.raises(IllegalTransitionError):
        sm.transition(State.RECEIVED)


# ============================================================================
# VALID PATH TESTS - Ensure legal transitions work
# ============================================================================

def test_valid_path_allow():
    """Test: Valid ALLOW path"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_APPROVED)
    sm.transition(State.EXECUTING)
    sm.transition(State.COMPLETED)
    
    assert sm.current_state == State.COMPLETED
    assert len(sm.history) == 8

def test_valid_path_rewrite():
    """Test: Valid REWRITE path"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_REWRITTEN)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_APPROVED)
    sm.transition(State.EXECUTING)
    sm.transition(State.COMPLETED)
    
    assert sm.current_state == State.COMPLETED
    assert len(sm.history) == 8

def test_valid_path_safety_block():
    """Test: Valid SAFETY_BLOCKED path"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_BLOCKED)
    
    assert sm.current_state == State.SAFETY_BLOCKED
    assert len(sm.history) == 3

def test_valid_path_enforcement_block():
    """Test: Valid ENFORCEMENT_BLOCKED path"""
    sm = StateMachine()
    sm.transition(State.SAFETY_VALIDATING)
    sm.transition(State.SAFETY_APPROVED)
    sm.transition(State.INTELLIGENCE_PROCESSING)
    sm.transition(State.ENFORCEMENT_VALIDATING)
    sm.transition(State.ENFORCEMENT_BLOCKED)
    
    assert sm.current_state == State.ENFORCEMENT_BLOCKED
    assert len(sm.history) == 6


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
