"""
test_email_content_extraction_pipeline.py — End-to-end regression tests for canonical email content extraction.

Covers:
- Inputs A, B, C, D
- Exact production problem utterance
- E. Invariant that canonical content != raw command
- F. Confirmation card payload contains canonical content
- G. Pending action stores canonical content
- H. Gmail executor receives canonical content only
- I. Gmail READ regression
- J. Gmail DRAFT regression (canonical draft body)
- K. Gmail SEND approval required
- L. Pending action direct REST confirmation
- M. GET /api/communication/drafts/{draft_id} endpoint
"""
import asyncio
import json
import uuid
from unittest.mock import MagicMock, patch
import pytest

from app.models.communication import CommunicationAction, CommunicationChannel, CommunicationIntent
from app.services.communication_service import communication_service
from app.services.pending_action_service import pending_action_service
from app.services.connected_account_service import connected_account_service
from app.executors.email_executor import EmailExecutor
from app.companion.companion_orchestrator import companion_orchestrator
from app.companion.capability_registry import capability_registry
from app.capabilities.email_capability import EmailCapability
from app.capabilities.email_entity_extractor import extract_email_entities, is_raw_command_text


@pytest.fixture(autouse=True)
def ensure_email_capability():
    if not capability_registry.get("email"):
        capability_registry.register(EmailCapability())


def test_a_send_saying_quoted():
    """A. Send an email to rajprajapati1729@gmail.com saying "Hello Raj" """
    text = 'Send an email to rajprajapati1729@gmail.com saying "Hello Raj"'
    extracted = extract_email_entities(text)
    assert extracted["recipient"] == "rajprajapati1729@gmail.com"
    assert extracted["content"] == "Hello Raj"
    assert extracted["content"] != text


def test_b_send_with_subject_and_message():
    """B. Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let's meet tomorrow." """
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow."'
    extracted = extract_email_entities(text)
    assert extracted["recipient"] == "rajprajapati1729@gmail.com"
    assert extracted["subject"] == "Meeting tomorrow"
    assert extracted["content"] == "Hi Raj, let's meet tomorrow."
    assert extracted["content"] != text


def test_b_exact_production_utterance():
    """Exact production problem input with contractions and sentences."""
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow. Please let me know what time works for you."'
    extracted = extract_email_entities(text)
    assert extracted["recipient"] == "rajprajapati1729@gmail.com"
    assert extracted["subject"] == "Meeting tomorrow"
    assert extracted["content"] == "Hi Raj, let's meet tomorrow. Please let me know what time works for you."
    assert extracted["content"] != text


def test_c_email_colon_message():
    """C. Email rajprajapati1729@gmail.com: "Please call me." """
    text = 'Email rajprajapati1729@gmail.com: "Please call me."'
    extracted = extract_email_entities(text)
    assert extracted["recipient"] == "rajprajapati1729@gmail.com"
    assert extracted["content"] == "Please call me."
    assert extracted["content"] != text


def test_d_send_with_subject_and_body():
    """D. Send an email to rajprajapati1729@gmail.com with subject "Meeting" and body "Let's meet at 5 PM." """
    text = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting" and body "Let\'s meet at 5 PM."'
    extracted = extract_email_entities(text)
    assert extracted["recipient"] == "rajprajapati1729@gmail.com"
    assert extracted["subject"] == "Meeting"
    assert extracted["content"] == "Let's meet at 5 PM."
    assert extracted["content"] != text


def test_e_invariant_canonical_content_never_raw_command():
    """E. Verify canonical content is never equal to the complete raw command."""
    test_utterances = [
        'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow. Please let me know what time works for you."',
        'Send an email to alice@example.com saying "Hello Alice"',
        'Create a draft email to rajprajapati1729@gmail.com saying "Meet me urgently."',
        'Email test@example.com: "Testing body extraction"',
        'Send an email to alice@example.com. Subject: Status. Body: All done.',
    ]
    for utterance in test_utterances:
        res = extract_email_entities(utterance)
        assert res["content"] != utterance
        assert not is_raw_command_text(res["content"], utterance)


