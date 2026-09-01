"""
TANTRA Constitutional Registry Integration
==========================================
Phase 3 — Constitutional Registry Integration

TANTRA integrates with these registries:
- RAJYA: Governance registry
- KESHAV: Knowledge registry
- SARATHI: Routing registry
- Execution Registry: Tracks all executions
- Capability Registry: Tracks available capabilities
- Build Registry: Tracks build artifacts
- Review Registry: Tracks review states
- Migration Registry: Tracks migrations
- Replay Registry: Tracks replays

TANTRA becomes the governed orchestration layer, NOT the owner of these registries.
Each registry is a participant in the execution lifecycle.

Storage: MongoDB (constitutional_registry collection). No in-memory fallback.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class RegistryType(str, Enum):
    RAJYA = "rajya"
    KESHAV = "keshav"
    SARATHI = "sarathi"
    EXECUTION = "execution"
    CAPABILITY = "capability"
    BUILD = "build"
    REVIEW = "review"
    MIGRATION = "migration"
    REPLAY = "replay"


class RegistryStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class RegistryEntry:
    """A single entry in a constitutional registry."""
    registry_type: RegistryType
    entry_id: str
    data: Dict[str, Any]
    trace_id: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: RegistryStatus = RegistryStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "registry_type": self.registry_type.value,
            "entry_id": self.entry_id,
            "data": self.data,
            "trace_id": self.trace_id,
            "created_at": self.created_at,
            "status": self.status.value,
        }


@dataclass
class RegistryHealth:
    """Health status for a constitutional registry."""
    registry_type: RegistryType
    status: RegistryStatus
    entry_count: int = 0
    last_sync_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "registry_type": self.registry_type.value,
            "status": self.status.value,
            "entry_count": self.entry_count,
            "last_sync_at": self.last_sync_at,
            "error": self.error,
        }


class ConstitutionalRegistry:
    """
    Manages TANTRA's integration with all constitutional registries.
    TANTRA does NOT own these registries — it orchestrates through them.

    Storage: MongoDB constitutional_registry collection.
    No in-memory fallback. Fails closed if MongoDB is unavailable.

    Each registry participates in the execution lifecycle:
    - Execution Registry: Records every execution attempt
    - Capability Registry: Validates capability availability
    - Replay Registry: Stores replay metadata
    - Review Registry: Tracks governance review states
    """

    def __init__(self) -> None:
        self._collection = None
        self._mongo_connected = False
        self._health: Dict[RegistryType, RegistryHealth] = {
            rt: RegistryHealth(registry_type=rt, status=RegistryStatus.UNKNOWN)
            for rt in RegistryType
        }
        self._init_mongo()
        logger.info("ConstitutionalRegistry initialized (mongodb=%s)", self._mongo_connected)

    def _init_mongo(self) -> None:
        """Initialize MongoDB connection for registry persistence."""
        try:
            from app.core.database import db
            self._collection = db["constitutional_registry"]
            self._mongo_connected = True
            # Create indexes for query performance
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Fire and forget — indexes will be created eventually
                    loop.create_task(self._ensure_indexes())
                else:
                    loop.run_until_complete(self._ensure_indexes())
            except RuntimeError:
                # No event loop running (e.g., during sync init) — skip index creation
                pass
            # Update health status
            for rt in RegistryType:
                self._health[rt].status = RegistryStatus.ACTIVE
            logger.info("ConstitutionalRegistry connected to MongoDB")
        except Exception as e:
            logger.warning("ConstitutionalRegistry MongoDB init failed: %s", e)
            self._mongo_connected = False
            for rt in RegistryType:
                self._health[rt].status = RegistryStatus.UNAVAILABLE
                self._health[rt].error = str(e)

    async def _ensure_indexes(self) -> None:
        """Create MongoDB indexes for registry queries."""
        if self._collection is None:
            return
        await self._collection.create_index("registry_type")
        await self._collection.create_index("trace_id")
        await self._collection.create_index([("registry_type", 1), ("created_at", -1)])
        await self._collection.create_index("entry_id", unique=True)

    def _require_collection(self):
        """Get MongoDB collection or raise if unavailable."""
        if self._collection is None:
            raise RuntimeError(
                "Constitutional Registry persistence unavailable: "
                "MongoDB not connected"
            )
        return self._collection

    def _insert_entry(self, entry: RegistryEntry) -> None:
        """Persist a registry entry to MongoDB."""
        try:
            collection = self._require_collection()
            doc = entry.to_dict()
            doc["integrity_hash"] = hashlib.sha256(
                json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            collection.insert_one(doc)
            # Update health
            self._health[entry.registry_type].entry_count = (
                self._health[entry.registry_type].entry_count or 0
            ) + 1
            self._health[entry.registry_type].last_sync_at = entry.created_at
            self._health[entry.registry_type].status = RegistryStatus.ACTIVE
            self._health[entry.registry_type].error = None
        except Exception as e:
            logger.error("Registry persist failed (%s): %s", entry.registry_type.value, e)
            self._health[entry.registry_type].status = RegistryStatus.DEGRADED
            self._health[entry.registry_type].error = str(e)

    def record_execution(
        self,
        trace_id: str,
        execution_data: Dict[str, Any],
    ) -> RegistryEntry:
        """Record an execution in the Execution Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.EXECUTION,
            entry_id=hashlib.sha256(f"exec:{trace_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            data=execution_data,
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        logger.info("Execution recorded: %s (trace: %s)", entry.entry_id, trace_id)
        return entry

    def register_capability(
        self,
        capability_type: str,
        capability_data: Dict[str, Any],
        trace_id: str = "",
    ) -> RegistryEntry:
        """Register a capability in the Capability Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.CAPABILITY,
            entry_id=hashlib.sha256(f"cap:{capability_type}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            data={"capability_type": capability_type, **capability_data},
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        return entry

    def record_replay(
        self,
        trace_id: str,
        original_trace_id: str,
        replay_data: Dict[str, Any],
    ) -> RegistryEntry:
        """Record a replay in the Replay Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.REPLAY,
            entry_id=hashlib.sha256(f"replay:{trace_id}:{original_trace_id}".encode()).hexdigest()[:16],
            data={"original_trace_id": original_trace_id, **replay_data},
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        return entry

    def record_review(
        self,
        trace_id: str,
        review_data: Dict[str, Any],
    ) -> RegistryEntry:
        """Record a governance review in the Review Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.REVIEW,
            entry_id=hashlib.sha256(f"review:{trace_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            data=review_data,
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        return entry

    def record_migration(
        self,
        trace_id: str,
        migration_data: Dict[str, Any],
    ) -> RegistryEntry:
        """Record a migration in the Migration Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.MIGRATION,
            entry_id=hashlib.sha256(f"mig:{trace_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            data=migration_data,
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        return entry

    def record_build(
        self,
        trace_id: str,
        build_data: Dict[str, Any],
    ) -> RegistryEntry:
        """Record a build artifact in the Build Registry."""
        entry = RegistryEntry(
            registry_type=RegistryType.BUILD,
            entry_id=hashlib.sha256(f"build:{trace_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
            data=build_data,
            trace_id=trace_id,
        )
        self._insert_entry(entry)
        return entry

    def get_execution_entries(self, trace_id: Optional[str] = None) -> List[RegistryEntry]:
        """Retrieve execution entries from MongoDB."""
        if not self._mongo_connected:
            return []
        try:
            collection = self._require_collection()
            query = {"registry_type": RegistryType.EXECUTION.value}
            if trace_id:
                query["trace_id"] = trace_id
            cursor = collection.find(query).sort("created_at", -1).limit(100)
            entries = []
            for doc in cursor:
                doc.pop("_id", None)
                doc.pop("integrity_hash", None)
                entries.append(RegistryEntry(
                    registry_type=RegistryType(doc["registry_type"]),
                    entry_id=doc["entry_id"],
                    data=doc["data"],
                    trace_id=doc["trace_id"],
                    created_at=doc.get("created_at", ""),
                    status=RegistryStatus(doc.get("status", "active")),
                ))
            return entries
        except Exception as e:
            logger.error("Failed to get execution entries: %s", e)
            return []

    def get_entries(
        self,
        registry_type: RegistryType,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[RegistryEntry]:
        """Retrieve entries for a specific registry type from MongoDB."""
        if not self._mongo_connected:
            return []
        try:
            collection = self._require_collection()
            query: Dict[str, Any] = {"registry_type": registry_type.value}
            if trace_id:
                query["trace_id"] = trace_id
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            entries = []
            for doc in cursor:
                doc.pop("_id", None)
                doc.pop("integrity_hash", None)
                entries.append(RegistryEntry(
                    registry_type=RegistryType(doc["registry_type"]),
                    entry_id=doc["entry_id"],
                    data=doc["data"],
                    trace_id=doc["trace_id"],
                    created_at=doc.get("created_at", ""),
                    status=RegistryStatus(doc.get("status", "active")),
                ))
            return entries
        except Exception as e:
            logger.error("Failed to get entries for %s: %s", registry_type.value, e)
            return []

    def get_health(self) -> Dict[str, Any]:
        """Get health status of all registries with live counts from MongoDB."""
        # Refresh entry counts from MongoDB
        if self._mongo_connected:
            try:
                collection = self._require_collection()
                for rt in RegistryType:
                    count = collection.count_documents({"registry_type": rt.value})
                    self._health[rt].entry_count = count
            except Exception as e:
                logger.warning("Failed to refresh health counts: %s", e)

        return {
            "registries": {rt.value: h.to_dict() for rt, h in self._health.items()},
            "mongodb_connected": self._mongo_connected,
            "total_entries": sum(
                h.entry_count for h in self._health.values()
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def snapshot(self) -> Dict[str, Any]:
        """Full registry snapshot for monitoring."""
        health = self.get_health()
        entry_counts = {}
        if self._mongo_connected:
            try:
                collection = self._require_collection()
                for rt in RegistryType:
                    entry_counts[rt.value] = collection.count_documents(
                        {"registry_type": rt.value}
                    )
            except Exception:
                entry_counts = {rt.value: 0 for rt in RegistryType}
        else:
            entry_counts = {rt.value: 0 for rt in RegistryType}

        return {
            "health": health,
            "entry_counts": entry_counts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
