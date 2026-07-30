# Module Dependency & Utilization (MDU) — Phase 1 Convergence

---

## 1. Module Mapping

| Module Name | Path | Purpose | Dependencies |
|---|---|---|---|
| **Companion API** | `backend/app/api/companion_api.py` | Canonical REST API | FastAPI, Pydantic |
| **UniGuru Engine** | `backend/app/uniguru/` | Deterministic Intelligence | `snapshot_v1.json`, Pydantic |
| **TANTRA Client** | `backend/app/services/tantra_client.py` | Governed Execution Client | httpx, asyncio |
| **Bucket Service** | `backend/app/services/bucket_service.py` | Provenance & Replay Logging | JSON / DB |
| **Hover Widget** | `frontend/frontend/public/mitra-hover.js` | Universal Embed | Vanilla JS (Shadow-free DOM) |
| **React Companion UI** | `frontend/frontend/src/` | Full-screen Companion Shell | React 18, Tailwind, Framer Motion |

---

## 2. Dependency Graph
```
App.tsx / mitra-hover.js
   └── companion_api.py
         ├── companion_orchestrator.py
         │     ├── UniGuru (RuleEngine / snapshot_v1.json)
         │     └── tantra_client.py
         │           └── Bucket & Replay
         └── companion_memory.py
```
