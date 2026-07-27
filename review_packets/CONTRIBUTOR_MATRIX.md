# CONTRIBUTOR MATRIX

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 27, 2026  
**Prepared by:** Raj Prajapati (praj33)

---

## Team Contributors

| Contributor | GitHub Handle(s) | Role | Primary Repos | Total Repos | Local Clones |
|-------------|-----------------|------|---------------|:-----------:|:------------:|
| **Raj** | `praj33` | Full-stack Lead / Architect | MITRA (canonical), BHIV-Core-TANTRA, svacs-state-engine | 8 | ✅ Owner |
| **Ashmit** | `blackholeinfiverse37`, `sharmavijay45` | Bucket/Audit + BHIV Core | ai-being, v2-BHIV-Core, BHIV installments (2nd-5th), UniGuru variants | 27 | ✅ `_ecosystem_repos/ai-being` |
| **Pratham** | `great1239` | Companion Runtime / Runtime Ops | Mitra-Live-Runtime-Sprint, mitra-final-phase, bhiv-bucket, Companion-Runtime-Foundations, 10+ sprints | 16 | ✅ `_ecosystem_repos/companion-runtime`, `ecosystem-hardening` |
| **Chandresh** | ❓ Unknown | Execution Layer (WhatsApp/Email/Telegram executors) | Code embedded in MITRA `backend/app/executors/` — standalone repo not found | — | — |
| **Nilesh** | `Nilesh057` | Audio / Duplex Voice | Final_AI_ASSISTANT_with_Duplex_Audio | 1 | ✅ `_ecosystem_repos/duplex-audio` |
| **Akanksha** | `aa2kansha90` | Safety / Governance | AI-Being-Governance-Layer | 1 | ✅ `_ecosystem_repos/governance-layer` |
| **Sankalp/Eisha** | `eishasingh929-sudo` | Intelligence / UniGuru | uniguru_v2-main, uniguru_V2, setu-tantra-convergence, Uniguru_Robustness_Finalization | 7 | ✅ `_ecosystem_repos/uniguru-v2` |
| **Kanishk** | ❓ Unknown | Capability Runtime | Contract defined (KANISHK_INTERFACE_CONTRACT.md) — no repos found | 0 | — |
| **Soham** | ❓ Unknown | Audio Layer | Audio service referenced in code — no repos found | 0 | — |

---

## Code Ownership in Canonical MITRA Monorepo

### Backend (`backend/app/`)

| Module Path | Primary Owner | Secondary | Purpose |
|------------|--------------|-----------|---------|
| `companion/companion_orchestrator.py` | Raj | — | Central companion orchestration logic |
| `companion/companion_session.py` | Raj | — | Session lifecycle management |
| `companion/companion_memory.py` | Raj | — | Persistent memory engine |
| `companion/workflow_engine.py` | Raj | — | Multi-step workflow execution |
| `core/llm_bridge.py` | Raj | — | Multi-provider LLM abstraction |
| `core/intentflow.py` | Raj | — | Intent detection and routing |
| `services/safety_service.py` | Akanksha | Raj | Safety validation pipeline |
| `services/intelligence_service.py` | Sankalp | Raj | Intelligence layer |
| `services/enforcement_service.py` | Raj | — | Enforcement engine (allow/block/rewrite) |
| `services/execution_service.py` | Chandresh | Raj | Capability execution |
| `services/bucket_service.py` | Ashmit | Raj | Bucket audit logging |
| `services/audio_service.py` | Soham | Raj | Audio STT/TTS |
| `services/multilingual_service.py` | Soham | Raj | Multilingual support |
| `core/assistant_orchestrator.py` | Nilesh | Raj | Assistant orchestration |
| `capabilities/*.py` (11 files) | Raj | — | All 11 capabilities |
| `routers/pages.py` | Raj | — | REST endpoints for dashboard pages |

### Frontend (`frontend/frontend/src/`)

| Module Path | Primary Owner | Purpose |
|------------|--------------|---------|
| `App.tsx` | Raj | Shell + page routing |
| `components/shell/*.tsx` (9 files) | Raj | TopBar, Sidebar, InputBar, ConversationCenter, ContextPanel, NotificationDropdown, SettingsModal, Toast |
| `components/pages/*.tsx` (5 files) | Raj | Calendar, Tasks, Reminders, Knowledge, Workflows |
| `store/companion.store.ts` | Raj | Zustand state management |
| `services/companion.service.ts` | Raj | API service layer |
| `index.css` | Raj | 1100+ lines design system |

---

## GitHub Handle Discovery Log

| Handle | Method | Owner | Confidence |
|--------|--------|-------|:----------:|
| `praj33` | Owner — verified | Raj | 🟢 100% |
| `sharmavijay45` | Local clones found | Ashmit | 🟢 100% |
| `blackholeinfiverse37` | `_ecosystem_repos/ai-being` remote | Ashmit | 🟢 100% |
| `great1239` | `_ecosystem_repos/companion-runtime` remote | Pratham | 🟢 100% |
| `Nilesh057` | `_ecosystem_repos/duplex-audio` remote | Nilesh | 🟢 100% |
| `aa2kansha90` | `_ecosystem_repos/governance-layer` remote | Akanksha | 🟢 100% |
| `eishasingh929-sudo` | `_ecosystem_repos/uniguru-v2` remote | Sankalp/Eisha | 🟢 100% |

