"""
policy_engine.py — Safety Policy Runtime (Embedded in Mitra)

Loads policy rules from JSON files, evaluates user input,
and produces structured safety decisions.

Supports: Mitra, Creator Core, future BHIV products.
"""

import re
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PolicyDecision(str, Enum):
    ALLOW  = "ALLOW"
    BLOCK  = "BLOCK"
    REWRITE = "REWRITE"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    rule_id: str
    category: str
    confidence: float
    trace_id: str
    matched_pattern: str
    reason: str
    timestamp: str
    system: str  # mitra | creator_core | bhiv
    policy_version: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision":        self.decision.value,
            "rule_id":         self.rule_id,
            "category":        self.category,
            "confidence":      self.confidence,
            "trace_id":        self.trace_id,
            "matched_pattern": self.matched_pattern,
            "reason":          self.reason,
            "timestamp":       self.timestamp,
            "system":          self.system,
            "policy_version":  self.policy_version,
        }


class PolicyEngine:
    """
    Loads content_rules.json, behavior_rules.json, regional_rules.json
    and evaluates input against them in priority order:
      1. Regional overrides (if region provided)
      2. Content rules  (BLOCK-first)
      3. Behavior rules (REWRITE-second)
    """

    POLICY_FILES = {
        "content":   "content_rules.json",
        "behavior":  "behavior_rules.json",
        "regional":  "regional_rules.json",
        "registry":  "policy_registry.json",
    }

    def __init__(self, policy_dir: Optional[str] = None):
        self.policy_dir = policy_dir or os.path.dirname(os.path.abspath(__file__))
        self._content_rules:  List[Dict] = []
        self._behavior_rules: List[Dict] = []
        self._regional_rules: Dict       = {}
        self._policy_version: str        = "unknown"
        self._load_policies()

    def _load_policies(self) -> None:
        self._content_rules  = self._load_file("content_rules.json").get("rules", [])
        self._behavior_rules = self._load_file("behavior_rules.json").get("rules", [])
        self._regional_rules = self._load_file("regional_rules.json").get("regions", {})
        registry = self._load_file("policy_registry.json")
        self._policy_version = registry.get("current_version", "unknown")

    def _load_file(self, filename: str) -> Dict:
        path = os.path.join(self.policy_dir, filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate(
        self,
        text: str,
        system: str = "mitra",
        region: Optional[str] = None,
    ) -> PolicyResult:
        trace_id  = self._make_trace_id(text, system)
        timestamp = datetime.now().isoformat() + "Z"
        text_lower = text.lower()

        # 1. Regional overrides
        if region:
            result = self._check_regional(text_lower, region, trace_id, timestamp, system)
            if result:
                return result

        # 2. Content rules (BLOCK priority)
        for rule in self._content_rules:
            if rule.get("decision") != "BLOCK":
                continue
            match = self._match_patterns(text_lower, rule["patterns"])
            if match:
                return PolicyResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id=rule["id"],
                    category=rule["category"],
                    confidence=float(rule.get("confidence_threshold", 85)),
                    trace_id=trace_id,
                    matched_pattern=match,
                    reason=f"Content rule {rule['id']} matched: {rule['category']}",
                    timestamp=timestamp,
                    system=system,
                    policy_version=self._policy_version,
                )

        # 3. Content rules (REWRITE)
        for rule in self._content_rules:
            if rule.get("decision") != "REWRITE":
                continue
            match = self._match_patterns(text_lower, rule["patterns"])
            if match:
                return PolicyResult(
                    decision=PolicyDecision.REWRITE,
                    rule_id=rule["id"],
                    category=rule["category"],
                    confidence=float(rule.get("confidence_threshold", 65)),
                    trace_id=trace_id,
                    matched_pattern=match,
                    reason=f"Content rule {rule['id']} matched: {rule['category']}",
                    timestamp=timestamp,
                    system=system,
                    policy_version=self._policy_version,
                )

        # 4. Behavior rules (BLOCK priority)
        for rule in self._behavior_rules:
            if rule.get("decision") != "BLOCK":
                continue
            match = self._match_patterns(text_lower, rule["patterns"])
            if match:
                return PolicyResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id=rule["id"],
                    category=rule["category"],
                    confidence=float(rule.get("confidence_threshold", 85)),
                    trace_id=trace_id,
                    matched_pattern=match,
                    reason=f"Behavior rule {rule['id']} matched: {rule['category']}",
                    timestamp=timestamp,
                    system=system,
                    policy_version=self._policy_version,
                )

        # 5. Behavior rules (REWRITE)
        for rule in self._behavior_rules:
            if rule.get("decision") != "REWRITE":
                continue
            match = self._match_patterns(text_lower, rule["patterns"])
            if match:
                return PolicyResult(
                    decision=PolicyDecision.REWRITE,
                    rule_id=rule["id"],
                    category=rule["category"],
                    confidence=float(rule.get("confidence_threshold", 65)),
                    trace_id=trace_id,
                    matched_pattern=match,
                    reason=f"Behavior rule {rule['id']} matched: {rule['category']}",
                    timestamp=timestamp,
                    system=system,
                    policy_version=self._policy_version,
                )

        # 6. Clean — no rules matched
        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            rule_id="NONE",
            category="clean",
            confidence=0.0,
            trace_id=trace_id,
            matched_pattern="",
            reason="No policy rules matched",
            timestamp=timestamp,
            system=system,
            policy_version=self._policy_version,
        )

    def _check_regional(self, text_lower, region, trace_id, timestamp, system):
        region_config = self._regional_rules.get(region, self._regional_rules.get("DEFAULT", {}))
        for rule in region_config.get("additional_rules", []):
            match = self._match_patterns(text_lower, rule["patterns"])
            if match:
                return PolicyResult(
                    decision=PolicyDecision.BLOCK,
                    rule_id=rule["id"],
                    category=rule["category"],
                    confidence=90.0 * region_config.get("confidence_boost", 1.0),
                    trace_id=trace_id,
                    matched_pattern=match,
                    reason=f"Regional rule {rule['id']} ({region}) matched: {rule['category']}",
                    timestamp=timestamp,
                    system=system,
                    policy_version=self._policy_version,
                )
        return None

    def _match_patterns(self, text_lower: str, patterns: List[str]) -> str:
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return pattern
        return ""

    def _make_trace_id(self, text: str, system: str) -> str:
        raw = f"{text}:{system}:{datetime.now().isoformat()}"
        return f"policy_{hashlib.md5(raw.encode()).hexdigest()[:12]}"


# Global singleton
_engine: Optional[PolicyEngine] = None

def get_policy_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine


def evaluate_policy(
    text: str,
    system: str = "mitra",
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Public API — evaluate text against all loaded policies."""
    return get_policy_engine().evaluate(text, system=system, region=region).to_dict()
