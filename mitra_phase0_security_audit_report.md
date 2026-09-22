# 🛡️ MITRA Enterprise Intelligence Ecosystem
## Phase 0: Comprehensive Security Audit & Architectural Report

**Target Workspace**: `c:\Users\Microsoft\Desktop\MITRA-INTEGRATED`  
**Git Branch**: `feature/mitra-production-foundation`  
**Audit Date**: September 3, 2026  
**Status**: Audit Complete — Implementation Pending (Phase 0 Baseline)

---

## 1. Executive Summary

A comprehensive, evidence-driven Phase 0 technical audit of the **MITRA Enterprise Intelligence** codebase was conducted across backend API routers, security middleware, JWT authentication mechanisms, database models, OAuth handlers, tool executors, capability registries, and React frontend components.

The audit identified significant architectural strengths—including a resilient multi-provider LLM bridge, dynamic capability routing, and index-level financial search disambiguation. However, it also revealed **critical security vulnerabilities**, including fallback JWT secrets, unauthenticated integration routes, widespread IDOR through client-supplied user identifiers, plaintext credential persistence, hardcoded OTP bypasses, and incomplete OAuth endpoints.

This report establishes the baseline architecture, details all critical vulnerabilities with exact line-number evidence, identifies system components to preserve, maps all target files needing modification, and presents a 5-phase engineering roadmap to achieve enterprise production readiness.

---

## 2. Current Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          React + TypeScript Frontend                        │
│                (companion.store.ts, IntegrationsModal.tsx)                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST & WebCal (.ics)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend Server                           │
│                            (app/main.py - Port 8000)                        │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ Global Security Middleware           │ Public Prefix Bypass List            │
│ (Rate Limiting, Audit Log)           │ (/api/auth, /api/integrations, etc.) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│     Auth & Integr.    │  │   Companion Engine    │  │  Tantra & Governance  │
│   (app/api/auth.py,   │  │(companion_orchestrator│  │ (app/tantra/api.py,   │
│    integrations.py)   │  │     llm_bridge.py)    │  │    ecosystem.py)      │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│ Dynamic Capabilities  │  │  Action Executors     │  │ Finance & Search      │
│  (app/capabilities/)  │  │ (whatsapp, email, etc)│  │ (app/tools/search.py) │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────────────────┘
            │                          │
            └──────────────────────────┴──────────────────────────┐
                                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Persistence Layer                              │
│  - MongoDB (ai_assistant): user_integrations, otp_codes                     │
│  - SQLite (assistant_core.db): Users, Tasks, Reminders                      │
│  - In-Memory Fallbacks: _OTP_CACHE, _presence, _notifications               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architectural Components
1. **Backend Application (`app/main.py`)**: FastAPI web server mounting modular APIRouters (`auth_router`, `integrations_router`, `companion_router`, `mitra_router`, `workflow_router`, `notifications_router`, `presence_router`).
2. **Intelligence Core (`app/core/llm_bridge.py`)**: Multi-model LLM cascade supporting UniGuru as primary provider with automated fallback to Groq (`openai/gpt-oss-120b`) and Google Gemini.
3. **Companion Orchestrator (`app/companion/companion_orchestrator.py`)**: Intent classification engine parsing user prompts into structured capability invocations.
4. **Action Executors (`app/executors/`)**: Modular execution handlers for external services (`whatsapp_executor.py`, `email_executor.py`, `calendar_executor.py`, `telegram_executor.py`).
5. **Persistence Systems**:
   * **MongoDB**: Stores integration tokens (`user_integrations`) and verification codes (`otp_codes`).
   * **SQLite**: Manages user accounts and scheduled tasks via SQLAlchemy.
   * **In-Memory Fallbacks**: Dictionary caches (`_OTP_CACHE`, `_presence`, `_notifications`) for fallback operation when database instances are disconnected.

---

## 3. In-Depth Security Vulnerabilities Audit

### 3.1 Fallback JWT Secrets & Weak Default Cryptography
* **Files**: 
  * `backend/app/core/security.py` (Line 15)
  * `backend/app/services/jwt_service.py` (Line 25)
* **Evidence**:
  ```python
  # app/core/security.py:15
  JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET") or "your-secret-key"

  # app/services/jwt_service.py:25
  JWT_SECRET = os.getenv("JWT_SECRET", "mitra_default_dev_secret_change_in_production")
  ```
* **Risk**: High / Critical. If `JWT_SECRET_KEY` is not defined in environment configurations, both authentication modules fall back to hardcoded string constants. An attacker can use these public strings to forge valid administrative and user JWT tokens.

---

