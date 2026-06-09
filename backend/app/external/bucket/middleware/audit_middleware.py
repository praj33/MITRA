from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AuditMiddleware:
    """Mongo-backed immutable audit trail. Persistence is mandatory."""

    def __init__(self, db=None):
        if db is None:
            raise RuntimeError("AuditMiddleware requires a persistent MongoDB database")
        self.audit_collection = db.audit_logs

    async def log_operation(
        self,
        operation_type: str,
        artifact_id: str,
        requester_id: str,
        integration_id: str,
        data_before: Optional[Dict] = None,
        data_after: Optional[Dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> str:
        result = self.audit_collection.insert_one(
            {
                "timestamp": datetime.now(timezone.utc),
                "operation_type": operation_type,
                "artifact_id": artifact_id,
                "requester_id": requester_id,
                "integration_id": integration_id,
                "status": status,
                "data_before": data_before,
                "data_after": data_after,
                "error_message": error_message,
                "immutable": True,
                "audit_version": "2.0",
            }
        )
        return str(result.inserted_id)

    async def get_artifact_history(self, artifact_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._serialize(
            self.audit_collection.find({"artifact_id": artifact_id}).sort("timestamp", 1).limit(limit)
        )

    async def get_user_activities(self, requester_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._serialize(
            self.audit_collection.find({"requester_id": requester_id}).sort("timestamp", -1).limit(limit)
        )

    async def get_recent_operations(
        self,
        limit: int = 100,
        operation_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = {"operation_type": operation_type} if operation_type else {}
        return self._serialize(self.audit_collection.find(query).sort("timestamp", -1).limit(limit))

    async def get_failed_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._serialize(
            self.audit_collection.find({"status": {"$in": ["failure", "blocked"]}})
            .sort("timestamp", -1)
            .limit(limit)
        )

    async def validate_immutability(self, artifact_id: str) -> bool:
        history = await self.get_artifact_history(artifact_id, limit=100)
        if not history:
            return False
        operations = {entry.get("operation_type") for entry in history}
        return not bool(operations & {"UPDATE", "DELETE"})

    @staticmethod
    def enforce_worm(operation_type: str, artifact_class: str) -> bool:
        immutable_classes = {
            "audit_entry",
            "model_checkpoint",
            "metadata",
            "iteration_history",
            "event_history",
        }
        return not (artifact_class in immutable_classes and operation_type in {"UPDATE", "DELETE"})

    @staticmethod
    def _serialize(cursor) -> List[Dict[str, Any]]:
        entries = []
        for entry in cursor:
            entry = dict(entry)
            if "_id" in entry:
                entry["_id"] = str(entry["_id"])
            entries.append(entry)
        return entries
