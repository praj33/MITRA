"""
causality_violation_tests.py - Tests for causality and dependency enforcement
"""

import pytest
from dependency-resolution-layer import (
    resolve_dependencies,
    validate_plan,
    check_temporal_preconditions,
    DependencyCycleError,
    DependencyReferenceError,
    CausalityViolationError,
)


def test_topological_order_deterministic_and_cycle_detection():
    actions = [
        {"id": "C", "kind": "compute", "requires": ["A", "B"]},
        {"id": "A", "kind": "validate", "requires": []},
        {"id": "B", "kind": "delegate", "requires": ["A"]},
    ]
    order = resolve_dependencies(actions)
    assert order == ["A", "B", "C"]

    # Introduce a cycle: A <- B <- C <- A
    actions_cycle = [
        {"id": "A", "kind": "validate", "requires": ["C"]},
        {"id": "B", "kind": "delegate", "requires": ["A"]},
        {"id": "C", "kind": "compute", "requires": ["B"]},
    ]
    with pytest.raises(DependencyCycleError):
        resolve_dependencies(actions_cycle)


def test_reference_integrity():
    actions = [
        {"id": "exec1", "kind": "execute", "requires": ["missing"]},
    ]
    with pytest.raises(DependencyReferenceError):
        resolve_dependencies(actions)


def test_temporal_gates_for_delegate_and_execute():
    # Delegate requires >= Validated
    with pytest.raises(CausalityViolationError):
        check_temporal_preconditions("Evaluated", "delegate")

    # Execute requires >= Delegated
    with pytest.raises(CausalityViolationError):
        check_temporal_preconditions("Validated", "execute")

    # Archived forbids any
    for kind in ["validate", "delegate", "execute", "compute", "io", "finalize"]:
        with pytest.raises(CausalityViolationError):
            check_temporal_preconditions("Archived", kind)


def test_execute_requires_validate_and_delegate_ancestors():
    actions = [
        {"id": "A", "kind": "validate", "requires": []},
        {"id": "B", "kind": "delegate", "requires": ["A"]},
        {"id": "X", "kind": "execute", "requires": ["B"]},
    ]
    # Missing validate ancestor for X (since B requires A, X has delegate ancestor but also validate via ancestry)
    # For clarity, make a failing case first
    actions_bad = [
        {"id": "B", "kind": "delegate", "requires": []},
        {"id": "X", "kind": "execute", "requires": ["B"]},
    ]
    with pytest.raises(CausalityViolationError, match="missing validate ancestor"):
        validate_plan(actions_bad, "Delegated")

    # Good plan passes when temporal state permits
    validate_plan(actions, "Delegated")


def test_delegation_requires_validation_ancestor():
    actions = [
        {"id": "D", "kind": "delegate", "requires": []},
    ]
    with pytest.raises(CausalityViolationError, match="missing validate ancestor"):
        validate_plan(actions, "Validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 
