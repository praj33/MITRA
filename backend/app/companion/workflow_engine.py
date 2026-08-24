"""
workflow_engine.py — Mitra Workflow Engine

Orchestrates named multi-step capability workflows.
Built-in workflows: morning_briefing, meeting_prep, email_followup, weekly_review, quick_reminder.
User workflows stored in MongoDB.
All steps invoke capability interfaces — no direct executor calls.
"""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from app.companion.capability_registry import capability_registry

logger = logging.getLogger(__name__)

WorkflowStatus = Literal["pending", "running", "completed", "failed", "partial"]


@dataclass
class WorkflowStep:
    capability: str
    intent: str
    params_template: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    optional: bool = False   # if True, failure won't abort the workflow


@dataclass
class WorkflowResult:
    workflow_name: str
    run_id: str
    status: WorkflowStatus
    steps_completed: int
    steps_total: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_name":    self.workflow_name,
            "run_id":           self.run_id,
            "status":           self.status,
            "steps_completed":  self.steps_completed,
            "steps_total":      self.steps_total,
            "results":          self.results,
            "summary":          self.summary,
            "started_at":       self.started_at,
            "completed_at":     self.completed_at,
        }


# ── Built-in Workflows ────────────────────────────────────────────────────

BUILT_IN_WORKFLOWS: Dict[str, List[WorkflowStep]] = {
    "morning_briefing": [
        WorkflowStep(
            capability="calendar", intent="list_events",
            params_template={"filter": "today"},
            description="Get today's calendar events",
        ),
        WorkflowStep(
            capability="email", intent="read_emails",
            params_template={"filter": "unread", "limit": 5},
            description="Check unread emails",
        ),
        WorkflowStep(
            capability="task", intent="list_tasks",
            params_template={"filter": "pending", "limit": 10},
            description="List pending tasks",
        ),
        WorkflowStep(
            capability="reminder", intent="list_reminders",
            params_template={"filter": "today"},
            description="Check today's reminders",
            optional=True,
        ),
    ],
    "meeting_prep": [
        WorkflowStep(
            capability="calendar", intent="list_events",
            params_template={"filter": "next"},
            description="Find next meeting",
        ),
        WorkflowStep(
            capability="notes", intent="list_notes",
            params_template={"filter": "recent", "limit": 3},
            description="Retrieve recent relevant notes",
            optional=True,
        ),
        WorkflowStep(
            capability="reminder", intent="create_reminder",
            params_template={"offset_minutes": 15, "message": "Meeting in 15 minutes"},
            description="Set 15-minute pre-meeting reminder",
        ),
    ],
    "email_followup": [
        WorkflowStep(
            capability="email", intent="read_emails",
            params_template={"filter": "sent", "limit": 10},
            description="Review sent emails",
        ),
        WorkflowStep(
            capability="email", intent="draft_email",
            params_template={"type": "followup"},
            description="Draft follow-up email",
        ),
    ],
    "weekly_review": [
        WorkflowStep(
            capability="task", intent="list_tasks",
            params_template={"filter": "completed_this_week"},
            description="List tasks completed this week",
        ),
        WorkflowStep(
            capability="notes", intent="list_notes",
            params_template={"filter": "this_week"},
            description="Retrieve this week's notes",
            optional=True,
        ),
        WorkflowStep(
            capability="calendar", intent="list_events",
            params_template={"filter": "this_week"},
            description="Review this week's meetings",
        ),
        WorkflowStep(
            capability="email", intent="draft_email",
            params_template={"type": "weekly_summary"},
            description="Draft weekly summary email",
            optional=True,
        ),
    ],
    "quick_reminder": [
        WorkflowStep(
            capability="reminder", intent="create_reminder",
            params_template={},
            description="Create reminder from message",
        ),
    ],
}


