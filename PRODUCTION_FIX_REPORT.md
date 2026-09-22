# MITRA Production Authentication & API Architecture Hardening Report

**Project**: MITRA Integrated Assistant
**Repository**: [praj33/MITRA](https://github.com/praj33/MITRA)
**Branch**: `feature/mitra-production-foundation`
**Target Environment**: Production (`https://mitra.blackholeinfiverse.com`)
**Date**: September 8, 2026
**Status**: Completed & Verified

---

## 1. Executive Summary

This report documents the architectural audit, hardening, and bug fixes implemented to resolve the critical production issue where chat messaging failed with:
```http
POST https://mitra.blackholeinfiverse.com/api/api/companion/chat
Status: 401 Unauthorized
```

All 17 phases of inspection, normalization, authentication synchronization, UI hardening, and test verification were executed directly in the working tree. The resulting implementation eliminates duplicate URL pathing, establishes a canonical JWT lifecycle, ensures authenticated requests send `Authorization: Bearer <JWT>`, connects Login to real backend OAuth/credentials, passes all 63 backend security tests, and compiles cleanly with zero frontend build errors or warnings.

---

## 2. Root Cause Analysis

### Issue A: Double API Path (`/api/api/companion/chat`)
- **Root Cause**: CI/CD (`.github/workflows/cicd.yml`) sets `--build-arg REACT_APP_API_URL=https://mitra.blackholeinfiverse.com/api`. Frontend service files concatenated this with `/api/companion/chat`, yielding an invalid double `/api/api/` route.
- **Remediation**: Built a centralized normalizer (`normalizeApiBase`) in `apiConfig.ts` that removes trailing slashes and any trailing `/api` (case-insensitive). Whether the environment supplies `https://mitra.blackholeinfiverse.com/api`, `https://mitra.blackholeinfiverse.com`, or `http://localhost:8000`, all endpoints resolve to single-prefixed paths: `${getApiBase()}/api/...`.

### Issue B: Missing `Authorization: Bearer <JWT>` Header
- **Root Cause**: The companion chat endpoint in `backend/app/api/companion_api.py` enforces `current_user: Dict[str, Any] = Depends(get_current_user)`. The frontend `companion.service.ts` only sent `X-API-Key` and omitted `Authorization: Bearer <JWT>`, triggering an immediate 401 response from the backend.
- **Remediation**: Created `getAuthHeaders()` in `apiConfig.ts`, which automatically injects `Authorization: Bearer <token>` when a token is present in storage, along with `X-API-Key` and `Content-Type: application/json`.

### Issue C: JWT Storage Key Fragmentation
- **Root Cause**: `AuthContext.tsx` and `authApi.ts` read and wrote `authToken`, whereas `companion.store.ts` and `App.tsx` checked `mitra_auth_token`. When a user logged in, `AuthContext` saved `authToken`, but the companion store and chat service never received it.
- **Remediation**: Standardized on **`mitra_auth_token`** as the canonical key. Implemented dual-write (`mitra_auth_token` and `authToken`) and fallback reading for seamless backward compatibility.

### Issue D: Auth State Disconnect
- **Root Cause**: Logging in updated React state in `AuthContext`, but failed to notify Zustand store (`useCompanionStore`), keeping the companion state unauthenticated.
- **Remediation**: Updated `AuthContext.tsx` to directly invoke `useCompanionStore.getState().setAuth(userData, token)` upon successful login, signup, and session restoration, and `logoutUser()` on logout.

### Issue E: Hardcoded Login Password & Insecure OAuth Fallbacks
- **Root Cause**: `Login.tsx` hardcoded `const [password] = useState('password123')` without a password input field, and hardcoded fake OAuth client IDs (`mitra-google-client-id...`, `com.mitra.app.signin`) pointing to `http://localhost:3000`.
- **Remediation**: Added a real password input with visibility toggle and validation. Replaced fake URLs with backend-driven OAuth initiation (`/api/oauth/{provider}/start?purpose=login`) with clean error handling.

### Issue F: Stale / Dead Render URLs
- **Root Cause**: Dead Render domains (`mitra-backend-q1f3.onrender.com` and `ai-assistant-backend-8hur.onrender.com`) lingered across `InputBar.tsx`, `ConversationCard.tsx`, and `App.tsx`.
- **Remediation**: Replaced all instances with `${getApiBase()}` routes.

---

## 3. Comprehensive File Changes

| File | Change Type | Summary of Changes |
| :--- | :--- | :--- |
| `frontend/frontend/src/services/apiConfig.ts` | **NEW** | Centralized API base normalizer, canonical token storage (`mitra_auth_token` + `authToken`), unified header builder, and error formatter. |
| `frontend/frontend/src/services/companion.service.ts` | **MODIFIED** | Connected chat and all 20+ companion/page endpoints to `getApiBase()` and `getAuthHeaders()`; added diagnostic error handling. |
| `frontend/frontend/src/services/authApi.ts` | **MODIFIED** | Switched `AUTH_BASE_URL` to `getApiBase()`; integrated `setAuthToken`, `getAuthToken`, `clearAuthToken`, and `getAuthHeaders()`. |
| `frontend/frontend/src/services/api.ts` | **MODIFIED** | Standardized base URL and request headers on `apiConfig`. |
| `frontend/frontend/src/contexts/AuthContext.tsx` | **MODIFIED** | Synced auth state across `apiConfig`, `AuthContext`, and Zustand `useCompanionStore`. |
| `frontend/frontend/src/store/companion.store.ts` | **MODIFIED** | Initialized state via `getAuthToken()`; synchronized `setAuth` and `logoutUser` with canonical token storage. |
| `frontend/frontend/src/components/auth/Login.tsx` | **MODIFIED** | Added real password input and validation; removed hardcoded password; routed OAuth to backend endpoints. |
| `frontend/frontend/src/App.tsx` | **MODIFIED** | Updated session recovery to use `getAuthToken()`; removed dead Render TTS URL fallback. |
| `src/services/controlPlane.js` | **MODIFIED** | Normalized base URL, added `Authorization: Bearer <token>` to `buildHeaders()`, removed `/api/api/` workaround. |
| `frontend/frontend/src/components/modals/IntegrationsModal.tsx` | **MODIFIED** | Used `getApiBase()` and `getAuthHeaders()` instead of un-normalized env variables. |
| `frontend/frontend/src/components/dashboard/BHIVDashboard.tsx` | **MODIFIED** | Used `getApiBase()` and `getAuthHeaders()`. |
| `frontend/frontend/src/components/dashboard/ReplayVisualization.tsx` | **MODIFIED** | Used `getApiBase()` and `getAuthHeaders()`. |
| `frontend/frontend/src/components/dashboard/SystemHealthPanel.tsx` | **MODIFIED** | Used `getApiBase()`. |
| `frontend/frontend/src/components/cards/ConversationCard.tsx` | **MODIFIED** | Replaced dead Render TTS URL with `${getApiBase()}/api/tts`. |
| `frontend/frontend/src/components/shell/InputBar.tsx` | **MODIFIED** | Replaced dead Render STT URLs with `${getApiBase()}/api/stt` and `getAuthHeaders()`. |

---

## 4. Verification & Testing

### 4.1. Backend Security Test Suite
Ran the complete backend security, IDOR, credentials, and OAuth pytest suite:
```bash
cd backend
python -m pytest tests\test_security_phase1.py tests\test_idor_phase2.py tests\test_credentials_phase3.py tests\test_oauth_phase4.py -q
```
**Result**:
- **63 passed, 35 warnings in 15.01s** (100% pass rate).
- All tenant isolation, IDOR prevention, credential hashing, and OAuth state verification tests passed.

### 4.2. Backend Application Import Verification
Verified backend app imports cleanly without dependency or routing errors:
```bash
python -c "from app.main import app; print('MITRA BACKEND IMPORT OK')"
```
**Result**:
- `MITRA BACKEND IMPORT OK` (Exit code 0).

### 4.3. Frontend Production Build
Compiled the full React application in production mode:
```bash
cd frontend/frontend
npm run build
```
**Result**:
- `Compiled successfully.` with **0 errors and 0 warnings** (Exit code 0).
- Bundle size: `166.99 kB` (gzip).

### 4.4. Git Diff Hygiene Check
Checked for any trailing whitespace or formatting defects:
```bash
git diff --check
```
**Result**:
- Clean (Exit code 0).

---

## 5. Security & Architecture Assessment

1. **CORS Security**:
   - `backend/app/main.py` explicitly whitelists `https://mitra.blackholeinfiverse.com`, `https://artha.blackholeinfiverse.com`, and localhost development origins with `allow_credentials=True`.
   - Wildcard `allow_origins=["*"]` is not used with credentials.
2. **IDOR & Identity Boundary**:
   - Identity is derived strictly from the verified JWT payload (`current_user["user_id"]`) in `backend/app/core/auth_dependencies.py`.
   - Modifying query parameters (e.g. `?user_id=attacker`) cannot bypass access control on protected routes.
3. **Secret Protection**:
   - No secrets, private keys, or credentials were committed or exposed.
   - Centralized `formatApiError()` displays helpful diagnostic info without logging JWTs or sensitive user data to the browser console.

---

## 6. Next Steps for Deployment

To commit and push these changes to GitHub:

```powershell
# 1. Review status
git status

# 2. Stage modified files and new apiConfig.ts
git add frontend/frontend/src/services/apiConfig.ts
git add frontend/frontend/src/
git add src/services/controlPlane.js
git add PRODUCTION_FIX_REPORT.md

# 3. Commit
git commit -m "fix(auth): normalize API base URL, unify JWT handling and add Authorization headers"

# 4. Push to feature branch
git push origin feature/mitra-production-foundation
```

Once pushed, the GitHub Actions workflow in `.github/workflows/cicd.yml` will automatically build the production Docker images with `--build-arg REACT_APP_API_URL=https://mitra.blackholeinfiverse.com/api`. The new normalization will resolve the URL to `https://mitra.blackholeinfiverse.com` and companion chat will succeed with valid bearer authorization.
