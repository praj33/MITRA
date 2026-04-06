# Integration Disclosure Report

Date: 2026-04-06

Update:
- The recommended merge has now been implemented.
- Current deployment guidance is in `MERGED_DEPLOYMENT_GUIDE.md`.

## Executive Summary

- The current workspace contains **three deployable runtimes**, not two:
  - `backend/` -> FastAPI assistant backend
  - `frontend/frontend/` -> React + TypeScript web app
  - `frontend/Signup/` -> Express + MongoDB auth microservice
- The React app already talks to the FastAPI backend for chat.
- The auth microservice is **not truly integrated** with the FastAPI assistant runtime yet.
- The backend is the strongest part of the system today and passed targeted in-process tests.
- The frontend is close to Vercel-ready, but environment setup and auth deployment strategy need cleanup first.
- If the goal is **Backend on Render + Frontend on Vercel**, the best path is to **merge the auth microservice into the FastAPI backend** so the system becomes a true two-service architecture.

## What Exists Today

### 1. Backend (`backend/`)

Technology:
- FastAPI
- MongoDB via `motor`
- API-key protected public endpoints
- Multi-channel execution and webhook handling

Primary public contract:
- `POST /api/assistant`
- `POST /api/mitra/evaluate`
- `GET /health`

Important behavior:
- The backend is intentionally designed around a **single assistant entrypoint**.
- It includes safety, enforcement, orchestration, multilingual support, TTS, webhooks, reminders, and external action executors.
- It already has a Render blueprint: `backend/render.yaml`.

Validation performed:
- `tests/test_mitra_api.py` -> `6 passed`
- `tests/test_generic_response_runtime.py` + `tests/test_mitra_control_plane_integration.py` -> `17 passed`

Notes:
- Tests required `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` because a global pytest plugin on the machine interfered with collection.
- The checked-in `backend/venv/` is stale and points to a missing Python path, so it should not be treated as portable.

### 2. Frontend UI (`frontend/frontend/`)

Technology:
- Create React App
- TypeScript
- Tailwind CSS

Current user flow:
- User hits login/signup gate first
- On successful login, user can access the chat UI
- Chat messages are sent to `POST /api/assistant`
- Chat history is stored in browser `localStorage`

Current deployment config:
- `frontend/frontend/vercel.json`
- Static build output: `build/`

Notes:
- The core chat path is wired to the backend correctly.
- There are extra API methods and UI panels for search, research, system info, task APIs, and analytics, but many of these are not part of the backend's locked public contract.
- Those extra panels appear to be partially aspirational / future-facing rather than fully integrated.

### 3. Auth Microservice (`frontend/Signup/`)

Technology:
- Express
- Mongoose
- JWT auth
- MongoDB Atlas / in-memory fallback for local dev

Current auth surface:
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Notes:
- This service currently stands alone.
- It has hardcoded CORS origins for old deployment URLs.
- It has no Render blueprint or production deployment file in the repo.

## Deep Integration Findings

### 1. This is not yet a true two-service system

At the moment:
- Frontend UI is one app
- Assistant backend is one app
- Auth is a separate third app

If you deploy only:
- backend on Render
- frontend on Vercel

then the auth service still needs its own host unless it is merged into the backend.

### 2. Auth is only enforcing UI access, not assistant identity

The login system currently protects the React UI, but user identity does **not** flow cleanly into assistant requests.

Why:
- The frontend auth client stores a JWT locally and uses it only for auth-service calls.
- The assistant API client sends `X-API-Key` but does **not** forward the bearer token.
- The FastAPI backend can optionally inspect an `Authorization` header, but the JWT format it expects does not match what the Express auth service issues.

Result:
- A user can be "logged in" to the UI while the assistant backend still effectively sees requests as generic API-key traffic.

### 3. JWT contracts are mismatched

Current mismatch:
- Express auth signs tokens with `{ id: userId }`
- FastAPI auth verification expects a `sub` claim
- Express auth uses `JWT_SECRET`
- FastAPI uses `JWT_SECRET_KEY`

Even if the frontend forwarded the token today, the backend would not interpret it as intended without alignment.

### 4. Environment file layout is currently misleading

Observed layout:
- `backend/.env` exists
- `frontend/.env` exists
- There is **no** `.env` inside `frontend/frontend/`
- There is **no** `.env` inside `frontend/Signup/`

Implication:
- The React app and Express auth service may not load the intended environment variables when started from their own directories.
- The frontend README expects `.env` inside `frontend/frontend/`, but that file is absent.

### 5. Frontend expects more API surface than the locked backend exposes

The backend docs say the frontend-safe public contract is centered on `/api/assistant`.

