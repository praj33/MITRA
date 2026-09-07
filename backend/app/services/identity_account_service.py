import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

_IN_MEMORY_IDENTITY_ACCOUNTS: Dict[str, Dict[str, Any]] = {}

def _get_db():
    try:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        return client[db_name]
    except Exception as exc:
        logger.warning(f"MongoDB connection error in identity_account_service: {exc}")
        return None

class IdentityAccountService:
    """
    Manages OAuth identity account bindings (provider + provider_subject -> MITRA user_id).
    Ensures safe account linking and prevents duplicate user creation.
    """
    def __init__(self):
        self.collection_name = "identity_accounts"

    def get_identity(self, provider: str, provider_subject: str) -> Optional[Dict[str, Any]]:
        if not provider or not provider_subject:
            return None

        key = f"{provider.lower()}_{provider_subject}"
        db = _get_db()
        record = None

        if db is not None:
            try:
                record = db[self.collection_name].find_one({
                    "provider": provider.lower(),
                    "provider_subject": provider_subject
                })
            except Exception as exc:
                logger.warning(f"Error reading identity account from DB: {exc}")

        if not record:
            record = _IN_MEMORY_IDENTITY_ACCOUNTS.get(key)

        return record

    def link_identity(self, user_id: str, provider: str, provider_subject: str, email: str) -> Dict[str, Any]:
        if not user_id or not provider or not provider_subject:
            raise ValueError("user_id, provider, and provider_subject are required for identity linking.")

        now_iso = datetime.utcnow().isoformat()
        key = f"{provider.lower()}_{provider_subject}"

        record = {
            "user_id": user_id,
            "provider": provider.lower(),
            "provider_subject": provider_subject,
            "email": email,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].update_one(
                    {"provider": provider.lower(), "provider_subject": provider_subject},
                    {"$set": record},
                    upsert=True
                )
            except Exception as exc:
                logger.error(f"Failed persisting identity account link to DB: {exc}")
                _IN_MEMORY_IDENTITY_ACCOUNTS[key] = record
        else:
            _IN_MEMORY_IDENTITY_ACCOUNTS[key] = record

        return record

identity_account_service = IdentityAccountService()
