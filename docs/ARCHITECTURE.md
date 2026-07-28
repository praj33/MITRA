# MITRA — Architecture Document

## System Identity

**MITRA** is the **Canonical Companion Layer** for the BHIV ecosystem.

- MITRA **orchestrates** — it does not contain intelligence or execution logic.
- **UniGuru** provides the backend intelligence (LLM inference, knowledge).
- **TANTRA** provides the governed execution runtime.
- **Bucket** records truth (provenance, replay).
- **Kanishk's Capability Runtime** executes all capabilities.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Gurukul  │  │Samruddhi │  │   SETU   │  │ MITRA Standalone │    │
│  │ (Hover)  │  │ (Hover)  │  │ (Hover)  │  │   (Full App)     │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘    │
│       │              │              │                │               │
│       └──────────────┴──────────────┴────────────────┘               │
│                              │                                       │
│                    JWT Token (shared secret)                          │
└──────────────────────────────┼───────────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     MITRA COMPANION BACKEND                          │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                   Canonical API Layer                           │ │
│  │  /api/auth    /api/companion    /api/v1/sessions                │ │
│  │  /api/v1/notifications          /api/v1/presence                │ │
│  │  /api/v1/attachments            /api/v1/intents                 │ │
│  └─────────────────────────┬───────────────────────────────────────┘ │
│                            │                                         │
│  ┌─────────────────────────▼───────────────────────────────────────┐ │
│  │               Companion Orchestrator                            │ │
│  │  Intent Classification → Capability Routing → Safety Gate       │ │
│  │  Session Management → Memory → Personality Engine               │ │
│  └───────┬──────────────────┬──────────────────────┬───────────────┘ │
│          │                  │                      │                  │
│  ┌───────▼──────┐  ┌───────▼──────┐  ┌────────────▼──────────────┐  │
│  │ Companion    │  │   Context    │  │     Continuity Service    │  │
│  │   Runtime    │  │   Runtime    │  │   (Cross-App Sessions)    │  │
│  │ (Sessions)   │  │ (Scopes)    │  │                            │  │
│  └──────────────┘  └──────────────┘  └────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────────┐ ┌─────────────────┐ ┌──────────────────┐
│    UniGuru v2    │ │  TANTRA Runtime │ │      Bucket      │
│  (Intelligence)  │ │  (Execution)    │ │  (Truth Layer)   │
│                  │ │       │         │ │  Provenance      │
│  LLM inference   │ │       ▼         │ │  Replay          │
│  Knowledge       │ │  Capability     │ │  InsightFlow     │
│  Reasoning       │ │  Runtime        │ │                  │
│                  │ │  (Kanishk)      │ │                  │
└──────────────────┘ └─────────────────┘ └──────────────────┘
```

---

## Data Flow

### Chat Message Flow
```
User types message
    → Frontend POST /api/companion/chat
    → CompanionOrchestrator.process()
    → IntentFlow.classify_intent()
    → if capability: CapabilityRegistry.execute()
    → if knowledge: UniGuru v2 API
    → if conversation: LLM (UniGuru primary → Groq fallback)
    → Safety Gate evaluation
    → Personality Engine formatting
    → Session + Memory persistence
    → Response to frontend
```

### Cross-App Continuity Flow
```
User opens Gurukul
    → Hover Companion loads with JWT
    → ContinuityService.resolve_session(user_id, "gurukul")
    → New session created, resume_token issued
    → User chats...

User opens Samruddhi
    → Hover Companion loads with same JWT
    → ContinuityService.resolve_session(user_id, "samruddhi")
    → Finds existing Gurukul session
    → SessionRuntime.transfer() carries context
    → Same conversation continues
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + TypeScript | Standalone app |
| Hover Companion | Vanilla JS widget | Embeddable in any product |
| Backend | Python + FastAPI | API server |
| Database | MongoDB Atlas | Sessions, users, memory |
| Intelligence | UniGuru v2 (Render) | Primary LLM inference |
| Fallback LLMs | Groq, OpenAI, Gemini | Backup intelligence |
| Auth | JWT (HS256) | Cross-app tokens |
| Execution | TANTRA Runtime | Governed execution |

---

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, router registration, middleware |
| `app/companion/companion_orchestrator.py` | Message processing brain |
| `app/companion/companion_session.py` | Session management |
| `app/companion/companion_config.py` | Configuration (LLM, capabilities) |
| `app/runtime/companion_runtime.py` | Universal runtime (sessions, context, attachments) |
| `app/runtime/api.py` | Runtime REST API |
| `app/runtime/contracts.py` | Versioned API contracts |
| `app/core/llm_bridge.py` | LLM provider routing (UniGuru primary) |
| `app/core/intentflow.py` | Intent classification |
| `app/services/jwt_service.py` | JWT token generation/verification |
| `app/services/continuity_service.py` | Cross-app session resolution |
| `app/services/tantra_client.py` | TANTRA runtime client |
| `app/services/auth_service.py` | User authentication |
| `app/interfaces/capability_runtime_interface.py` | Kanishk's runtime contract |
