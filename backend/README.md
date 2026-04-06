# AI Assistant Backend

Production backend for the AI Assistant.
This backend now serves both assistant APIs and merged auth APIs for frontend integration.

---

## Public API

POST /api/assistant  
POST /api/mitra/evaluate  
POST /api/auth/signup  
POST /api/auth/login  
GET /api/auth/me  
POST /api/auth/logout  
GET /health

`/api/assistant` remains the main assistant entrypoint.
`/api/mitra/evaluate` exposes Mitra's deterministic decision flow for structured event input.
`/api/auth/*` now provides merged user authentication for the web frontend.

---

## Authentication

Assistant and Mitra requests require:

X-API-Key: <api-key>

Auth routes manage their own bearer-token flow and do not require the assistant API key.

---

## API Contract

The assistant request and response schemas are strictly defined and versioned.

See: ASSISTANT_BACKEND_CONTRACT.md

---

## Architecture

The backend uses a single-entry orchestration model.
All intelligence, workflows, and integrations are internal.

See: ARCHITECTURE_OVERVIEW.md

---

## Health Check

GET /health

---

## Status

Backend integrated and ready for merged frontend auth + assistant usage.

## Optional TTS Runtime

The main backend deploy does not require Coqui XTTS.
Optional TTS dependencies are isolated from the base deployment so the core API can build reliably on Render.

To enable the XTTS stack on a dedicated environment, install:

`pip install -r requirements-tts.txt`