### 3.2 Unauthenticated Integration & Service Endpoints
* **File**: `backend/app/main.py` (Lines 263-265, 276-277)
* **Evidence**:
  ```python
  public_prefixes = ("/api/auth", "/api/integrations", "/api/companion", "/api/ecosystem", "/api/replay", "/api/metrics", "/api/tantra")
  if any(request.url.path.startswith(prefix) for prefix in public_prefixes):
      response = await call_next(request)
      return response
  ```
* **Risk**: Critical. Global security middleware explicitly excludes `/api/integrations` and `/api/companion` from API key and JWT token checks, allowing unauthenticated public traffic to hit integration management endpoints.

---

### 3.3 IDOR (Insecure Direct Object Reference) via Client-Supplied User Identifiers
* **Files**: 
  * `backend/app/api/integrations.py` (Lines 43, 73, 81, 105, 118, 146, 158)
  * `backend/app/api/notifications_api.py` (Lines 27, 55, 86)
  * `backend/app/api/presence_api.py` (Lines 48, 61)
  * `backend/app/api/mitra_api.py` (Lines 40, 84, 98)
* **Evidence**:
  ```python
  # app/api/integrations.py:43
  @router.get("/api/integrations")
  async def get_integrations(user_id: str = Query(..., description="User ID")):

  # app/api/integrations.py:81
  db["user_integrations"].update_one({"user_id": req.user_id}, ...)
  ```
* **Risk**: Critical. API endpoints take `user_id` directly from query strings or JSON bodies without verifying that the requesting client owns that ID. Any user (or anonymous caller) can read, modify, overwrite, or delete integration records, notification feeds, or presence states belonging to any other user.

---

### 3.4 Plaintext Storage of Sensitive User Credentials
* **File**: `backend/app/api/integrations.py` (Lines 73-95)
* **Evidence**:
  ```python
  db["user_integrations"].update_one(
      {"user_id": req.user_id},
      {
          "$set": {
              "gmail": {
                  "email": req.email,
                  "app_password": req.app_password,
                  "connected": True,
                  "updated_at": datetime.utcnow().isoformat()
              }
          }
      },
      upsert=True
  )
  ```
* **Risk**: High. User Gmail credentials (`app_password`) are stored in plaintext inside the MongoDB `user_integrations` collection without encryption. Database leaks or unauthorized database reads immediately compromise user email accounts.

---

### 3.5 Hardcoded OTP Bypasses & Information Leaks
* **File**: `backend/app/api/integrations.py` (Lines 142, 153)
* **Evidence**:
  ```python
  # Hardcoded Bypass in verify_whatsapp_otp (Line 153)
  if code == "123456" or _OTP_CACHE.get(cache_key) == code or _OTP_CACHE.get(req.user_id) == code:
      valid = True

  # Cleartext OTP Payload Leak in send_whatsapp_otp (Line 142)
  return {
      "status": "success",
      "message": f"OTP sent to {phone}. (Sandbox Demo Code: {otp})",
      "demo_otp": otp
  }
  ```
* **Risk**: High / Critical. Any client can pass `"123456"` to bypass WhatsApp OTP verification for any phone number. Additionally, the OTP generation endpoint returns the valid OTP directly in the HTTP JSON response payload.

---

### 3.6 Incomplete & Missing OAuth Infrastructure
* **Files**: 
  * `frontend/frontend/src/components/modals/IntegrationsModal.tsx` (Lines 58-65)
  * `backend/app/api/auth.py`
* **Evidence**:
  ```typescript
  // IntegrationsModal.tsx:58
  const res = await fetch(`${API_BASE}/api/auth/google`);
  if (res.ok) {
    const data = await res.json();
    if (data.auth_url) { window.location.href = data.auth_url; return; }
  }
  ```
* **Risk**: High. The frontend expects a Google OAuth initiation endpoint (`GET /api/auth/google`), but the backend router (`app/api/auth.py`) does not implement this route or its callback handler (`/api/auth/google/callback`). No OAuth state validation or refresh token rotation exists.

---

### 3.7 Production Simulation & Fake Success Fallbacks
* **File**: `frontend/frontend/src/components/modals/IntegrationsModal.tsx` (Lines 129-131)
* **Evidence**:
  ```typescript
  // Fallback demo mode if backend server is unreachable
  setShowOtpModal(true);
  setStatusMessage(`Verification code dispatched to ${whatsappNumber}`);
  ```
* **Risk**: Medium / High. When backend requests fail or failover occurs, frontend modals silently proceed to show mock success states, leading users to believe an integration is active when no backend state exists.

---

### 3.8 Global Integration Token Dependencies
* **Files**: `backend/app/executors/whatsapp_executor.py`, `email_executor.py`
* **Risk**: Medium. Actions execute using system-wide default environment credentials (e.g. global Twilio tokens) rather than verifying per-user OAuth tokens or scoped user credentials.

