import os
import secrets
import hashlib
import base64
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
from pymongo import MongoClient

logger = logging.getLogger(__name__)

_IN_MEMORY_OAUTH_TRANSACTIONS: Dict[str, Dict[str, Any]] = {}

def _get_db():
    try:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        return client[db_name]
    except Exception as exc:
        logger.warning(f"MongoDB connection error in oauth_transaction_service: {exc}")
        return None

class OAuthTransactionService:
    """
    Manages OAuth authentication transactions, state validation, and PKCE verification.
    Guarantees state uniqueness, single-use, expiration, and user binding.
    """
    def __init__(self):
        self.collection_name = "oauth_transactions"
        self.default_ttl_minutes = 10

    def generate_pkce(self) -> Dict[str, str]:
        """Generate PKCE verifier and S256 code challenge."""
        code_verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

    def create_transaction(
        self,
        provider: str,
        purpose: str = "connect",
        user_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a cryptographically secure OAuth transaction state record.
        State string is pure random entropy and contains no user IDs or sensitive data.
        """
        if purpose == "connect" and not user_id:
            raise ValueError("user_id is required for 'connect' purpose OAuth transactions.")

        state = secrets.token_urlsafe(32)
        pkce = self.generate_pkce()
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.default_ttl_minutes)

        record = {
            "state": state,
            "user_id": user_id,
            "provider": provider.lower(),
            "purpose": purpose,
            "redirect_uri": redirect_uri,
            "code_verifier": pkce["code_verifier"],
            "code_challenge": pkce["code_challenge"],
            "code_challenge_method": pkce["code_challenge_method"],
            "scopes": scopes or [],
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used_at": None
        }

        _IN_MEMORY_OAUTH_TRANSACTIONS[state] = record

        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].insert_one(dict(record))
            except Exception as exc:
                logger.error(f"Failed persisting OAuth transaction to DB: {exc}")

        return dict(record)

    def validate_and_consume_transaction(
        self,
        state: str,
        provider: str,
        expected_user_id: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate OAuth transaction state.
        Ensures state is valid, not expired, not previously used, matches provider,
        purpose, and expected user identity.
        Marks state as used (single-use).
        """
        if not state or not isinstance(state, str):
            raise HTTPException(status_code=400, detail="Invalid or missing OAuth state parameter.")

        record = None
        if state in _IN_MEMORY_OAUTH_TRANSACTIONS:
            record = _IN_MEMORY_OAUTH_TRANSACTIONS[state]
        else:
            db = _get_db()
            if db is not None:
                try:
                    record = db[self.collection_name].find_one({"state": state})
                except Exception as exc:
                    logger.warning(f"Error querying OAuth transaction DB: {exc}")

        if not record:
            raise HTTPException(status_code=400, detail="Invalid OAuth state parameter. Request rejected.")

        # Check provider match
        if record.get("provider") != provider.lower():
            raise HTTPException(status_code=400, detail="OAuth provider mismatch for state.")

        # Check purpose match if specified
        if purpose and record.get("purpose") != purpose:
            raise HTTPException(status_code=400, detail="OAuth purpose mismatch for state.")

        # Check user identity match if expected
        if expected_user_id and record.get("user_id") and record.get("user_id") != expected_user_id:
            raise HTTPException(status_code=403, detail="Forbidden: OAuth state is bound to a different user.")

        # Check single-use
        if record.get("used_at") is not None:
            raise HTTPException(status_code=400, detail="OAuth state has already been used. Replay rejected.")

        # Check expiration
        expires_at_val = record.get("expires_at")
        if expires_at_val:
            try:
                if isinstance(expires_at_val, str):
                    expires_at = datetime.fromisoformat(expires_at_val)
                elif isinstance(expires_at_val, datetime):
                    expires_at = expires_at_val
                else:
                    expires_at = None
                
                if expires_at and datetime.utcnow() > expires_at:
                    raise HTTPException(status_code=400, detail="OAuth transaction state has expired.")
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning(f"Failed parsing expires_at: {exc}")

        # Mark consumed
        now_used = datetime.utcnow().isoformat()
        record["used_at"] = now_used
        _IN_MEMORY_OAUTH_TRANSACTIONS[state] = record

        db = _get_db()
        if db is not None:
            try:
                db[self.collection_name].update_one(
                    {"state": state},
                    {"$set": {"used_at": now_used}}
                )
            except Exception as exc:
                logger.error(f"Failed marking OAuth transaction consumed: {exc}")

        return dict(record)

oauth_transaction_service = OAuthTransactionService()
