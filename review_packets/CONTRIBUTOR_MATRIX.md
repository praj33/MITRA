# CONTRIBUTOR MATRIX

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 16, 2026

---

## Contributor Ownership Map

| Contributor | GitHub Handle | Email | Primary Role | Modules Owned | Repos Confirmed |
|-------------|--------------|-------|-------------|---------------|-----------------|
| **Raj Prajapati** | `praj33` | rajprajapati8286@gmail.com | Enforcement + Product + Companion | enforcement_service, companion layer, capability hub, workflow engine, LLM bridge, frontend responsive | ✅ 8 MITRA-related repos |
| **Yashika Tirkey** | `yashikart` | yashikartirkey@gmail.com | Frontend | React shell, component primitives, initial UI | ✅ Commits in MITRA repo |
| **Ashmit / Vijay Sharma** | `sharmavijay45` | blackholeinfiverse45@gmail.com | Bucket/Audit + Convergence | bucket_service, audit logging, BHIV Core | ⚠️ 2 repos found (local clones) |
| **Akanksha** | ❓ Unknown | ❓ | Safety Layer | safety_service, behavior_validator | ❌ No repos discovered |
| **Sankalp** | ❓ Unknown | ❓ | Intelligence Layer | intelligence_service, UniGuru v2 | ❌ No repos discovered |
| **Nilesh** | ❓ Unknown | ❓ | Orchestration | assistant_orchestrator | ❌ No repos discovered |
| **Chandresh** | ❓ Unknown | ❓ | Execution Layer | execution_service, device gateway | ❌ No repos discovered |
| **Soham** | ❓ Unknown | ❓ | Audio Layer | audio_service, multilingual_service | ❌ No repos discovered |
| **Kanishk** | ❓ Unknown | ❓ | Capability Runtime | Runtime service (contract defined, not built) | ❌ No repos discovered |
| **Pratham** | ❓ Unknown | ❓ | Product / Design | Design system, IA, UX wireframes | ❌ No repos discovered |

---

## Code Ownership in Canonical MITRA Repo

### Backend (`backend/app/`)

| Module Path | Primary Owner | Secondary | Lines |
|------------|--------------|-----------|-------|
| `services/safety_service.py` | Akanksha | Raj | ~100 |
| `services/intelligence_service.py` | Sankalp | Raj | ~120 |
| `services/enforcement_service.py` | Raj | — | ~150 |
| `services/execution_service.py` | Chandresh | Raj | ~200 |
| `services/bucket_service.py` | Ashmit | Raj | ~250 |
| `services/audio_service.py` | Soham | Raj | ~80 |
| `services/multilingual_service.py` | Soham | Raj | ~100 |
| `core/assistant_orchestrator.py` | Nilesh | Raj | ~300 |
| `core/llm_bridge.py` | Raj | — | 259 |
| `core/intentflow.py` | Raj | — | ~150 |
| `companion/companion_orchestrator.py` | Raj | — | 288 |
| `companion/companion_session.py` | Raj | — | 250 |
| `companion/companion_memory.py` | Raj | — | 220 |
| `companion/personality_engine.py` | Raj | — | 159 |
| `companion/capability_registry.py` | Raj | — | 100 |
| `companion/workflow_engine.py` | Raj | — | 298 |
| `capabilities/*.py` (11 files) | Raj | — | ~200 ea |

### Frontend (`frontend/frontend/src/`)

| Module Path | Primary Owner | Secondary |
|------------|--------------|-----------|
| `components/shell/*` | Yashika | Raj (responsive) |
| `components/cards/*` | Yashika | Raj (responsive) |
| `store/companion.store.ts` | Raj | Yashika |
| `services/*` | Raj | — |
| `index.css` | Raj | Yashika |
| `App.tsx` | Raj | Yashika |

---

## Visibility Gaps

> [!CAUTION]
> **6 of 10 contributors have NO discoverable repositories.** Their work exists only as integrated code within the MITRA monorepo or as undiscovered standalone repos. Each must self-report.

| Gap | Impact |
|-----|--------|
| Akanksha's safety repos unknown | Cannot verify if separate validator exists outside MITRA |
| Sankalp's intelligence repos unknown | UniGuru v2 deployed but source repo not documented |
| Nilesh's orchestration repos unknown | May have standalone orchestrator implementations |
| Chandresh's execution repos unknown | May have device/platform executor prototypes |
| Soham's audio repos unknown | May have standalone STT/TTS implementations |
| Kanishk's runtime repos unknown | Contract defined but implementation status unknown |
