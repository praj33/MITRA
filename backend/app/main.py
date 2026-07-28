import sys
import os
from datetime import datetime
from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

# -------------------------------------------------
# Path setup
# -------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()  # Load from current directory

# -------------------------------------------------
# Optional Sentry
# -------------------------------------------------
if os.getenv("SENTRY_DSN"):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENV", "production"),
    )

# -------------------------------------------------
# Local imports
# -------------------------------------------------
from app.core.logging import setup_logging, get_logger
from app.core.database import create_tables
from app.core.security import rate_limit, audit_log
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.mitra_api import router as mitra_router
from app.api.webhooks import router as webhook_router
from app.api.tts import router as tts_router
from app.api.companion_api import router as companion_router
from app.api.workflow_api import router as workflow_router
from app.api.presence_api import router as presence_router
from app.api.notifications_api import router as notifications_router
from app.executors.telegram_executor import TelegramExecutor
from app.services.reminder_scheduler import ReminderScheduler, SchedulerConfig
from app.mitra_system_health import get_system_health_snapshot

# -------------------------------------------------
# Ecosystem routers (from integrated repos)
# -------------------------------------------------
try:
    from app.routers.voice_stt import router as voice_stt_router
    from app.routers.voice_tts import router as voice_tts_router
    _voice_routers = True
except ImportError:
    _voice_routers = False

try:
    from app.routers.bhiv import router as bhiv_router
    _bhiv_router = True
except ImportError:
    _bhiv_router = False

try:
    from app.routers.embed import router as embed_router
    _embed_router = True
except ImportError:
    _embed_router = False

try:
    from app.routers.rl_action import router as rl_router
    _rl_router = True
except ImportError:
    _rl_router = False

try:
    from app.routers.external_app import router as external_app_router
    _ext_app_router = True
except ImportError:
    _ext_app_router = False

try:
    from app.routers.external_llm import router as external_llm_router
    _ext_llm_router = True
except ImportError:
    _ext_llm_router = False

try:
    from app.routers.telephony_inbound import router as telephony_router
    _telephony_router = True
except ImportError:
    _telephony_router = False

try:
    from app.routers.whatsapp_inbound import router as whatsapp_inbound_router
    _whatsapp_router = True
except ImportError:
    _whatsapp_router = False

try:
    from app.routers.email_inbound import router as email_inbound_router
    _email_router = True
except ImportError:
    _email_router = False

try:
    from app.routers.pages import router as pages_router
    _pages_router = True
except ImportError:
    _pages_router = False

# -------------------------------------------------
# Logging
# -------------------------------------------------
setup_logging()
logger = get_logger(__name__)


def _telegram_webhook_url() -> str | None:
    explicit = (os.getenv("TELEGRAM_WEBHOOK_URL") or "").strip()
    if explicit:
        return explicit

    public_base = (
        os.getenv("RENDER_EXTERNAL_URL")
        or os.getenv("BASE_URL")
        or os.getenv("PUBLIC_BASE_URL")
        or ""
    ).strip()
    if not public_base or "localhost" in public_base or "127.0.0.1" in public_base:
        return None
    return f"{public_base.rstrip('/')}/webhook/telegram"


def _register_telegram_webhook() -> None:
    webhook_url = _telegram_webhook_url()
    if not webhook_url:
        logger.info("Telegram webhook registration skipped: no public webhook URL configured")
        return

    executor = TelegramExecutor()
    if not executor.bot_token:
        logger.info("Telegram webhook registration skipped: TELEGRAM_BOT_TOKEN not configured")
        return

    result = executor.set_webhook(webhook_url)
    if result.get("status") == "success":
        logger.info("Telegram webhook registered: %s", webhook_url)
    else:
        logger.warning("Telegram webhook registration failed: %s", result)


