"""
workflow_api.py — Mitra Workflow REST API

Endpoints to list, run, and create workflows.
Part of the Canonical MITRA API (Phase 2 Hardened).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.companion.workflow_engine import workflow_engine, WorkflowStep
from app.core.auth_dependencies import get_current_user
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class WorkflowRunRequest(BaseModel):
    workflow_name: str
    user_id: Optional[str] = None
    message: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None


class WorkflowCreateRequest(BaseModel):
    name: str
    steps: List[Dict[str, Any]]   # [{capability, intent, params_template, description, optional}]


@router.get("/api/workflow/list")
async def list_workflows(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """List all available workflows (built-in + custom)."""
    return {"workflows": workflow_engine.list_workflows()}


@router.post("/api/workflow/run")
async def run_workflow(
    request: WorkflowRunRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Run a workflow by name for the authenticated user."""
    auth_user_id = current_user["user_id"]
    extra = request.extra_params or {}
    if request.message:
        extra["message"] = request.message

    try:
        result = await workflow_engine.run(
            workflow_name=request.workflow_name,
            user_id=auth_user_id,
            extra_params=extra,
        )
        return JSONResponse(status_code=200, content=result.to_dict())
    except Exception as exc:
        logger.exception("Workflow run failed for user %s: %s", auth_user_id, exc)
        return JSONResponse(status_code=500, content={"error": str(exc)})


@router.post("/api/workflow/create")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a custom workflow."""
    try:
        steps = [
            WorkflowStep(
                capability=s.get("capability", ""),
                intent=s.get("intent", ""),
                params_template=s.get("params_template", {}),
                description=s.get("description", ""),
                optional=s.get("optional", False),
            )
            for s in request.steps
        ]
        workflow_engine.register_workflow(request.name, steps)
        return {"name": request.name, "steps": len(steps), "status": "created"}
    except Exception as exc:
        logger.exception("Workflow create failed: %s", exc)
        return JSONResponse(status_code=500, content={"error": str(exc)})
