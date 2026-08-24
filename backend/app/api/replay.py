"""
MITRA Replay API Endpoint
-------------------------
Provides trace-based replay for governance and testing.
Includes disaster recovery replay proof generation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.core.logging import get_logger
from app.replay.harness import ReplayHarness

logger = get_logger(__name__)

router = APIRouter()


class ReplayRequest(BaseModel):
    modifications: Optional[Dict[str, Any]] = None


class CompareRequest(BaseModel):
    trace_id: str


@router.post("/api/replay/{trace_id}")
async def replay_trace(
    trace_id: str,
    request: ReplayRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Replay a historical trace through the Mitra pipeline.

    Args:
        trace_id: The trace_id to replay
        modifications: Optional modifications to apply to the original request

    Returns:
        ReplayResult with original stages and replayed response
    """
    harness = ReplayHarness()

    result = await harness.replay(
        trace_id=trace_id,
        modifications=request.modifications,
    )

    return result.to_dict()


@router.get("/api/replay/{trace_id}/stages")
async def get_trace_stages(
    trace_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get all stages for a given trace_id from the bucket.
    """
    harness = ReplayHarness()
    stages = harness.load_trace(trace_id)

    return {
        "trace_id": trace_id,
        "stages_count": len(stages),
        "stages": [
            {
                "stage": s.get("stage"),
                "timestamp": s.get("timestamp"),
                "artifact_locator": s.get("artifact_locator"),
            }
            for s in stages
        ],
    }


@router.post("/api/replay/compare")
async def compare_traces(
    request: CompareRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Compare original and replayed responses for a trace.
    """
    harness = ReplayHarness()

    # Load original
    stages = harness.load_trace(request.trace_id)
    original_request = harness.extract_original_request(stages)

    if not original_request:
        return {"error": "Could not extract original request"}

    # Replay
    result = await harness.replay(request.trace_id)

    if not result.success:
        return {"error": result.error}

    # Compare
    comparison = harness.compare(
        original=original_request,
        replayed=result.replayed_response,
    )

    return {
        "trace_id": request.trace_id,
        "comparison": comparison,
        "replayed_response": result.replayed_response,
    }


# ============================================================
# DISASTER RECOVERY REPLAY PROOF ENDPOINTS
# ============================================================

@router.post("/api/replay/{trace_id}/dr-proof")
async def generate_dr_proof(
    trace_id: str,
    request: ReplayRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Generate disaster recovery replay proof.
    Demonstrates ability to recover from failure by replaying historical traces.
    
    Returns:
        DisasterRecoveryProof with integrity verification
    """
    harness = ReplayHarness()
    
    proof = await harness.replay_with_dr_proof(
        trace_id=trace_id,
        modifications=request.modifications,
    )
    
    from dataclasses import asdict
    return {
        "status": "ok",
        "proof": asdict(proof),
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/replay/dr-proofs")
async def get_dr_proofs(
    limit: int = 100,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get all disaster recovery replay proofs.
    Provides evidence of system recoverability.
    """
    harness = ReplayHarness()
    proofs = harness.get_dr_proofs(limit=limit)
    
    from dataclasses import asdict
    return {
        "status": "ok",
        "total_proofs": len(proofs),
        "proofs": [asdict(p) for p in proofs],
        "summary": harness.get_dr_summary(),
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/replay/dr-proof/{trace_id}")
async def get_dr_proof_by_trace_id(
    trace_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get DR proof for a specific trace_id.
    """
    harness = ReplayHarness()
    proof = harness.get_dr_proof_by_trace_id(trace_id)
    
    if not proof:
        return {"error": f"No DR proof found for trace_id: {trace_id}"}
    
    from dataclasses import asdict
    return {
        "status": "ok",
        "proof": asdict(proof),
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/replay/verify-dr-proof/{trace_id}")
async def verify_dr_proof(
    trace_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Verify the integrity of a DR proof by re-loading original trace.
    Ensures proof has not been tampered with.
    """
    harness = ReplayHarness()
    proof = harness.get_dr_proof_by_trace_id(trace_id)
    
    if not proof:
        return {"error": f"No DR proof found for trace_id: {trace_id}"}
    
    is_valid = harness.verify_dr_proof_integrity(proof)
    
    return {
        "status": "ok",
        "trace_id": trace_id,
        "valid": is_valid,
        "proof_id": proof.proof_id,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/replay/dr-summary")
async def get_dr_summary(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get summary of all disaster recovery proofs.
    Shows system recoverability metrics.
    """
    harness = ReplayHarness()
    summary = harness.get_dr_summary()
    
    return {
        "status": "ok",
        "summary": summary,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
    }
