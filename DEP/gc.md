# Governance & Control Plane (GC) — Phase 1 Convergence

> **System**: MITRA Universal Companion Layer  
> *Governance Model*: BHIV Ecosystem Canonical Governance  

---

## 1. Governance Architecture

MITRA operates strictly as the **Companion & Control Plane Layer**. It routes:
1. **Intelligence Queries** → UniGuru Rule Engine (`app.uniguru`)
2. **Capability Actions** → TANTRA Governed Runtime (`app.services.tantra_client`)
3. **Audit Provenance** → Bucket & Replay Logging (`app.services.bucket_service`)

```
User / Web App
      ↓
MITRA Companion (mitra-hover.js / App.tsx)
      ↓
Control Plane (/api/companion/*)
      ↓
 ┌────┴──────────────────────────┐
 ↓                               ↓
UniGuru Intelligence      TANTRA Runtime Engine
(Deterministic Snapshot)  (Capability Runtime - Kanishk)
                                 ↓
                           Bucket & Replay
```

---

## 2. Governance Rules Enforced by UniGuru
- **Safety Enforcement**: Query policy verification prior to execution.
- **Authority Levels**: Tiered execution permissions (`user`, `admin`, `system`).
- **Delegation Control**: Capability routing restrictions.
- **Emotional & Ambiguity Calibration**: Response fallback rules.
