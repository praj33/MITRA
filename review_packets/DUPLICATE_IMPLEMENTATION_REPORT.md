# DUPLICATE IMPLEMENTATION REPORT

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 16, 2026

---

## Identified Duplications

### 1. Safety → Intelligence → Enforcement Pipeline

| Repository | Location | Status |
|-----------|----------|--------|
| **MITRA** (canonical) | `backend/app/services/{safety,intelligence,enforcement}_service.py` | ✅ Active |
| ai-assistant-backend | Standalone repo — same services | ⚠️ **SUPERSEDED** — merged into MITRA |
| mitra-bhiv-control-plane | Standalone control plane — same pipeline | ⚠️ **SUPERSEDED** — merged into MITRA |

**Resolution:** Already converged. `ai-assistant-backend` and `mitra-bhiv-control-plane` are frozen predecessors. Mark as archived.

---

### 2. Enforcement Engine

| Repository | Location | Status |
|-----------|----------|--------|
| **MITRA** (canonical) | `backend/app/services/enforcement_service.py` | ✅ Active |
| ai-being-enforcement | `https://github.com/praj33/ai-being-enforcement.git` | ⚠️ **SUPERSEDED** |

**Resolution:** Enforcement logic is now in MITRA's `enforcement_service.py`. The standalone repo was an early implementation. Mark as archived.

---

### 3. Workflow Execution

| Repository | Location | Status |
|-----------|----------|--------|
| **MITRA** (canonical) | `backend/app/companion/workflow_engine.py` | ✅ Active |
| workflow-executor | `https://github.com/praj33/workflow-executor.git` | ⚠️ **SUPERSEDED** |

**Resolution:** Workflow logic merged and enhanced in MITRA's companion layer. Standalone repo is obsolete. Mark as archived.

---

### 4. BHIV Core (Multiple Clones)

| Location | Remote | Status |
|----------|--------|--------|
| `Desktop/BHIV-Core/` | None (no commits) | ❌ Empty skeleton |
| `Desktop/BHIV-Core/BHIV-Core/` | None | ❌ Nested empty |
| `Downloads/BHIV-Core/` | None | ❌ No remote |
| `Downloads/bhiv_core/` | `sharmavijay45/bhiv_core` | ⚠️ Different from Desktop version |
| `Documents/bhiv_core second installment/` | `sharmavijay45/BHIV-Second-Installment` | ⚠️ Unknown relationship |
| **BHIV-Core-TANTRA-Sutradhar** | `praj33/BHIV-Core-TANTRA-Sutradhar` | ✅ Active |

**Resolution:** 4 local BHIV clones are stale/empty. Only `BHIV-Core-TANTRA-Sutradhar` is the active version. Ashmit's repos need clarification on which is canonical.

---

### 5. Deployment URLs (Multiple Render Services)

| URL | Purpose | Status |
|-----|---------|--------|
| `ai-assistant-backend-8hur.onrender.com` | Legacy backend deployment | ⚠️ Likely stale |
| `ai-assistant-backend-70rt.onrender.com` | Alternate backend deployment | ⚠️ Likely stale |
| `ai-assistant-yykb.onrender.com` | CORS-listed frontend | ⚠️ Unknown |
| `ai-assistant-frontend.onrender.com` | CORS-listed frontend | ⚠️ Unknown |
| `uniguru-v2.onrender.com` | UniGuru API | 🟢 Active (used by LLM bridge) |

**Resolution:** Clean up old deployment URLs from code. Confirm which are still live.

---

## Overlapping Features (Potential)

> [!WARNING]
> **Cannot fully assess** without access to other team members' repos. The following overlaps are suspected based on code references:

| Feature | MITRA has it | Possible external repo |
|---------|:----------:|----------------------|
| Safety validation | ✅ `safety_service.py` | Akanksha may have standalone `behavior_validator` repo |
| Intelligence core | ✅ `intelligence_service.py` | Sankalp may have standalone `AI-BEING-INTELLIGENCE-LAYER` repo |
| UniGuru v2 | ✅ API integration | Sankalp likely has the UniGuru source repo |
| Text risk scoring | ❌ Referenced only | Akanksha likely owns `text-risk-scoring-service` (Render) |
| Audio/TTS | ✅ `audio_service.py` | Soham may have standalone audio processing repo |

---

## Abandoned / Dead Builds

| Repository | Last Activity | Reason |
|-----------|--------------|--------|
| `Desktop/BHIV-Core/` | Never committed | Empty skeleton |
| `Desktop/BHIV-Core/BHIV-Core/` | Never committed | Nested empty |
| `Downloads/BHIV-Core/` | Unknown | No remote, unclear purpose |

---

## Reusable Components

| Component | Source | Can Be Reused In |
|-----------|--------|------------------|
| `BaseCapability` abstract class | MITRA | Any capability system |
| `CapabilityRegistry` | MITRA | Plugin architectures |
| `LLMBridge` multi-provider | MITRA | Any LLM-consuming service |
| `PersonalityEngine` | MITRA | Any companion/chatbot |
| `WorkflowEngine` | MITRA | Any multi-step automation |
| TANTRA execution chain | BHIV-Core-TANTRA | Governance-aware agent systems |
| State Engine | svacs-state-engine | Event-to-state mapping systems |
