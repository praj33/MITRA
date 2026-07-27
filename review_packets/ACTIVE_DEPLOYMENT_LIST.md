# ACTIVE DEPLOYMENT LIST

**Ecosystem:** BHIV / MITRA / AI Being  
**Last Updated:** July 16, 2026

---

## Confirmed Active Deployments

| # | Service | Platform | URL | Owner | Source Repo | Status |
|---|---------|----------|-----|-------|------------|--------|
| 1 | **UniGuru v2 API** | Render | `https://uniguru-v2.onrender.com` | Sankalp (?) | ❓ Unknown | 🟢 Active — called by MITRA's `llm_bridge.py` |
| 2 | **Text Risk Scoring** | Render | `https://text-risk-scoring-service.onrender.com` | Akanksha (?) | ❓ Unknown | 🟢 Active — seen in browser tabs |

---

## Known Legacy Deployments (Status Unknown)

| # | Service | Platform | URL | Owner | Source Repo | Status |
|---|---------|----------|-----|-------|------------|--------|
| 3 | AI Assistant Backend (8hur) | Render | `https://ai-assistant-backend-8hur.onrender.com` | Raj | `praj33/ai-assistant-backend` | ⚠️ Legacy — may be offline |
| 4 | AI Assistant Backend (70rt) | Render | `https://ai-assistant-backend-70rt.onrender.com` | Raj | `praj33/ai-assistant-backend` | ⚠️ Legacy — test reference |
| 5 | AI Assistant Frontend (yykb) | Render | `https://ai-assistant-yykb.onrender.com` | Unknown | ❓ Unknown | ⚠️ CORS-listed, unknown |
| 6 | AI Assistant Frontend | Render | `https://ai-assistant-frontend.onrender.com` | Unknown | ❓ Unknown | ⚠️ CORS-listed, unknown |

---

## Planned / Target Deployments

| # | Service | Platform | URL | Source Repo | Status |
|---|---------|----------|-----|------------|--------|
| 7 | **Mitra Backend** | Render | `https://mitra-backend.onrender.com` | `praj33/MITRA` | 📋 Planned |
| 8 | **Mitra Frontend** | Vercel | `https://mitra-frontend.vercel.app` | `praj33/MITRA` | 📋 Planned |

---

## Deployment Ownership Gaps

> [!IMPORTANT]
> The following deployments are referenced in code but **ownership and source repos are unconfirmed**:

| URL | Referenced In | Owner Needed |
|-----|-------------|-------------|
| `uniguru-v2.onrender.com` | `llm_bridge.py`, `.env` | Sankalp must confirm |
| `text-risk-scoring-service.onrender.com` | Browser tab (user session) | Akanksha must confirm |
| `ai-assistant-yykb.onrender.com` | `assistant.py` CORS list | Team must identify |
| `ai-assistant-frontend.onrender.com` | `assistant.py` CORS list | Team must identify |

---

## Infrastructure Notes

- All backend services use **Render** (free tier — subject to cold starts)
- Frontend intended for **Vercel** deployment
- Database: **MongoDB Atlas** (connection string in `.env`)
- LLM providers: Groq (primary), OpenAI, Google Gemini, Mistral (keys in `.env`)
