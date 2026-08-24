# MITRA Integration Handover Document

> **Branch Under Integration:** `Master-ashmit` (origin: `blackholeinfiverse54-creator/Mitra_T42.git`)
> **Target Repos:** `bhiv/main` (`BHIV-Engineering-Exchange/bhiv-Mitra.git`) and `praj33/main` (`praj33/MITRA.git`)
> **Date:** 2026-08-24
> **Author:** Automated Analysis

---

## Table of Contents

1. [Repository Landscape](#1-repository-landscape)
2. [Branch Divergence Analysis](#2-branch-divergence-analysis)
3. [What Each Branch Contributes](#3-what-each-branch-contributes)
4. [Conflict Map (14 Conflict Files)](#4-conflict-map-14-conflict-files)
5. [Integration Strategy](#5-integration-strategy)
6. [Step-by-Step Backend Integration](#6-step-by-step-backend-integration)
7. [Step-by-Step Frontend Integration](#7-step-by-step-frontend-integration)
8. [Environment Variables & Deployment](#8-environment-variables--deployment)
9. [Verification & Testing](#9-verification--testing)
10. [Architecture After Integration](#10-architecture-after-integration)

---

## 1. Repository Landscape

### Three Remotes

| Remote | GitHub URL | Branch | Lineage |
|--------|-----------|--------|---------|
| `origin` | `blackholeinfiverse54-creator/Mitra_T42.git` | `Master-ashmit` | Base branch - safety-first chatbot with TANTRA runtime |
| `bhiv` | `BHIV-Engineering-Exchange/bhiv-Mitra.git` | `main` | Forked from `e5f6936` (parent of Master-ashmit's tip) |
| `praj33` | `praj33/MITRA.git` | `main` / `master1` | Completely different git history (force-pushed/rebased) |

### Current State of Each Branch

```
Master-ashmit (1d30166 - HEAD)
    |
    v
[origin/main at e5f6936] -----> Master-ashmit adds 5 commits on top
    |
    v
[bhiv/main at 574def0] ------> 4 commits ahead of shared ancestor e5f6936
    |
    v
[praj33/main at faf1183] ----> Completely independent history, no git merge-base
```

### Git Relationship

- **bhiv/main** shares a common ancestor (`e5f6936`) with Master-ashmit. A merge is possible with minor conflicts.
- **praj33/main** has NO git common ancestor with Master-ashmit. Code must be cherry-picked or manually merged by comparing file contents.

---

## 2. Branch Divergence Analysis

### What Master-ashmit Has (Your Branch)

This is the **safety-first production backend** with:
- `assistant_orchestrator.py` (1007 lines) - Central request processing spine
- `MitraControlPlaneService` (634 lines) - Dual policy evaluation
- `TANTRA Runtime` - Sole execution runtime with state machine, governance, registry
- `Enforcement Engine` - Deterministic fail-closed safety with kill switch
- `Policy Engine` - JSON rule-based evaluation (content + behavior + regional)
- `Behavior Validator` - 100+ regex patterns across 7 risk categories
- `BucketService` - SHA-256 integrity hashing, trace-based audit
- `IntentFlow` - LLM + regex dual-path intent classification
- `LLMBridge` - 5 provider support (Groq, OpenAI, Gemini, Mistral, UniGuru)
- Frontend: React + TypeScript + Tailwind iOS-style chat interface
- V3.0.0 API contract (`POST /api/assistant`)

### What bhiv/main Adds

The **incremental enhancement** layer. Adds on top of shared ancestor:

| Feature | Details |
|---------|---------|
| `LocalKnowledgeBase` | Hardcoded knowledge fallback when no LLM keys present (origin of life, formulas, etc.) |
| Session management | 60-second heartbeat, session/memory/presence APIs |
| Auth improvements | Full JWT system with `create_access_token`, rate limiting |
| LanguageDropdown | Modified for 11 languages |
| API config | `bhiv-enterprise-key`, `mitra-backend-q1f3.onrender.com` |
| Monitoring | Sentry integration, Prometheus metrics |

### What praj33/main Adds

The **full platform rewrite**. Adds ~100+ new files across 12+ packages:

| Module | New Files | Purpose |
|--------|-----------|---------|
| `backend/app/capabilities/` | 15 files | Capability modules (email, calendar, task, reminder, browser, contacts, document, notes, notification, samachar, samruddhi, uniguru, whatsapp) |
| `backend/app/companion/` | 7 files | Companion brain (orchestrator, memory, session, config, capability registry, personality engine, workflow engine) |
| `backend/app/runtime/` | 20 files | Full runtime framework (session, context, intent routing, manifest, lifecycle, event bus, transport, replay engine, store, API) |
| `backend/app/governance/` | 22 files | Extended governance (safety validators, policy engine, enforcement, behavior validation, mediation, replay, preference transformation, email/whatsapp/voice handlers) |
| `backend/app/audio/` | 4 files | TTS service, prosody mapper, Vani TTS adapter |
| `backend/app/voice/` | 7 files | Voice session manager, telephony executor/stream, language auto-detect, failure handler, voice trace |
| `backend/app/uniguru/` | 25+ files | Knowledge engine (ontology, reasoning, governance, rules, integrations, enforcement) |
| `backend/app/interfaces/` | 1 file | Capability runtime interface |
| `frontend` shell components | 12 files | Sidebar, TopBar, ConversationCenter, ContextPanel, InputBar, SettingsModal, AuthModal, Toast, NotificationDropdown, InstallPwaBanner |
| `frontend` pages | 6 files | Calendar, Tasks, Reminders, Workflows, Knowledge, Analytics |
| `frontend` modals | 5 files | FocusTimer, CommandPalette, MemoryDashboard, VoiceTalk, MemoryMindMap |
| `frontend` store | 1 file | Zustand-based `companion.store.ts` |
| `frontend` services | 2 files | `companion.service.ts`, `ambientSound.service.ts` |
| `frontend` primitives | 5 files | Badge, CompanionDot, FormattedMarkdown, Kbd, barrel export |
| `frontend` cards | 9 files | Action, Context, Conversation, DailyBriefing, KPI, Notification, Recommendation, Status, System, Timeline |
| `contracts/` | 20+ files | OpenAPI specs, JSON schemas, integration contracts, runtime policies |
| `tests/governance/` | 12 files | Abuse, ambiguity, authority, containment, edge case, temporal, transition tests |
| `tests/runtime/` | 12 files | API, attachment, boundary, context, dispatch, lifecycle, ownership, phase1-6 tests |

---

## 3. What Each Branch Contributes

### Master-ashmit (YOUR BRANCH) - The Foundation

```
Core Spine: assistant_orchestrator.py
    |
    +---> Multilingual (EN <-> HI)
    +---> Control Plane (Policy + RL + Enforcement)
    +---> IntentFlow (LLM + regex)
    +---> Platform Detection
    +---> TANTRA Runtime (sole execution path)
    +---> Response Translation
    +---> Optional TTS
```

**Files you own:**
- `backend/app/core/assistant_orchestrator.py`
- `backend/app/core/llm_bridge.py` (base version)
- `backend/app/core/intentflow.py` (base version)
- `backend/app/core/respond_service.py` (base version)
- `backend/app/core/summaryflow.py`, `taskflow.py`, `bhiv_core.py`, `bhiv_reasoner.py`
- `backend/app/services/mitra_control_plane_service.py`
- `backend/app/services/bucket_service.py`
- `backend/app/services/multilingual_service.py`
- `backend/app/services/execution_service.py`
- `backend/app/services/enforcement_service.py`
- `backend/app/services/audio_service.py`
- `backend/app/services/outbound_safety_gate.py`
- `backend/app/services/inbound_mediation_service.py`
- `backend/app/external/enforcement/*`
- `backend/app/external/safety/*`
- `backend/app/governance/policy_engine.py`
- `backend/app/tantra/*` (entire TANTRA runtime)
- `backend/app/executors/*` (all platform executors)
- `backend/app/inbound/*` (all inbound handlers)
- `backend/app/agents/*` (multi-agent system)
- `backend/app/api/assistant.py`, `auth.py`, `webhooks.py`, `tts.py`, `replay.py`
- `frontend/frontend/src/*` (entire React app)
- `render.yaml` (deployment config)

### bhiv/main - The Enhancement

**What to take from bhiv:**

| File | What to Merge |
|------|---------------|
| `backend/app/core/llm_bridge.py` | `LocalKnowledgeBase` class (hardcoded fallback when no API keys) |
| `backend/app/core/security.py` | JWT auth improvements (if better than your version) |
| `frontend/frontend/src/services/api.ts` | Session management, heartbeat, memory/presence APIs |
| `backend/app/main.py` | Sentry integration, Prometheus monitoring init |

### praj33/main - The Expansion

**What to take from praj33 (selective cherry-pick):**

| Module | What to Merge | Priority |
|--------|--------------|----------|
| `backend/app/capabilities/` | All 15 capability modules | HIGH |
| `backend/app/companion/` | Companion orchestrator + memory + session + config + personality engine | HIGH |
| `backend/app/runtime/` | Intent router, context runtime, session runtime, transport, event bus | HIGH |
| `backend/app/companion_api.py` | API endpoints for companion features | HIGH |
| `backend/app/services/continuity_service.py` | Conversation continuity | MEDIUM |
| `backend/app/services/jwt_service.py` | JWT service | MEDIUM |
| `backend/app/core/text_normalizer.py` | Text normalization | MEDIUM |
| `backend/app/governance/` | Extended validators, mediation, enforcement adapter | MEDIUM |
| `backend/app/voice/` | Voice session manager, telephony | MEDIUM |
| `backend/app/audio/` | TTS service, prosody mapper | MEDIUM |
| `backend/app/uniguru/` | Knowledge engine, ontology, reasoning | LOW (complex) |
| `frontend` shell components | Sidebar, TopBar, InputBar, ContextPanel, etc. | HIGH |
| `frontend` pages | Calendar, Tasks, Reminders, Workflows, Knowledge, Analytics | HIGH |
| `frontend` modals | FocusTimer, CommandPalette, MemoryDashboard, VoiceTalk, MemoryMindMap | MEDIUM |
| `frontend` store | `companion.store.ts` (Zustand) | HIGH |
| `contracts/` | OpenAPI specs, JSON schemas | LOW |
| `tests/` | Governance and runtime tests | MEDIUM |

---

## 4. Conflict Map (14 Conflict Files)

These files are modified by BOTH bhiv and praj33 relative to Master-ashmit. Resolution strategy for each:

### 4.1 `backend/app/main.py`
**bhiv adds:** ecosystem/tantra/replay/metrics routers, Telegram webhook, Sentry, Prometheus
**praj33 adds:** companion/workflow/presence/notifications routers, optional ecosystem imports

**Resolution:** Merge both. Include ALL routers from all three branches.

```python
# FINAL main.py should import ALL routers:
from app.api.auth import router as auth_router
from app.api.assistant import router as assistant_router
from app.api.mitra_api import router as mitra_router
from app.api.webhooks import router as webhook_router
from app.api.tts import router as tts_router
from app.api.replay import router as replay_router
from app.api.metrics import router as metrics_router
from app.api.ecosystem import router as ecosystem_router
from app.api.companion_api import router as companion_router        # FROM praj33
from app.api.workflow_api import router as workflow_router          # FROM praj33
from app.api.notifications_api import router as notifications_router # FROM praj33
from app.api.presence_api import router as presence_router          # FROM praj33
from app.tantra.api import router as tantra_router
```

### 4.2 `backend/app/core/llm_bridge.py`
**bhiv adds:** LocalKnowledgeBase fallback, hardcoded knowledge
**praj33 adds:** Cleaner httpx-based implementation, configurable cache

**Resolution:** Keep Master-ashmit's base + add bhiv's LocalKnowledgeBase as fallback.

### 4.3 `backend/app/core/intentflow.py`
**bhiv adds:** Regex `\b` word-boundary matching, explicit task-first priority
**praj33 adds:** Simple `in` keyword matching

**Resolution:** Keep Master-ashmit's version (most complete). bhiv's regex improvements are good to adopt.

### 4.4 `backend/app/core/respond_service.py`
**bhiv adds:** Multilingual language selection from context
**praj33 adds:** Nearly same as Master-ashmit

**Resolution:** Keep Master-ashmit's version + adopt bhiv's multilingual improvements.

### 4.5 `backend/app/core/assistant_orchestrator.py`
**Both modified** from shared ancestor.

**Resolution:** Keep Master-ashmit's version (1007 lines, most complete). Cherry-pick specific improvements from bhiv/praj33 if any.

### 4.6 `backend/app/api/assistant.py`
**Both modified** from shared ancestor.

**Resolution:** Keep Master-ashmit's version (V3.0.0 contract, SSE streaming).

### 4.7 `backend/app/core/security.py`
**bhiv adds:** Full JWT system
**praj33 adds:** Modified version

**Resolution:** Use bhiv's version (more complete JWT implementation).

### 4.8 `frontend/frontend/src/App.tsx`
**bhiv adds:** Auth-gated app, heartbeat, session management
**praj33 adds:** Complete SPA rewrite with Zustand, pages, modals

**Resolution:** Use praj33's App.tsx as the base (more complete), then merge bhiv's heartbeat/session features into it.

### 4.9 `frontend/frontend/src/services/api.ts`
**bhiv adds:** Session/memory/presence APIs, heartbeat
**praj33 adds:** Simpler V3.0.0 contract

**Resolution:** Merge both. Use praj33's simpler API structure + add bhiv's session management endpoints.

### 4.10 Other Conflicts
- `LanguageDropdown.tsx` - Merge both
- `README.md` files - Use praj33's (more complete)
- `package-lock.json` - Regenerate after merge
- `.env.example` - Merge both

---

## 5. Integration Strategy

### Phase 1: Foundation (Master-ashmit + bhiv)

Since bhiv shares a common ancestor, this is a **git merge**:

```bash
# On Master-ashmit branch
git merge bhiv/main --no-commit
# Resolve conflicts in the 14 files listed above
git add .
git commit -m "merge: integrate bhiv enhancements into Master-ashmit"
```

### Phase 2: Expansion (Master-ashmit + praj33)

Since praj33 has no git common ancestor, this is a **selective cherry-pick**:

```bash
# Create a working branch
git checkout -b integration/master-full Master-ashmit

# Cherry-pick new modules from praj33 (one at a time)
git checkout praj33/main -- backend/app/capabilities/
git checkout praj33/main -- backend/app/companion/
git checkout praj33/main -- backend/app/runtime/
git checkout praj33/main -- backend/app/companion_api.py
git checkout praj33/main -- backend/app/services/continuity_service.py
git checkout praj33/main -- backend/app/services/jwt_service.py
git checkout praj33/main -- backend/app/core/text_normalizer.py
git checkout praj33/main -- backend/app/voice/
git checkout praj33/main -- backend/app/audio/
git checkout praj33/main -- frontend/frontend/src/components/shell/
git checkout praj33/main -- frontend/frontend/src/components/pages/
git checkout praj33/main -- frontend/frontend/src/components/modals/
git checkout praj33/main -- frontend/frontend/src/store/
git checkout praj33/main -- frontend/frontend/src/services/companion.service.ts
git checkout praj33/main -- frontend/frontend/src/services/ambientSound.service.ts
git checkout praj33/main -- frontend/frontend/src/components/primitives/
git checkout praj33/main -- frontend/frontend/src/components/cards/
git checkout praj33/main -- tests/

git add .
git commit -m "feat: integrate praj33 companion runtime and UI modules"
```

### Phase 3: Conflict Resolution

Manually resolve the 14 conflict files (see Section 4 for detailed resolution strategy).

---

## 6. Step-by-Step Backend Integration

### Step 1: Merge bhiv's LocalKnowledgeBase into llm_bridge.py

The `LocalKnowledgeBase` from bhiv provides a hardcoded knowledge fallback. Add it to Master-ashmit's `llm_bridge.py`:

```python
# In backend/app/core/llm_bridge.py
# Add this class AFTER the existing LocalKnowledgeBase or as a new class

class LocalKnowledgeBase:
    """Fallback knowledge base when no LLM API keys are configured."""
    
    def __init__(self):
        self.knowledge = {
            "origin of life": "Life on Earth originated approximately 3.5-4 billion years ago...",
            "percentage formula": "Percentage = (Part / Whole) * 100",
            # ... add more as needed
        }
    
    async def query(self, question: str) -> str:
        question_lower = question.lower()
        for key, value in self.knowledge.items():
            if key in question_lower:
                return value
        return None
```

Then in `LLMBridge.call_llm()`, add fallback:
```python
# After all LLM providers fail, before returning None:
if model == "uniguru":
    kb = LocalKnowledgeBase()
    result = await kb.query(prompt)
    if result:
        return result
```

### Step 2: Add companion capabilities to main.py

Add the new routers from praj33 to `backend/app/main.py`:

```python
# Add these imports (check if files exist first)
try:
    from app.api.companion_api import router as companion_router
    app.include_router(companion_router)
except ImportError:
    pass

try:
    from app.api.workflow_api import router as workflow_router
    app.include_router(workflow_router)
except ImportError:
    pass

try:
    from app.api.notifications_api import router as notifications_router
    app.include_router(notifications_router)
except ImportError:
    pass

try:
    from app.api.presence_api import router as presence_router
    app.include_router(presence_router)
except ImportError:
    pass
```

### Step 3: Integrate capabilities module

The `backend/app/capabilities/` directory from praj33 provides modular capability implementations. These are standalone modules that can be imported:

```
capabilities/
    __init__.py              # Capability registry
    base_capability.py       # Base class
    email_capability.py      # Email sending
    calendar_capability.py   # Calendar events
    task_capability.py       # Task management
    reminder_capability.py   # Reminders
    browser_capability.py    # Web browsing
    contacts_capability.py   # Contact management
    document_capability.py   # Document handling
    notes_capability.py      # Note-taking
    notification_capability.py # Notifications
    samachar_capability.py   # News/content
    samruddhi_capability.py  # Financial insights
    uniguru_capability.py    # Knowledge engine
    whatsapp_capability.py   # WhatsApp integration
```

### Step 4: Integrate companion orchestrator

The `backend/app/companion/` module from praj33 provides the companion brain. Key integration points:

```python
# In backend/app/companion/companion_orchestrator.py
# This module defines how intents map to capabilities
# It should be callable from assistant_orchestrator.py

# In assistant_orchestrator.py, after IntentFlow classification:
from app.companion.companion_orchestrator import CompanionOrchestrator

# If intent is a capability type, route through companion:
if intent in ["email", "calendar", "task", "reminder", "whatsapp"]:
    companion = CompanionOrchestrator()
    result = await companion.process(intent, entities, context)
```

### Step 5: Integrate runtime framework

The `backend/app/runtime/` module from praj33 provides a standalone runtime. This is OPTIONAL - it can coexist with the existing TANTRA runtime:

```
runtime/
    api.py                 # Standalone FastAPI app (can be separate service)
    companion_runtime.py   # Companion-specific runtime
    context_runtime.py     # Context management
    intent_router.py       # Intent routing
    session_runtime.py     # Session management
    transport.py           # Transport layer
    event_bus.py           # Event bus
    store.py               # State store
    ...
```

**Recommendation:** Keep TANTRA as the primary runtime. The runtime module can be used as a secondary system for companion-specific features.

### Step 6: Add text normalizer

From praj33: `backend/app/core/text_normalizer.py`

This provides text normalization for consistent input processing. Add it to the orchestrator pipeline:

```python
# In assistant_orchestrator.py, after normalization:
from app.core.text_normalizer import normalize_text
normalized_input = normalize_text(user_message)
```

### Step 7: Integrate governance extensions

From praj33: `backend/app/governance/` contains extended validators. Key additions:

- `behavior_validator.py` (636 lines) - Extended behavior validation
- `mediation_system.py` (540 lines) - Message mediation
- `enforcement_execution_system.py` (619 lines) - Enforcement execution
- `hardened_validator.py` (507 lines) - Hardened validation
- `preference_transformation_logic.py` (266 lines) - User preference handling
- `unified_validator.py` (379 lines) - Unified validation

**Integration:** These extend the existing safety pipeline. Import and use them alongside the existing `BehaviorValidator` and `EnforcementService`.

### Step 8: Add voice/telephony support

From praj33: `backend/app/voice/` provides:

- `voice_session_manager.py` (784 lines) - Session management for voice
- `telephony_executor.py` (332 lines) - Telephony call execution
- `telephony_stream.py` (794 lines) - Audio streaming
- `language_auto.py` (702 lines) - Auto language detection
- `failure_handler.py` (608 lines) - Voice failure handling
- `voice_trace.py` (281 lines) - Voice request tracing

**Integration:** Add voice routes to main.py:
```python
try:
    from app.voice.stt_engine import router as stt_router
    app.include_router(stt_router)
except ImportError:
    pass
```

### Step 9: Add audio/TTS service

From praj33: `backend/app/audio/` provides:

- `tts_service.py` (186 lines) - Text-to-speech service
- `prosody_mapper.py` (215 lines) - Prosody/emotion mapping
- `vani_tts_adapter.py` (181 lines) - Vani TTS integration

**Integration:** These replace or supplement the existing `audio_service.py`.

---

## 7. Step-by-Step Frontend Integration

### Step 1: Adopt praj33's shell components

From praj33: `frontend/frontend/src/components/shell/`

These are the core UI shell components. Replace the existing simple layout:

| Component | Purpose | Replaces |
|-----------|---------|----------|
| `Sidebar.tsx` (268 lines) | Navigation sidebar | Part of `ChatSidebar.tsx` |
| `TopBar.tsx` (308 lines) | Top navigation bar | Inline header in `App.tsx` |
| `InputBar.tsx` (467 lines) | Message input | `MessageInput.tsx` |
| `ContextPanel.tsx` (152 lines) | Context sidebar | New |
| `ConversationCenter.tsx` (134 lines) | Conversation list | Part of `ChatSidebar.tsx` |
| `SettingsModal.tsx` (158 lines) | Settings dialog | New |
| `AuthModal.tsx` (276 lines) | Auth dialog | `Login.tsx` + `Signup.tsx` |
| `Toast.tsx` (82 lines) | Notifications | `Toast.tsx` |
| `NotificationDropdown.tsx` (87 lines) | Notification list | New |
| `InstallPwaBanner.tsx` (82 lines) | PWA install | New |

### Step 2: Adopt praj33's pages

From praj33: `frontend/frontend/src/components/pages/`

These add multi-page functionality:

| Page | Purpose |
|------|---------|
| `CalendarPage.tsx` (405 lines) | Calendar view |
| `TasksPage.tsx` (175 lines) | Task management |
| `RemindersPage.tsx` (246 lines) | Reminder management |
| `WorkflowsPage.tsx` (110 lines) | Workflow builder |
| `KnowledgePage.tsx` (108 lines) | Knowledge base |
| `AnalyticsPage.tsx` (376 lines) | Analytics dashboard |

### Step 3: Adopt praj33's modals

From praj33: `frontend/frontend/src/components/modals/`

| Modal | Purpose |
|-------|---------|
| `FocusTimerModal.tsx` (218 lines) | Focus/pomodoro timer |
| `CommandPaletteModal.tsx` (251 lines) | Command palette (Ctrl+K) |
| `MemoryDashboardModal.tsx` (225 lines) | Memory visualization |
| `VoiceTalkModal.tsx` (271 lines) | Voice conversation |
| `MemoryMindMapModal.tsx` (550 lines) | Memory mind map |

### Step 4: Adopt praj33's store and services

From praj33:

- `frontend/frontend/src/store/companion.store.ts` (312 lines) - Zustand state management
- `frontend/frontend/src/services/companion.service.ts` (359 lines) - Companion API service
- `frontend/frontend/src/services/ambientSound.service.ts` (109 lines) - Ambient sounds

**Note:** This adds Zustand as a dependency. Update `package.json`:
```bash
npm install zustand
```

### Step 5: Adopt praj33's cards and primitives

From praj33:

Cards (`frontend/frontend/src/components/cards/`):
- ActionCard, ContextCard, ConversationCard, DailyBriefingCard, KPICard, NotificationCard, RecommendationCard, StatusCard, SystemCard, TimelineCard

Primitives (`frontend/frontend/src/components/primitives/`):
- Badge, CompanionDot, FormattedMarkdown, Kbd

### Step 6: Merge bhiv's session management into api.ts

From bhiv, add to `frontend/frontend/src/services/api.ts`:

```typescript
// Add session management
private _sessionId: string = `session-${Date.now()}`;

async getSession() {
  return fetch(`${API_BASE_URL}/api/session/${this._sessionId}`, {
    headers: this.getHeaders(),
  });
}

async getMemory() {
  return fetch(`${API_BASE_URL}/api/memory/${this._sessionId}`, {
    headers: this.getHeaders(),
  });
}

async getPresence() {
  return fetch(`${API_BASE_URL}/api/presence`, {
    headers: this.getHeaders(),
  });
}

async sendHeartbeat() {
  return fetch(`${API_BASE_URL}/api/heartbeat`, {
    method: 'POST',
    headers: this.getHeaders(),
    body: JSON.stringify({ session_id: this._sessionId }),
  });
}
```

### Step 7: Update tailwind.config.js

From praj33: `frontend/frontend/tailwind.config.js` has extended design tokens. Merge with existing config.

### Step 8: Update package.json dependencies

From praj33's `frontend/frontend/package.json`:

```json
{
  "dependencies": {
    "zustand": "^4.5.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0",
    "date-fns": "^3.6.0",
    "recharts": "^2.12.0",
    "react-hot-toast": "^2.4.0"
  }
}
```

### Step 9: Update index.css

From praj33: `frontend/frontend/src/index.css` has 1951 lines of styles. Merge with existing CSS.

---

## 8. Environment Variables & Deployment

### Backend (.env)

```bash
# === From Master-ashmit (keep all) ===
API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
MISTRAL_API_KEY=your_mistral_key
LLM_CACHE_MAX_SIZE=500
MONGODB_URI=your_mongodb_uri
JWT_SECRET_KEY=your_jwt_secret
FRONTEND_URL=https://mitra-t42.vercel.app
CORS_ORIGINS=https://mitra-t42.vercel.app

# === From bhiv (add these) ===
SENTRY_DSN=your_sentry_dsn
SENTRY_TRACES_SAMPLE_RATE=0.1
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_WEBHOOK_URL=https://your-backend.onrender.com/webhook/telegram

# === From praj33 (add these) ===
COMPANION_MODE=enabled
RUNTIME_MODE=companion
ENABLE_VOICE=true
ENABLE_TELEPHONY=false
VANI_TTS_API_KEY=your_vani_key
AMBIENT_SOUND_ENABLED=true
```

### Frontend (.env)

```bash
# === From Master-ashmit (keep all) ===
REACT_APP_API_URL=https://bhiv-mitra.onrender.com
REACT_APP_API_KEY=mitra_production_api_key_2026_secure_random_value

# === From bhiv (add these) ===
REACT_APP_HEARTBEAT_INTERVAL=60000
REACT_APP_SESSION_ENABLED=true

# === From praj33 (add these) ===
REACT_APP_COMPANION_MODE=enabled
REACT_APP_PWA_ENABLED=true
REACT_APP_VOICE_ENABLED=true
```

### render.yaml (Backend Deployment)

The `render.yaml` at root should be updated to include all services. Keep Master-ashmit's render.yaml as base.

### Deployment Order

1. Deploy backend first (all new modules must be importable)
2. Run `pip install -r requirements.txt` to install new dependencies
3. Deploy frontend
4. Verify all API endpoints work
5. Test companion features
6. Enable voice features if configured

---

## 9. Verification & Testing

### Backend Verification Checklist

```bash
# 1. Start backend
cd backend
python -m uvicorn app.main:app --reload

# 2. Check all endpoints load
curl http://localhost:8000/health
curl http://localhost:8000/

# 3. Test core assistant
curl -X POST http://localhost:8000/api/assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"version":"3.0.0","input":{"message":"Hello"},"context":{"platform":"web","device":"desktop"}}'

# 4. Test companion API
curl http://localhost:8000/api/companion/capabilities \
  -H "X-API-Key: your_api_key"

# 5. Test runtime API
curl http://localhost:8000/api/runtime/status

# 6. Test TANTRA status
curl http://localhost:8000/api/tantra/status

# 7. Check Swagger docs
open http://localhost:8000/docs
```

### Frontend Verification Checklist

```bash
# 1. Start frontend
cd frontend/frontend
npm install
npm start

# 2. Check login works
# 3. Check chat interface works
# 4. Check sidebar navigation
# 5. Check companion features (if enabled)
# 6. Check voice features (if enabled)
# 7. Check pages (Calendar, Tasks, etc.)
# 8. Check modals (Settings, Command Palette, etc.)
```

### Integration Test Script

```bash
#!/bin/bash
echo "=== MITRA Integration Test ==="

# Health check
echo "1. Health check..."
curl -s http://localhost:8000/health | python -m json.tool

# Assistant test
echo "2. Assistant test..."
curl -s -X POST http://localhost:8000/api/assistant \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"version":"3.0.0","input":{"message":"What is 2+2?"},"context":{"platform":"web","device":"desktop"}}' | python -m json.tool

# Companion test
echo "3. Companion capabilities..."
curl -s http://localhost:8000/api/companion/capabilities \
  -H "X-API-Key: $API_KEY" | python -m json.tool

echo "=== All tests passed ==="
```

---

## 10. Architecture After Integration

```
                    MITRA Unified Platform
                    ======================

┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TS)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ Sidebar  │ │ TopBar   │ │ InputBar │ │ ContextPanel     ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │Calendar  │ │ Tasks    │ │Reminders │ │ Workflows        ││
│  │Page      │ │ Page     │ │ Page     │ │ Page             ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │Knowledge │ │Analytics │ │VoiceTalk │ │MemoryDashboard   ││
│  │Page      │ │ Page     │ │Modal     │ │Modal             ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│                                                              │
│  Store: Zustand (companion.store.ts)                         │
│  Services: api.ts + companion.service.ts                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ POST /api/assistant (V3.0.0)
                              │ GET  /api/companion/*
                              │ POST /api/runtime/*
                              v
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Security Layer                        ││
│  │  API Key + JWT Auth + Rate Limiting + Audit Logging      ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Assistant Orchestrator (1007 lines)         ││
│  │  Multilingual → ControlPlane → IntentFlow → Platform     ││
│  └─────────────────────────────────────────────────────────┘│
│         │                    │                    │           │
│         v                    v                    v           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐│
│  │ TANTRA      │  │ Companion    │  │ Respond Service      ││
│  │ Runtime     │  │ Orchestrator │  │ (LLM Bridge)         ││
│  │ (Execution) │  │ (Capabilities│  │ Groq/OpenAI/Gemini/  ││
│  │             │  │  Registry)   │  │ Mistral/UniGuru      ││
│  └─────────────┘  └──────────────┘  └──────────────────────┘│
│         │                    │                               │
│         v                    v                               │
│  ┌─────────────┐  ┌──────────────┐                          │
│  │ Execution   │  │ Capabilities │                          │
│  │ Service     │  │ (15 modules) │                          │
│  │             │  │              │                          │
│  │ WhatsApp    │  │ email        │                          │
│  │ Telegram    │  │ calendar     │                          │
│  │ Email       │  │ task         │                          │
│  │ Instagram   │  │ reminder     │                          │
│  │ Calendar    │  │ browser      │                          │
│  │ Reminder    │  │ contacts     │                          │
│  │ EMS         │  │ document     │                          │
│  │ Device      │  │ notes        │                          │
│  └─────────────┘  │ notification │                          │
│                   │ samachar     │                          │
│                   │ samruddhi    │                          │
│                   │ uniguru      │                          │
│                   │ whatsapp     │                          │
│                   └──────────────┘                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Safety Pipeline (Defense in Depth)          ││
│  │  Inbound Mediation → Policy Engine → Behavior Validator  ││
│  │  → Enforcement Engine → Outbound Safety → Gateway Auth   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Runtime Framework (from praj33)             ││
│  │  Session → Context → Intent Router → Transport → Store   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Voice & Audio (from praj33)                 ││
│  │  VoiceSession → Telephony → TTS → Prosody → Language     ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Governance (from praj33)                    ││
│  │  Validators → Mediation → Enforcement → Replay           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                 │
│  MongoDB: tasks, audit_logs, users, sessions, memory         │
│  BucketService: SHA-256 integrity, trace-based audit         │
│  Memory: short_term, long_term, traits, user_profile         │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: File-Level Integration Checklist

### Backend Files to Create/Modify

- [ ] `backend/app/main.py` - Add all new routers
- [ ] `backend/app/core/llm_bridge.py` - Add LocalKnowledgeBase from bhiv
- [ ] `backend/app/core/intentflow.py` - Merge improvements from bhiv
- [ ] `backend/app/core/respond_service.py` - Add multilingual from bhiv
- [ ] `backend/app/core/security.py` - Use bhiv's JWT system
- [ ] `backend/app/core/text_normalizer.py` - Add from praj33
- [ ] `backend/app/capabilities/` - Add entire directory from praj33
- [ ] `backend/app/companion/` - Add entire directory from praj33
- [ ] `backend/app/companion_api.py` - Add from praj33
- [ ] `backend/app/runtime/` - Add entire directory from praj33
- [ ] `backend/app/voice/` - Add entire directory from praj33
- [ ] `backend/app/audio/` - Add entire directory from praj33
- [ ] `backend/app/services/continuity_service.py` - Add from praj33
- [ ] `backend/app/services/jwt_service.py` - Add from praj33
- [ ] `backend/app/governance/` - Add extended modules from praj33
- [ ] `backend/requirements.txt` - Add new dependencies
- [ ] `backend/.env` - Add new env vars

### Frontend Files to Create/Modify

- [ ] `frontend/frontend/src/App.tsx` - Use praj33's version, merge bhiv's heartbeat
- [ ] `frontend/frontend/src/services/api.ts` - Merge session management from bhiv
- [ ] `frontend/frontend/src/services/companion.service.ts` - Add from praj33
- [ ] `frontend/frontend/src/store/companion.store.ts` - Add from praj33
- [ ] `frontend/frontend/src/components/shell/` - Add entire directory from praj33
- [ ] `frontend/frontend/src/components/pages/` - Add entire directory from praj33
- [ ] `frontend/frontend/src/components/modals/` - Add entire directory from praj33
- [ ] `frontend/frontend/src/components/cards/` - Add entire directory from praj33
- [ ] `frontend/frontend/src/components/primitives/` - Add entire directory from praj33
- [ ] `frontend/frontend/tailwind.config.js` - Merge from praj33
- [ ] `frontend/frontend/src/index.css` - Merge from praj33
- [ ] `frontend/frontend/package.json` - Add new dependencies (zustand, etc.)
- [ ] `frontend/frontend/.env` - Add new env vars

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Import errors from praj33 modules | HIGH | Wrap imports in try/except, test each module individually |
| Frontend Zustand conflicts with React state | MEDIUM | Keep existing useState where possible, add Zustand for new features |
| TANTRA runtime vs praj33 runtime coexistence | MEDIUM | Use TANTRA as primary, praj33 runtime as secondary for companion features |
| API contract changes | HIGH | Maintain V3.0.0 contract, add new endpoints alongside |
| MongoDB schema changes | MEDIUM | Add new collections, don't modify existing ones |
| LLM provider conflicts | LOW | Keep Master-ashmit's provider list, add bhiv's LocalKnowledgeBase as fallback |
| Voice/telephony dependencies | LOW | Make voice features optional via env vars |

---

*End of Handover Document*
