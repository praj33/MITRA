from fastapi import APIRouter, Header, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal, Union, AsyncGenerator
from datetime import datetime
import json
import os

from app.core.assistant_orchestrator import handle_assistant_request
from app.core.pydantic_compat import model_to_dict
from app.core.security import verify_token_string

router = APIRouter()

# =========================
# REQUEST SCHEMAS (LOCKED)
# =========================

class AssistantInput(BaseModel):
    message: Optional[str] = None
    summarized_payload: Optional[dict] = None
    audio_data: Optional[bytes] = None
    audio_format: Optional[str] = "mp3"


class AssistantContext(BaseModel):
    platform: str = "web"
    device: str = "desktop"
    session_id: Optional[str] = None
    voice_input: bool = False
    preferred_language: Optional[str] = "auto"
    detected_language: Optional[str] = None
    audio_input_data: Optional[bytes] = None
    audio_output_requested: bool = False
    age_gate_status: bool = False
    region_policy: Optional[dict] = None
    platform_policy: Optional[dict] = None
    user_context: Optional[dict] = None
    authenticated_user_context: Optional[dict] = None


class AssistantRequest(BaseModel):
    version: Literal["3.0.0"]
    input: AssistantInput
    context: AssistantContext


# =========================
# RESPONSE SCHEMAS (LOCKED)
# =========================

class AssistantResult(BaseModel):
    type: Literal["passive", "intelligence", "workflow"]
    response: str
    task: Optional[dict] = None
    enforcement: Optional[dict] = None
    safety: Optional[dict] = None
    execution: Optional[dict] = None
    language_metadata: Optional[dict] = None
    audio_response: Optional[bytes] = None
    system_context: Optional[dict] = None
    mitra: Optional[dict] = None


class AssistantSuccessResponse(BaseModel):
    version: Literal["3.0.0"]
    status: Literal["success"]
    result: AssistantResult
    processed_at: str
    trace_id: Optional[str] = None
    signal_type: Optional[
        Literal["correction", "intent_refinement", "implicit_positive", "implicit_negative"]
    ] = None
    system_context: Optional[dict] = None


class AssistantErrorResponse(BaseModel):
    version: Literal["3.0.0"]
    status: Literal["error"]
    error: dict
    processed_at: str
    trace_id: Optional[str] = None
    signal_type: Optional[
        Literal["correction", "intent_refinement", "implicit_positive", "implicit_negative"]
    ] = None
    system_context: Optional[dict] = None


def _build_authenticated_user_context(
    *,
    request_context: AssistantContext,
    x_api_key: str,
    authorization: Optional[str],
) -> dict:
    auth_context = dict(request_context.user_context or {})
    auth_context.update(request_context.authenticated_user_context or {})

    auth_context["api_key_present"] = bool(x_api_key)
    auth_context.setdefault("auth_method", "api_key")
    auth_context.setdefault("principal", "api_key_user")

    if authorization:
        auth_context["authorization_present"] = True
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                token_data = verify_token_string(token)
                auth_context["principal"] = token_data.user_id or token_data.username or auth_context["principal"]
                if token_data.user_id:
                    auth_context["user_id"] = token_data.user_id
                if token_data.email:
                    auth_context["email"] = token_data.email
                if token_data.name:
                    auth_context["name"] = token_data.name
                auth_context["auth_method"] = "bearer"
                auth_context["token_valid"] = True
            except Exception:
                auth_context["token_valid"] = False
        else:
            auth_context["token_valid"] = False
    else:
        auth_context["authorization_present"] = False

    if request_context.session_id:
        auth_context.setdefault("session_id", request_context.session_id)
    auth_context.setdefault("platform", request_context.platform)
    auth_context.setdefault("device", request_context.device)

    return {k: v for k, v in auth_context.items() if v is not None}


# =========================
# SINGLE PUBLIC ENDPOINT
# =========================

