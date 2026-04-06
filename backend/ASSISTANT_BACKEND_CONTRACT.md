# Assistant Backend API Contract

## Overview
This document defines the **locked, production-ready assistant contract** for the AI Assistant Backend.

The backend now also exposes merged auth routes for the web frontend, but this document covers the assistant entrypoint only:
POST /api/assistant

All assistant intelligence, workflows, and routing logic are internal and encapsulated.

---

## Endpoint

POST /api/assistant

**Authentication**
X-API-Key header is required.

**Content-Type**
application/json

---

## Request Schema (LOCKED)

```json
{
  "version": "3.0.0",
  "input": {
    "message": "string (optional)",
    "summarized_payload": {
      "summary": "string"
    }
  },
  "context": {
    "platform": "web | mobile | desktop",
    "device": "string",
    "session_id": "string (optional)",
    "voice_input": false
  }
}