---

### 3.9 Duplicated & Mismatched Authentication / API Logic
* **Competing JWT Modules**: `app/core/security.py` (PyJWT) and `app/services/jwt_service.py` (custom HMAC implementation) contain competing JWT verification logic.
* **Mismatched Endpoint Slugs**: Frontend `IntegrationsModal.tsx` calls `POST /api/integrations/whatsapp/verify`, whereas backend `integrations.py` exposes `POST /api/integrations/whatsapp/verify-otp`.

---

## 4. Preserved System Components

The following modules demonstrate high stability and will be preserved during remediation:

1. **LLM Cascade Bridge (`backend/app/core/llm_bridge.py`)**: Sub-400ms provider fallback engine prioritizing UniGuru, Groq (`openai/gpt-oss-120b`), and Gemini.
2. **Companion Orchestrator (`backend/app/companion/companion_orchestrator.py`)**: Intent classification pipeline and tool execution dispatcher.
3. **Financial & Search Tools (`backend/app/tools/search_tool.py`)**: Market index benchmark disambiguation (`^NSEI`, `^BSESN`) and structured weather lookup.
4. **Capability Registry (`backend/app/capabilities/`)**: Core registry interface for dynamic capability loading.
5. **WebCal Feed Generator**: Core iCalendar (.ics) stream generation logic.

---

## 5. Target Files Requiring Remediation

| Target File | Current Issues | Required Remediation Action |
| :--- | :--- | :--- |
| `backend/app/core/security.py` | Hardcoded `"your-secret-key"` fallback. | Enforce strict environment `JWT_SECRET_KEY` check (fail startup if missing in prod). Implement unified `get_current_user` dependency. |
| `backend/app/services/jwt_service.py` | Custom HMAC implementation competing with `security.py`. | Deprecate duplicate custom HMAC logic; delegate token operations to `security.py`. |
| `backend/app/main.py` | Integrations & companion paths excluded from security middleware. | Remove `/api/integrations` and `/api/companion` from public unauthenticated bypass lists. |
| `backend/app/api/integrations.py` | IDOR on all routes, plaintext Gmail password storage, hardcoded `"123456"` OTP bypass, cleartext OTP responses. | Add `Depends(_current_user)`, extract `user_id` from JWT context, encrypt passwords using Fernet/AES-256, remove OTP bypass and cleartext response fields. |
| `backend/app/api/auth.py` | Missing Google OAuth endpoints. | Add `/api/auth/google` and `/api/auth/google/callback` routers for PKCE/OAuth2 code exchange. |
| `backend/app/api/companion_api.py`, `mitra_api.py`, `notifications_api.py`, `presence_api.py`, `workflow_api.py` | Query/body parameter `user_id` acceptance. | Derive `user_id` strictly from JWT claims in `_current_user`. |
| `frontend/.../IntegrationsModal.tsx` | Mismatched verification URL, mock success fallbacks, unauthenticated requests. | Fix endpoint URL (`/verify-otp`), attach `Authorization: Bearer <token>` header, remove fake fallback success paths. |
| `frontend/.../companion.service.ts` | Passing `user_id` in URL parameters. | Configure central HTTP client to inject Bearer token headers into all requests. |

---

## 6. Recommended Implementation Order (Phased Roadmap)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Security Core & Authentication Hardening                          │
│ - Enforce strict JWT_SECRET_KEY check at startup.                           │
│ - Unify JWT verification in app/core/security.py.                            │
│ - Remove /api/integrations from public middleware bypass in app/main.py.    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Endpoint IDOR Elimination & Token Claim Extraction                 │
│ - Protect all integration, companion, and task endpoints with JWT auth.    │
│ - Extract user_id strictly from validated JWT claims.                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Credential Encryption & OTP Hardening                              │
│ - Add Fernet AES-256 symmetric encryption for stored credentials in MongoDB. │
│ - Strip "123456" OTP bypass and cleartext demo_otp response payloads.        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: OAuth Infrastructure Implementation                                │
│ - Implement /api/auth/google and /api/auth/google/callback endpoints.       │
│ - Securely store and refresh OAuth tokens per user in MongoDB.              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Frontend Alignment & Integration Verification                      │
│ - Globalize Authorization Bearer header injection in companion.service.ts.   │
│ - Align URL paths in IntegrationsModal.tsx and strip fake success fallbacks. │
└─────────────────────────────────────────────────────────────────────────────┘
```

---
*Report generated for branch `feature/mitra-production-foundation`. Baseline audit phase complete. No code changes executed during Phase 0.*
