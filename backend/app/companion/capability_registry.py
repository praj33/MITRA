"""
capability_registry.py — Mitra Capability Registry

Central registry for all Mitra capabilities.
Capabilities are attached at startup and can be added/removed at runtime.
No capability is hardcoded — all are pluggable via register().
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.capabilities.base_capability import BaseCapability, CapabilityResult

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """
    Manages all registered capabilities.
    Provides intent-based routing to the correct capability.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, BaseCapability] = {}
        self._intent_map: Dict[str, str] = {}  # intent → capability name

    def register(self, capability: BaseCapability) -> None:
        """Attach a capability to the registry."""
        if capability.name in self._registry:
            logger.warning("Capability '%s' already registered — replacing.", capability.name)
        self._registry[capability.name] = capability
        for intent in capability.supported_intents:
            self._intent_map[intent] = capability.name
        logger.info("Capability registered: %s (intents: %s)", capability.name, capability.supported_intents)

    def unregister(self, name: str) -> None:
        """Detach a capability from the registry."""
        cap = self._registry.pop(name, None)
        if cap:
            for intent in cap.supported_intents:
                self._intent_map.pop(intent, None)
            logger.info("Capability unregistered: %s", name)

    def get(self, name: str) -> Optional[BaseCapability]:
        """Get capability by name."""
        return self._registry.get(name)

    def resolve(self, intent: str) -> Optional[BaseCapability]:
        """Get the capability that handles this intent."""
        name = self._intent_map.get(intent)
        if name:
            return self._registry.get(name)
        return None

    async def execute(
        self,
        intent: str,
        params: Dict,
        trace_id: Optional[str] = None,
    ) -> Optional[CapabilityResult]:
        """
        Route intent to the correct capability and execute.
        Returns None if no capability handles this intent.
        """
        cap = self.resolve(intent)
        if not cap:
            logger.debug("No capability found for intent: %s", intent)
            return None
        try:
            return await cap.execute(intent, params, trace_id)
        except Exception as exc:
            logger.exception("Capability '%s' failed for intent '%s': %s", cap.name, intent, exc)
            return CapabilityResult.error_result(cap.name, intent, str(exc), trace_id)

    def list_capabilities(self) -> List[Dict]:
        """Return a summary of all registered capabilities."""
        return [
            {
                "name": cap.name,
                "description": cap.description,
                "intents": cap.supported_intents,
            }
            for cap in self._registry.values()
        ]

    @property
    def intent_map(self) -> Dict[str, str]:
        return dict(self._intent_map)

    def __len__(self) -> int:
        return len(self._registry)

    def __repr__(self) -> str:
        return f"<CapabilityRegistry: {list(self._registry.keys())}>"


# Singleton registry
capability_registry = CapabilityRegistry()
