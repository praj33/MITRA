# CODE PACKET — Ecosystem Convergence

**Prepared by:** Raj Prajapati (praj33)  
**Date:** July 27, 2026

---

## Codebase Snapshot

### Canonical MITRA Repo (`praj33/MITRA`)

**Branch:** `main`  
**Latest Commits (most recent first):**

```
aa61274 feat: toast notifications + page transition animations
bcbdb20 feat: notification dropdown, settings modal with dark/light theme toggle
bc15a24 feat: wire all sidebar buttons with dedicated pages + voice input + suggestion chips
3099b56 fix: Lazy OpenAI client + eager import removal — backend starts clean
ff7cbbd feat: Akanksha test suites + policy setup + e2e flow system
503ab1a deliverables
c21ab57 feat: full responsive overhaul — mobile, tablet, desktop compatibility
1a6e623 Fix: LLM fallback chain + rule-based responses, UniGuru as primary provider
c27fd64 Mitra v4: Frontend shell — CSS Grid layout, 9 card primitives, Zustand store
ae013e8 Mitra v4: Backend companion layer + Kanishk contract + UX Foundation complete
89f6e47 Mitra v4: UX Foundation — IA, Design System, Component Inventory, Wireframes
c20bec1 Fix unified Mitra control plane regressions
3c1ad60 MITRA UNIFIED: Embed governance layer + bucket service into single sovereign pipeline
3f0f34f Fix Pydantic v1 compatibility for deployed API routes
0c6c4a8 Integrate backend and frontend into monorepo
```

### Repository Structure

