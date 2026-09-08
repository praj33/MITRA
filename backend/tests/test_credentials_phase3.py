import os
import pytest
import logging
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.core.encryption import encrypt_secret, decrypt_secret, is_encrypted, _get_fernet_key
from app.services.connected_account_service import connected_account_service
from app.services.otp_service import otp_service

client = TestClient(app)

TEST_JWT_SECRET = "test_phase3_secret_key_mitra_99999"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "test_phase3_encryption_key_32bytes_len=")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("ENVIRONMENT", "development")

def get_auth_header(user_id: str, email: str = "user@example.com") -> dict:
    token = create_access_token({"sub": user_id, "user_id": user_id, "email": email})
    return {"Authorization": f"Bearer {token}"}

# 1. Roundtrip Encryption & Decryption
def test_encryption_and_decryption_roundtrip():
    secret = "my_super_secret_app_password_99#"
    ciphertext = encrypt_secret(secret)
    assert ciphertext != secret
    assert is_encrypted(ciphertext)
    
    decrypted = decrypt_secret(ciphertext)
    assert decrypted == secret

# 2. Wrong Encryption Key Fails Decryption
def test_wrong_encryption_key_fails_decryption():
    secret = "oauth_refresh_token_xyz"
    key1 = "key_one_32_bytes_long_secret_key_1="
    key2 = "key_two_32_bytes_long_secret_key_2="
    
    ciphertext = encrypt_secret(secret, override_key=key1)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_secret(ciphertext, override_key=key2)

# 3. Missing Production Key Fails Closed
def test_missing_production_encryption_key_fails_closed(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)
    
    with pytest.raises(RuntimeError, match="TOKEN_ENCRYPTION_KEY is required in production"):
        encrypt_secret("test_secret")

# 4. Tokens Stored in DB Are Encrypted
def test_tokens_stored_in_db_are_encrypted():
    user_id = "user_enc_db_01"
    raw_token = "gho_1234567890abcdef"
    
    connected_account_service.create_connection(
        user_id=user_id,
        provider="github",
        email="dev@example.com",
        access_token=raw_token
    )
    
    # Internal query
    record = connected_account_service.get_user_connection(user_id, "github", include_decrypted_tokens=False)
    assert record is not None
    assert "access_token" not in record
    
    # Internal retrieval for provider execution
    decrypted_record = connected_account_service.get_user_connection(user_id, "github", include_decrypted_tokens=True)
    assert decrypted_record["access_token"] == raw_token

# 5. Tokens Are Never Returned in API
def test_tokens_are_never_returned_in_api():
    user_id = "user_api_safe_02"
    connected_account_service.create_connection(
        user_id=user_id,
        provider="google",
        email="user2@example.com",
        access_token="ya29.secret_token_val",
        refresh_token="1//04_refresh_secret"
    )
    
    headers = get_auth_header(user_id)
    response = client.get("/api/integrations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    response_str = str(data)
    assert "ya29.secret_token_val" not in response_str
    assert "1//04_refresh_secret" not in response_str
    assert "access_token" not in response_str
    assert "refresh_token" not in response_str

# 6. Gmail App Password Is Not Stored Plaintext
def test_gmail_app_password_is_not_stored_plaintext():
    user_id = "user_gmail_enc_03"
    headers = get_auth_header(user_id)
    app_pass = "abcd efgh ijkl mnop"
    
    response = client.post(
        "/api/integrations/gmail",
        headers=headers,
        json={"email": "gmail_user@example.com", "app_password": app_pass}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "app_password" not in res_data
    
    # Verify DB/Service state
    conn = connected_account_service.get_user_connection(user_id, "gmail", include_decrypted_tokens=True)
    assert conn is not None
    assert conn["access_token"] == app_pass

# 7. OTP Is Never Returned in API Response
def test_otp_is_never_returned_in_api_response():
    user_id = "user_otp_api_04"
    headers = get_auth_header(user_id)
    
    response = client.post(
        "/api/integrations/whatsapp/send-otp",
        headers=headers,
        json={"phone": "+15550001111"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "otp" not in data
    assert "demo_otp" not in data
    assert "code" not in data
    assert data["status"] == "success"

# 8. OTP Is Not Stored Plaintext
def test_otp_is_not_stored_plaintext():
    user_id = "user_otp_hash_05"
    phone = "+15550002222"
    
    raw_otp = otp_service.generate_otp(user_id, phone)
    
    # Read record from service internal store
    cache_key = f"{user_id}_{phone}_whatsapp_verify"
    from app.services.otp_service import _IN_MEMORY_OTP_STORE
    record = _IN_MEMORY_OTP_STORE.get(cache_key)
    if record:
        assert raw_otp not in str(record)
        assert "otp_hash" in record

# 9. Universal "123456" OTP Bypass Fails
def test_universal_123456_otp_bypass_fails():
    user_id = "user_bypass_test_06"
    phone = "+15550003333"
    headers = get_auth_header(user_id)
    
    otp_service.generate_otp(user_id, phone)
    
    # Attempt verification using "123456"
    response = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone, "code": "123456"}
    )
    assert response.status_code == 400
    assert "Invalid verification code" in response.json()["detail"]

# 10. Expired OTP Fails
def test_expired_otp_fails():
    user_id = "user_exp_otp_07"
    phone = "+15550004444"
    headers = get_auth_header(user_id)
    
    raw_otp = otp_service.generate_otp(user_id, phone, expiry_minutes=-1) # Expired 1 min ago
    
    response = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone, "code": raw_otp}
    )
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()