def test_f_g_h_streaming_pipeline_canonical_content_and_executor():
    """F, G, H. Confirmation card preview, pending action, and Gmail executor receive canonical content only."""
    async def _run():
        user_id = f"test_user_pipeline_{uuid.uuid4().hex[:8]}"
        account_id = "user@example.com"
        raw_cmd = 'Send an email to rajprajapati1729@gmail.com with subject "Meeting tomorrow" and message "Hi Raj, let\'s meet tomorrow. Please let me know what time works for you."'
        expected_content = "Hi Raj, let's meet tomorrow. Please let me know what time works for you."
        expected_subject = "Meeting tomorrow"

        with patch.object(connected_account_service, "get_user_connection") as mock_conn, \
             patch.object(EmailExecutor, "send_message") as mock_send:

            mock_conn.return_value = {
                "provider": "gmail",
                "email": "user@example.com",
                "access_token": "valid_token",
            }
            mock_send.return_value = {
                "status": "success",
                "message_id": "gmail_msg_canonical_123",
                "from": "user@example.com",
            }

            # 1. Process streaming command
            events = []
            async for evt in companion_orchestrator.process_stream(user_id=user_id, message=raw_cmd):
                events.append(evt)

            # F. Assert approval_required event has canonical preview
            approval_evt = next((e for e in events if e.get("type") == "approval_required"), None)
            assert approval_evt is not None
            conf = approval_evt.get("confirmation", {})
            assert conf.get("recipient") == "rajprajapati1729@gmail.com"
            assert conf.get("subject") == expected_subject
            assert conf.get("content") == expected_content
            assert conf.get("content") != raw_cmd

            pending_action_id = approval_evt.get("pending_action_id")
            assert pending_action_id is not None

            # G. Assert pending action in DB has canonical content
            pending = pending_action_service.get_pending_action(pending_action_id, user_id=user_id)
            assert pending is not None
            assert pending.recipient == "rajprajapati1729@gmail.com"
            assert pending.subject == expected_subject
            assert pending.content == expected_content
            assert pending.content != raw_cmd

            # Send executor MUST NOT have been called yet
            mock_send.assert_not_called()

            # H. Confirm action via dedicated REST endpoint
            confirm_res = communication_service.confirm_pending_action(
                pending_action_id=pending_action_id,
                user_id=user_id,
            )
            assert confirm_res.status in ("sent", "success")

            # Assert Gmail executor was called with CANONICAL content only, never raw command
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["to_email"] == "rajprajapati1729@gmail.com"
            assert call_kwargs["subject"] == expected_subject
            assert call_kwargs["message"] == expected_content
            assert call_kwargs["message"] != raw_cmd

    asyncio.run(_run())


def test_i_gmail_read_regression():
    """I. Regression test existing Gmail READ."""
    async def _run():
        user_id = f"test_user_read_{uuid.uuid4().hex[:8]}"

        with patch.object(connected_account_service, "get_user_connection") as mock_conn, \
             patch.object(EmailExecutor, "read_inbox_gmail") as mock_read:

            mock_conn.return_value = {"provider": "gmail", "email": "user@example.com"}
            mock_read.return_value = {
                "status": "success",
                "messages": [
                    {"id": "m1", "from": "boss@example.com", "subject": "Project", "snippet": "Good job"},
                ],
                "count": 1,
            }

            resp = await companion_orchestrator.process(
                user_id=user_id,
                message="Show me my latest 5 emails.",
            )
            assert resp.capability_result is not None
            assert resp.capability_result["status"] == "success"
            assert "boss@example.com" in resp.message

    asyncio.run(_run())


