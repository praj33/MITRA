"""
MITRA Ecosystem Integration API
--------------------------------
Provides REST endpoints for BHIV product integration management.
Includes live runtime proof endpoints for integration verification.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.ecosystem.adapter_registry import AdapterRegistry, register_all_adapters
from app.ecosystem.base_adapter import IntegrationRequest
from app.services.ecosystem_integration_service import (
    get_ecosystem_integration_service,
    RuntimeProof,
    ExecutionProof,
)

logger = get_logger(__name__)

router = APIRouter()

# Initialize adapter registry at module load
register_all_adapters()


class EcosystemQueryRequest(BaseModel):
    product: str
    action: str
    payload: Optional[Dict[str, Any]] = None


class EcosystemExecuteRequest(BaseModel):
    product: str
    action: str
    payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class RuntimeProofRequest(BaseModel):
    """Request for generating runtime proof."""
    product: str
    action: str
    payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@router.get("/api/ecosystem/products")
async def list_ecosystem_products(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """List all registered BHIV products and their integration status."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "products": registry.list_products(),
        "active_adapters": registry.list_active_adapters(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/manifests")
async def get_ecosystem_manifests(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get integration manifests for all registered BHIV products."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "manifests": registry.get_manifests(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/health")
async def ecosystem_health_check(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Health check for all BHIV product integrations."""
    registry = AdapterRegistry()
    health = await registry.health_check_all()
    return {
        "status": "ok",
        "integrations": health,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/ecosystem/query")
async def ecosystem_query(
    request: EcosystemQueryRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Query data from a BHIV product through its adapter."""
    registry = AdapterRegistry()
    adapter = registry.get_adapter(request.product)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter registered for product: {request.product}",
        )

    integration_request = IntegrationRequest(
        action=request.action,
        payload=request.payload or {},
        trace_id=f"eco_q_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        source_product="mitra",
        target_product=request.product,
    )

    result = await adapter.query(integration_request)
    return result.to_dict()


@router.post("/api/ecosystem/execute")
async def ecosystem_execute(
    request: EcosystemExecuteRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Execute an action on a BHIV product through its adapter."""
    registry = AdapterRegistry()
    adapter = registry.get_adapter(request.product)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter registered for product: {request.product}",
        )

    integration_request = IntegrationRequest(
        action=request.action,
        payload=request.payload or {},
        trace_id=f"eco_e_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        source_product="mitra",
        target_product=request.product,
        user_id=request.user_id,
        session_id=request.session_id,
    )

    result = await adapter.execute(integration_request)
    return result.to_dict()


@router.get("/api/ecosystem/snapshot")
async def ecosystem_snapshot(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get full ecosystem registry snapshot for monitoring."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "snapshot": registry.snapshot(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ============================================================
# LIVE RUNTIME PROOF ENDPOINTS
# ============================================================

@router.post("/api/ecosystem/runtime-proof")
async def generate_runtime_proof(
    request: RuntimeProofRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Generate live runtime proof for BHIV product integration.
    Demonstrates actual integration with the product.
    """
    service = get_ecosystem_integration_service()

    proof = await service.execute_product_action(
        product=request.product,
        action=request.action,
        payload=request.payload or {},
        user_id=request.user_id,
        session_id=request.session_id,
    )

    from dataclasses import asdict
    return {
        "status": "ok",
        "proof": asdict(proof),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/ecosystem/query-proof")
async def generate_query_proof(
    request: RuntimeProofRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Generate live query proof for BHIV product integration.
    Demonstrates actual data retrieval from the product.
    """
    service = get_ecosystem_integration_service()

    proof = await service.query_product_data(
        product=request.product,
        action=request.action,
        payload=request.payload or {},
    )

    from dataclasses import asdict
    return {
        "status": "ok",
        "proof": asdict(proof),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/runtime-proofs")
async def get_runtime_proofs(
    product: Optional[str] = None,
    limit: int = 100,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get all runtime execution proofs.
    Provides evidence of live integration with BHIV products.
    """
    service = get_ecosystem_integration_service()
    proofs = service.get_runtime_proofs(product=product, limit=limit)

    from dataclasses import asdict
    return {
        "status": "ok",
        "total_proofs": len(proofs),
        "proofs": [asdict(p) for p in proofs],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/execution-proofs")
async def get_execution_proofs(
    platform: Optional[str] = None,
    limit: int = 100,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get all platform execution proofs.
    Provides evidence of live execution on WhatsApp, Email, Telegram, etc.
    """
    service = get_ecosystem_integration_service()
    proofs = service.get_execution_proofs(platform=platform, limit=limit)

    from dataclasses import asdict
    return {
        "status": "ok",
        "total_proofs": len(proofs),
        "proofs": [asdict(p) for p in proofs],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/integration-summary")
async def get_integration_summary(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Get summary of all integration proofs.
    Shows total integrations and execution evidence.
    """
    service = get_ecosystem_integration_service()
    summary = service.get_integration_summary()

    return {
        "status": "ok",
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/ecosystem/demonstrate")
async def demonstrate_ecosystem_integration(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Demonstrate live integration with all ecosystem products.
    Generates runtime proofs for each registered product.
    """
    service = get_ecosystem_integration_service()
    result = await service.demonstrate_ecosystem_integration()

    return {
        "status": "ok",
        "demonstration": result,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/verify-proof/{trace_id}")
async def verify_runtime_proof(
    trace_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """
    Verify the integrity of a runtime proof by trace_id.
    Ensures proof has not been tampered with.
    """
    service = get_ecosystem_integration_service()
    proofs = service.get_runtime_proofs()

    for proof in proofs:
        if proof.trace_id == trace_id:
            is_valid = service.verify_integrity(proof)
            from dataclasses import asdict
            return {
                "status": "ok",
                "trace_id": trace_id,
                "valid": is_valid,
                "proof": asdict(proof),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    raise HTTPException(
        status_code=404,
        detail=f"No proof found for trace_id: {trace_id}",
    )