# -------------------------------------------------
# App lifespan
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = None
    scheduler = None
    # Initialize database tables
    try:
        await create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        # Don't fail startup if database is read-only - app can still run
        # but database features won't work
        logger.warning("Continuing startup without database initialization")

    # Register all companion capabilities
    try:
        from app.capabilities import register_all_capabilities
        register_all_capabilities()
        logger.info("Companion capabilities registered")
    except Exception as e:
        logger.warning(f"Capability registration failed (non-fatal): {e}")

    # Initialize Companion Runtime (Universal Runtime layer)
    try:
        from app.runtime.config import RuntimeSettings
        from app.runtime.companion_runtime import CompanionRuntime
        settings = RuntimeSettings.from_environment()
        runtime = CompanionRuntime(settings)
        runtime.start()
        app.state.companion_runtime = runtime
        logger.info("Companion Runtime started (Phase V Universal Layer)")
    except Exception as e:
        logger.warning(f"Companion Runtime init failed (non-fatal): {e}")
        app.state.companion_runtime = None

    # Initialize voice session manager (if available)
    try:
        from app.voice.voice_session_manager import get_voice_session_manager
        vsm = get_voice_session_manager()
        await vsm.start()
        logger.info("Voice session manager started")
    except Exception as e:
        logger.debug(f"Voice session manager not started (optional): {e}")

    # Initialize voice trace logger (if available)
    try:
        from app.voice.voice_trace import get_voice_trace_logger
        vtl = get_voice_trace_logger()
        await vtl.connect()
        logger.info("Voice trace logger connected")
    except Exception as e:
        logger.debug(f"Voice trace logger not connected (optional): {e}")

    # Optional: start reminder scheduler worker
    if os.getenv("REMINDER_SCHEDULER_ENABLED", "0").lower() in {"1", "true", "yes"}:
        try:
            scheduler = ReminderScheduler(
                SchedulerConfig(
                    poll_interval_seconds=float(os.getenv("REMINDER_SCHEDULER_POLL_SECONDS", "1.0")),
                    max_batch=int(os.getenv("REMINDER_SCHEDULER_MAX_BATCH", "25")),
                )
            )
            scheduler_task = asyncio.create_task(scheduler.start())
            logger.info("Reminder scheduler started")
        except Exception as e:
            logger.error(f"Failed to start reminder scheduler: {e}")

    try:
        _register_telegram_webhook()
    except Exception as e:
        logger.warning(f"Telegram webhook setup failed: {e}")

    yield

    # Shutdown voice session manager
    try:
        from app.voice.voice_session_manager import get_voice_session_manager
        vsm = get_voice_session_manager()
        await vsm.stop()
    except Exception:
        pass

    # Shutdown reminder scheduler
    if scheduler:
        try:
            scheduler.stop()
        except Exception:
            pass
    if scheduler_task:
        scheduler_task.cancel()

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="Mitra — Universal AI Companion",
    description=(
        "Mitra v4 Companion Backend — Persistent AI companion with capability hub, "
        "UniGuru knowledge engine (embedded), voice/telephony duplex audio, "
        "agent system, multi-step workflow orchestration, and full governance layer."
    ),
    version="5.0.0",
    lifespan=lifespan,
)

# -------------------------------------------------
# CORS - Allow all origins (frontend is a separate project)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# -------------------------------------------------
# Security Middleware
# -------------------------------------------------
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Allow health check and root without auth
    if request.url.path in ["/health", "/", "/health/system", "/docs", "/openapi.json", "/redoc"]:
        response = await call_next(request)
        return response

    # Auth endpoints manage their own bearer-token validation
    if request.url.path.startswith("/api/auth"):
        response = await call_next(request)
        return response

    # Allow webhook routes and page data routes without API key
    if request.url.path.startswith("/api/webhooks") or request.url.path.startswith("/webhook") or request.url.path.startswith("/api/pages"):
        response = await call_next(request)
        return response

    # Allow OPTIONS requests (CORS preflight) without auth
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    if request.url.path.startswith("/api"):
        from fastapi import HTTPException
        try:
            rate_limit(request)
        except HTTPException as e:
            if e.status_code == 429:
                return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}. Allowing request.")

        api_key = request.headers.get("X-API-Key")
        expected_api_key = os.getenv("API_KEY")

        # Whitelist frontend-facing routes (no API key required)
        whitelisted_prefixes = ("/api/companion", "/api/pages", "/api/workflow", "/api/v1", "/health")
        is_whitelisted = any(request.url.path.startswith(p) for p in whitelisted_prefixes)

        # Check API key (handle None cases gracefully)
        if not is_whitelisted:
            if not expected_api_key:
                logger.error("API_KEY environment variable is not set! Authentication will fail.")
            if not api_key or api_key != expected_api_key:
                # Get origin from request for CORS headers
                origin = request.headers.get("origin", "")
                cors_origin = origin if origin else "*"

                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication failed"},
                    headers={
                        "Access-Control-Allow-Origin": cors_origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                    }
                )

        try:
            audit_log(request, "api_key_user")
        except Exception as e:
            logger.warning(f"Audit logging failed: {e}. Continuing with request.")

    response = await call_next(request)
    return response

