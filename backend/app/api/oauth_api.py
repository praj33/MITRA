import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse

from app.core.auth_dependencies import get_current_user
from app.services.oauth_transaction_service import oauth_transaction_service
from app.services.connected_account_service import connected_account_service
from app.services.identity_account_service import identity_account_service
from app.integrations.oauth.registry import oauth_provider_registry
from app.services.auth_service import auth_service
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

def _token_payload(user: dict) -> dict:
    return {
        "sub": user["id"],
        "user_id": user["id"],
        "email": user["email"],
        "name": user["name"],
    }

@router.get("/api/oauth/{provider}/start")
@router.get("/api/auth/{provider}")  # Compatible route alias
async def start_oauth_flow(
    provider: str,
    purpose: str = Query("connect", description="OAuth transaction purpose: 'connect' or 'login'"),
    user_id: Optional[str] = Query(None, description="Ignored: identity is derived strictly from Bearer token"),
    request: Request = None
):
    """
    Initiates secure OAuth 2.0 PKCE transaction.
    For 'connect' purpose: requires valid JWT bearer token.
    For 'login' purpose: public endpoint.
    Returns JSON authorization URL or HTTP 302 redirect.
    """
    provider_name = provider.lower()
    try:
        provider_inst = oauth_provider_registry.get(provider_name)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    auth_user_id = None
    if purpose == "connect":
        # Extract JWT identity strictly from Authorization header
        auth_header = request.headers.get("Authorization") if request else None
        if not auth_header or not auth_header.strip().lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Authentication required for connecting service accounts.")
        
        from app.core.security import verify_token_string
        token = auth_header.split(" ")[1]
        try:
            token_data = verify_token_string(token)
            auth_user_id = token_data.user_id or token_data.username
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token.")

        if not auth_user_id:
            raise HTTPException(status_code=401, detail="Invalid user session.")

    # Create cryptographically secure OAuth transaction
    tx = oauth_transaction_service.create_transaction(
        provider=provider_name,
        purpose=purpose,
        user_id=auth_user_id
    )

    auth_url = provider_inst.get_authorization_url(
        state=tx["state"],
        code_challenge=tx["code_challenge"],
        purpose=purpose
    )

    return {
        "url": auth_url,
        "auth_url": auth_url,
        "state": tx["state"],
        "provider": provider_name,
        "purpose": purpose
    }

