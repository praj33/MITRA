# MITRA Integration Guide

## For Downstream Teams

This guide explains how to integrate with MITRA's canonical companion APIs.

> **Rule:** Every downstream team must integrate against these contracts ONLY.
> No duplicate companion implementations.

---

## Authentication

All API calls require a JWT token obtained from `/api/auth/login`:

```bash
# Login and get JWT
curl -X POST https://mitra-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@bhiv.com", "password": "..."}'

# Response
{
  "user": { "id": "user_xxx", "name": "Raj", "email": "user@bhiv.com" },
  "token": "eyJhbGci..."
}
```

Use the token in subsequent requests:
```bash
Authorization: Bearer eyJhbGci...
```

---

## Core APIs

### Chat with Companion
```bash
POST /api/companion/chat
{
  "user_id": "user_xxx",
  "message": "Create a task to review PRs",
  "platform": "web"  # or "gurukul", "samruddhi", "setu"
}

# Response
{
  "message": "Done — Task processed: ...",
  "capability_result": { "capability": "task", "status": "success", ... },
  "session_id": "sess_abc123",
  "intent": "task"
}
```

### Session Management
```bash
# Create session
POST /api/v1/sessions
{
  "actor_id": "user_xxx",
  "client_type": "web",
  "workspace_id": "default",
  "product_id": "gurukul",
  "schema_version": "1.0.0",
  "contract_version": "1.0.0",
  "runtime_version": "1.0.0",
  "compatibility_version": "1.0.0"
}

# Resume session (cross-app)
POST /api/v1/sessions/{session_id}/resume
{ "resume_token": "..." }

# Transfer context to new product
POST /api/v1/sessions/{session_id}/transfer
{
  "target_workspace_id": "default",
  "target_product_id": "samruddhi",
  "portable_context": { "conversation_summary": "..." }
}
```

### Notifications
```bash
# Push notification to user
POST /api/v1/notifications/
{
  "user_id": "user_xxx",
  "title": "Task completed",
  "body": "Your PR review task is done",
  "type": "success",
  "product_id": "gurukul"
}

# Get user notifications
GET /api/v1/notifications/{user_id}?unread_only=true
```

### Presence
```bash
# Send heartbeat (every 30s)
POST /api/v1/presence/heartbeat?product_id=gurukul

# Check user status
GET /api/v1/presence/{user_id}
# Response: { "status": "online" | "away" | "offline" }
```

---

## Integration Block Contracts

### For Ashmit (TANTRA & BHIV Core)
- Set `TANTRA_RUNTIME_URL` env var on MITRA backend
- TANTRA must expose: `POST /execute` accepting `{ capability, intent, params, trace_id, user_id }`
- Bucket integration via `tantra_client.py`

### For Kanishk (Capability Runtime)
- Set `CAPABILITY_RUNTIME_URL` env var on MITRA backend
- Runtime must expose endpoints per `capability_runtime_interface.py`:
  - `POST /runtime/execute`
  - `GET /runtime/status/{run_id}`
  - `GET /runtime/capabilities`

### For Vijay (UniGuru)
- UniGuru v2 already integrated at `https://uniguru-v2.onrender.com`
- MITRA calls `POST /new_query` with `{ query: "..." }`
- UniGuru is now the PRIMARY intelligence engine

### For Ashwini (Hover Companion)
- Consume ONLY `/api/companion/chat` and `/api/v1/sessions`
- No frontend execution logic
- Use JWT from shared `JWT_SECRET`

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `JWT_SECRET` | Shared JWT signing secret | `mitra_default_dev_secret_change_in_production` |
| `MONGODB_URI` | MongoDB connection string | — |
| `UNIGURU_URL` | UniGuru v2 API | `https://uniguru-v2.onrender.com/new_query` |
| `TANTRA_RUNTIME_URL` | TANTRA runtime API | (empty — falls back to local) |
| `CAPABILITY_RUNTIME_URL` | Kanishk's runtime | `http://localhost:8100` |
| `COMPANION_LLM_PROVIDER` | Primary LLM | `uniguru` |
| `GROQ_API_KEY` | Groq fallback | — |
