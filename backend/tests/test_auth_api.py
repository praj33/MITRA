import os

os.environ.setdefault("API_KEY", "localtest")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUTH_STORE_MODE", "inmemory")

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import auth_service


client = TestClient(app)
client.headers.update({"X-API-Key": "localtest"})


def setup_function():
    auth_service.reset_inmemory_store()


def test_signup_login_and_me_flow():
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Gauri Test",
            "email": "gauri@example.com",
            "password": "securepass123",
        },
    )

    assert signup_response.status_code == 201
    signup_body = signup_response.json()
    assert signup_body["user"]["email"] == "gauri@example.com"
    assert signup_body["user"]["name"] == "Gauri Test"
    assert signup_body["token"]

    duplicate_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Gauri Test",
            "email": "gauri@example.com",
            "password": "securepass123",
        },
    )
    assert duplicate_response.status_code == 409

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "gauri@example.com",
            "password": "securepass123",
        },
    )

    assert login_response.status_code == 200
    login_body = login_response.json()
    token = login_body["token"]
    assert login_body["user"]["id"] == signup_body["user"]["id"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["user"] == signup_body["user"]


def test_assistant_request_carries_authenticated_user_context():
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Mitra User",
            "email": "mitra@example.com",
            "password": "securepass123",
        },
    )

    assert signup_response.status_code == 201
    signup_body = signup_response.json()
    token = signup_body["token"]
    user_id = signup_body["user"]["id"]

    assistant_response = client.post(
        "/api/assistant",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "version": "3.0.0",
            "input": {"message": "hello"},
            "context": {
                "platform": "web",
                "device": "desktop",
                "session_id": "auth_assistant_session",
                "preferred_language": "en",
            },
        },
    )

    assert assistant_response.status_code == 200
    body = assistant_response.json()
    assert body["status"] == "success"
    assert body["system_context"]["user_id"] == user_id
    assert body["result"]["mitra"]["system_context"]["user_id"] == user_id
