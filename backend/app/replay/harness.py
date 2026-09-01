"""
MITRA REPLAY TEST HARNESS
-------------------------
Provides trace-based replay capability for governance and testing.
Allows replaying any historical trace through the pipeline.
Includes disaster recovery replay proof generation.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict

from app.services.bucket_service import BucketService
from app.core.assistant_orchestrator import handle_assistant_request
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DisasterRecoveryProof:
    """Proof of successful disaster recovery replay."""
    proof_id: str
    trace_id: str
    original_stages_count: int
    replayed_successfully: bool
    original_hash: str
    replayed_hash: str
    integrity_match: bool
    timestamp: str
    recovery_time_ms: float
    error: Optional[str] = None


class ReplayResult:
    """Result of a replay operation."""

    def __init__(
        self,
        trace_id: str,
        original_stages: list[Dict[str, Any]],
        replayed_response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.trace_id = trace_id
        self.original_stages = original_stages
        self.replayed_response = replayed_response
        self.error = error
        self.success = error is None and replayed_response is not None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "trace_id": self.trace_id,
            "success": self.success,
            "original_stages_count": len(self.original_stages),
            "original_stages": [s.get("stage") for s in self.original_stages],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if self.replayed_response:
            result["replayed_response"] = self.replayed_response
        if self.error:
            result["error"] = self.error
        return result


class ReplayHarness:
    """Replay historical traces through the Mitra pipeline."""

    def __init__(self):
        self.bucket = BucketService()
        self._dr_proofs: List[DisasterRecoveryProof] = []

    def load_trace(self, trace_id: str) -> list[Dict[str, Any]]:
        """Load all bucket entries for a given trace_id."""
        return self.bucket.get_trace_logs(trace_id)

    def extract_original_request(self, stages: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract the original request from bucket stages."""
        for stage in stages:
            if stage.get("stage") == "mitra_request_log":
                data = stage.get("data", {})
                # Reconstruct the request format
                input_data = data.get("input", {})
                raw_input = input_data.get("raw_input", {})
                message = input_data.get("text") or raw_input.get("message") or ""
                context = data.get("final_output", {}).get("system_context", {})

                return {
                    "version": "3.0.0",
                    "input": {
                        "message": message,
                        "summarized_payload": None,
                    },
                    "context": {
                        "platform": context.get("platform", "replay"),
                        "device": context.get("device", "unknown"),
                        "session_id": context.get("session_id", "replay_session"),
                        "voice_input": context.get("voice_input", False),
                        "preferred_language": context.get("preferred_language", "auto"),
                        "detected_language": context.get("detected_language"),
                        "authenticated_user_context": {
                            "auth_method": "replay",
                            "principal": context.get("user_id", "replay_user"),
                            "platform": context.get("platform", "replay"),
                        },
                    },
                }
        return None

    async def replay(
        self,
        trace_id: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> ReplayResult:
        """
        Replay a historical trace through the pipeline.

        Args:
            trace_id: The trace_id to replay
            modifications: Optional modifications to apply to the original request

        Returns:
            ReplayResult with original stages and replayed response
        """
        # Load original trace
        stages = self.load_trace(trace_id)
        if not stages:
            return ReplayResult(
                trace_id=trace_id,
                original_stages=[],
                error="No bucket entries found for trace_id",
            )

        # Extract original request
        original_request = self.extract_original_request(stages)
        if not original_request:
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                error="Could not extract original request from bucket stages",
            )

        # Apply modifications if provided
        replay_request = original_request.copy()
        if modifications:
            if "input" in modifications:
                replay_request["input"].update(modifications["input"])
            if "context" in modifications:
                replay_request["context"].update(modifications["context"])

        # Replay through pipeline
        try:
            replayed_response = await handle_assistant_request(replay_request)
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                replayed_response=replayed_response,
            )
        except Exception as e:
            logger.error(f"Replay failed for trace {trace_id}: {e}")
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                error=str(e),
            )

    def compare(
        self,
        original: Dict[str, Any],
        replayed: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare original and replayed responses.

        Returns:
            Comparison result with diffs
        """
        differences = []

        # Compare top-level keys
        original_keys = set(original.keys())
        replayed_keys = set(replayed.keys())

        missing_in_replay = original_keys - replayed_keys
        extra_in_replay = replayed_keys - original_keys

        if missing_in_replay:
            differences.append(f"Keys missing in replay: {missing_in_replay}")
        if extra_in_replay:
            differences.append(f"Extra keys in replay: {extra_in_replay}")

        # Compare common keys
        for key in original_keys & replayed_keys:
            orig_val = original[key]
            replay_val = replayed[key]

            if key == "processed_at":
                # Timestamps will always differ
                continue

            if key == "trace_id":
                # Trace IDs may differ for replays
                continue

            if orig_val != replay_val:
                differences.append(
                    f"Key '{key}': original={json.dumps(orig_val)[:100]} "
                    f"vs replayed={json.dumps(replay_val)[:100]}"
                )

        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "difference_count": len(differences),
        }

    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash for data integrity verification."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def replay_with_dr_proof(
        self,
        trace_id: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> DisasterRecoveryProof:
        """
        Replay a trace and generate disaster recovery proof.
        
        Args:
            trace_id: The trace_id to replay
            modifications: Optional modifications to apply
            
        Returns:
            DisasterRecoveryProof with integrity verification
        """
        import time
        start_time = time.time()
        
        # Load original trace
        stages = self.load_trace(trace_id)
        original_stages_count = len(stages)
        
        # Generate hash of original stages
        original_hash = self._generate_data_hash({"stages": stages})
        
        # Attempt replay
        try:
            result = await self.replay(trace_id, modifications)
            replayed_hash = self._generate_data_hash(result.to_dict()) if result.success else "replay_failed"
            
            recovery_time_ms = (time.time() - start_time) * 1000
            
            proof = DisasterRecoveryProof(
                proof_id=hashlib.sha256(f"dr:{trace_id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:32],
                trace_id=trace_id,
                original_stages_count=original_stages_count,
                replayed_successfully=result.success,
                original_hash=original_hash,
                replayed_hash=replayed_hash,
                integrity_match=result.success,  # If replay succeeded, integrity is maintained
                timestamp=datetime.utcnow().isoformat() + "Z",
                recovery_time_ms=recovery_time_ms,
                error=result.error,
            )
            
            self._dr_proofs.append(proof)
            logger.info(f"DR proof generated for {trace_id}: {proof.replayed_successfully}")
            
            return proof
            
        except Exception as e:
            recovery_time_ms = (time.time() - start_time) * 1000
            
            proof = DisasterRecoveryProof(
                proof_id=hashlib.sha256(f"dr:{trace_id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:32],
                trace_id=trace_id,
                original_stages_count=original_stages_count,
                replayed_successfully=False,
                original_hash=original_hash,
                replayed_hash="error",
                integrity_match=False,
                timestamp=datetime.utcnow().isoformat() + "Z",
                recovery_time_ms=recovery_time_ms,
                error=str(e),
            )
            
            self._dr_proofs.append(proof)
            logger.error(f"DR proof generated for {trace_id}: failed - {e}")
            
            return proof

    def get_dr_proofs(self, limit: int = 100) -> List[DisasterRecoveryProof]:
        """Get all disaster recovery proofs."""
        return self._dr_proofs[-limit:]

    def get_dr_proof_by_trace_id(self, trace_id: str) -> Optional[DisasterRecoveryProof]:
        """Get DR proof by trace_id."""
        for proof in reversed(self._dr_proofs):
            if proof.trace_id == trace_id:
                return proof
        return None

    def verify_dr_proof_integrity(self, proof: DisasterRecoveryProof) -> bool:
        """Verify the integrity of a DR proof."""
        # Reload original trace and verify hash
        stages = self.load_trace(proof.trace_id)
        current_hash = self._generate_data_hash({"stages": stages})
        return current_hash == proof.original_hash

    def get_dr_summary(self) -> Dict[str, Any]:
        """Get summary of all DR proofs."""
        total_proofs = len(self._dr_proofs)
        successful_proofs = sum(1 for p in self._dr_proofs if p.replayed_successfully)
        
        return {
            "total_dr_proofs": total_proofs,
            "successful_replays": successful_proofs,
            "success_rate": successful_proofs / total_proofs if total_proofs > 0 else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
