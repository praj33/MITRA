# Changed Files Inventory — Phase 1 Convergence

The following files represent the core changes implemented for Phase 1 Convergence:

1. `backend/app/uniguru/enforcement/enforcement.py` (Fixed verifier imports & rule enforcement)
2. `backend/app/uniguru/ontology/__init__.py` (Fixed relative package imports)
3. `backend/app/uniguru/reasoning/__init__.py` (Fixed relative package imports)
4. `backend/app/uniguru/ontology/snapshots/snapshot_v1.json` (Bootstrapped deterministic rule snapshot)
5. `backend/app/api/companion_api.py` (Implemented `/api/companion/auth`, `/api/companion/state`, `/api/companion/execute`)
6. `backend/app/main.py` (Mounted `/static/mitra-hover.js` static assets & security exclusions)
7. `frontend/frontend/src/App.tsx` (Fixed mobile bottom navbar grid area & bottom scroll padding)
8. `frontend/frontend/src/index.css` (Fixed mobile navbar flex-row layout & snap-scrolling calendar week strip)
9. `frontend/frontend/src/components/shell/InputBar.tsx` (Fixed microphone `getUserMedia` permissions)
10. `frontend/frontend/public/mitra-hover.js` (Created standalone 1-line HTML embed companion widget)
11. `vercel.json` & `package.json` (Created root Vercel auto-deployment build configuration)
12. `docs/EMBED_GUIDE.md` (Created external BHIV product integration guide)
