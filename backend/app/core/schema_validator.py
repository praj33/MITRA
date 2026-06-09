"""Schema validation for the locked Assistant Backend contract."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Literal, Optional, Type

from pydantic import BaseModel, ValidationError


class AssistantInput(BaseModel):
    message: Optional[str] = None
    summarized_payload: Optional[Dict[str, Any]] = None


class AssistantContext(BaseModel):
    platform: str
    device: str
    session_id: Optional[str] = None
    voice_input: bool = False


class AssistantRequest(BaseModel):
    version: Literal["3.0.0"]
    input: AssistantInput
    context: AssistantContext


class AssistantResult(BaseModel):
    type: str
    response: str
    task: Optional[Dict[str, Any]] = None
    enforcement: Optional[Dict[str, Any]] = None
    safety: Optional[Dict[str, Any]] = None


class AssistantSuccessResponse(BaseModel):
    version: str
    status: Literal["success"]
    result: AssistantResult
    processed_at: str


class AssistantErrorResponse(BaseModel):
    version: str
    status: Literal["error"]
    error: Dict[str, Any]
    processed_at: str


class SchemaValidator:
    """Validate the stable assistant request and response envelopes."""

    def __init__(self, strict_hash_checking: bool = False) -> None:
        self.strict_hash_checking = strict_hash_checking
        self.request_schema_hash = self._compute_schema_hash(AssistantRequest)
        self.response_success_schema_hash = self._compute_schema_hash(
            AssistantSuccessResponse
        )
        self.response_error_schema_hash = self._compute_schema_hash(
            AssistantErrorResponse
        )

    @staticmethod
    def _compute_schema_hash(model_class: Type[BaseModel]) -> str:
        schema_factory = getattr(model_class, "model_json_schema", model_class.schema)
        schema = schema_factory()
        canonical_schema = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()

    def validate_request(self, data: Dict[str, Any]) -> AssistantRequest:
        try:
            return AssistantRequest(**data)
        except ValidationError as exc:
            raise ValueError(f"Request validation failed: {exc}") from exc

    def validate_response(self, data: Dict[str, Any]) -> bool:
        try:
            if data.get("status") == "success":
                AssistantSuccessResponse(**data)
            elif data.get("status") == "error":
                AssistantErrorResponse(**data)
            else:
                raise ValueError("Invalid response status")
        except ValidationError as exc:
            raise ValueError(f"Response validation failed: {exc}") from exc
        return True


schema_validator = SchemaValidator()
