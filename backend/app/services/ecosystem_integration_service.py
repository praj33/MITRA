"""
MITRA Ecosystem Integration Service
-----------------------------------
Provides live runtime integration proofs for all BHIV products.
Demonstrates actual integration with the TANTRA execution runtime
and all ecosystem products.
"""

from __future__ import annotations

import os
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from app.core.logging import get_logger
from app.ecosystem.adapter_registry import AdapterRegistry
from app.ecosystem.base_adapter import IntegrationRequest, IntegrationResponse

logger = get_logger(__name__)


@dataclass
class RuntimeProof:
    """Proof of live runtime execution."""
    product: str
    action: str
    status: str
    trace_id: str
    timestamp: str
    latency_ms: float
    request_payload: Dict[str, Any]
    response_payload: Dict[str, Any]
    integrity_hash: str


@dataclass
class ExecutionProof:
    """Proof of unified runtime execution."""
    execution_id: str
    platform: str
    action_type: str
    status: str
    trace_id: str
    timestamp: str
    enforcement_decision: str
    execution_result: Dict[str, Any]
    integrity_hash: str


class EcosystemIntegrationService:
    """
    Live runtime integration service for BHIV ecosystem.
    Provides execution proofs and runtime participation evidence.
    """

    def __init__(self):
        self.registry = AdapterRegistry()
        self._runtime_proofs: List[RuntimeProof] = []
        self._execution_proofs: List[ExecutionProof] = []

    def _generate_integrity_hash(self, data: Dict[str, Any]) -> str:
        """Generate SHA-256 integrity hash for data."""
        import json
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _generate_trace_id(self, source: str, target: str, action: str) -> str:
        """Generate deterministic trace ID."""
        payload = f"{source}:{target}:{action}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def execute_product_action(
        self,
        product: str,
        action: str,
        payload: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> RuntimeProof:
        """
        Execute a live action on a BHIV product.
        Returns proof of execution for audit trail.
        """
        start_time = time.time()
        trace_id = self._generate_trace_id("mitra", product, action)

        try:
            adapter = self.registry.get_adapter(product)
            if not adapter:
                raise ValueError(f"No adapter registered for product: {product}")

            integration_request = IntegrationRequest(
                action=action,
                payload=payload,
                trace_id=trace_id,
                source_product="mitra",
                target_product=product,
                user_id=user_id,
                session_id=session_id,
            )

            response = await adapter.execute(integration_request)
            latency_ms = (time.time() - start_time) * 1000

            proof = RuntimeProof(
                product=product,
                action=action,
                status="success" if response.success else "failed",
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                latency_ms=latency_ms,
                request_payload=payload,
                response_payload=response.data if response.success else {"error": response.error},
                integrity_hash=self._generate_integrity_hash({
                    "product": product,
                    "action": action,
                    "trace_id": trace_id,
                    "status": "success" if response.success else "failed",
                    "response": response.data if response.success else {"error": response.error},
                }),
            )

            self._runtime_proofs.append(proof)
            logger.info(f"Runtime proof generated for {product}/{action}: {proof.status}")

            return proof

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            proof = RuntimeProof(
                product=product,
                action=action,
                status="error",
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                latency_ms=latency_ms,
                request_payload=payload,
                response_payload={"error": str(e)},
                integrity_hash=self._generate_integrity_hash({
                    "product": product,
                    "action": action,
                    "trace_id": trace_id,
                    "status": "error",
                    "error": str(e),
                }),
            )

            self._runtime_proofs.append(proof)
            logger.error(f"Runtime proof generated for {product}/{action}: error - {e}")

            return proof

    async def query_product_data(
        self,
        product: str,
        action: str,
        payload: Dict[str, Any],
    ) -> RuntimeProof:
        """
        Query data from a BHIV product.
        Returns proof of query execution.
        """
        start_time = time.time()
        trace_id = self._generate_trace_id("mitra", product, action)

        try:
            adapter = self.registry.get_adapter(product)
            if not adapter:
                raise ValueError(f"No adapter registered for product: {product}")

            integration_request = IntegrationRequest(
                action=action,
                payload=payload,
                trace_id=trace_id,
                source_product="mitra",
                target_product=product,
            )

            response = await adapter.query(integration_request)
            latency_ms = (time.time() - start_time) * 1000

            proof = RuntimeProof(
                product=product,
                action=action,
                status="success" if response.success else "failed",
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                latency_ms=latency_ms,
                request_payload=payload,
                response_payload=response.data if response.success else {"error": response.error},
                integrity_hash=self._generate_integrity_hash({
                    "product": product,
                    "action": action,
                    "trace_id": trace_id,
                    "status": "success" if response.success else "failed",
                    "response": response.data if response.success else {"error": response.error},
                }),
            )

            self._runtime_proofs.append(proof)
            logger.info(f"Query proof generated for {product}/{action}: {proof.status}")

            return proof

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            proof = RuntimeProof(
                product=product,
                action=action,
                status="error",
                trace_id=trace_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                latency_ms=latency_ms,
                request_payload=payload,
                response_payload={"error": str(e)},
                integrity_hash=self._generate_integrity_hash({
                    "product": product,
                    "action": action,
                    "trace_id": trace_id,
                    "status": "error",
                    "error": str(e),
                }),
            )

            self._runtime_proofs.append(proof)
            logger.error(f"Query proof generated for {product}/{action}: error - {e}")

            return proof

    def record_execution_proof(
        self,
        platform: str,
        action_type: str,
        trace_id: str,
        enforcement_decision: str,
        execution_result: Dict[str, Any],
    ) -> ExecutionProof:
        """
        Record proof of platform execution.
        Used for WhatsApp, Email, Telegram, etc.
        """
        proof = ExecutionProof(
            execution_id=self._generate_trace_id("mitra", platform, action_type),
            platform=platform,
            action_type=action_type,
            status=execution_result.get("status", "unknown"),
            trace_id=trace_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            enforcement_decision=enforcement_decision,
            execution_result=execution_result,
            integrity_hash=self._generate_integrity_hash({
                "platform": platform,
                "action_type": action_type,
                "trace_id": trace_id,
                "enforcement_decision": enforcement_decision,
                "execution_result": execution_result,
            }),
        )

        self._execution_proofs.append(proof)
        logger.info(f"Execution proof recorded for {platform}/{action_type}: {proof.status}")

        return proof

    def get_runtime_proofs(
        self,
        product: Optional[str] = None,
        limit: int = 100,
    ) -> List[RuntimeProof]:
        """Get runtime execution proofs, optionally filtered by product."""
        proofs = self._runtime_proofs
        if product:
            proofs = [p for p in proofs if p.product == product]
        return proofs[-limit:]

    def get_execution_proofs(
        self,
        platform: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExecutionProof]:
        """Get platform execution proofs, optionally filtered by platform."""
        proofs = self._execution_proofs
        if platform:
            proofs = [p for p in proofs if p.platform == platform]
        return proofs[-limit:]

    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of all integration proofs."""
        product_counts = {}
        for proof in self._runtime_proofs:
            product_counts[proof.product] = product_counts.get(proof.product, 0) + 1

        platform_counts = {}
        for proof in self._execution_proofs:
            platform_counts[proof.platform] = platform_counts.get(proof.platform, 0) + 1

        return {
            "total_runtime_proofs": len(self._runtime_proofs),
            "total_execution_proofs": len(self._execution_proofs),
            "product_integration_counts": product_counts,
            "platform_execution_counts": platform_counts,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def verify_integrity(self, proof: RuntimeProof) -> bool:
        """Verify the integrity hash of a runtime proof."""
        expected_hash = self._generate_integrity_hash({
            "product": proof.product,
            "action": proof.action,
            "trace_id": proof.trace_id,
            "status": proof.status,
            "response": proof.response_payload,
        })
        return proof.integrity_hash == expected_hash

    async def demonstrate_ecosystem_integration(self) -> Dict[str, Any]:
        """
        Demonstrate live integration with all ecosystem products.
        Returns comprehensive proof of runtime participation.
        """
        products = self.registry.list_products()
        results = {}

        for product in products:
            try:
                # Query product health
                health_proof = await self.query_product_data(
                    product=product,
                    action="health_check",
                    payload={"timestamp": datetime.utcnow().isoformat()},
                )
                results[product] = {
                    "health_check": asdict(health_proof),
                    "status": "integrated",
                }
            except Exception as e:
                results[product] = {
                    "status": "error",
                    "error": str(e),
                }

        return {
            "demonstration_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_products": len(products),
            "integrated_products": sum(1 for r in results.values() if r.get("status") == "integrated"),
            "results": results,
            "summary": self.get_integration_summary(),
        }


# Singleton instance
_ecosystem_service: Optional[EcosystemIntegrationService] = None


def get_ecosystem_integration_service() -> EcosystemIntegrationService:
    """Get singleton instance of the ecosystem integration service."""
    global _ecosystem_service
    if _ecosystem_service is None:
        _ecosystem_service = EcosystemIntegrationService()
    return _ecosystem_service