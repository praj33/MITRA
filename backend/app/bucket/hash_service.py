"""
Deterministic Hash Service for Artifact Integrity (Embedded in Mitra)
Provides SHA256 hashing with sorted keys for reproducibility.
"""

import hashlib
import json
from typing import Dict, Any


def deterministic_hash(payload: Dict[str, Any]) -> str:
    """Generate deterministic SHA256 hash of payload."""
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_artifact_hash(artifact: Dict[str, Any]) -> str:
    """Compute hash for artifact (excluding hash field itself)."""
    artifact_copy = {k: v for k, v in artifact.items() if k not in ("artifact_hash", "hash")}
    return deterministic_hash(artifact_copy)


def verify_artifact_hash(artifact: Dict[str, Any]) -> bool:
    """Verify artifact hash matches computed hash."""
    stored = artifact.get("artifact_hash") or artifact.get("hash")
    if not stored:
        return False
    computed = compute_artifact_hash(artifact)
    return computed == stored
