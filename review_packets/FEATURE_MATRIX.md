# FEATURE MATRIX

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 27, 2026  
**Prepared by:** Raj Prajapati (praj33)

---

## Feature Implementation Map

| Feature | MITRA (praj33) | ai-being (Ashmit) | Companion-Runtime (Chandresh) | Duplex-Audio (Nilesh) | Governance (Akanksha) | UniGuru-v2 (Sankalp) | BHIV-Core (Ashmit) |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Safety Pipeline** | ✅ | — | — | — | ✅ | — | — |
| **Intelligence Layer** | ✅ | — | — | — | — | ✅ | — |
| **Enforcement Engine** | ✅ | — | — | — | ✅ | — | — |
| **Execution Service** | ✅ | — | — | — | — | — | — |
| **Bucket/Audit Logging** | ✅ | — | — | — | — | — | ✅ |
| **Companion Orchestrator** | ✅ | — | ⚠️ | — | — | — | — |
| **Session Management** | ✅ | — | ⚠️ | — | — | — | — |
| **Persistent Memory** | ✅ | — | — | — | — | — | — |
| **Personality Engine** | ✅ | — | — | — | — | — | — |
| **Capability Registry (11)** | ✅ | — | — | — | — | — | — |
| **Workflow Engine** | ✅ | — | — | — | — | — | — |
| **Multi-LLM Bridge** | ✅ | — | — | — | — | — | — |
| **UniGuru Integration** | ✅ | — | — | — | — | ✅ | — |
| **Responsive Frontend** | ✅ | — | — | — | — | — | — |
| **6-Page Dashboard** | ✅ | — | — | — | — | — | — |
| **Dark/Light Theme** | ✅ | — | — | — | — | — | — |
| **Notification System** | ✅ | — | — | — | — | — | — |
| **Toast Notifications** | ✅ | — | — | — | — | — | — |
| **Voice Input (Web Speech)** | ✅ | — | — | ✅ | — | — | — |
| **Duplex Audio / STT / TTS** | ✅ | — | — | ✅ | — | — | — |
| **WhatsApp Integration** | ✅ | — | — | ✅ | — | — | — |
| **Telegram Integration** | ✅ | — | — | — | — | — | — |
| **Email Integration** | ✅ | — | — | — | — | — | — |
| **Telephony** | ✅ | — | — | — | — | — | — |
| **TANTRA Chain** | ✅ (via BHIV-Core-TANTRA) | — | ⚠️ | — | — | ⚠️ | ✅ |
| **State Engine** | ✅ (svacs-state-engine) | — | — | — | — | — | — |
| **Auth (Signup/Login)** | ✅ | — | — | — | — | — | — |
| **API Key Middleware** | ✅ | — | — | — | — | — | — |
| **Health Monitoring** | ✅ | — | — | — | — | — | — |
| **Settings Modal** | ✅ | — | — | — | — | — | — |

Legend: ✅ = Implemented | ⚠️ = Partial/Unknown overlap | — = Not present

---

## Feature Convergence Status

| Feature Area | Canonical Location | External Repos | Action Needed |
|-------------|-------------------|----------------|---------------|
| Full Backend | `MITRA/backend/app/` | ai-assistant-backend, control-plane | ✅ Already merged |
| Companion Layer | `MITRA/backend/app/companion/` | Companion-Runtime-Foundations | ⚠️ Review for unique logic |
| All 11 Capabilities | `MITRA/backend/app/capabilities/` | workflow-executor | ✅ Already merged |
| Frontend Dashboard | `MITRA/frontend/frontend/` | — | ✅ Canonical |
| UniGuru | API integration in MITRA | uniguru_v2-main (source) | ⚠️ Source repo is external |
| Voice/Audio | `MITRA/services/audio_service.py` | Final_AI_ASSISTANT_with_Duplex_Audio | ⚠️ Review Nilesh's implementation |
| Governance | `MITRA/services/enforcement_service.py` | AI-Being-Governance-Layer | ⚠️ Review Akanksha's implementation |
| BHIV Core / TANTRA | `BHIV-Core-TANTRA-Sutradhar` | 6+ BHIV repos (Ashmit) | 🔴 Needs canonical designation |
| State Engine | `svacs-state-engine` | — | ⚠️ Standalone — integration planned |

---

## Feature Gaps

| Missing Feature | Required For | Likely Owner |
|----------------|-------------|-------------|
| Production MongoDB schemas | Live data on all pages | Raj |
| Persistent user auth (JWT alignment) | Multi-user sessions | Raj |
| Capability runtime service | Dynamic capability loading | Kanishk |
| Device gateway / platform adapters | Cross-platform execution | Chandresh |
| Text risk scoring service (source) | Safety pipeline | Akanksha |
