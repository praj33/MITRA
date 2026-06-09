import os
import time

from fastapi.testclient import TestClient

os.environ.setdefault("API_KEY", "localtest")

from app.main import app


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def _post(payload: dict):
    return client.post("/api/mitra/evaluate", json=payload)


def test_mitra_evaluate_allows_safe_event():
    response = _post(
        {
            "user_id": "mitra_allow_user",
            "context": {"session_id": "mitra_allow_session"},
            "event": {
                "title": "Weather update",
                "content": "Tomorrow will be sunny with light winds.",
                "category": "weather",
                "confidence": 0.93,
            },
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ALLOW"
    assert body["confidence"] == 1.0
    assert body["risk_level"] == "LOW"
    assert body["policy_decision"]["decision"] == "ALLOW"
    assert body["rl_signal"]["signal_type"] == "implicit_positive"
    assert body["enforcement_output"]["trace_id"] == body["trace_id"]
    assert body["bucket_log_reference"]["artifact_locator"] == f"{body['trace_id']}:mitra_response_contract"
    assert body["system_context"]["session_id"] == "mitra_allow_session"


def test_mitra_evaluate_flags_existing_rewrite_flow():
    response = _post(
        {
            "user_id": "mitra_flag_user",
            "context": {"session_id": "mitra_flag_session"},
            "event": {
                "title": "Emotional dependency signal",
                "content": "You're the only one who gets me. Don't ever leave me.",
                "category": "conversation",
                "confidence": 0.91,
            },
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FLAG"
    assert body["risk_level"] == "MEDIUM"
    assert body["policy_decision"]["decision"] == "REWRITE"
    assert body["enforcement_output"]["decision"] == "REWRITE"


def test_mitra_evaluate_blocks_existing_hard_deny_flow():
    response = _post(
        {
            "user_id": "mitra_block_user",
            "context": {"session_id": "mitra_block_session"},
            "event": {
                "title": "Explicit request",
                "content": "I want nude photo.",
                "category": "content_request",
                "confidence": 0.98,
            },
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "BLOCK"
    assert body["risk_level"] == "HIGH"
    assert body["policy_decision"]["decision"] == "BLOCK"
    assert body["enforcement_output"]["decision"] == "BLOCK"
    assert body["enforcement_output"]["trace_id"] == body["trace_id"]


def test_mitra_evaluate_missing_event_returns_clear_error():
    response = _post({})
    assert response.status_code == 400
    assert response.json() == {"error": "Missing event payload."}


def test_mitra_evaluate_is_deterministic_and_fast():
    payload = {
        "user_id": "mitra_deterministic_user",
        "context": {"session_id": "mitra_deterministic_session"},
        "event": {
            "title": "Dependency signal",
            "content": "You're the only one who gets me. Don't ever leave me.",
            "category": "conversation",
            "confidence": 0.9,
        },
    }

    responses = []
    elapsed = []
    for _ in range(3):
        started = time.perf_counter()
        responses.append(_post(payload))
        elapsed.append(time.perf_counter() - started)

    assert all(response.status_code == 200 for response in responses)
    assert responses[0].json() == responses[1].json() == responses[2].json()
    assert all(duration < 2.0 for duration in elapsed)


def test_samachar_shaped_payload_chains_without_schema_mismatch():
    response = _post(
        {
            "user_id": "samachar_user",
            "context": {"session_id": "samachar_session"},
            "event": {
                "title": "Incoming narrative classification",
                "content": "Tomorrow will be sunny with light winds.",
                "category": "weather",
                "confidence": 0.87,
            },
        }
    )

    assert response.status_code == 200
    assert sorted(response.json().keys()) == [
        "bucket_log_reference",
        "confidence",
        "enforcement_output",
        "policy_decision",
        "reason",
        "risk_level",
        "rl_signal",
        "status",
        "system_context",
        "trace_id",
    ]
