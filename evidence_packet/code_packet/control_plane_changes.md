# Control Plane Changes — Phase 1 Convergence

---

## 1. Updates to Control Plane
- Bound canonical endpoints in `backend/app/api/companion_api.py`.
- Enforced single routing orchestrator (`CompanionOrchestrator`) for all incoming user queries.
- Mounted `/static/mitra-hover.js` in `main.py` without auth restrictions for seamless cross-app frontend loading.