@router.get("/api/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    request: Request = None
):
    """
    Handles OAuth 2.0 server-side authorization code exchange and identity verification.
    Validates state, performs code exchange with PKCE, encrypts tokens, and updates connection/identity stores.
    """
    provider_name = provider.lower()
    
    if error:
        logger.warning(f"OAuth callback returned error from provider {provider}: {error}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error": "authorization_denied", "detail": f"OAuth provider error: {error}"}
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing required authorization code or state parameter.")

    # 1. Validate and consume OAuth state transaction (enforces expiration, single-use, provider match)
    tx = oauth_transaction_service.validate_and_consume_transaction(
        state=state,
        provider=provider_name
    )

    try:
        provider_inst = oauth_provider_registry.get(provider_name)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")

    # 2. Server-side code exchange with PKCE code_verifier
    try:
        tokens = provider_inst.exchange_code(
            code=code,
            code_verifier=tx.get("code_verifier"),
            redirect_uri=tx.get("redirect_uri")
        )
    except Exception as exc:
        logger.error(f"OAuth code exchange failed: {exc}")
        raise HTTPException(status_code=400, detail="Authorization code exchange failed. Please try again.")

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    raw_expires = tokens.get("expires_in")
    expires_in = int(raw_expires) if raw_expires is not None else 3600
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

    if not access_token:
        raise HTTPException(status_code=400, detail="Provider response did not include a valid access token.")

    # 3. Retrieve provider identity
    try:
        identity = provider_inst.get_user_identity(access_token=access_token, id_token=tokens.get("id_token"))
    except Exception as exc:
        logger.error(f"Failed fetching user identity from {provider}: {exc}")
        raise HTTPException(status_code=400, detail="Failed to verify identity with provider.")

    provider_subject = identity["provider_subject"]
    email = identity["email"]
    purpose = tx.get("purpose", "connect")

    if purpose == "connect":
        user_id = tx.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid connection transaction state.")

        # Persist connected account with encrypted tokens
        connected_account_service.create_connection(
            user_id=user_id,
            provider=provider_name,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            provider_account_id=provider_subject,
            scopes=tx.get("scopes"),
            expires_at=expires_at
        )

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        redirect_target = f"{frontend_url}/settings?status=success&provider={provider_name}&email={email}"
        
        # Check if browser requested JSON API or HTML redirect
        accept = request.headers.get("accept", "") if request else ""
        if "text/html" in accept:
            return RedirectResponse(url=redirect_target, status_code=302)

        return {
            "status": "success",
            "message": f"Successfully connected {provider_name.capitalize()} account ({email}).",
            "provider": provider_name,
            "email": email,
            "user_id": user_id
        }

    else:
        # LOGIN FLOW
        existing_link = identity_account_service.get_identity(provider_name, provider_subject)
        
        if existing_link:
            user_id = existing_link["user_id"]
            user = await auth_service.get_public_user_by_id(user_id)
            if not user:
                # User record missing; recreate user record safely
                user = await auth_service.create_user(name=identity["name"], email=email, password=create_access_token({"sub": "oauth_user"}))
                identity_account_service.link_identity(user["id"], provider_name, provider_subject, email)
        else:
            # Check if user with same email exists in auth_service
            user = await auth_service.get_user_by_email(email)
            if not user:
                # Create new MITRA user
                import uuid
                random_pass = f"oauth_pass_{uuid.uuid4().hex}"
                user = await auth_service.create_user(name=identity["name"], email=email, password=random_pass)

            user_id = user["id"]
            identity_account_service.link_identity(user_id, provider_name, provider_subject, email)

        # Generate MITRA access token
        jwt_token = create_access_token(data=_token_payload(user))

        # Store connected account tokens encrypted
        connected_account_service.create_connection(
            user_id=user_id,
            provider=provider_name,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            provider_account_id=provider_subject,
            scopes=tx.get("scopes"),
            expires_at=expires_at
        )

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        redirect_target = f"{frontend_url}/auth/callback?token={jwt_token}"

        accept = request.headers.get("accept", "") if request else ""
        if "text/html" in accept:
            return RedirectResponse(url=redirect_target, status_code=302)

        return {
            "status": "success",
            "token": jwt_token,
            "user": user
        }

@router.get("/api/connections")
async def list_user_connections(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves safe metadata for all active connected accounts for the authenticated user.
    Tokens and secrets are strictly excluded.
    """
    auth_user_id = current_user["user_id"]
    connections = connected_account_service.list_user_connections(auth_user_id)
    return {
        "user_id": auth_user_id,
        "connections": connections
    }

@router.delete("/api/connections/{provider}")
async def disconnect_account(
    provider: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Disconnects and removes the specified provider connection for the authenticated user only.
    Prevents cross-user disconnection (IDOR safe).
    """
    auth_user_id = current_user["user_id"]
    provider_name = provider.lower()

    # Best effort token revocation
    conn = connected_account_service.get_user_connection(auth_user_id, provider_name, include_decrypted_tokens=True)
    if conn and conn.get("access_token"):
        try:
            provider_inst = oauth_provider_registry.get(provider_name)
            provider_inst.revoke_token(conn["access_token"])
        except Exception:
            pass

    deleted = connected_account_service.delete_connection(auth_user_id, provider_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No active connection found for provider '{provider}'.")

    return {
        "status": "success",
        "message": f"Successfully disconnected {provider_name.capitalize()} account.",
        "provider": provider_name
    }
