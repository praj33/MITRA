# FEATURE MATRIX

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 16, 2026

---

## Feature Implementation Map

| Feature | MITRA Monorepo | ai-assistant-backend | mitra-bhiv-control-plane | ai-being-enforcement | svacs-state-engine | BHIV-Core-TANTRA |
|---------|:-------------:|:-------------------:|:------------------------:|:--------------------:|:------------------:|:----------------:|
| **Safety Pipeline** | ✅ | ✅ | ✅ | — | — | — |
| **Intelligence Layer** | ✅ | ✅ | ✅ | — | — | — |
| **Enforcement Engine** | ✅ | ✅ | ✅ | ✅ | — | — |
| **Execution Service** | ✅ | ✅ | — | — | — | — |
| **Bucket/Audit Logging** | ✅ | ✅ | ✅ | — | — | — |
| **Companion Orchestrator** | ✅ | — | — | — | — | — |
| **Session Management** | ✅ | — | — | — | — | — |
| **Persistent Memory** | ✅ | — | — | — | — | — |
| **Personality Engine** | ✅ | — | — | — | — | — |
| **Capability Registry** | ✅ | — | — | — | — | — |
| **11 Capabilities** | ✅ | — | — | — | — | — |
| **Workflow Engine** | ✅ | — | — | — | — | — |
| **Multi-LLM Bridge** | ✅ | Partial | — | — | — | — |
| **UniGuru Integration** | ✅ | — | — | — | — | — |
| **Responsive Frontend** | ✅ | — | — | — | — | — |
| **Mobile Bottom Nav** | ✅ | — | — | — | — | — |
| **Inbound WhatsApp** | ✅ | ✅ | — | — | — | — |
| **Inbound Telegram** | ✅ | ✅ | — | — | — | — |
| **Inbound Email** | ✅ | ✅ | — | — | — | — |
| **Inbound Telephony** | ✅ | ✅ | — | — | — | — |
| **Audio STT/TTS** | ✅ | ✅ | — | — | — | — |
| **Multilingual Support** | ✅ | ✅ | — | — | — | — |
| **State Engine** | — | — | — | — | ✅ | — |
| **TANTRA Chain** | — | — | — | — | — | ✅ |
| **Karma Adapter** | ✅ | — | — | — | — | — |
| **BHIV Gateway** | ✅ | — | — | — | — | — |
| **System Health** | ✅ | ✅ | — | — | — | — |
| **Auth (signup/login)** | ✅ | — | — | — | — | — |
| **Design System** | ✅ (docs) | — | — | — | — | — |

---

## Feature Convergence Status

| Feature Area | Canonical Location | Superseded Repos | Action |
|-------------|-------------------|------------------|--------|
| Safety + Intelligence + Enforcement | `MITRA/backend/app/services/` | `ai-assistant-backend`, `mitra-bhiv-control-plane`, `ai-being-enforcement` | ✅ Already merged |
| Companion Layer | `MITRA/backend/app/companion/` | None (new) | ✅ Canonical |
| Capability Hub | `MITRA/backend/app/capabilities/` | `workflow-executor` | ✅ Already merged |
| Frontend | `MITRA/frontend/frontend/` | None | ✅ Canonical |
| State Engine | `svacs-state-engine` | None | ⚠️ Standalone — needs integration plan |
| BHIV Core / TANTRA | `BHIV-Core-TANTRA-Sutradhar` | Empty desktop clone | ⚠️ Separate ecosystem — integration via gateway |