@router.options("/api/assistant")
async def assistant_options(request: Request):
    """
    Handle CORS preflight requests for /api/assistant.
    This explicit handler prevents FastAPI from trying to validate OPTIONS requests
    against the POST route handler which requires headers and body.
    """
    # Get allowed origins from environment
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        allowed_origins.append(frontend_url)
        if frontend_url.startswith("https://"):
            allowed_origins.append(frontend_url.replace("https://", "http://"))
        elif frontend_url.startswith("http://"):
            allowed_origins.append(frontend_url.replace("http://", "https://"))
    
    # Additional CORS origins from env
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if cors_origins:
        allowed_origins.extend([o.strip() for o in cors_origins.split(",") if o.strip()])
    
    origin = request.headers.get("origin", "")
    
    # Check if origin is allowed
    is_allowed = False
    if origin:
        if origin in allowed_origins:
            is_allowed = True
        # Also allow any FRONTEND_URL subdomain pattern if it's a Render/Vercel URL
        if frontend_url and origin != frontend_url:
            import re
            base_domain = re.escape(frontend_url.split("://")[-1].split("/")[0])
            if re.match(rf"https?://{base_domain}$", origin):
                is_allowed = True
    
    # Determine allowed origin
    if is_allowed and origin:
        allowed_origin = origin
    elif allowed_origins:
        allowed_origin = allowed_origins[0]
    else:
        allowed_origin = "*"
    
    # Return 200 OK with CORS headers for preflight
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-API-Key, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

@router.post(
    "/api/assistant",
    response_model=Union[AssistantSuccessResponse, AssistantErrorResponse]
)
async def assistant_endpoint(
    request: AssistantRequest,
    x_api_key: str = Header(...),
    authorization: Optional[str] = Header(None),
):
    """
    SINGLE production entrypoint for AI Assistant.
    Backend is LOCKED and frontend-safe.
    """
    try:
        request_payload = model_to_dict(request)
        authenticated_user_context = _build_authenticated_user_context(
            request_context=request.context,
            x_api_key=x_api_key,
            authorization=authorization,
        )
        request_payload["context"]["authenticated_user_context"] = authenticated_user_context
        request_payload["context"]["user_context"] = authenticated_user_context
        return await handle_assistant_request(request_payload)
    except Exception as e:
        # Final safety net - catch any unhandled exceptions
        import traceback
        from datetime import datetime
        error_trace = traceback.format_exc()
        print(f"Unhandled exception in assistant endpoint: {e}\n{error_trace}")
        
        # Return error response in expected format
        return {
            "version": "3.0.0",
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing your request."
            },
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }


# =========================
# SSE STREAMING ENDPOINT
# =========================

async def _stream_assistant_response(
    request_payload: dict,
) -> AsyncGenerator[str, None]:
    """Generate SSE events from assistant response."""
    try:
        yield f"event: start\ndata: {json.dumps({'status': 'processing'})}\n\n"

        result = await handle_assistant_request(request_payload)

        # Stream the full response as a single event
        yield f"event: message\ndata: {json.dumps(result)}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    except Exception as e:
        error_payload = {
            "version": "3.0.0",
            "status": "error",
            "error": {"code": "STREAM_ERROR", "message": str(e)},
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }
        yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"


@router.post("/api/assistant/stream")
async def assistant_stream_endpoint(
    request: AssistantRequest,
    x_api_key: str = Header(...),
    authorization: Optional[str] = Header(None),
):
    """SSE streaming endpoint for real-time assistant responses."""
    try:
        request_payload = model_to_dict(request)
        authenticated_user_context = _build_authenticated_user_context(
            request_context=request.context,
            x_api_key=x_api_key,
            authorization=authorization,
        )
        request_payload["context"]["authenticated_user_context"] = authenticated_user_context
        request_payload["context"]["user_context"] = authenticated_user_context

        return StreamingResponse(
            _stream_assistant_response(request_payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        error_payload = {
            "version": "3.0.0",
            "status": "error",
            "error": {"code": "STREAM_ERROR", "message": str(e)},
            "processed_at": datetime.utcnow().isoformat() + "Z",
        }
        return StreamingResponse(
            iter([f"event: error\ndata: {json.dumps(error_payload)}\n\n"]),
            media_type="text/event-stream",
        )
