"""
continuity_service.py — MITRA Cross-Application Session Continuity

Bridges the Companion Orchestrator's session management with the
Universal Companion Runtime's SessionRuntime for cross-product continuity.

This service ensures:
1. Sessions are resolved by actor_id (user_id) across products
2. Context transfers when a user moves between BHIV products
3. No new session is created unless explicitly requested
4. Conversation history travels with the user
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ContinuityService:
    """
    Resolves sessions across BHIV products.

    When a user opens Gurukul and then opens Samruddhi,
    this service ensures the same session and conversation
    continue seamlessly.
    """

    def __init__(self) -> None:
        self._runtime = None

    def _get_runtime(self):
        """Lazy-load the companion runtime from app state."""
        if self._runtime is not None:
            return self._runtime
        try:
            from app.main import app
            self._runtime = getattr(app.state, "companion_runtime", None)
        except Exception:
            pass
        return self._runtime

    def resolve_session(
        self,
        user_id: str,
        product_id: str = "mitra",
        client_type: str = "web",
        workspace_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Find an existing active session for this user, or create one.

        This is the canonical entry point for session resolution.
        All BHIV products call this when the companion initializes.

        Returns:
            {
                "session_id": "ses_...",
                "resume_token": "...",  (only on create)
                "actor_id": "user_123",
                "workspace_id": "default",
                "active_product_id": "gurukul",
                "state": "ACTIVE",
                "is_new": true/false,
                "transferred_from": null | "ses_..."
            }
        """
        runtime = self._get_runtime()
        if not runtime:
            # Fallback: return a basic session dict if runtime not available
            logger.warning("ContinuityService: Runtime not available, using basic session")
            return {
                "session_id": f"fallback_{user_id}",
                "actor_id": user_id,
                "workspace_id": workspace_id,
                "active_product_id": product_id,
                "state": "ACTIVE",
                "is_new": True,
                "transferred_from": None,
            }

        # Check for existing session by actor_id
        try:
            existing = self._find_active_session(runtime, user_id)
            if existing:
                current_product = existing.get("active_product_id")
                if current_product and current_product != product_id:
                    # User moved to a different product — transfer context
                    return self._transfer_session(
                        runtime, existing, product_id, workspace_id
                    )
                # Same product — reuse session
                return {**existing, "is_new": False, "transferred_from": None}
        except Exception as exc:
            logger.warning("ContinuityService.resolve_session lookup failed: %s", exc)

        # No existing session — create new
        try:
            session = runtime.sessions.create(
                actor_id=user_id,
                client_type=client_type,
                workspace_id=workspace_id,
                product_id=product_id,
            )
            return {**session, "is_new": True, "transferred_from": None}
        except Exception as exc:
            logger.warning("ContinuityService.create_session failed: %s", exc)
            return {
                "session_id": f"fallback_{user_id}",
                "actor_id": user_id,
                "workspace_id": workspace_id,
                "active_product_id": product_id,
                "state": "ACTIVE",
                "is_new": True,
                "transferred_from": None,
            }

    def _find_active_session(self, runtime, user_id: str) -> Optional[Dict[str, Any]]:
        """Find an active session by actor_id (user_id)."""
        try:
            sessions = runtime.store.list_sessions(limit=50)
            for sess in sessions:
                if sess.get("actor_id") == user_id and sess.get("state") == "ACTIVE":
                    return sess
        except Exception as exc:
            logger.warning("Session lookup by actor failed: %s", exc)
        return None

    def _transfer_session(
        self,
        runtime,
        source_session: Dict[str, Any],
        target_product_id: str,
        target_workspace_id: str,
    ) -> Dict[str, Any]:
        """Transfer session context to a new product."""
        try:
            source_id = source_session["session_id"]

            # Load portable context from source session
            context = runtime.context.load(source_id)
            portable = context.get("merged", {})

            # Execute transfer
            result = runtime.sessions.transfer(
                source_session_id=source_id,
                target_workspace_id=target_workspace_id,
                target_product_id=target_product_id,
                portable_context=portable,
            )

            new_session = result.get("session", {})
            return {
                **new_session,
                "is_new": False,
                "transferred_from": source_id,
            }
        except Exception as exc:
            logger.warning("Context transfer failed: %s — creating fresh session", exc)
            session = runtime.sessions.create(
                actor_id=source_session.get("actor_id", "unknown"),
                client_type=source_session.get("client_type", "web"),
                workspace_id=target_workspace_id,
                product_id=target_product_id,
            )
            return {
                **session,
                "is_new": True,
                "transferred_from": None,
            }

    def get_session_for_product(
        self, user_id: str, product_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the user's session for a specific product (if any)."""
        runtime = self._get_runtime()
        if not runtime:
            return None
        try:
            sessions = runtime.store.list_sessions(limit=100)
            for sess in sessions:
                if (
                    sess.get("actor_id") == user_id
                    and sess.get("active_product_id") == product_id
                    and sess.get("state") == "ACTIVE"
                ):
                    return sess
        except Exception:
            pass
        return None


# Singleton
continuity_service = ContinuityService()