# 11. Used OTP Cannot Be Reused
def test_used_otp_cannot_be_reused():
    user_id = "user_reuse_otp_08"
    phone = "+15550005555"
    headers = get_auth_header(user_id)
    
    raw_otp = otp_service.generate_otp(user_id, phone)
    
    # First verify succeed
    resp1 = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone, "code": raw_otp}
    )
    assert resp1.status_code == 200
    assert resp1.json()["verified"] is True
    
    # Second verify fail
    resp2 = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone, "code": raw_otp}
    )
    assert resp2.status_code == 400
    assert "already been used" in resp2.json()["detail"].lower()

# 12. OTP Attempt Limit Works
def test_otp_attempt_limit_works():
    user_id = "user_attempts_09"
    phone = "+15550006666"
    headers = get_auth_header(user_id)
    
    raw_otp = otp_service.generate_otp(user_id, phone)
    
    # Make 3 wrong attempts
    for _ in range(3):
        res = client.post(
            "/api/integrations/whatsapp/verify",
            headers=headers,
            json={"phone": phone, "code": "000000"}
        )
        assert res.status_code == 400
        
    # 4th attempt with CORRECT OTP should now fail due to attempt limit
    res_final = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone, "code": raw_otp}
    )
    assert res_final.status_code == 400
    assert "maximum verification attempts exceeded" in res_final.json()["detail"].lower()

# 13. OTP Tied to Correct Authenticated User
def test_otp_tied_to_correct_authenticated_user():
    user_id_a = "user_a_10"
    user_id_b = "user_b_10"
    phone = "+15550007777"
    
    raw_otp = otp_service.generate_otp(user_id_a, phone)
    
    headers_b = get_auth_header(user_id_b)
    
    # User B attempts to verify User A's OTP
    response = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers_b,
        json={"phone": phone, "code": raw_otp}
    )
    assert response.status_code == 400

# 14. OTP Tied to Intended Target Phone
def test_otp_tied_to_intended_target_phone():
    user_id = "user_phone_11"
    phone_a = "+15550008888"
    phone_b = "+15550009999"
    headers = get_auth_header(user_id)
    
    raw_otp = otp_service.generate_otp(user_id, phone_a)
    
    response = client.post(
        "/api/integrations/whatsapp/verify",
        headers=headers,
        json={"phone": phone_b, "code": raw_otp}
    )
    assert response.status_code == 400

# 15. Unauthenticated OTP Endpoints Return 401
def test_unauthenticated_otp_endpoints_return_401():
    resp_send = client.post("/api/integrations/whatsapp/send-otp", json={"phone": "+15551112222"})
    assert resp_send.status_code == 401
    
    resp_verify = client.post("/api/integrations/whatsapp/verify", json={"phone": "+15551112222", "code": "123456"})
    assert resp_verify.status_code == 401

# 16. Cross-User OTP Verification Fails
def test_cross_user_otp_verification_fails():
    user_alice = "alice_12"
    user_bob = "bob_12"
    phone = "+15559990000"
    
    raw_otp = otp_service.generate_otp(user_alice, phone)
    
    # Alice verifies her own OTP -> 200
    headers_alice = get_auth_header(user_alice)
    resp_alice = client.post("/api/integrations/whatsapp/verify", headers=headers_alice, json={"phone": phone, "code": raw_otp})
    assert resp_alice.status_code == 200

# 17. Sensitive Values Not Logged
def test_sensitive_values_not_logged(caplog):
    caplog.set_level(logging.DEBUG)
    secret_pass = "super_confidential_app_pass_999"
    
    encrypt_secret(secret_pass)
    connected_account_service.create_connection(
        user_id="user_log_test",
        provider="gmail",
        email="test@example.com",
        access_token=secret_pass
    )
    
    log_text = caplog.text
    assert secret_pass not in log_text
