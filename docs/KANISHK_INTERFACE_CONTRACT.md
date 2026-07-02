# Kanishk Interface Contract
## Mitra v4 — Capability Runtime API

**Owner:** Kanishk Singh (Platform / Runtime)  
**Consumer:** Raj Prajapati (Mitra Product Layer)  
**Version:** v1.0 | **Date:** July 2026

---

## Overview

Kanishk is building the **Capability Runtime** — a platform service that allows Mitra to safely discover, schedule, execute, monitor, recover, and report capability execution regardless of where the capability lives.

Mitra's product layer will **consume** this runtime through the 5 endpoints defined below.  
**We will not implement execution logic ourselves.**

---

## Base URL

```
CAPABILITY_RUNTIME_URL=http://<kanishk-runtime-host>:<port>
```

Set via environment variable. Default during development: `http://localhost:8100`

## Authentication

All requests include:
```
X-API-Key: <shared key>
```

---

## Contract: 5 Required Endpoints

### 1. Execute Capability

```
POST /runtime/execute
```

**Request:**
```json
{
  "capability": "email",
  "intent":     "draft_email",
  "params": {
    "to":      "john@example.com",
    "subject": "Meeting tomorrow",
    "body":    "Hi John, confirming our 3pm meeting.",
    "user_id": "user_abc123"
  },
  "user_id":   "user_abc123",
  "trace_id":  "mitra-trace-xyz789"
}
```

**Response:**
```json
{
  "run_id":      "run_abc123",
  "status":      "success",
  "result": {
    "summary":   "Email draft created.",
    "draft_id":  "draft_001",
    "preview":   "Hi John, confirming our 3pm..."
  },
  "error":       null,
  "executed_at": "2026-07-02T11:00:00Z"
}
```

**Status values:** `success` | `error` | `pending` (async execution)

---

### 2. Check Execution Status

```
GET /runtime/status/{run_id}
```

**Response:**
```json
{
  "run_id":      "run_abc123",
  "status":      "success",
  "result":      { ... },
  "error":       null,
  "retries":     0,
  "executed_at": "2026-07-02T11:00:00Z"
}
```

---

### 3. List Available Capabilities

```
GET /runtime/capabilities
```

**Response:**
```json
[
  {
    "name":               "email",
    "status":             "operational",
    "version":            "1.2.0",
    "supported_intents":  ["draft_email", "send_email", "read_emails"]
  },
  {
    "name":               "calendar",
    "status":             "operational",
    "version":            "1.0.0",
    "supported_intents":  ["create_event", "list_events", "check_availability"]
  }
]
```

**Status values:** `operational` | `degraded` | `unavailable`

---

### 4. Schedule Future Execution

```
POST /runtime/schedule
```

**Request:**
```json
{
  "capability":   "reminder",
  "intent":       "create_reminder",
  "params": {
    "message":    "Call mom",
    "remind_at":  "2026-07-02T17:00:00Z"
  },
  "user_id":      "user_abc123",
  "scheduled_at": "2026-07-02T17:00:00Z"
}
```

**Response:**
```json
{
  "schedule_id":  "sched_xyz001",
  "status":       "scheduled",
  "scheduled_at": "2026-07-02T17:00:00Z"
}
```

---

### 5. Cancel Scheduled Execution

```
DELETE /runtime/schedule/{schedule_id}
```

**Response:**
```json
{
  "schedule_id": "sched_xyz001",
  "status":      "cancelled"
}
```

---

## Error Response Format

All endpoints return errors in this format:
```json
{
  "status":  "error",
  "error":   "Human-readable error message",
  "code":    "CAPABILITY_UNAVAILABLE | EXECUTION_FAILED | TIMEOUT | NOT_FOUND"
}
```

---

## Mitra's Fallback Behavior

If the runtime is unavailable:
1. Mitra falls back to calling existing `ExecutionService` executors directly
2. Logs the fallback in the audit trail
3. The user sees the same response — the fallback is invisible

This ensures Mitra continues working while the runtime is being built.

---

## Implementation Timeline (Suggested)

| Milestone | Endpoint |
|-----------|---------|
| Week 1 | `/runtime/execute` + `/runtime/status/{run_id}` |
| Week 2 | `/runtime/capabilities` |
| Week 3 | `/runtime/schedule` + `/runtime/schedule/{id}` (DELETE) |

---

## Notes for Kanishk

- Mitra sends `trace_id` on every execution — please include it in logs for cross-system tracing
- The `result` object shape is capability-specific — Mitra reads: `result.summary`, `result.data`, `result.error`
- `pending` status is supported — Mitra will poll `/runtime/status/{run_id}` for async ops
- Auth is `X-API-Key` header — value set via `CAPABILITY_RUNTIME_API_KEY` env var on both sides