class WorkflowEngine:
    """
    Runs named multi-step workflows by routing each step
    through the CapabilityRegistry.
    """

    def __init__(self) -> None:
        self._custom_workflows: Dict[str, List[WorkflowStep]] = {}
        self._run_history: List[WorkflowResult] = []
        self._mongo_col = None
        self._init_mongo()

    def _init_mongo(self) -> None:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            return
        try:
            from pymongo import MongoClient  # type: ignore
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db = client[os.getenv("MONGODB_DB", "mitra")]
            self._mongo_col = db["mitra_workflows"]
        except Exception as exc:
            logger.warning("WorkflowEngine: MongoDB unavailable: %s", exc)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Return all available workflows (built-in + custom)."""
        all_wf = {**BUILT_IN_WORKFLOWS, **self._custom_workflows}
        return [
            {
                "name": name,
                "steps": len(steps),
                "type": "built_in" if name in BUILT_IN_WORKFLOWS else "custom",
                "description": steps[0].description if steps else "",
            }
            for name, steps in all_wf.items()
        ]

    def register_workflow(self, name: str, steps: List[WorkflowStep]) -> None:
        """Register a custom workflow."""
        self._custom_workflows[name] = steps
        if self._mongo_col is not None:
            try:
                self._mongo_col.replace_one(
                    {"name": name},
                    {
                        "name": name,
                        "steps": [
                            {"capability": s.capability, "intent": s.intent,
                             "params_template": s.params_template,
                             "description": s.description, "optional": s.optional}
                            for s in steps
                        ],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                    upsert=True,
                )
            except Exception as exc:
                logger.warning("WorkflowEngine.register_workflow save failed: %s", exc)

    async def run(
        self,
        workflow_name: str,
        user_id: str,
        extra_params: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> WorkflowResult:
        """Execute a workflow by name."""
        all_wf = {**BUILT_IN_WORKFLOWS, **self._custom_workflows}
        steps = all_wf.get(workflow_name)
        if not steps:
            return WorkflowResult(
                workflow_name=workflow_name,
                run_id=f"run_{uuid.uuid4().hex[:8]}",
                status="failed",
                steps_completed=0,
                steps_total=0,
                summary=f"Workflow '{workflow_name}' not found.",
            )

        run_id = f"run_{uuid.uuid4().hex[:8]}"
        result = WorkflowResult(
            workflow_name=workflow_name,
            run_id=run_id,
            status="running",
            steps_completed=0,
            steps_total=len(steps),
        )

        logger.info("WorkflowEngine: starting '%s' run_id=%s for user=%s", workflow_name, run_id, user_id)
        failed = False

        for step in steps:
            params = {
                **(step.params_template or {}),
                **(extra_params or {}),
                "user_id": user_id,
                "message": extra_params.get("message", "") if extra_params else "",
            }
            cap_result = await capability_registry.execute(
                intent=step.intent, params=params, trace_id=trace_id
            )
            if cap_result:
                result.results.append({
                    "step":       step.description,
                    "capability": step.capability,
                    "intent":     step.intent,
                    "status":     cap_result.status,
                    "summary":    cap_result.summary,
                    "data":       cap_result.data,
                })
                if cap_result.status == "success":
                    result.steps_completed += 1
                elif not step.optional:
                    failed = True
                    logger.warning(
                        "WorkflowEngine: step '%s' failed (non-optional): %s",
                        step.description, cap_result.error
                    )
                    break
            else:
                if not step.optional:
                    failed = True
                    result.results.append({
                        "step": step.description, "status": "error",
                        "summary": f"No capability for intent: {step.intent}"
                    })
                    break

        result.completed_at = datetime.now(timezone.utc).isoformat()
        if failed:
            result.status = "partial" if result.steps_completed > 0 else "failed"
        else:
            result.status = "completed"

        result.summary = self._build_summary(result)
        self._run_history.append(result)
        return result

    @staticmethod
    def _build_summary(result: WorkflowResult) -> str:
        if result.status == "completed":
            summaries = [r["summary"] for r in result.results if r.get("summary")]
            return " | ".join(summaries[:3]) or f"{result.workflow_name} completed."
        return f"{result.workflow_name}: {result.steps_completed}/{result.steps_total} steps completed."


# Singleton
workflow_engine = WorkflowEngine()
