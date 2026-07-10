# Mitra — Universal AI Companion

**Version:** v4.0.0 | **Status:** Production-Ready  
**Backend:** FastAPI (Python 3.10) → Render  
**Frontend:** React + TypeScript + Tailwind → Vercel

---

## What is Mitra?

Mitra is a deterministic, safety-first AI companion platform. It provides a single conversational interface through which users can access email, calendar, tasks, reminders, notes, contacts, knowledge retrieval (UniGuru), WhatsApp, browser automation, notifications, and document interaction — all governed by a mandatory safety → enforcement → execution pipeline.

Every request follows the same immutable path:  
`Safety → Intelligence → Enforcement → Orchestration → Execution → Bucket`

No module can bypass this sequence. Every step is traced, logged, and auditable.

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
# Set environment variables (see DEPLOYMENT_CONFIG.md)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend/frontend
npm install
npm start
# Opens http://localhost:3000
```

### Environment Variables
```env
# Backend (.env)
MONGODB_URI=mongodb+srv://...
GROQ_API_KEY=gsk_...
API_KEY=your_api_key
BREVO_API_KEY=...

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your_api_key
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React/Vercel)                │
│  TopBar │ Sidebar │ ConversationCenter │ ContextPanel    │
│  InputBar │ BottomNav (mobile) │ Drawers (mobile)       │
└──────────────────────┬───────────────────────────────────┘
                       │ REST API
┌──────────────────────▼───────────────────────────────────┐
│                   Backend (FastAPI/Render)                │
│                                                          │
│  ┌─────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │  Safety  │──▶│Intelligence │──▶│ Enforcement │       │
│  │(Akanksha)│   │ (Sankalp)   │   │   (Raj)     │       │
│  └─────────┘   └─────────────┘   └──────┬──────┘       │
│                                          │               │
│  ┌──────────────┐   ┌────────────────────▼──────┐       │
│  │ Companion    │──▶│  Execution (Chandresh)    │       │
│  │ Orchestrator │   │  ┌────────────────────┐   │       │
│  │ (Brain)      │   │  │ Capability Registry│   │       │
│  └──────────────┘   │  │ 11 Modules         │   │       │
│                      │  └────────────────────┘   │       │
│  ┌──────────────┐   └───────────────────────────┘       │
│  │ Bucket/Audit │  (immutable logging, MongoDB)          │
│  │  (Ashmit)    │                                        │
│  └──────────────┘                                        │
└──────────────────────────────────────────────────────────┘
```

---

## Key Modules

### Companion Layer (`app/companion/`)
| Module | Purpose |
|--------|---------|
| `companion_orchestrator.py` | Main brain — routes messages to LLM or capabilities |
| `companion_session.py` | Multi-session continuity with MongoDB persistence |
| `companion_memory.py` | Per-user fact store, conversation summaries, capability history |
| `personality_engine.py` | Configurable tone, greeting, system prompts |
| `capability_registry.py` | Dynamic capability attach/detach at runtime |
| `workflow_engine.py` | Multi-step workflow orchestration (morning briefing, meeting prep, etc.) |
| `companion_config.py` | Central configuration for personality, capabilities, LLM |

### Capability Hub (`app/capabilities/`)
| Capability | Intents |
|-----------|---------|
| Email | `draft_email`, `send_email`, `read_emails` |
| Calendar | `create_event`, `list_events`, `check_availability` |
| WhatsApp | `send_whatsapp`, `check_messages` |
| Task | `create_task`, `list_tasks`, `update_task` |
| Reminder | `create_reminder`, `list_reminders`, `cancel_reminder` |
| Notes | `create_note`, `list_notes`, `search_notes` |
| Contacts | `lookup_contact`, `add_contact`, `list_contacts` |
| Browser | `web_search`, `summarize_page` |
| Notification | `send_notification`, `list_notifications` |
| Document | `upload_document`, `summarize_document`, `search_document` |
| UniGuru | `knowledge`, `explain`, `learn`, `educational` |

All capabilities extend `BaseCapability` and are pluggable via `capability_registry.register()`.

### LLM Abstraction (`app/core/llm_bridge.py`)
Supports multiple providers behind a single interface:
- **Groq** (Llama 3.1 — primary)
- **OpenAI** (GPT-4o)
- **Google** (Gemini)
- **Mistral**
- **UniGuru** (live API endpoint)

### Safety Pipeline (`app/services/`)
| Service | Owner | Role |
|---------|-------|------|
| `safety_service.py` | Akanksha | Content validation, behavior checks |
| `intelligence_service.py` | Sankalp | Intent classification, risk scoring |
| `enforcement_service.py` | Raj | Policy enforcement (allow/rewrite/block/terminate) |
| `execution_service.py` | Chandresh | Universal execution gateway |
| `bucket_service.py` | Ashmit | Immutable audit logging with integrity hashes |

---

## Frontend Architecture

### Responsive Design (3 Breakpoints)
| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Mobile | `<768px` | Single column + bottom nav + drawer overlays |
| Tablet | `768–1023px` | Collapsed icon sidebar + full center |
| Desktop | `≥1024px` | Full 3-panel grid (sidebar + center + context) |

### Tech Stack
- React 18 + TypeScript
- Tailwind CSS (extended with design tokens)
- Zustand (state management)
- Framer Motion (animations)
- Lucide React (icons)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/assistant` | Main assistant entrypoint |
| `POST` | `/api/mitra/evaluate` | Deterministic decision flow |
| `POST` | `/api/companion/chat` | Companion conversation |
| `GET`  | `/api/companion/greeting/{user_id}` | User greeting |
| `GET`  | `/api/companion/memory/{user_id}` | User memory/facts |
| `GET`  | `/api/companion/capabilities` | List registered capabilities |
| `POST` | `/api/auth/signup` | User registration |
| `POST` | `/api/auth/login` | Authentication |
| `GET`  | `/health` | Health check |
| `GET`  | `/health/system` | Deep system status |

