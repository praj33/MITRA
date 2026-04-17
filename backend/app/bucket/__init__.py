"""
Mitra Bucket Package — Embedded from BHIV Bucket Service

Append-only artifact storage with tamper-evident hash chains.
Core philosophy: Bucket is MEMORY, never DECISION.

Components:
  - AppendOnlyStorage: JSONL hash-chain storage
  - ArtifactSchema: Envelope validation
  - HashService: Deterministic SHA256
"""

from app.bucket.hash_service import deterministic_hash, compute_artifact_hash, verify_artifact_hash
from app.bucket.artifact_schema import validate_artifact, REQUIRED_ENVELOPE_FIELDS

__all__ = [
    "deterministic_hash",
    "compute_artifact_hash",
    "verify_artifact_hash",
    "validate_artifact",
    "REQUIRED_ENVELOPE_FIELDS",
]
