"""
task_capability.py — Mitra Task Capability
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult
import logging
logger = logging.getLogger(__name__)

def _get_user_tasks_from_db(user_id: str) -> List[Dict[str, Any]]:
    """Fetch tasks for user from MongoDB with strict enterprise user data isolation."""
    try:
        from pymongo import MongoClient
        import os
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "ai_assistant")
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client[db_name]
        docs = list(db["user_tasks"].find({"user_id": user_id}).sort("created_at", -1).limit(20))
        if not docs:
            docs = list(db["tasks"].find({"user_id": user_id}).sort("created_at", -1).limit(20))
        filtered = []
        dummy_exact = {"task", "new task", "create task", "check my tasks", "show my pending tasks", "what are my tasks"}
        for doc in docs:
            t_lower = (doc.get("title") or doc.get("task") or "").lower().strip()
            if t_lower in dummy_exact or t_lower.startswith("check my task") or t_lower.startswith("what is a task"):
                continue
            doc["id"] = str(doc.get("_id"))
            doc.pop("_id", None)
            filtered.append(doc)
        return filtered
    except Exception as e:
        logger.warning(f"Failed to fetch tasks from DB: {e}")
        return []


class TaskCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "task"

    @property
    def description(self) -> str:
        return "Create, update, and track tasks and to-dos."

    @property
    def supported_intents(self) -> List[str]:
        return ["ems", "task", "create_task", "update_task", "list_tasks", "assign_task", "todo"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "user_default")
            message = params.get("message", "").strip()
            msg_lower = message.lower()

            # Differentiate READ / CHECK queries from CREATE actions
            read_keywords = (
                "check", "what", "show", "view", "list", "get", "see",
                "do i have", "my tasks", "any task", "todo", "to-do", "to do"
            )
            create_keywords = ("create task", "add task", "new task", "assign task", "create a task")

            is_read_query = any(k in msg_lower for k in read_keywords) and not any(msg_lower.startswith(k) for k in create_keywords)

            if is_read_query or intent == "list_tasks":
                tasks = _get_user_tasks_from_db(user_id)
                if tasks:
                    task_list_str = ", ".join([f"'{t.get('title', t.get('task', 'Task'))}'" for t in tasks[:5]])
                    summary = f"You have {len(tasks)} task(s) on your board: {task_list_str}."
                else:
                    summary = "You have no pending tasks on your task board."

                return CapabilityResult(
                    capability=self.name,
                    intent="list_tasks",
                    status="success",
                    summary=summary,
                    data={"tasks": tasks, "count": len(tasks)},
                    trace_id=trace_id,
                    actions=[{"label": "View task board", "action": "View task board"}],
                )

            # Otherwise: CREATE TASK action
            from app.mitra_system_registry import mitra_registry
            execution_svc = mitra_registry.execution_service
            action_params = {
                "intent": intent,
                "raw_message": message,
                "priority": params.get("context", {}).get("priority", "medium"),
                "trace_id": trace_id,
            }
            result = execution_svc.execute_action("ems", action_params)
            summary = result.get("summary") or result.get("message") or "Task created."
            return CapabilityResult(
                capability=self.name, intent=intent, status="success",
                summary=summary, data=result, trace_id=trace_id,
                actions=[{"label": "View task board", "action": "View task board"}],
            )
        except Exception as exc:
            logger.warning("TaskCapability failed: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)
