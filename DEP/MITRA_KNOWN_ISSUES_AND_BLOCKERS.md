# MITRA â€” Known Issues, Blockers, and Resolution Registry

> **Document Type:** Operational Defect and Risk Registry
> **Source of Truth:** Commit History, Defect Investigations, Test Logs, Runtime Audits
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Branch:** `main` | **HEAD:** `1a0bd3b9ef624007cdb72e961ecb058966d5cffb`
> **Audited For:** Raj Prajapati, Ashwini Wadekar, and Riddhi
> **Status:** OFFICIAL HANDOVER AUDIT

---

## 1. Issue Classification Standard

- **P0 (Critical / Blocker):** System unviable, security vulnerability, data loss, or primary communication workflow broken.
- **P1 (High):** Major capability impaired, authentication barrier for external users, or dependency blocking key ecosystem feature.
- **P2 (Medium):** Secondary integration unconfigured, graceful degradation active, or UI cosmetic inconsistency.
- **P3 (Low):** Minor enhancement, simulated backend adapter, or non-blocking roadmap item.

---

## 2. Active, Resolved, and Operational Issues

### [P0-1] Email Draft Edit-Before-Sending Body Contamination
- **Classification:** P0 â€” Critical Functional Defect
- **Status:** **FIXED** (Resolved in commit `a4c982d`)
- **Affected Module:** [frontend/.../InputBar.tsx](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/frontend/frontend/src/components/shell/InputBar.tsx), [backend/app/services/communication_service.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/services/communication_service.py)
- **Description:** Previously, clicking "Edit Before Sending" populated the draft into the chat input bar as a natural language command (e.g. `Send an email to user@example.com with subject...`). When submitted, the LLM re-prompted the instruction, prepending the entire prompt to the email body (`"Hello Raj, Send an email to..."`).
- **Remediation:** Replaced natural language composer recycling with a dedicated, isolated `DraftEditState` UI and a structured REST endpoint (`POST /api/communication/drafts/{id}/prepare-send`). The draft fields (To, Subject, Body) are edited discretely without LLM re-prompting.
- **Verification:** Verified by unit and integration tests in `backend/tests/test_email_draft_edit_flow.py`. Production verification confirmed natural language contamination is completely eliminated.
- **Recommended Owner:** Ashwini Wadekar (Backend) / Riddhi (Draft Edit UI)

---

### [P0-2] Account ID Authorization Mismatch on Structured Draft Send
- **Classification:** P0 â€” Critical Security & Execution Defect
- **Status:** **FIXED IN CODE / PENDING FINAL LIVE PRODUCTION SMOKE TEST** (Resolved in commit `1a0bd3b`)
- **Affected Module:** [backend/app/services/communication_service.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/services/communication_service.py) (`prepare_send_draft`)
- **Description:** When the user clicked "Send" from the new structured draft editor, production returned `403 Authorization error: account_id 'blackholeinfiverse20@gmail.com' does not belong to authenticated user`. The backend security validator compared the Google email identity directly against the internal user ID string without resolving the user's bound OAuth account connection.
- **Remediation:** Updated `prepare_send_draft` to resolve the user's registered Google OAuth account dynamically, validating that the target Google account belongs strictly to the authenticated caller while allowing valid email-based account identifiers.
- **Verification:** Regression tests passed (115/115 passing in communication suite). A final end-to-end live click test on production VM is assigned to Ashwini as an immediate post-handover smoke verification.
- **Recommended Owner:** Ashwini Wadekar

---

### [P1-1] Google OAuth "Unverified App" Warning Screen for External Users
- **Classification:** P1 â€” High Operational Blocker
- **Status:** **OPEN** (External Google Cloud Trust & Safety review dependency)
- **Affected Module:** Google Cloud Console / OAuth Consent Screen
- **Description:** Because MITRA requests sensitive Gmail and Calendar scopes (`gmail.send`, `gmail.compose`, `gmail.readonly`, `calendar.events`), users attempting to link their Google accounts see a Google warning: *"Google hasn't verified this app"*.
- **Impact:** Internal team members and pre-whitelisted test accounts can bypass this by clicking *"Advanced -> Go to MITRA (unsafe)"*, but external public users are deterred.
- **Workaround:** Whitelist user email addresses in Google Cloud Console under "Test Users" while the formal OAuth verification application is pending.
- **Recommended Owner:** Ashwini Wadekar (Technical Submission) / Raj Prajapati (Organizational Authority)

