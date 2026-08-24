"""
BHIV Ecosystem Adapter Registry
--------------------------------
Central registry managing all BHIV product adapters.
Provides discovery, health monitoring, and routing for Mitra integrations.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Type

from app.ecosystem.base_adapter import (
    AdapterHealth,
    AdapterStatus,
    BaseBHIVAdapter,
    IntegrationProtocol,
)

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Central registry for all BHIV product adapters.
    Singleton pattern - one registry per Mitra instance.
    """

    _instance: Optional["AdapterRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._adapters: Dict[str, BaseBHIVAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseBHIVAdapter]] = {}
        self._initialized = True
        logger.info("AdapterRegistry initialized")

    def register_adapter_class(self, product_name: str, adapter_class: Type[BaseBHIVAdapter]):
        """Register an adapter class (lazy instantiation)."""
        self._adapter_classes[product_name] = adapter_class
        logger.info(f"Registered adapter class for {product_name}")

    def get_adapter(self, product_name: str) -> Optional[BaseBHIVAdapter]:
        """Get or instantiate an adapter for a BHIV product."""
        if product_name in self._adapters:
            return self._adapters[product_name]

        if product_name in self._adapter_classes:
            try:
                adapter = self._adapter_classes[product_name]()
                self._adapters[product_name] = adapter
                logger.info(f"Instantiated adapter for {product_name}")
                return adapter
            except Exception as e:
                logger.error(f"Failed to instantiate adapter for {product_name}: {e}")
                return None

        logger.warning(f"No adapter registered for {product_name}")
        return None

    def list_products(self) -> List[str]:
        """List all registered BHIV products."""
        return list(self._adapter_classes.keys())

    def list_active_adapters(self) -> List[str]:
        """List all instantiated (active) adapters."""
        return list(self._adapters.keys())

    async def health_check_all(self) -> Dict[str, Any]:
        """Get health status of all active adapters."""
        health = {}
        for name, adapter in self._adapters.items():
            try:
                health[name] = await adapter.health_check()
            except Exception as e:
                health[name] = {
                    "product": name,
                    "status": AdapterStatus.UNHEALTHY.value,
                    "error": str(e),
                }
        return health

    def get_manifests(self) -> Dict[str, Any]:
        """Get integration manifests for all registered adapters."""
        manifests = {}
        for name, adapter_class in self._adapter_classes.items():
            try:
                adapter = adapter_class()
                manifests[name] = adapter.manifest
            except Exception as e:
                logger.error(f"Failed to get manifest for {name}: {e}")
        return manifests

    def snapshot(self) -> Dict[str, Any]:
        """Get full registry snapshot for monitoring."""
        return {
            "registered_products": self.list_products(),
            "active_adapters": self.list_active_adapters(),
            "manifests": self.get_manifests(),
        }


def register_all_adapters():
    """
    Register all BHIV product adapter classes.
    Called once at startup.
    """
    registry = AdapterRegistry()

    from app.ecosystem.adapters.uniguru_adapter import UniGuruAdapter
    from app.ecosystem.adapters.setu_adapter import SETUAdapter
    from app.ecosystem.adapters.gurukul_adapter import GurukulAdapter
    from app.ecosystem.adapters.samruddhi_adapter import SamruddhiAdapter
    from app.ecosystem.adapters.namami_gange_adapter import NamamiGangeAdapter
    from app.ecosystem.adapters.svacs_adapter import SVACSAdapter
    from app.ecosystem.adapters.uccis_adapter import UCCISAdapter
    from app.ecosystem.adapters.nyai_adapter import NYAIAdapter
    from app.ecosystem.adapters.brahmanda_adapter import BrahmandaAdapter
    from app.ecosystem.adapters.bucket_adapter import BucketAdapter
    from app.ecosystem.adapters.tantra_adapter import TANTRAAdapter

    adapters = [
        ("UniGuru", UniGuruAdapter),
        ("SETU", SETUAdapter),
        ("Gurukul", GurukulAdapter),
        ("Samruddhi", SamruddhiAdapter),
        ("NamamiGange", NamamiGangeAdapter),
        ("SVACS", SVACSAdapter),
        ("UCCIS", UCCISAdapter),
        ("NYAI", NYAIAdapter),
        ("Brahmanda", BrahmandaAdapter),
        ("Bucket", BucketAdapter),
        ("TANTRA", TANTRAAdapter),
    ]

    for name, cls in adapters:
        registry.register_adapter_class(name, cls)

    logger.info(f"Registered {len(adapters)} BHIV product adapters")
