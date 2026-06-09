from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from app.external.bucket.database.mongo_db import MongoDBClient

logger = logging.getLogger(__name__)


class BucketPersistenceError(RuntimeError):
    pass


class BucketService:
    """Persistent BHIV Bucket adapter. There is no in-memory runtime fallback."""

    @classmethod
    def clear_memory_logs(cls) -> None:
        # Compatibility hook for older test callers. Runtime storage is MongoDB only.
        return None

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): BucketService._normalize_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [BucketService._normalize_value(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    @classmethod
    def _integrity_hash(cls, trace_id: str, stage: str, data: Dict[str, Any]) -> str:
        canonical = {
            "trace_id": str(trace_id),
            "stage": str(stage),
            "data": cls._normalize_value(data),
        }
        blob = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def _field_present(data: Dict[str, Any], field_path: str) -> bool:
        current: Any = data
        for segment in field_path.split("."):
            if not isinstance(current, dict) or segment not in current:
                return False
            current = current[segment]
        return True

    def __init__(self) -> None:
        self._mongo = MongoDBClient()

    def _require_collection(self):
        collection = self._mongo.audit_collection
        if collection is None:
            raise BucketPersistenceError(
                f"BHIV Bucket persistence unavailable: {MongoDBClient.connection_error() or 'unknown error'}"
            )
        return collection

    def enforcement_artifact_required(self) -> bool:
        return True

    def log_event(self, trace_id: str, stage: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if not trace_id or not stage:
            raise BucketPersistenceError("trace_id and stage are required for BHIV Bucket persistence")

        collection = self._require_collection()
        normalized_data = self._normalize_value(data)
        timestamp = datetime.now(timezone.utc)
        artifact_locator = f"{trace_id}:{stage}"
        document = {
            "artifact_id": trace_id,
            "trace_id": trace_id,
            "stage": stage,
            "data": normalized_data,
            "integrity_hash": self._integrity_hash(trace_id, stage, normalized_data),
            "integrity_version": "sha256-v1",
            "timestamp": timestamp,
            "service": "mitra_bucket",
            "immutable": True,
            "audit_version": "2.0",
        }
        result = collection.insert_one(document)
        logger.info("BUCKET_LOG [%s] %s", trace_id, stage)
        return {
            "trace_id": trace_id,
            "stage": stage,
            "artifact_locator": artifact_locator,
            "backend": "mongodb",
            "record_id": str(result.inserted_id),
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        }

    def get_artifact(self, trace_id: str, *, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not trace_id:
            return None
        query: Dict[str, Any] = {"trace_id": trace_id}
        if stage is not None:
            query["stage"] = stage
        document = self._require_collection().find_one(query, sort=[("timestamp", -1)])
        if not document:
            return None
        document = dict(document)
        if "_id" in document:
            document["_id"] = str(document["_id"])
        return document

    def artifact_exists(self, trace_id: str, *, stage: Optional[str] = None) -> bool:
        return self.get_artifact(trace_id, stage=stage) is not None

    def validate_artifact(
        self,
        trace_id: str,
        *,
        stage: str,
        required_fields: Optional[Iterable[str]] = None,
        expected_trace_id: Optional[str] = None,
    ) -> bool:
        artifact = self.get_artifact(trace_id, stage=stage)
        if not artifact:
            return False
        data = artifact.get("data")
        if not isinstance(data, dict):
            return False
        expected_hash = self._integrity_hash(
            str(artifact.get("trace_id", trace_id)),
            str(artifact.get("stage", stage)),
            data,
        )
        if artifact.get("integrity_hash") != expected_hash:
            return False
        if expected_trace_id is not None and str(data.get("trace_id") or "") != str(expected_trace_id):
            return False
        if required_fields and any(not self._field_present(data, field) for field in required_fields):
            return False
        return True

    def get_trace_logs(self, trace_id: str) -> list[Dict[str, Any]]:
        cursor = self._require_collection().find({"trace_id": trace_id}).sort("timestamp", 1)
        logs = []
        for document in cursor:
            document = dict(document)
            if "_id" in document:
                document["_id"] = str(document["_id"])
            logs.append(document)
        return logs

    def find_recent_stage_events(
        self,
        stage: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        exclude_trace_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        query: Dict[str, Any] = {"stage": stage}
        if user_id is not None:
            query["data.user_id"] = str(user_id)
        if session_id is not None:
            query["data.session_id"] = str(session_id)
        if exclude_trace_id:
            query["trace_id"] = {"$ne": exclude_trace_id}

        cursor = self._require_collection().find(query).sort("timestamp", -1).limit(limit)
        results = []
        for document in cursor:
            document = dict(document)
            if "_id" in document:
                document["_id"] = str(document["_id"])
            results.append(document)
        return results

    def get_status(self) -> Dict[str, Any]:
        connected = self._mongo.audit_collection is not None
        return {
            "service": "mitra_bucket",
            "status": "active" if connected else "unavailable",
            "persistent_backend": "mongodb" if connected else "unavailable",
            "mongo_connected": connected,
            "audit_active": connected,
            "mongo_error": None if connected else MongoDBClient.connection_error(),
        }
