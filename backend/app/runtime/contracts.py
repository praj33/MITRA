from __future__ import annotations

from typing import Any, List, Optional

try:
    from pydantic import BaseModel, Field
    from pydantic import ConfigDict
    _pydantic_v2 = True
except ImportError:
    from pydantic import BaseModel, Field
    _pydantic_v2 = False

try:
    from pydantic import HttpUrl
except ImportError:
    HttpUrl = str

from .constants import (
    COMPATIBILITY_VERSION,
    CONTRACT_VERSION,
    RUNTIME_VERSION,
    SCHEMA_VERSION,
)
from .errors import ContractCompatibilityError


class VersionedContract(BaseModel):
    class Config:
        extra = "forbid"

    schema_version: str = SCHEMA_VERSION
    contract_version: str = CONTRACT_VERSION
    runtime_version: str = RUNTIME_VERSION
    compatibility_version: str = COMPATIBILITY_VERSION


class DispatchTarget(BaseModel):
    class Config:
        extra = "forbid"

    mode: str = Field(...)
    endpoint: str = Field(...)
    timeout_seconds: Optional[float] = Field(default=None)
    options: dict = Field(default_factory=dict)


class IntentRegistration(BaseModel):
    class Config:
        extra = "forbid"

    intent_id: str = Field(...)
    description: str = Field(...)
    input_schema: dict = Field(default_factory=dict)
    dispatch: DispatchTarget
    metadata: dict = Field(default_factory=dict)


class CapabilityRegistration(BaseModel):
    class Config:
        extra = "forbid"

    capability_id: str = Field(...)
    description: str = Field(...)
    context_scopes: List[str] = Field(
        default_factory=lambda: ["session", "workspace", "product"]
    )
    intents: List[IntentRegistration] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ProductAttachmentManifest(BaseModel):
    class Config:
        extra = "forbid"

    product_id: str = Field(...)
    display_name: str = Field(...)
    product_version: str = Field(...)
    contract_version: str = CONTRACT_VERSION
    attachment_mode: str = Field(...)
    base_url: Optional[str] = None
    health_endpoint: Optional[str] = None
    capabilities: List[CapabilityRegistration] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class AttachmentRequest(VersionedContract):
    manifest: ProductAttachmentManifest


class SessionCreateRequest(VersionedContract):
    actor_id: str = Field(...)
    client_type: str = Field(...)
    workspace_id: str = Field(...)
    product_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class SessionResumeRequest(VersionedContract):
    resume_token: str = Field(...)


class ContextUpdateRequest(VersionedContract):
    scope: str = Field(...)
    patch: dict = Field(default_factory=dict)
    expected_revision: Optional[int] = None
    replace: bool = False


class ContextTransferRequest(VersionedContract):
    target_workspace_id: str = Field(...)
    target_product_id: Optional[str] = None
    portable_context: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class IntentDispatchRequest(VersionedContract):
    session_id: str = Field(...)
    intent_id: str = Field(...)
    product_id: Optional[str] = None
    capability_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    correlation_id: Optional[str] = None


def validate_contract(contract: VersionedContract) -> None:
    expected = {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "compatibility_version": COMPATIBILITY_VERSION,
    }
    received = contract.dict(include=set(expected))
    incompatible = {
        field: {"received": received[field], "supported": value}
        for field, value in expected.items()
        if received[field] != value
    }
    if incompatible:
        raise ContractCompatibilityError(
            f"Incompatible companion runtime contract: {incompatible}"
        )


def versioned_response(**payload: Any) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "compatibility_version": COMPATIBILITY_VERSION,
        **payload,
    }
