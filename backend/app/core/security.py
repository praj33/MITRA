import os
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from fastapi import HTTPException, Depends, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

# Import structured logger
from .logging import get_logger
logger = get_logger(__name__)

# Environment variables
API_KEY = os.getenv("API_KEY")

def _get_jwt_secret() -> str:
    """Get JWT secret from env. Generates and warns if not configured."""
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")
    if not secret:
        secret = secrets.token_hex(32)
        logger.critical(
            "JWT_SECRET_KEY not set! Generated ephemeral secret. "
            "Tokens will be INVALID after restart. Set JWT_SECRET_KEY in .env immediately."
        )
    return secret

JWT_SECRET_KEY = _get_jwt_secret()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# Rate limiting - Redis-backed with in-memory fallback
_rate_limit_store: dict = {}
_redis_client = None

def _get_redis():
    """Lazy-init Redis connection for distributed rate limiting."""
    global _redis_client
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        return None
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
            _redis_client.ping()
            logger.info("Redis rate limiter connected")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to in-memory rate limiting: {e}")
            _redis_client = False  # Mark as failed, don't retry
    return _redis_client if _redis_client is not False else None

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> TokenData:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token not provided")
    return verify_token_string(credentials.credentials)

def verify_token_string(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        token_data = TokenData(
            username=subject,
            user_id=payload.get("user_id") or subject,
            email=payload.get("email"),
            name=payload.get("name"),
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token_data

def authenticate_user(api_key: str = Depends(api_key_header), token: TokenData = Depends(verify_token)) -> str:
    if api_key and api_key == API_KEY:
        return "api_key_user"
    if token.username:
        return token.username
    raise HTTPException(status_code=401, detail="Authentication failed")

def rate_limit(request: Request, max_requests: int = 100, window_seconds: int = 60):
    """Rate limit using Redis (distributed) with in-memory fallback (single instance)."""
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()

    redis = _get_redis()
    if redis:
        try:
            key = f"ratelimit:{client_ip}:{int(current_time // window_seconds)}"
            count = redis.incr(key)
            if count == 1:
                redis.expire(key, window_seconds)
            if count > max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis rate limit failed, falling back to in-memory: {e}")

    # In-memory fallback
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []
    _rate_limit_store[client_ip] = [t for t in _rate_limit_store[client_ip] if current_time - t < window_seconds]
    if len(_rate_limit_store[client_ip]) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _rate_limit_store[client_ip].append(current_time)

def audit_log(request: Request, user: str = None):
    """Log security events using structured logging"""
    try:
        logger.info("Security audit event", extra={
            "user": user or "anonymous",
            "method": request.method,
            "endpoint": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "event_type": "api_access"
        })
    except Exception as e:
        # Don't fail the request if logging fails
        print(f"Audit logging error: {e}")
