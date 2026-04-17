"""
BucketService — Mitra Pipeline Persistence (BHIV Bucket Integration)

Provides append-only, tamper-evident artifact storage for every pipeline stage.
Uses JSONL hash-chain storage as primary persistence (BHIV philosophy: memory, not decision).
Optional MongoDB audit via AuditMiddleware as secondary persistence.
"""

import json
import os
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Iterable

from app.bucket.append_only_storage import AppendOnlyStorage
from app.bucket.hash_service import deterministic_hash

logger = logging.getLogger(__name__)


class BucketService:
    """
    Unified bucket service embedding BHIV append-only storage.

    Primary:   JSONL append-only log with hash chains (tamper-evident)
    Secondary: MongoDB audit collection (if MONGODB_URI available)
    Fallback:  In-memory log (for tests / no-storage environments)
    """

    _memory_logs: list[Dict[str, Any]] = []

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def clear_memory_logs(cls) -> None:
        cls._memory_logs.clear()

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
        blob = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    @staticmethod
    def _field_present(data: Dict[str, Any], field_path: str) -> bool:
        current: Any = data
        for segment in field_path.split("."):
            if not isinstance(current, dict) or segment not in current:
                return False
            current = current[segment]
        return True

    def __init__(self):
        # Primary: BHIV append-only storage (JSONL hash chains)
        storage_path = os.getenv("BUCKET_STORAGE_PATH", "data/mitra_pipeline_artifacts")
        self._append_only = AppendOnlyStorage(storage_path=storage_path)

        # Secondary: MongoDB audit (optional)
        self._mongo_client = None
        self._audit_collection = None
        self._init_mongo_audit()

    def _init_mongo_audit(self):
        """Initialize MongoDB audit collection if MONGODB_URI is available."""
        try:
            mongo_uri = os.getenv("MONGODB_URI")
            if mongo_uri:
                from pymongo import MongoClient
                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
                client.admin.command("ping")
                db = client.get_default_database()
                if db is None:
                    db = client["mitra_bucket"]
                self._mongo_client = client
                self._audit_collection = db["pipeline_audit"]
                logger.info("BucketService: MongoDB audit connected")
            else:
                logger.info("BucketService: No MONGODB_URI — file-only mode")
        except Exception as exc:
            logger.warning("BucketService: MongoDB audit unavailable: %s", exc)
            self._mongo_client = None
            self._audit_collection = None

    def enforcement_artifact_required(self) -> bool:
        return self._env_bool("BUCKET_MONGO_ENABLED", True)

    def log_event(self, trace_id: str, stage: str, data: Dict[str, Any]) -> bool:
        """
        Log a pipeline event as a BHIV artifact.

        1. Normalize data
        2. Build BHIV artifact envelope
        3. Store in append-only JSONL (primary — tamper-evident)
        4. Store in MongoDB audit (secondary — queryable)
        5. Keep in-memory copy (for fast lookups within request)
        """
        try:
            normalized_data = self._normalize_value(data)
            timestamp = datetime.utcnow().isoformat() + "Z"

            # Build BHIV artifact envelope
            artifact_id = f"{trace_id}_{stage}_{timestamp.replace(':', '').replace('-', '')}"
            artifact = {
                "artifact_id": artifact_id,
                "timestamp_utc": timestamp,
                "schema_version": "1.0.0",
                "source_module_id": "mitra_control_plane",
                "artifact_type": "pipeline_event",
                "payload": {
                    "trace_id": trace_id,
                    "stage": stage,
                    "data": normalized_data,
                },
            }

            # Primary: Append-only storage (hash chain)
            try:
                self._append_only.store_artifact(artifact)
            except Exception as aoe:
                logger.warning("Append-only storage write failed: %s", aoe)

            # Build legacy-compatible log entry (for in-memory + MongoDB)
            log_entry = {
                "trace_id": trace_id,
                "stage": stage,
                "data": normalized_data,
                "integrity_hash": self._integrity_hash(trace_id, stage, normalized_data),
                "integrity_version": "sha256-v1",
                "timestamp": timestamp,
                "service": "bucket_service",
                "artifact_id": artifact_id,
            }

            # In-memory copy
            BucketService._memory_logs.append(log_entry)

            # Secondary: MongoDB audit
            if self._audit_collection is not None:
                try:
                    self._audit_collection.insert_one({
                        "timestamp": datetime.utcnow(),
                        "operation_type": "CREATE",
                        "artifact_id": trace_id,
                        "requester_id": "bucket_service",
                        "integration_id": "mitra_runtime",
                        "status": "success",
                        "stage": stage,
                        "data_after": log_entry,
                        "immutable": True,
                        "audit_version": "1.0",
                    })
                except Exception as me:
                    logger.warning("MongoDB audit write failed: %s", me)

            logger.debug("BUCKET_LOG [%s] %s", trace_id, stage)
            return True
        except Exception as exc:
            logger.error("Bucket logging failed for %s: %s", trace_id, exc)
            return False

    def get_artifact(self, trace_id: str, *, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not trace_id:
            return None

        # Check in-memory first (fast path for current request)
        for entry in reversed(BucketService._memory_logs):
            if entry.get("trace_id") != trace_id:
                continue
            if stage is not None and entry.get("stage") != stage:
                continue
            return dict(entry)

        # Check MongoDB audit
        try:
            if self._audit_collection is not None:
                query: Dict[str, Any] = {"artifact_id": trace_id}
                if stage is not None:
                    query["stage"] = stage
                doc = self._audit_collection.find_one(query, sort=[("timestamp", -1)])
                if doc:
                    payload = doc.get("data_after")
                    if isinstance(payload, dict):
                        return dict(payload)
        except Exception as exc:
            logger.error("Failed to retrieve artifact for %s: %s", trace_id, exc)

        return None

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

        integrity_hash = artifact.get("integrity_hash")
        if not integrity_hash:
            return False

        expected_hash = self._integrity_hash(
            str(artifact.get("trace_id", trace_id)),
            str(artifact.get("stage", stage)),
            data,
        )
        if integrity_hash != expected_hash:
            return False

        if expected_trace_id is not None:
            embedded_trace_id = data.get("trace_id")
            if str(embedded_trace_id or "") != str(expected_trace_id):
                return False

        if required_fields:
            for field_path in required_fields:
                if not self._field_present(data, field_path):
                    return False

        return True

    def get_trace_logs(self, trace_id: str) -> Optional[list]:
        try:
            if self._audit_collection is not None:
                logs = list(
                    self._audit_collection.find({"artifact_id": trace_id}).sort("timestamp", -1)
                )
                if logs:
                    return logs

            return [entry for entry in BucketService._memory_logs if entry.get("trace_id") == trace_id]
        except Exception as exc:
            logger.error("Failed to retrieve trace logs for %s: %s", trace_id, exc)
            return None

    def find_recent_stage_events(
        self,
        stage: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        exclude_trace_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        matches: list[Dict[str, Any]] = []
        normalized_user_id = str(user_id) if user_id is not None else None
        normalized_session_id = str(session_id) if session_id is not None else None

        for entry in reversed(BucketService._memory_logs):
            if entry.get("stage") != stage:
                continue
            if exclude_trace_id and entry.get("trace_id") == exclude_trace_id:
                continue

            data = entry.get("data") or {}
            if normalized_user_id is not None and str(data.get("user_id")) != normalized_user_id:
                continue
            if normalized_session_id is not None and str(data.get("session_id")) != normalized_session_id:
                continue

            matches.append(dict(entry))
            if len(matches) >= limit:
                return matches

        # Also check MongoDB
        try:
            if self._audit_collection is not None:
                query: Dict[str, Any] = {"stage": stage}
                if normalized_user_id is not None:
                    query["data_after.data.user_id"] = normalized_user_id
                if normalized_session_id is not None:
                    query["data_after.data.session_id"] = normalized_session_id
                if exclude_trace_id:
                    query["artifact_id"] = {"$ne": exclude_trace_id}

                docs = list(
                    self._audit_collection.find(query).sort("timestamp", -1).limit(limit)
                )
                for doc in docs:
                    payload = doc.get("data_after")
                    if isinstance(payload, dict):
                        matches.append(dict(payload))
                        if len(matches) >= limit:
                            break
        except Exception as exc:
            logger.error("Failed to query recent stage events for %s: %s", stage, exc)

        return matches[:limit]

    def get_chain_state(self) -> Dict[str, Any]:
        """Get BHIV append-only chain state."""
        return self._append_only.get_chain_state()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get BHIV append-only storage stats."""
        return self._append_only.get_storage_stats()

    def validate_chain_integrity(self) -> Dict[str, Any]:
        """Validate entire BHIV artifact chain integrity."""
        is_valid, errors = self._append_only.validate_chain_integrity()
        return {"is_valid": is_valid, "errors": errors}

    def get_status(self) -> Dict[str, Any]:
        chain_state = self._append_only.get_chain_state()
        return {
            "service": "bucket_service",
            "status": "active",
            "mongo_connected": self._audit_collection is not None,
            "append_only_storage": "active",
            "artifact_count": chain_state.get("artifact_count", 0),
            "last_hash": chain_state.get("last_hash"),
            "fallback_mode": self._audit_collection is None,
        }