```
MITRA-INTEGRATED/
├── README.md
├── REVIEW_PACKET.md
├── MERGED_DEPLOYMENT_GUIDE.md
├── INTEGRATION_DISCLOSURE_REPORT.md
├── TEST_RESULTS.md
│
├── _ecosystem_repos/                    # Cloned team repos
│   ├── ai-being/                        # Ashmit (blackholeinfiverse37)
│   ├── companion-runtime/               # Chandresh (great1239)
│   ├── duplex-audio/                    # Nilesh (Nilesh057)
│   ├── ecosystem-hardening/             # Chandresh (great1239)
│   ├── governance-layer/                # Akanksha (aa2kansha90)
│   └── uniguru-v2/                      # Sankalp/Eisha (eishasingh929-sudo)
│
├── backend/
│   ├── app/
│   │   ├── api/                         # REST API endpoints
│   │   │   ├── assistant.py             # Main assistant endpoint
│   │   │   └── companion_routes.py      # Companion conversation routes
│   │   ├── companion/                   # Companion brain layer
│   │   │   ├── companion_orchestrator.py  # Central brain
│   │   │   ├── companion_session.py       # Session continuity
│   │   │   ├── companion_memory.py        # Persistent memory
│   │   │   ├── personality_engine.py      # Configurable personality
│   │   │   ├── capability_registry.py     # Dynamic capability attach
│   │   │   ├── workflow_engine.py         # Multi-step workflows
│   │   │   └── companion_config.py        # Central configuration
│   │   ├── capabilities/                # 11 pluggable capabilities
│   │   │   ├── base_capability.py         # Abstract interface + CapabilityResult
│   │   │   ├── email_capability.py
│   │   │   ├── calendar_capability.py
│   │   │   ├── whatsapp_capability.py
│   │   │   ├── task_capability.py
│   │   │   ├── reminder_capability.py
│   │   │   ├── notes_capability.py
│   │   │   ├── contacts_capability.py
│   │   │   ├── browser_capability.py
│   │   │   ├── notification_capability.py
│   │   │   ├── document_capability.py
│   │   │   └── uniguru_capability.py
│   │   ├── core/                        # Core services
│   │   │   ├── llm_bridge.py              # 4-provider LLM abstraction
│   │   │   ├── assistant_orchestrator.py  # Pipeline orchestrator
│   │   │   ├── decision_hub.py
│   │   │   ├── intentflow.py
│   │   │   └── respond_service.py
│   │   ├── services/                    # Safety pipeline
│   │   │   ├── safety_service.py          # Akanksha — content validation
│   │   │   ├── intelligence_service.py    # Sankalp — intent classification
│   │   │   ├── enforcement_service.py     # Raj — policy enforcement
│   │   │   ├── execution_service.py       # Chandresh — execution gateway
│   │   │   ├── bucket_service.py          # Ashmit — audit logging
│   │   │   ├── audio_service.py           # Soham — STT/TTS
│   │   │   └── multilingual_service.py    # Soham — language support
│   │   ├── routers/                     # REST routers
│   │   │   └── pages.py                   # Dashboard page data endpoints
│   │   └── inbound/                     # Multi-channel ingestion
│   │       ├── telegram_handler.py
│   │       ├── whatsapp_handler.py
│   │       └── email_handler.py
│   ├── client_adapters/                 # Platform adapter specs
│   ├── deploy/                          # Deployment configs
│   └── tests/                           # Test suite
│
├── frontend/
│   ├── Signup/                          # Auth/signup module
│   └── frontend/                        # Main React app
│       ├── src/
│       │   ├── components/
│       │   │   ├── shell/               # 9 shell components
│       │   │   │   ├── TopBar.tsx
│       │   │   │   ├── Sidebar.tsx
│       │   │   │   ├── ConversationCenter.tsx
│       │   │   │   ├── InputBar.tsx
│       │   │   │   ├── ContextPanel.tsx
│       │   │   │   ├── NotificationDropdown.tsx
│       │   │   │   ├── SettingsModal.tsx
│       │   │   │   └── Toast.tsx
│       │   │   └── pages/               # 5 dashboard pages
│       │   │       ├── CalendarPage.tsx
│       │   │       ├── TasksPage.tsx
│       │   │       ├── RemindersPage.tsx
│       │   │       ├── KnowledgePage.tsx
│       │   │       └── WorkflowsPage.tsx
│       │   ├── store/companion.store.ts # Zustand state management
│       │   ├── services/companion.service.ts # API service layer
│       │   ├── App.tsx                  # Root shell + routing
│       │   └── index.css                # 1200+ lines design system
│       └── public/index.html           # PWA-ready HTML
│
├── docs/
│   ├── CAPABILITY_MAP.md
│   ├── CROSS_PLATFORM_FLOWS.md
│   ├── PRODUCTION_ROADMAP.md
│   ├── INFORMATION_ARCHITECTURE.md
│   ├── KANISHK_INTERFACE_CONTRACT.md
│   └── design-system/
│
└── review_packets/                      # Convergence audit
    ├── MASTER_REPOSITORY_INDEX.md
    ├── CONTRIBUTOR_MATRIX.md
    ├── FEATURE_MATRIX.md
    ├── DUPLICATE_IMPLEMENTATION_REPORT.md
    ├── ACTIVE_DEPLOYMENT_LIST.md
    ├── CODE_PACKET.md
    └── REVIEW_PACKET.md
```

### Key Integration Points

```python
# How capabilities are registered (startup)
from app.capabilities import register_all_capabilities
register_all_capabilities()  # Registers all 11 capabilities

# How the companion processes a message
result = await companion_orchestrator.process_message(
    user_id="user_123",
    message="Draft an email to John about tomorrow's meeting",
    platform="web",
)

# How the safety pipeline works
safety_result = await safety_service.check(content)          # Akanksha
intel_result = await intelligence_service.analyze(content)   # Sankalp
enforce_result = await enforcement_service.decide(intel_result)  # Raj
exec_result = await execution_service.execute(action)        # Chandresh
bucket_service.log(trace_id, all_artifacts)                  # Ashmit
```

### External Service Dependencies

```env
# LLM Providers
GROQ_API_KEY=gsk_...          # Primary LLM (Llama 3.1)
OPENAI_API_KEY=sk-...         # Fallback
GOOGLE_API_KEY=...            # Fallback
MISTRAL_API_KEY=...           # Fallback

# External Services (other team members' deployments)
UNIGURU_URL=https://uniguru-v2.onrender.com/new_query  # Sankalp's service
UNIGURU_API_KEY=uniguru_secret_123

# Database
MONGODB_URI=mongodb+srv://...

# Email
BREVO_API_KEY=...

# Auth
API_KEY=...
```

### Frontend Stack

```
React 18 + TypeScript
Zustand (state management)
Framer Motion (animations)
Lucide React (icons)
Vanilla CSS (1200+ lines, CSS variables for theming)
```
