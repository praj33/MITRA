"""
Append-Only Storage Service for Mitra Pipeline (Embedded from BHIV Bucket)

Core Philosophy:
- Bucket is MEMORY, not DECISION
- Artifacts are stored EXACTLY as produced
- NO modification, NO deletion, NO interpretation
- Tamper-evident through hash chains
- Deterministic replay guaranteed

Architecture:
- Append-only log (JSONL format)
- Each artifact is independent
- Hash chain for integrity
- Server-computed hashes (never trust client)
"""

import json
import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AppendOnlyStorage:
    """
    Append-only artifact storage with tamper-evident hash chains.

    Key Guarantees:
    1. Immutability — artifacts never modified after write
    2. Deterministic hashing — server computes all hashes
    3. Chain integrity — each artifact links to parent
    4. Replayability — deterministic ordering guaranteed
    5. Domain neutrality — no payload interpretation
    """

    MAX_PAYLOAD_SIZE = 16 * 1024 * 1024  # 16MB
    CURRENT_SCHEMA_VERSION = "1.0.0"

    def __init__(self, storage_path: str = "data/mitra_pipeline_artifacts"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.log_file = self.storage_path / "artifact_log.jsonl"
        self.index_file = self.storage_path / "artifact_index.json"
        self.chain_state_file = self.storage_path / "chain_state.json"

        self._initialize_storage()
        logger.info(f"Append-only storage initialized at {self.storage_path}")

    def _initialize_storage(self):
        if not self.log_file.exists():
            self.log_file.touch()
        if not self.index_file.exists():
            self._save_index({})
        if not self.chain_state_file.exists():
            self._save_chain_state({"last_hash": None, "artifact_count": 0})

    def _load_index(self) -> Dict[str, int]:
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_index(self, index: Dict[str, int]):
        try:
            with open(self.index_file, "w") as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _load_chain_state(self) -> Dict:
        try:
            with open(self.chain_state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"last_hash": None, "artifact_count": 0}

    def _save_chain_state(self, state: Dict):
        try:
            with open(self.chain_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chain state: {e}")

    def compute_hash(self, artifact: Dict) -> str:
        """Compute deterministic SHA256 hash of artifact. Server-side only."""
        hash_input = {
            "artifact_id": artifact.get("artifact_id"),
            "timestamp_utc": artifact.get("timestamp_utc"),
            "schema_version": artifact.get("schema_version"),
            "source_module_id": artifact.get("source_module_id"),
            "artifact_type": artifact.get("artifact_type"),
            "parent_hash": artifact.get("parent_hash"),
            "payload": artifact.get("payload"),
        }
        serialized = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def store_artifact(self, artifact: Dict) -> Dict:
        """
        Store artifact in append-only log.

        Process:
        1. Check for duplicate artifact_id
        2. Set parent_hash from chain state
        3. Compute server-side hash
        4. Append to log (atomic write)
        5. Update index and chain state
        """
        index = self._load_index()
        artifact_id = artifact.get("artifact_id", "")

        if artifact_id in index:
            logger.warning(f"Duplicate artifact_id: {artifact_id} — skipping")
            return artifact

        # Set chain linkage
        chain_state = self._load_chain_state()
        if chain_state["artifact_count"] > 0:
            artifact["parent_hash"] = chain_state["last_hash"]
        else:
            artifact["parent_hash"] = None

        # Server-computed hash
        computed_hash = self.compute_hash(artifact)
        artifact["hash"] = computed_hash

        # Append to JSONL log
        try:
            with open(self.log_file, "a") as f:
                position = f.tell()
                f.write(json.dumps(artifact, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"Failed to append artifact: {e}")
            raise

        # Update index
        index[artifact_id] = position
        self._save_index(index)

        # Update chain state
        chain_state["last_hash"] = computed_hash
        chain_state["artifact_count"] += 1
        self._save_chain_state(chain_state)

        logger.debug(f"Artifact {artifact_id} stored with hash {computed_hash[:16]}...")
        return artifact

    def get_artifact(self, artifact_id: str) -> Optional[Dict]:
        """Retrieve artifact by ID."""
        index = self._load_index()
        if artifact_id not in index:
            return None

        position = index[artifact_id]
        try:
            with open(self.log_file, "r") as f:
                f.seek(position)
                line = f.readline()
                return json.loads(line)
        except Exception as e:
            logger.error(f"Failed to read artifact {artifact_id}: {e}")
            return None

    def find_by_prefix(self, prefix: str, limit: int = 10) -> List[Dict]:
        """Find artifacts whose artifact_id starts with prefix."""
        index = self._load_index()
        matching_ids = sorted(
            [aid for aid in index if aid.startswith(prefix)],
            reverse=True,
        )[:limit]

        results = []
        for aid in matching_ids:
            artifact = self.get_artifact(aid)
            if artifact:
                results.append(artifact)
        return results

    def find_by_payload_field(self, field: str, value: str, limit: int = 10) -> List[Dict]:
        """Scan artifacts for a payload field match. O(n) — use sparingly."""
        results = []
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        artifact = json.loads(line)
                        payload = artifact.get("payload", {})
                        if isinstance(payload, dict) and str(payload.get(field)) == str(value):
                            results.append(artifact)
                            if len(results) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to scan artifacts: {e}")
        return results

    def get_chain_state(self) -> Dict:
        """Get current chain state."""
        return self._load_chain_state()

    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        chain_state = self._load_chain_state()
        log_size = self.log_file.stat().st_size if self.log_file.exists() else 0
        return {
            "artifact_count": chain_state["artifact_count"],
            "last_hash": chain_state["last_hash"],
            "log_file_size_bytes": log_size,
            "log_file_size_mb": round(log_size / (1024 * 1024), 2),
            "storage_path": str(self.storage_path),
            "schema_version": self.CURRENT_SCHEMA_VERSION,
        }

    def validate_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Validate entire artifact chain integrity."""
        errors = []
        previous_hash = None
        artifact_count = 0

        try:
            with open(self.log_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    try:
                        artifact = json.loads(line)
                        artifact_count += 1

                        stored_hash = artifact.get("hash")
                        artifact_copy = {k: v for k, v in artifact.items() if k != "hash"}
                        computed_hash = self.compute_hash(artifact_copy)

                        if stored_hash != computed_hash:
                            errors.append(f"Line {line_num}: Hash mismatch for {artifact.get('artifact_id')}")

                        if artifact_count == 1:
                            if artifact.get("parent_hash") is not None:
                                errors.append(f"Line {line_num}: First artifact has parent_hash")
                        else:
                            if artifact.get("parent_hash") != previous_hash:
                                errors.append(f"Line {line_num}: Parent hash mismatch")

                        previous_hash = stored_hash
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {e}")
        except Exception as e:
            errors.append(f"Failed to read log file: {e}")

        return len(errors) == 0, errors