The frontend service layer still contains methods for:
- `/api/tasks`
- `/api/system/info`
- `/api/system/stats`
- search/research helpers

This is not fatal today because the core chat path is the main active path, but it creates drift and confusion.

### 6. CORS and deployment URLs need normalization

Current state:
- FastAPI globally allows all origins in middleware
- The assistant `OPTIONS` handler also contains extra explicit origin logic and old Render domain assumptions
- Express auth has hardcoded localhost + old Render/Vercel domains

This should be normalized before production so deployed origins are explicit and easy to manage.

### 7. Deployment docs are partially stale / inconsistent

Examples:
- Some backend docs mention env names that differ from the active runtime config
- `render.yaml` is the most trustworthy deployment source for the backend right now
- The auth service has no equivalent production blueprint

## What Should Be Done After Integration

## Recommended Target Architecture

### Option A (Recommended): Merge auth into the FastAPI backend

Target:
- `backend/` on Render
- `frontend/frontend/` on Vercel

What changes:
- Recreate or port `frontend/Signup` auth routes into the FastAPI backend
- Store users in the same MongoDB cluster used by the backend
- Standardize one JWT contract for the whole system
- Forward `Authorization: Bearer ...` from the frontend to the backend
- Let the backend inject authenticated user identity into assistant context
- Remove the need to deploy the standalone Express auth service

Why this is best:
- Reduces production from 3 services to 2
- Simplifies CORS
- Simplifies env management
- Makes user identity available to the assistant pipeline
- Matches your requested deployment model

### Option B: Keep auth as a separate microservice

Target:
- `backend/` on Render
- `frontend/Signup/` on Render
- `frontend/frontend/` on Vercel

Required extra work:
- Deploy and maintain a second Render service
- Align JWT format and secrets between Express and FastAPI
- Forward bearer token from frontend chat requests to backend
- Maintain CORS for two backend origins instead of one

This works, but it is more operationally complex.

## Recommended Integration Work Plan

### Phase 1. Normalize architecture
- Decide whether auth is merged into FastAPI or kept separate
- Recommended: merge auth into FastAPI

### Phase 2. Fix identity flow
- Standardize JWT payload format
- Standardize secret naming
- Forward bearer token from frontend assistant requests
- Attach authenticated user identity to backend request context

### Phase 3. Clean frontend contract
- Keep `sendMessage()` as the primary production path
- Remove, hide, or clearly mark unsupported APIs/panels
- Optionally keep future panels behind feature flags

### Phase 4. Fix environment management
- Move frontend env to `frontend/frontend/.env` for local use
- If auth remains separate, give `frontend/Signup/` its own `.env`
- Keep production secrets only in Render/Vercel dashboards

### Phase 5. Production hardening
- Replace hardcoded origins with env-driven origin config
- Add deployment docs specifically for the final chosen architecture
- Add one end-to-end test path covering login -> chat -> assistant response

## Deployment Plan

### Backend on Render

Use:
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Minimum environment variables:
- `API_KEY`
- `MONGODB_URI`
- `DATABASE_NAME`
- `FRONTEND_URL`

Optional feature variables:
- email credentials
- Twilio / WhatsApp credentials
- Telegram bot token
- calendar integrations
- TTS / model provider keys

### Frontend on Vercel

Use:
- Root directory: `frontend/frontend`
- Build command: `npm run build`
- Output directory: `build`

Minimum environment variables:
- `REACT_APP_API_URL`
- `REACT_APP_API_KEY`

If auth remains separate:
- `REACT_APP_AUTH_API_URL`

### Auth service on Render (only if not merged)

Would need:
- Root directory: `frontend/Signup`
- Build command: `npm install`
- Start command: `npm start`

Required environment variables:
- `MONGO_URI`
- `JWT_SECRET`
- `PORT`
- production CORS origins

## Final Assessment

### Ready now
- Backend core assistant and Mitra evaluation runtime
- Backend Render blueprint
- Frontend Vercel static deployment config
- Frontend core chat -> backend integration

### Not fully integrated yet
- Auth identity propagation into assistant runtime
- Two-service deployment alignment
- Environment file organization
- Removal or alignment of unsupported frontend API surface
- Production CORS cleanup

## Recommendation

Proceed with this order:

1. Merge `frontend/Signup` auth into `backend/`
2. Update the React app to use backend auth routes and forward bearer token
3. Clean env placement and deployment config
4. Deploy backend to Render
5. Deploy frontend to Vercel
6. Run end-to-end validation on production URLs

This gives you the cleanest and most maintainable architecture for the deployment model you asked for.
