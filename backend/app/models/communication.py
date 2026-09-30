"""
backend/app/models/communication.py — Unified Communication Capability Contract

Defines the provider-independent canonical contract for all MITRA communication:
- Channels: EMAIL, WHATSAPP
- Intents: SEND_MESSAGE, DRAFT_MESSAGE, READ_MESSAGES, SEARCH_MESSAGES
- Centralized Approval Policy & Confirmation Payload
- Standardized Communication Result & Delivery State
- Normalized Error Categories
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, validator

# ── 1. UNIFIED COMMUNICATION INTENTS & CHANNELS ──────────────────────────────

class CommunicationIntent(str, Enum):
    SEND_MESSAGE = "SEND_MESSAGE"
    DRAFT_MESSAGE = "DRAFT_MESSAGE"
    READ_MESSAGES = "READ_MESSAGES"
    SEARCH_MESSAGES = "SEARCH_MESSAGES"


class CommunicationChannel(str, Enum):
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"


CommunicationStatus = Literal[
    "requested",
    "confirmation_required",
    "accepted",
    "sent",
    "delivered",
    "failed",
]

DeliveryState = Literal[
    "pending",
    "accepted",
    "sent",
    "delivered",
    "failed",
    "unknown",
]

CommunicationErrorCode = Literal[
    "AUTH_REQUIRED",
    "ACCOUNT_NOT_CONNECTED",
    "ACCOUNT_NOT_AUTHORIZED",
    "CONFIRMATION_REQUIRED",
    "INVALID_RECIPIENT",
    "PROVIDER_UNAVAILABLE",
    "RATE_LIMITED",
    "DELIVERY_FAILED",
    "PROVIDER_REJECTED",
    "CONFIGURATION_REQUIRED",
    "WHATSAPP_BUSINESS_REQUIRED",
]

# Sensitive keys that must NEVER enter canonical contract or result
FORBIDDEN_CREDENTIAL_KEYS = {
    "password", "app_password", "access_token", "refresh_token",
    "auth_token", "token", "client_secret", "secret", "private_key",
    "api_key", "encrypted_access_token", "encrypted_refresh_token"
}


# ── 2. CANONICAL COMMUNICATION ACTION CONTRACT ─────────────────────────────

class CommunicationAction(BaseModel):
    """
    Provider-independent canonical contract for communication actions.
    Never accepts client-supplied credentials, access tokens, or raw secrets.
    """
    intent: CommunicationIntent
    channel: CommunicationChannel
    user_id: str
    account_id: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    confirmation_confirmed: bool = False
    idempotency_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("user_id")
    def validate_user_id(cls, v: str) -> str:
        if not v or not str(v).strip() or str(v).strip().lower() in ("user_default", "default", "none", "null", "anonymous"):
            raise ValueError("Authentication required: user-owned communication actions must specify a valid, authenticated user_id.")
        return str(v).strip()

    @validator("channel", pre=True)
    def normalize_channel(cls, v: Any) -> CommunicationChannel:
        if isinstance(v, str):
            clean = v.strip().upper()
            if clean in ("EMAIL", "MAIL", "GMAIL", "OUTLOOK"):
                return CommunicationChannel.EMAIL
            elif clean in ("WHATSAPP", "WA"):
                return CommunicationChannel.WHATSAPP
        return v

    @validator("intent", pre=True)
    def normalize_intent(cls, v: Any) -> CommunicationIntent:
        if isinstance(v, str):
            clean = v.strip().upper()
            if clean in ("SEND_MESSAGE", "SEND_EMAIL", "SEND_WHATSAPP", "SEND", "EMAIL", "WHATSAPP"):
                return CommunicationIntent.SEND_MESSAGE
            elif clean in ("DRAFT_MESSAGE", "DRAFT_EMAIL", "DRAFT"):
                return CommunicationIntent.DRAFT_MESSAGE
            elif clean in ("READ_MESSAGES", "READ_EMAILS", "READ_INBOX", "READ"):
                return CommunicationIntent.READ_MESSAGES
            elif clean in ("SEARCH_MESSAGES", "SEARCH_EMAILS", "SEARCH"):
                return CommunicationIntent.SEARCH_MESSAGES
        return v

    @validator("metadata")
    def prevent_credential_leakage(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not v:
            return {}
        cleaned = {}
        for key, val in v.items():
            if key.lower() in FORBIDDEN_CREDENTIAL_KEYS:
                raise ValueError(f"Security error: client-supplied credential '{key}' is forbidden in communication action.")
            cleaned[key] = val
        return cleaned

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "channel": self.channel.value,
            "user_id": self.user_id,
            "account_id": self.account_id,
            "recipient": self.recipient,
            "subject": self.subject,
            "content": self.content,
            "confirmation_confirmed": self.confirmation_confirmed,
            "idempotency_key": self.idempotency_key,
            "metadata": self.metadata or {},
        }


# ── 3. CONFIRMATION PAYLOAD MODEL ──────────────────────────────────────────

class CommunicationConfirmationPayload(BaseModel):
    """
    Provider-independent confirmation representation for the UI.
    Contains clear recipient, sender identity, subject, and content.
    Never exposes OAuth tokens, passwords, or provider secrets.
    """
    type: Literal["communication_confirmation"] = "communication_confirmation"
    channel: CommunicationChannel
    sender_account: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    action: Literal["SEND_MESSAGE"] = "SEND_MESSAGE"
    idempotency_key: Optional[str] = None
    requires_confirmation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "channel": self.channel.value,
            "sender_account": self.sender_account,
            "recipient": self.recipient,
            "subject": self.subject,
            "content": self.content,
            "action": self.action,
            "idempotency_key": self.idempotency_key,
            "requires_confirmation": self.requires_confirmation,
        }


# ── 4. STANDARDIZED COMMUNICATION RESULT MODEL ─────────────────────────────

class CommunicationResult(BaseModel):
    """
    Normalized result model for all communication actions.
    Enforces delivery invariants:
    - HTTP 200 / provider API acceptance MUST NOT automatically be represented as DELIVERED.
    - Delivery confirmation is asynchronous: SENT/ACCEPTED -> pending delivery state.
    """
    status: CommunicationStatus
    delivery_state: DeliveryState = "unknown"
    channel: CommunicationChannel
    provider: Optional[str] = None
    sender_account: Optional[str] = None
    recipient: Optional[str] = None
    provider_message_id: Optional[str] = None
    error_code: Optional[CommunicationErrorCode] = None
    error: Optional[str] = None
    message: Optional[str] = None
    confirmation: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "delivery_state": self.delivery_state,
            "channel": self.channel.value,
            "provider": self.provider,
            "sender_account": self.sender_account,
            "recipient": self.recipient,
            "provider_message_id": self.provider_message_id,
            "error_code": self.error_code,
            "error": self.error,
            "message": self.message,
            "confirmation": self.confirmation,
            "action": self.action,
            "idempotency_key": self.idempotency_key,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }
