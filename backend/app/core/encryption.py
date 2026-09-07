import os
import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Fallback dev key derived deterministically for local testing when ENV != "production"
DEV_FALLBACK_SEED = b"mitra_dev_token_encryption_key_safe_fallback_v1_2026"
DEV_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(DEV_FALLBACK_SEED).digest())

def _get_fernet_key() -> bytes:
    env_mode = (os.getenv("ENV") or os.getenv("ENVIRONMENT") or "development").strip().lower()
    is_production = env_mode == "production"
    raw_key = os.getenv("TOKEN_ENCRYPTION_KEY", "").strip()

    if not raw_key:
        if is_production:
            raise RuntimeError(
                "CRITICAL SECURITY FAILURE: TOKEN_ENCRYPTION_KEY is required in production environment."
            )
        else:
            logger.warning(
                "TOKEN_ENCRYPTION_KEY is missing. Using safe deterministic development encryption key. DO NOT USE IN PRODUCTION."
            )
            return DEV_FERNET_KEY

    # Format key properly into a 32-byte url-safe base64 Fernet key
    try:
        # Check if already a valid Fernet key
        if len(raw_key) == 44 and raw_key.endswith("="):
            # Test key validity
            Fernet(raw_key.encode("utf-8"))
            return raw_key.encode("utf-8")
    except Exception:
        pass

    # If key is an arbitrary string, derive a valid 32-byte key using SHA-256
    derived_bytes = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(derived_bytes)

def _get_cipher(override_key: Optional[str] = None) -> Fernet:
    if override_key:
        try:
            if len(override_key) == 44 and override_key.endswith("="):
                key_bytes = override_key.encode("utf-8")
            else:
                key_bytes = base64.urlsafe_b64encode(hashlib.sha256(override_key.encode("utf-8")).digest())
            return Fernet(key_bytes)
        except Exception as exc:
            raise ValueError(f"Invalid encryption key: {exc}")
    return Fernet(_get_fernet_key())

def encrypt_secret(value: Optional[str], override_key: Optional[str] = None) -> str:
    """
    Encrypt a sensitive string value using authenticated symmetric encryption (Fernet).
    Returns ciphertext string. Handles empty/None values safely.
    """
    if not value:
        return ""
    
    cipher = _get_cipher(override_key)
    encrypted_bytes = cipher.encrypt(value.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_secret(ciphertext: Optional[str], override_key: Optional[str] = None) -> str:
    """
    Decrypt Fernet ciphertext string to return plaintext secret.
    Raises ValueError on invalid token, wrong key, or corrupted payload.
    """
    if not ciphertext:
        return ""
    
    try:
        cipher = _get_cipher(override_key)
        decrypted_bytes = cipher.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise ValueError("Decryption failed: invalid ciphertext or wrong encryption key")
    except Exception as exc:
        raise ValueError(f"Decryption failed: {exc}")

def is_encrypted(value: Optional[str]) -> bool:
    """Check if value matches standard Fernet ciphertext format."""
    if not value or not isinstance(value, str):
        return False
    return value.startswith("gAAAAA") and len(value) > 50