def test_j_gmail_draft_regression_canonical_content():
    """J. Regression test existing Gmail DRAFT: creates draft with canonical content, never raw command."""
    async def _run():
        user_id = f"test_user_draft_{uuid.uuid4().hex[:8]}"
        raw_prompt = 'Create a draft email to rajprajapati1729@gmail.com saying "Meet me urgently."'

        with patch.object(connected_account_service, "get_user_connection") as mock_conn, \
             patch.object(EmailExecutor, "create_draft_gmail") as mock_create_draft:

            mock_conn.return_value = {"provider": "gmail", "email": "user@example.com"}
            mock_create_draft.return_value = {
                "status": "success",
                "draft_id": "draft_789_urgent",
                "message": "Draft created successfully for rajprajapati1729@gmail.com.",
            }

            resp = await companion_orchestrator.process(
                user_id=user_id,
                message=raw_prompt,
            )
            assert resp.capability_result is not None
            assert resp.capability_result["status"] == "success"
            assert "draft" in resp.message.lower()

            # Verify executor received canonical body only
            mock_create_draft.assert_called_once()
            call_kwargs = mock_create_draft.call_args[1]
            assert call_kwargs["to_email"] == "rajprajapati1729@gmail.com"
            assert call_kwargs["message"] == "Meet me urgently."
            assert call_kwargs["message"] != raw_prompt

    asyncio.run(_run())


def test_k_gmail_send_approval_invariant():
    """K. Regression test Gmail SEND approval required (never sends directly)."""
    async def _run():
        user_id = f"test_user_approval_{uuid.uuid4().hex[:8]}"

        with patch.object(connected_account_service, "get_user_connection") as mock_conn, \
             patch.object(EmailExecutor, "send_message") as mock_send:

            mock_conn.return_value = {"provider": "gmail", "email": "user@example.com"}

            resp = await companion_orchestrator.process(
                user_id=user_id,
                message='Send an email to rajprajapati1729@gmail.com saying "Hello Raj"',
            )
            assert resp.capability_result is not None
            assert resp.capability_result["status"] == "pending"
            assert resp.capability_result["data"]["status"] == "confirmation_required"
            mock_send.assert_not_called()

    asyncio.run(_run())


def test_l_pending_action_direct_rest_confirmation():
    """L. Regression test pending-action direct REST confirmation."""
    user_id = f"test_user_rest_confirm_{uuid.uuid4().hex[:8]}"
    account_id = "user@example.com"

    with patch.object(connected_account_service, "get_user_connection") as mock_conn, \
         patch.object(EmailExecutor, "send_message") as mock_send:

        mock_conn.return_value = {
            "provider": "gmail",
            "email": "user@example.com",
            "access_token": "valid_token",
        }
        mock_send.return_value = {
            "status": "success",
            "message_id": "gmail_msg_rest_456",
            "from": "user@example.com",
        }

        # Stage canonical action
        action = CommunicationAction(
            intent=CommunicationIntent.SEND_MESSAGE,
            channel=CommunicationChannel.EMAIL,
            recipient="test@example.com",
            subject="Canonical Subject",
            content="Canonical Message Body",
            user_id=user_id,
            account_id=account_id,
            confirmation_confirmed=False,
        )
        staged = communication_service.execute_action(action)
        assert staged.status == "confirmation_required"
        mock_send.assert_not_called()

        # Confirm via REST path
        res = communication_service.confirm_pending_action(
            pending_action_id=staged.pending_action_id,
            user_id=user_id,
        )
        assert res.status in ("sent", "success")
        mock_send.assert_called_once()
        assert mock_send.call_args[1]["message"] == "Canonical Message Body"


def test_m_get_draft_endpoint():
    """M. Regression test GET /api/communication/drafts/{draft_id} endpoint."""
    user_id = f"test_user_draft_api_{uuid.uuid4().hex[:8]}"

    with patch.object(connected_account_service, "has_gmail_compose_access", return_value=True), \
         patch.object(EmailExecutor, "get_draft_gmail") as mock_get_draft:

        mock_get_draft.return_value = {
            "status": "success",
            "draft_id": "draft_abc_123",
            "draft": {
                "id": "draft_abc_123",
                "recipient": "recipient@example.com",
                "subject": "Draft Subject",
                "content": "Draft Content",
            },
        }

        res = communication_service.get_draft(draft_id="draft_abc_123", user_id=user_id)
        assert res["status"] == "success"
        assert res["draft"]["recipient"] == "recipient@example.com"
        assert res["draft"]["content"] == "Draft Content"
        mock_get_draft.assert_called_once_with(user_id=user_id, draft_id="draft_abc_123", trace_id=None)