# -------------------------------------------------
# Core Routers
# -------------------------------------------------
app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(mitra_router)
app.include_router(webhook_router)
app.include_router(tts_router)
# Companion v4
app.include_router(companion_router)
app.include_router(workflow_router)
# Canonical MITRA APIs (Phase 1)
app.include_router(presence_router)
app.include_router(notifications_router)
logger.info("Canonical APIs registered: presence, notifications")

# -------------------------------------------------
# Ecosystem Routers (integrated from team repos)
# -------------------------------------------------
if _voice_routers:
    app.include_router(voice_stt_router, prefix="/api", tags=["Voice STT"])
    app.include_router(voice_tts_router, prefix="/api", tags=["Voice TTS"])
    logger.info("Voice STT/TTS routers registered")

if _bhiv_router:
    app.include_router(bhiv_router, prefix="/api", tags=["BHIV Core"])
    logger.info("BHIV router registered")

if _embed_router:
    app.include_router(embed_router, prefix="/api", tags=["Embeddings"])
    logger.info("Embed router registered")

if _rl_router:
    app.include_router(rl_router, prefix="/api", tags=["RL Actions"])
    logger.info("RL Action router registered")

if _ext_app_router:
    app.include_router(external_app_router, prefix="/api", tags=["External Apps"])
    logger.info("External App router registered")

if _ext_llm_router:
    app.include_router(external_llm_router, prefix="/api", tags=["External LLM"])
    logger.info("External LLM router registered")

if _telephony_router:
    app.include_router(telephony_router, tags=["Telephony Inbound"])
    logger.info("Telephony inbound router registered")

if _whatsapp_router:
    app.include_router(whatsapp_inbound_router, tags=["WhatsApp Inbound"])
    logger.info("WhatsApp inbound router registered")

if _email_router:
    app.include_router(email_inbound_router, tags=["Email Inbound"])
    logger.info("Email inbound router registered")

# -------------------------------------------------
if _pages_router:
    app.include_router(pages_router, tags=["Page Data"])
    logger.info("Pages data router registered")

# -------------------------------------------------
# System Endpoints
# -------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Mitra — Universal AI Companion v5.0.0",
        "status": "running",
        "role": "Canonical Companion Layer — BHIV Ecosystem",
        "modules": {
            "companion": True,
            "companion_runtime": getattr(app.state, 'companion_runtime', None) is not None,
            "voice_duplex": _voice_routers,
            "bhiv_governance": _bhiv_router,
            "uniguru_backend": True,
            "agents": True,
            "tools": True,
        },
        "canonical_apis": {
            "auth_signup":         "/api/auth/signup",
            "auth_login":          "/api/auth/login",
            "companion_chat":      "/api/companion/chat",
            "companion_greeting":  "/api/companion/greeting/{user_id}",
            "companion_memory":    "/api/companion/memory/{user_id}",
            "companion_session":   "/api/companion/session/{user_id}",
            "companion_caps":      "/api/companion/capabilities",
            "notifications":       "/api/v1/notifications/{user_id}",
            "presence":            "/api/v1/presence/{user_id}",
            "presence_heartbeat":  "/api/v1/presence/heartbeat",
            "workflow_list":       "/api/workflow/list",
            "workflow_run":        "/api/workflow/run",
        },
        "runtime_apis": {
            "runtime_status":      "/api/v1/runtime/status",
            "sessions":            "/api/v1/sessions",
            "context":             "/api/v1/sessions/{id}/context",
            "attachments":         "/api/v1/attachments",
            "intents":             "/api/v1/intents",
            "dispatch":            "/api/v1/intents/dispatch",
            "capabilities":        "/api/v1/capabilities",
        },
        "integration": {
            "uniguru":  "https://uniguru-v2.onrender.com",
            "health":   "/health",
            "docs":     "/docs",
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "5.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/health/system")
async def system_health():
    """
    Deep system health endpoint.
    Reports module status, bucket status, and runtime version.
    """
    return get_system_health_snapshot()