---

## Deployment

| Component | Platform | URL |
|-----------|----------|-----|
| Backend | Render | `https://mitra-backend.onrender.com` |
| Frontend | Vercel | `https://mitra-frontend.vercel.app` |

See: [`MERGED_DEPLOYMENT_GUIDE.md`](MERGED_DEPLOYMENT_GUIDE.md) for full deployment instructions.

---

## Documentation Index

| Document | Location |
|----------|----------|
| System Architecture | [`backend/MITRA_SYSTEM_ARCHITECTURE.md`](backend/MITRA_SYSTEM_ARCHITECTURE.md) |
| Capability Map | [`docs/CAPABILITY_MAP.md`](docs/CAPABILITY_MAP.md) |
| Interface Contract (Kanishk) | [`docs/KANISHK_INTERFACE_CONTRACT.md`](docs/KANISHK_INTERFACE_CONTRACT.md) |
| Information Architecture | [`docs/INFORMATION_ARCHITECTURE.md`](docs/INFORMATION_ARCHITECTURE.md) |
| Design System | [`docs/design-system/`](docs/design-system/) |
| Integration Guide | [`frontend/frontend/INTEGRATION_GUIDE.md`](frontend/frontend/INTEGRATION_GUIDE.md) |
| Demo Runbook | [`backend/DEMO_RUNBOOK.md`](backend/DEMO_RUNBOOK.md) |
| Deployment Guide | [`MERGED_DEPLOYMENT_GUIDE.md`](MERGED_DEPLOYMENT_GUIDE.md) |
| Review Packet | [`REVIEW_PACKET.md`](REVIEW_PACKET.md) |
| Production Roadmap | [`docs/PRODUCTION_ROADMAP.md`](docs/PRODUCTION_ROADMAP.md) |
| Cross-Platform Flows | [`docs/CROSS_PLATFORM_FLOWS.md`](docs/CROSS_PLATFORM_FLOWS.md) |
| Review History | [`review_packets/`](review_packets/) |

---

## License

Private — BHIV Project
