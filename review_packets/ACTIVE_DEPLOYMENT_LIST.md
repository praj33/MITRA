# ACTIVE DEPLOYMENT LIST

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 27, 2026  
**Prepared by:** Raj Prajapati (praj33)

---

## Confirmed Active Deployments

| # | Service | Platform | URL | Owner | Source Repo | Status |
|---|---------|----------|-----|-------|------------|--------|
| 1 | **UniGuru v2 API** | Render | `https://uniguru-v2.onrender.com` | Sankalp/Eisha | `eishasingh929-sudo/uniguru_v2-main` | 🟢 Active — used by MITRA's `llm_bridge.py` |
| 2 | **Text Risk Scoring** | Render | `https://text-risk-scoring-service.onrender.com` | Akanksha (?) | Unknown — not in public repos | 🟢 Active — referenced in browser |

---

## Local Development Servers

| # | Service | Port | URL | Source |
|---|---------|------|-----|--------|
| 3 | **MITRA Backend** | 8000 | `http://localhost:8000` | `praj33/MITRA` → `backend/` |
| 4 | **MITRA Frontend** | 3000 | `http://localhost:3000` | `praj33/MITRA` → `frontend/frontend/` |

---

## Legacy Deployments (Status Unknown)

| # | Service | Platform | URL | Owner | Source Repo | Status |
|---|---------|----------|-----|-------|------------|--------|
| 5 | AI Assistant Backend (8hur) | Render | `https://ai-assistant-backend-8hur.onrender.com` | Raj | `praj33/ai-assistant-backend` | ⚠️ Legacy — likely offline |
| 6 | AI Assistant Backend (70rt) | Render | `https://ai-assistant-backend-70rt.onrender.com` | Raj | `praj33/ai-assistant-backend` | ⚠️ Legacy — test reference |
| 7 | AI Assistant (yykb) | Render | `https://ai-assistant-yykb.onrender.com` | Unknown | Unknown | ⚠️ CORS-listed only |
| 8 | AI Assistant Frontend | Render | `https://ai-assistant-frontend.onrender.com` | Unknown | Unknown | ⚠️ CORS-listed only |

---

## Planned Production Deployments

| # | Service | Platform | URL | Source Repo | Status |
|---|---------|----------|-----|------------|--------|
| 9 | **Mitra Backend** | Render | `https://mitra-backend.onrender.com` | `praj33/MITRA` | 📋 Planned |
| 10 | **Mitra Frontend** | Vercel | `https://mitra-frontend.vercel.app` | `praj33/MITRA` | 📋 Planned |

---

## Deployment Ownership Gaps

> [!IMPORTANT]
> The following deployed services have **unconfirmed ownership or missing source repos**:

| URL | Referenced In | Action Required |
|-----|-------------|-----------------|
| `uniguru-v2.onrender.com` | `llm_bridge.py`, `.env` | ✅ Confirmed — `eishasingh929-sudo/uniguru_v2-main` |
| `text-risk-scoring-service.onrender.com` | Browser tab | ❌ Akanksha must share source repo |
| `ai-assistant-yykb.onrender.com` | `assistant.py` CORS | ❌ Team must identify owner |
| `ai-assistant-frontend.onrender.com` | `assistant.py` CORS | ❌ Team must identify owner |

---

## Infrastructure Stack

| Component | Provider | Notes |
|-----------|----------|-------|
| Backend hosting | Render (free tier) | Subject to cold starts |
| Frontend hosting | Vercel (planned) | — |
| Database | MongoDB Atlas | Connection string in `.env` |
| LLM providers | Groq (primary), OpenAI, Google Gemini, Mistral | Keys in `.env` |
| UniGuru API | Render | External dependency |
