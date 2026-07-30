# Blockers & Resolution Log — Phase 1 Convergence

| Blocker Description | Impact | Resolution Status | Resolution Action |
|---|---|---|---|
| **UniGuru ImportError / Missing Snapshot** | High (Engine crash on startup) | ✅ Resolved | Bootstrapped `snapshot_v1.json` via `SnapshotManager` & fixed package import paths in `app/uniguru`. |
| **Vercel Build Failure** | High (Deployment stalled) | ✅ Resolved | Added root `vercel.json` and `package.json` pointing to `frontend/frontend/build`. |
| **Mobile Bottom Nav Vertical Collapse** | Medium (UI broken on smartphones) | ✅ Resolved | Standardized `.mobile-bottom-nav` CSS rules (`flex-direction: row !important; width: 100%`). |
| **Mobile Microphone STT & Audio TTS** | Medium (Voice input silent on iOS) | ✅ Resolved | Added `getUserMedia` permission prompt and inline `playsinline` speech audio playback. |
