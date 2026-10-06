# Evidence Packet 02 â€” Working System Demonstration Checklist

> **Document Type:** Executable Live Runtime Test Script
> **Status:** **STATUS: PROTOCOL REVIEWED DURING HANDOVER**
> **Environment:** Production (`https://mitra.blackholeinfiverse.com`)
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Target HEAD Commit:** `1a0bd3b9ef624007cdb72e961ecb058966d5cffb`

---

## 1. Demonstration Metadata

- **Status:** PROTOCOL REVIEWED DURING HANDOVER
- **Date:** `[Pending Live Execution]`
- **Participants:**
  - Raj Prajapati (Demonstrator)
  - Ashwini Wadekar (Technical Evaluator)
  - Riddhi (Product & UX Evaluator)
- **Verifier:** `[Ashwini Wadekar & Riddhi]`
- **Notes:** Execute each of the following 18 steps against the production environment. Record actual observed runtime outcomes without fabrication.

---

## 2. 18-Step Live System Demonstration Protocol

### Step 1: Open Production MITRA Web Application
- **Action:** Navigate to `https://mitra.blackholeinfiverse.com` in a clean browser window.
- **Expected:** React SPA loads with valid SSL, TopBar rendered, conversation container visible, responsive shell active.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Capture screenshot or network request log]`

---

### Step 2: Authentication & Session Verification
- **Action:** Open `AuthModal.tsx`, log in with an authenticated user account (or test guest token generation).
- **Expected:** JWT access token returned, user profile reflected in header, bearer token stored in localStorage/authStore.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Network log: POST /api/auth/login -> 200 OK]`

---

### Step 3: New Conversation Initialization
- **Action:** Click "New Chat" / Clear existing conversation state.
- **Expected:** Chat feed resets cleanly, welcome prompt displays, active session ID initialized.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[DOM inspection]`

---

### Step 4: Normal Conversational Chat
- **Action:** Submit conversational prompt: *"Explain how photosynthesis works in 3 bullet points."*
- **Expected:** Real-time token streaming over SSE (`/api/companion/chat/stream`), fast time-to-first-token (< 800ms), markdown bullets rendered properly.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[SSE stream inspection in Network tab]`

---

### Step 5: Direct Capability Invocation (Web Search / Task)
- **Action:** Submit intent prompt: *"Create a high priority task to review MITRA handover documents by tomorrow."*
- **Expected:** Intent classified into `TaskCapability`, task inserted into MongoDB `tasks` collection, task card rendered in UI.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[TaskCard rendered with Priority: High]`

---

### Step 6: Gmail READ (Inbox Query)
- **Action:** Submit prompt: *"Check my recent unread emails."*
- **Expected:** `EmailCapability` dispatches to `email_executor.py`, calls Gmail API `messages/list`, extracts subject, sender, and snippet, renders summary card.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Email summary cards displayed in chat]`

---

### Step 7: Gmail DRAFT Creation
- **Action:** Submit prompt: *"Draft an email to rajprajapati1729@gmail.com with subject Handover Walkthrough and body Hi Raj, looking forward to our session."*
- **Expected:** Draft created in user's Gmail mailbox via `POST /users/me/drafts`, draft confirmation card displayed with "View Full Draft" and "Edit Before Sending" buttons.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Draft card rendered with valid draft_id]`

---

### Step 8: Gmail Structured DRAFT Editing
- **Action:** Click "Edit Before Sending" on the created draft card.
- **Expected:** `InputBar` switches into `DraftEditState`. Structured fields for Recipient, Subject, and Body appear above the input. The body is populated with clean draft text without natural-language command contamination.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[DraftEditState active; no conversational preamble]`

---

### Step 9: Gmail SEND & B.COMM-3 Approval Flow
- **Action:** Edit body text in structured editor, click "Send".
- **Expected:** Direct POST to `/api/communication/drafts/{id}/prepare-send`. Backend stages action in MongoDB with HMAC hash, returns `confirmation_required`. `CommunicationConfirmationCard` appears. Click "Confirm & Send". Backend verifies JWT, executes `users/me/messages/send`, transitions state to `CONFIRMED`.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Confirmation card approval followed by success toast and email delivery]`

