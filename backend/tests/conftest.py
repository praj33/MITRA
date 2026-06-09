from __future__ import annotations

import copy
import os
from types import SimpleNamespace

import pytest

os.environ["API_KEY"] = "localtest"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["AUTH_STORE_MODE"] = "inmemory"

import app.core.database as runtime_database
import app.services.auth_service as auth_service_module
from app.external.bucket.database.mongo_db import MongoDBClient
from app.services.telegram_contact_service import TelegramContactService


def _nested_value(document, field_path: str):
    current = document
    for segment in field_path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return None
        current = current[segment]
    return current


def _matches(document: dict, query: dict) -> bool:
    for key, value in (query or {}).items():
        if isinstance(value, dict) and "$ne" in value:
            if _nested_value(document, key) == value["$ne"]:
                return False
            continue
        if isinstance(value, dict) and "$in" in value:
            if _nested_value(document, key) not in value["$in"]:
                return False
            continue
        if _nested_value(document, key) != value:
            return False
    return True


class FakeCursor:
    def __init__(self, documents):
        self._documents = list(documents)

    def sort(self, field: str, direction: int):
        self._documents.sort(key=lambda item: _nested_value(item, field), reverse=direction == -1)
        return self

    def limit(self, size: int):
        self._documents = self._documents[:size]
        return self

    def __iter__(self):
        return iter(copy.deepcopy(self._documents))


class FakeAuditCollection:
    def __init__(self):
        self.documents = []

    def reset(self):
        self.documents.clear()

    def insert_one(self, document: dict):
        stored = copy.deepcopy(document)
        stored["_id"] = str(len(self.documents) + 1)
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def find_one(self, query: dict, sort=None):
        matches = [doc for doc in self.documents if _matches(doc, query)]
        if sort:
            field, direction = sort[0]
            matches.sort(key=lambda item: _nested_value(item, field), reverse=direction == -1)
        return copy.deepcopy(matches[0]) if matches else None

    def find(self, query: dict, projection=None):
        return FakeCursor([doc for doc in self.documents if _matches(doc, query)])


class FakeUsersCollection:
    def __init__(self):
        self.documents = []

    def reset(self):
        self.documents.clear()

    async def find_one(self, query: dict):
        for document in self.documents:
            if _matches(document, query):
                return copy.deepcopy(document)
        return None

    async def insert_one(self, document: dict):
        if any(existing.get("email") == document.get("email") for existing in self.documents):
            from pymongo.errors import DuplicateKeyError

            raise DuplicateKeyError("duplicate email")
        self.documents.append(copy.deepcopy(document))
        return SimpleNamespace(inserted_id=document.get("_id"))

    async def update_one(self, query: dict, update: dict):
        for index, document in enumerate(self.documents):
            if _matches(document, query):
                updated = copy.deepcopy(document)
                updated.update(copy.deepcopy((update or {}).get("$set") or {}))
                self.documents[index] = updated
                return SimpleNamespace(matched_count=1, modified_count=1)
        return SimpleNamespace(matched_count=0, modified_count=0)


class FakeTelegramContactsCollection:
    def __init__(self):
        self.documents = {}

    def reset(self):
        self.documents.clear()

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        chat_id = int(query["chat_id"])
        current = copy.deepcopy(self.documents.get(chat_id, {"chat_id": chat_id}))
        current.update(copy.deepcopy((update or {}).get("$set") or {}))
        self.documents[chat_id] = current
        return SimpleNamespace(matched_count=1, modified_count=1)

    def find_one(self, query: dict):
        for document in self.documents.values():
            if _matches(document, query):
                return copy.deepcopy(document)
        return None

    def find(self, query: dict, projection=None):
        return iter(
            copy.deepcopy([document for document in self.documents.values() if _matches(document, query)])
        )


_TEST_AUDIT_COLLECTION = FakeAuditCollection()
_TEST_USERS_COLLECTION = FakeUsersCollection()
_TEST_TELEGRAM_CONTACTS_COLLECTION = FakeTelegramContactsCollection()


class FakeDB:
    def __init__(self):
        self.audit_logs = _TEST_AUDIT_COLLECTION

    def get_collection(self, name: str):
        if name == "telegram_contacts":
            return _TEST_TELEGRAM_CONTACTS_COLLECTION
        return _TEST_AUDIT_COLLECTION


def _fake_connect(self) -> None:
    cls = type(self)
    self.client = object()
    self.db = FakeDB()
    self.audit_collection = _TEST_AUDIT_COLLECTION
    cls._shared_client = self.client
    cls._shared_db = self.db
    cls._shared_audit_collection = self.audit_collection
    cls._connection_attempted = True
    cls._last_error = None


MongoDBClient.connect = _fake_connect
runtime_database.users_collection = _TEST_USERS_COLLECTION
auth_service_module.users_collection = _TEST_USERS_COLLECTION


async def _fake_create_tables():
    return None


runtime_database.create_tables = _fake_create_tables


@pytest.fixture(autouse=True)
def _reset_test_stores():
    _TEST_AUDIT_COLLECTION.reset()
    _TEST_USERS_COLLECTION.reset()
    _TEST_TELEGRAM_CONTACTS_COLLECTION.reset()
    TelegramContactService._memory_store.clear()
    TelegramContactService._contacts_by_chat_id.clear()
    auth_service_module.auth_service.reset_inmemory_store()
    yield
