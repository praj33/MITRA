from __future__ import annotations

from typing import Any, Dict


def model_to_dict(model: Any) -> Dict[str, Any]:
    """
    Support both Pydantic v1 (`dict`) and v2 (`model_dump`) without forcing
    the deployment environment to match the local virtualenv exactly.
    """
    if isinstance(model, dict):
        return model

    if hasattr(model, "model_dump"):
        return model.model_dump()

    if hasattr(model, "dict"):
        return model.dict()

    raise TypeError(f"Object of type {type(model)!r} cannot be converted to dict")
