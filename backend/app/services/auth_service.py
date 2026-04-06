from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pymongo.errors import DuplicateKeyError, PyMongoError

from app.core.database import users_collection
from app.core.logging import get_logger


logger = get_logger(__name__)

_INMEMORY_USERS_BY_ID: dict[str, Dict[str, Any]] = {}
_INMEMORY_USERS_BY_EMAIL: dict[str, Dict[str, Any]] = {}


def _utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _clean_name(name: str) -> str:
    return " ".join(name.strip().split())


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 390000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def _verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iteration_str, salt_b64, digest_b64 = encoded_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual_digest, expected_digest)
    except Exception:
        return False


def _public_user(document: Dict[str, Any]) -> Dict[str, str]:
    return {
        "id": str(document["_id"]),
        "name": str(document["name"]),
        "email": str(document["email"]),
    }


class UserAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self) -> None:
        self._runtime_fallback_enabled = False

    def _mode(self) -> str:
        return (os.getenv("AUTH_STORE_MODE") or "auto").strip().lower()

    def _is_production(self) -> bool:
        env_value = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "").strip().lower()
        return env_value == "production"

    def _can_fallback(self) -> bool:
        mode = self._mode()
        return mode == "inmemory" or (mode == "auto" and not self._is_production())

    def _use_inmemory(self) -> bool:
        return self._mode() == "inmemory" or self._runtime_fallback_enabled

    def _activate_fallback(self, exc: Exception) -> None:
        if self._runtime_fallback_enabled or not self._can_fallback():
            raise exc
        self._runtime_fallback_enabled = True
        logger.warning("Auth service switching to in-memory store: %s", exc)

    def reset_inmemory_store(self) -> None:
        _INMEMORY_USERS_BY_ID.clear()
        _INMEMORY_USERS_BY_EMAIL.clear()
        self._runtime_fallback_enabled = False

    def _build_user_document(self, *, name: str, email: str, password: str) -> Dict[str, Any]:
        now = _utc_now()
        return {
            "_id": f"user_{uuid4().hex}",
            "name": _clean_name(name),
            "email": _normalize_email(email),
            "password_hash": _hash_password(password),
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
        }

    async def _find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        normalized_email = _normalize_email(email)
        if self._use_inmemory():
            document = _INMEMORY_USERS_BY_EMAIL.get(normalized_email)
            return deepcopy(document) if document else None

        try:
            return await users_collection.find_one({"email": normalized_email})
        except PyMongoError as exc:
            self._activate_fallback(exc)
            document = _INMEMORY_USERS_BY_EMAIL.get(normalized_email)
            return deepcopy(document) if document else None

    async def _find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self._use_inmemory():
            document = _INMEMORY_USERS_BY_ID.get(user_id)
            return deepcopy(document) if document else None

        try:
            return await users_collection.find_one({"_id": user_id})
        except PyMongoError as exc:
            self._activate_fallback(exc)
            document = _INMEMORY_USERS_BY_ID.get(user_id)
            return deepcopy(document) if document else None

    async def _insert_user(self, document: Dict[str, Any]) -> None:
        if self._use_inmemory():
            if document["email"] in _INMEMORY_USERS_BY_EMAIL:
                raise UserAlreadyExistsError
            stored = deepcopy(document)
            _INMEMORY_USERS_BY_ID[stored["_id"]] = stored
            _INMEMORY_USERS_BY_EMAIL[stored["email"]] = stored
            return

        try:
            await users_collection.insert_one(deepcopy(document))
        except DuplicateKeyError as exc:
            raise UserAlreadyExistsError from exc
        except PyMongoError as exc:
            self._activate_fallback(exc)
            await self._insert_user(document)

    async def _update_last_login(self, user_id: str) -> None:
        now = _utc_now()
        if self._use_inmemory():
            document = _INMEMORY_USERS_BY_ID.get(user_id)
            if document:
                document["last_login_at"] = now
                document["updated_at"] = now
            return

        try:
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": {"last_login_at": now, "updated_at": now}},
            )
        except PyMongoError as exc:
            self._activate_fallback(exc)
            await self._update_last_login(user_id)

    async def create_user(self, *, name: str, email: str, password: str) -> Dict[str, str]:
        document = self._build_user_document(name=name, email=email, password=password)
        await self._insert_user(document)
        return _public_user(document)

    async def authenticate(self, *, email: str, password: str) -> Optional[Dict[str, str]]:
        document = await self._find_user_by_email(email)
        if not document:
            return None
        if not _verify_password(password, str(document.get("password_hash") or "")):
            return None
        await self._update_last_login(str(document["_id"]))
        document["last_login_at"] = _utc_now()
        return _public_user(document)

    async def get_public_user_by_id(self, user_id: str) -> Optional[Dict[str, str]]:
        document = await self._find_user_by_id(user_id)
        if not document:
            return None
        return _public_user(document)


auth_service = AuthService()