---

### [P1-2] Meta WhatsApp Cloud API Production Account Verification
- **Classification:** P1 â€” High Integration Blocker
- **Status:** **OPEN** (External Meta Business Verification dependency)
- **Affected Module:** [backend/app/executors/whatsapp_executor.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/executors/whatsapp_executor.py), [backend/app/routers/whatsapp_inbound.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/routers/whatsapp_inbound.py)
- **Description:** WhatsApp inbound webhook verification is fully functional and signature-tested. However, outbound messaging via `WhatsAppExecutor` requires a live Meta WhatsApp Cloud API System Token and registered Phone Number ID.
- **Impact:** Live outbound messages cannot be sent to arbitrary external phone numbers until Meta Business Manager verification is approved.
- **Workaround:** Restrict outbound WhatsApp testing to developer numbers registered in the Meta Developer portal sandbox.
- **Recommended Owner:** Ashwini Wadekar

---

### [P2-1] Microsoft Graph & GitHub OAuth Credentials Missing in Production
- **Classification:** P2 â€” Medium Configuration Deficiency
- **Status:** **PARTIALLY FIXED** (Code fully implemented; environment credentials missing)
- **Affected Module:** `backend/.env` on production VM, [backend/app/integrations/oauth/microsoft.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/integrations/oauth/microsoft.py), [backend/app/integrations/oauth/github.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/integrations/oauth/github.py)
- **Description:** The backend contains complete implementations for Microsoft OAuth / Graph email sending and GitHub OAuth repository operations. However, `MICROSOFT_CLIENT_ID` and `GITHUB_CLIENT_ID` are not populated in the production VM environment.
- **Impact:** Clicking "Connect Microsoft" or "Connect GitHub" in the frontend `IntegrationsModal` produces configuration or callback errors.
- **Workaround:** Provision official Azure App Registration and GitHub OAuth App credentials, then add to GitHub Actions secrets.
- **Recommended Owner:** Ashwini Wadekar

---

### [P2-2] Multi-Modal OCR and Vector Indexing for Document Attachments
- **Classification:** P2 â€” Medium Feature Gap
- **Status:** **OPEN / ROADMAP**
- **Affected Module:** [backend/app/runtime/attachment_runtime.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/runtime/attachment_runtime.py), [backend/app/capabilities/document_capability.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/capabilities/document_capability.py)
- **Description:** The attachment subsystem currently ingests plaintext and markdown attachments. Binary PDFs, scanned images, and audio files lack native OCR or chunked vector embeddings for long-context semantic retrieval.
- **Impact:** Complex multi-page PDF documents cannot be deeply analyzed or queried conversationally.
- **Recommended Owner:** Ashwini Wadekar / Kanishk Runtime Integration

---

### [P3-1] Samachar Capability Relies on Tavily Web Search Simulator
- **Classification:** P3 â€” Low Integration Gap
- **Status:** **ADAPTER ONLY / SIMULATED**
- **Affected Module:** [backend/app/capabilities/samachar_capability.py](file:///c:/Users/Microsoft/Desktop/MITRA-INTEGRATED/backend/app/capabilities/samachar_capability.py)
- **Description:** The Samachar news intelligence capability is currently an in-process adapter that dispatches news queries to the Tavily search API. There is no active microservice for Samachar in the production infrastructure.
- **Impact:** Users receive real-time news results from Tavily, but dedicated BHIV media intelligence and editorial filters are not yet operational.
- **Recommended Owner:** Ashwini Wadekar / Ecosystem Coordination