---

### Step 10: Google Calendar Schedule Verification
- **Action:** Submit prompt: *"Schedule a meeting called Handover Sync tomorrow at 3 PM."*
- **Expected:** `CalendarCapability` invokes `calendar_executor.py`, stages approval card, and creates event on Google Calendar upon confirmation.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Google Calendar event link returned]`

---

### Step 11: Integrations Modal & Provider Status
- **Action:** Click "Integrations" in navigation or TopBar to open `IntegrationsModal.tsx`.
- **Expected:** Modal renders status badges for Google (Connected), Microsoft (Not Connected), GitHub (Not Connected), WhatsApp (Configured).
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Screenshot of IntegrationsModal]`

---

### Step 12: Mobile PWA Responsive Behavior
- **Action:** Open Chrome DevTools, switch to iPhone 14 / Pixel 7 mobile viewport emulation.
- **Expected:** Collapsible drawer replaces fixed sidebar, input bar fits touch keyboard viewport, cards reflow without horizontal overflow.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Mobile viewport rendering evaluation]`

---

### Step 13: Desktop Multi-Panel Layout
- **Action:** Expand viewport to 1920x1080 desktop resolution.
- **Expected:** Three-column view option accessible (Sidebar, Conversation Center, Context / Memory Panel).
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Desktop layout evaluation]`

---

### Step 14: Error Handling & Graceful Degradation
- **Action:** Submit an invalid or unreachable request (e.g. malformed email address or disconnection simulation).
- **Expected:** User-friendly error card or toast notification displayed; no unhandled React error boundary whiteout or raw stack trace leakage.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Error toast rendered with sanitized error message]`

---

### Step 15: Loading & Processing Feedback States
- **Action:** Submit a multi-step capability request.
- **Expected:** Pulsing indicator or progress spinner in `InputBar` and `ConversationCenter` while waiting for external API response.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Spinner rendering during async wait]`

---

### Step 16: Approval Expiration & Cancellation States
- **Action:** Trigger a pending email send, then click "Cancel" on the confirmation card.
- **Expected:** Action state transitions to `CANCELLED` via `POST /api/communication/actions/{id}/cancel`. Re-clicking confirm returns 400 `ACTION_CANCELLED`.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Action marked cancelled in MongoDB and UI]`

---

### Step 17: Production Logs & Telemetry Inspection
- **Action:** SSH to production VM and inspect live container logs:
  ```bash
  docker compose -f docker-compose.production.yml logs -f --tail=50 backend
  ```
- **Expected:** Structured JSON logs stamped with `trace_id`, `service: "bucket_service"`, no plaintext credentials printed.
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Terminal log snippet]`

---

### Step 18: Live Deployment & Image Verification
- **Action:** Run container inspection on the VM:
  ```bash
  docker compose -f docker-compose.production.yml images
  ```
- **Expected:** Running images match current Git SHA tag (`1a0bd3b` or target verified commit).
- **Observed:** `[Pending Live Demonstration]`
- **Pass/Fail:** `[PENDING]`
- **Evidence:** `[Terminal output showing container image tags]`

---

## 3. Demonstration Attestation

```
================================================================================
DEMONSTRATION PROTOCOL: REVIEWED & TRANSFERRED
================================================================================

This 18-step verification protocol was reviewed during the in-person handover.
The technical and product execution steps remain available for production smoke
testing and acceptance by the receiving team.

Technical Evaluator:
Ashwini Wadekar â€” Demonstration protocol reviewed and acknowledged.

Product Evaluator:
Riddhi â€” User journey and interaction verification protocol acknowledged.

Transferor:
Raj Prajapati â€” Demonstration procedures explained.
================================================================================
```
