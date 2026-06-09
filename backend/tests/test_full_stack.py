import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def test_root_reports_current_backend():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "AI Assistant Backend API v3.0.0"


@pytest.mark.parametrize(
    "retired_endpoint",
    [
        "/api/summarize",
        "/api/intent",
        "/api/task",
        "/api/decision_hub",
        "/api/rl_action",
        "/api/embed",
        "/api/respond",
        "/api/voice_stt",
        "/api/voice_tts",
        "/api/external_llm",
        "/api/external_app",
    ],
)
def test_retired_parallel_entrypoints_are_not_exposed(retired_endpoint):
    response = client.post(retired_endpoint, json={})

    assert response.status_code == 404


def test_mitra_is_the_single_decision_entrypoint():
    response = client.post(
        "/api/mitra/evaluate",
        json={
            "event": {
                "type": "content",
                "content": "Help me plan a study schedule",
                "metadata": {},
            },
            "context": {
                "user_id": "full-stack-user",
                "session_id": "full-stack-session",
                "platform": "web",
                "device": "desktop",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ALLOW"
    assert body["confidence"] == 1.0
    assert body["trace_id"] == body["policy_decision"]["trace_id"]
    assert body["trace_id"] == body["enforcement_output"]["trace_id"]
    assert body["trace_id"] == body["bucket_log_reference"]["trace_id"]
    assert set(body) == {
        "status",
        "risk_level",
        "reason",
        "confidence",
        "trace_id",
        "policy_decision",
        "rl_signal",
        "enforcement_output",
        "bucket_log_reference",
        "system_context",
    }
