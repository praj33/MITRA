# DUPLICATE IMPLEMENTATION REPORT

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 27, 2026  
**Prepared by:** Raj Prajapati (praj33)

---

## 1. BHIV Core — 7+ Versions Across 2 Accounts

> [!CAUTION]
> **Highest duplication risk.** Multiple BHIV Core implementations exist across Ashmit's two accounts. Canonical version must be designated.

| Repository | Owner | Account | Status |
|-----------|-------|---------|--------|
| `v1-BHIV_CORE` | Ashmit | `sharmavijay45` | ⚠️ Likely superseded |
| `v2-BHIV-Core` | Ashmit | `sharmavijay45` | ⚠️ Likely latest |
| `bhiv_core` | Ashmit | `sharmavijay45` | ⚠️ Base version |
| `BHIV-Second-Installment` | Ashmit | `sharmavijay45` | ⚠️ Installment |
| `BHIV-Third-Installment` | Ashmit | `sharmavijay45` | ⚠️ Installment |
| `BHIV-5th-Installment` | Ashmit | `sharmavijay45` | ⚠️ Installment |
| `BHIV-Core-TANTRA-Sutradhar` | Raj | `praj33` | ✅ Active (TANTRA chain) |

**Resolution needed:** Ashmit must confirm which BHIV Core is canonical. All others should be archived.

---

## 2. UniGuru — 5+ Versions Across 2 Accounts

| Repository | Owner | Account | Status |
|-----------|-------|---------|--------|
| `uniguru_v2-main` | Sankalp/Eisha | `eishasingh929-sudo` | ✅ Deployed to Render |
| `uniguru_V2` | Sankalp/Eisha | `eishasingh929-sudo` | ⚠️ Possible duplicate |
| `Uniguru_Robustness_Finalization` | Sankalp/Eisha | `eishasingh929-sudo` | ⚠️ Testing fork |
| `uniguru` | Ashmit | `sharmavijay45` | ⚠️ Older version |
| `Enhanced-Uni-Guru` | Ashmit | `sharmavijay45` | ⚠️ Enhanced version |
| `Complete-Uniguru` | Ashmit | `sharmavijay45` | ⚠️ Complete version |

**Resolution:** `eishasingh929-sudo/uniguru_v2-main` is the active deployment. All others should be reviewed for unique features, then archived.

---

## 3. Safety / Intelligence / Enforcement Pipeline — 3 Superseded

| Repository | Owner | Status |
|-----------|-------|--------|
| **MITRA** (canonical) | Raj | ✅ `backend/app/services/{safety,intelligence,enforcement}_service.py` |
| `ai-assistant-backend` | Raj | ⚠️ **SUPERSEDED** — merged into MITRA |
| `mitra-bhiv-control-plane` | Raj | ⚠️ **SUPERSEDED** — merged into MITRA |
| `ai-being-enforcement` | Raj | ⚠️ **SUPERSEDED** — merged into MITRA |

**Resolution:** ✅ Already converged. Legacy repos should be archived.

---

## 4. Companion / Runtime Foundations — Overlapping

| Repository | Owner | Status |
|-----------|-------|--------|
| **MITRA** (canonical) | Raj | ✅ `backend/app/companion/` — full orchestrator, session, memory, workflow |
| `Companion-Runtime-Foundations` | Pratham | ⚠️ Separate companion runtime — may overlap |
| `Mitra-Live-Runtime-Sprint` | Pratham | ⚠️ Runtime sprint — may contain companion patches |
| `mitra-final-phase` | Pratham | ⚠️ Final phase convergence |

**Resolution needed:** Review Pratham's repos for unique runtime logic not in canonical MITRA. Merge or archive.

---

## 5. Workflow Execution — 4 Versions

| Repository | Owner | Status |
|-----------|-------|--------|
| **MITRA** (canonical) | Raj | ✅ `companion/workflow_engine.py` |
| `workflow-executor` | Raj | ⚠️ **SUPERSEDED** — merged into MITRA |
| `main-workflow` | Ashmit | ⚠️ Unknown status |
| `Workflow0` | Ashmit | ⚠️ Unknown status |
| `workflow_ai_agents` | Ashmit | ⚠️ Unknown status |

**Resolution needed:** Ashmit's workflow repos should be reviewed for unique logic, then archived.

---

## 6. Governance Layer — Separate Implementation

| Repository | Owner | Status |
|-----------|-------|--------|
| **MITRA** (canonical) | Raj | ✅ Enforcement + safety in `services/` |
| `AI-Being-Governance-Layer` | Akanksha | ⚠️ Separate governance implementation |

**Resolution needed:** Compare Akanksha's governance layer with MITRA's enforcement service. Merge unique logic.

---

## 7. AI Being Core

| Repository | Owner | Status |
|-----------|-------|--------|
| `ai-being` | Ashmit (`blackholeinfiverse37`) | ✅ Core AI Being repo |
| `ai-being-enforcement` | Raj | ⚠️ **SUPERSEDED** — enforcement only |
| `AI-Being-Governance-Layer` | Akanksha | ⚠️ Governance only |

**Resolution needed:** Ashmit's `ai-being` should be the canonical AI Being repo. Others are feature-specific forks.

---

## 8. TANTRA / SHAKTI — Multiple Sprint Repos

| Repository | Owner | Purpose |
|-----------|-------|---------|
| `BHIV-Core-TANTRA-Sutradhar` | Raj | ✅ Active TANTRA chain |
| `SHAKTI-TANTRA-Operationalization-Sprint` | Pratham | Sprint deliverable |
| `tantra-evidence-integration` | Pratham | Evidence integration |
| `setu-tantra-convergence` | Sankalp/Eisha | Setu convergence |

**Resolution needed:** Consolidate TANTRA work from Pratham and Sankalp into Raj's canonical repo.

---

## Summary: Duplication Heat Map

| Area | Duplicate Count | Risk | Owner(s) |
|------|:--------------:|:----:|----------|
| BHIV Core | 7+ | 🔴 HIGH | Ashmit, Raj |
| UniGuru | 5+ | 🔴 HIGH | Sankalp/Eisha, Ashmit |
| Safety/Enforcement | 3 | 🟢 RESOLVED | Raj |
| Companion Runtime | 4 | 🟡 MEDIUM | Raj, Pratham |
| Workflow | 4 | 🟡 MEDIUM | Raj, Ashmit |
| Governance | 2 | 🟡 MEDIUM | Raj, Akanksha |
| TANTRA/SHAKTI | 4 | 🟡 MEDIUM | Raj, Pratham, Sankalp |

> [!IMPORTANT]
> **Total: 29+ duplicate/overlapping repositories** across the ecosystem. Only 3 duplications (Safety/Enforcement) have been resolved via merge into canonical MITRA.
