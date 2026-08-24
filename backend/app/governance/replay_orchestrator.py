"""
replay_orchestrator.py - Deterministic replay harness for AI-Being
Captures intent → states → outputs for replay verification
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class StateSnapshot:
    """Immutable state snapshot"""
    state_id: str
    state_name: str
    timestamp: str
    data: Dict[str, Any]
    hash: str

@dataclass
class Transition:
    """State transition record"""
    from_state: str
    to_state: str
    trigger: str
    timestamp: str
    hash: str

@dataclass
class ReplayLog:
    """Complete replay log"""
    request_id: str
    intent: Dict[str, Any]
    states: List[StateSnapshot]
    transitions: List[Transition]
    output: Dict[str, Any]
    replay_hash: str

class ReplayOrchestrator:
    """Orchestrator with replay capability"""
    
    def __init__(self):
        self.logs = []
    
    def hash_state(self, state: Dict[str, Any]) -> str:
        """Generate deterministic hash of state"""
        state_json = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()[:16]
    
    def capture_state(self, state_name: str, data: Dict[str, Any]) -> StateSnapshot:
        """Capture immutable state snapshot"""
        timestamp = datetime.now().isoformat()
        state_hash = self.hash_state(data)
        
        return StateSnapshot(
            state_id=f"{state_name}_{state_hash[:8]}",
            state_name=state_name,
            timestamp=timestamp,
            data=data,
            hash=state_hash
        )
    
    def record_transition(self, from_state: str, to_state: str, trigger: str) -> Transition:
        """Record state transition"""
        timestamp = datetime.now().isoformat()
        transition_data = f"{from_state}→{to_state}:{trigger}"
        transition_hash = hashlib.sha256(transition_data.encode()).hexdigest()[:16]
        
        return Transition(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            timestamp=timestamp,
            hash=transition_hash
        )
    
    def execute_workflow(self, intent: Dict[str, Any]) -> ReplayLog:
        """Execute workflow with full replay logging"""
        request_id = hashlib.sha256(json.dumps(intent, sort_keys=True).encode()).hexdigest()[:16]
        
        states = []
        transitions = []
        
        # State 1: RECEIVED
        state1 = self.capture_state("RECEIVED", {"content": intent["content"]})
        states.append(state1)
        
        # Transition: RECEIVED → SAFETY_VALIDATING
        trans1 = self.record_transition("RECEIVED", "SAFETY_VALIDATING", "auto")
        transitions.append(trans1)
        
        # State 2: SAFETY_VALIDATING
        state2 = self.capture_state("SAFETY_VALIDATING", {
            "content": intent["content"],
            "patterns_checked": True
        })
        states.append(state2)
        
        # Simulate safety decision
        safety_decision = "ALLOW" if "threat" not in intent["content"].lower() else "BLOCK"
        
        if safety_decision == "BLOCK":
            trans2 = self.record_transition("SAFETY_VALIDATING", "SAFETY_BLOCKED", "risk_detected")
            transitions.append(trans2)
            
            state3 = self.capture_state("SAFETY_BLOCKED", {
                "decision": "BLOCK",
                "reason": "Threat detected"
            })
            states.append(state3)
            
            output = {"decision": "BLOCK", "trace_id": request_id}
        else:
            trans2 = self.record_transition("SAFETY_VALIDATING", "SAFETY_APPROVED", "risk_clear")
            transitions.append(trans2)
            
            state3 = self.capture_state("SAFETY_APPROVED", {
                "decision": "ALLOW",
                "content": intent["content"]
            })
            states.append(state3)
            
            output = {"decision": "ALLOW", "trace_id": request_id}
        
        # Generate replay hash
        replay_data = {
            "intent": intent,
            "states": [s.hash for s in states],
            "transitions": [t.hash for t in transitions],
            "output": output
        }
        replay_hash = self.hash_state(replay_data)
        
        log = ReplayLog(
            request_id=request_id,
            intent=intent,
            states=states,
            transitions=transitions,
            output=output,
            replay_hash=replay_hash
        )
        
        self.logs.append(log)
        return log
    
    def replay_workflow(self, original_log: ReplayLog) -> ReplayLog:
        """Replay workflow from original log"""
        return self.execute_workflow(original_log.intent)
    
    def verify_replay(self, original: ReplayLog, replayed: ReplayLog) -> bool:
        """Verify replay produces identical output"""
        checks = [
            original.replay_hash == replayed.replay_hash,
            len(original.states) == len(replayed.states),
            len(original.transitions) == len(replayed.transitions),
            original.output == replayed.output
        ]
        return all(checks)
    
    def export_log(self, log: ReplayLog) -> str:
        """Export log as JSON"""
        return json.dumps({
            "request_id": log.request_id,
            "intent": log.intent,
            "states": [asdict(s) for s in log.states],
            "transitions": [asdict(t) for t in log.transitions],
            "output": log.output,
            "replay_hash": log.replay_hash
        }, indent=2)
