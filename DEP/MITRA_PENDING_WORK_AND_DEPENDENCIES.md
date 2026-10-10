# MITRA â€” Pending Work and Dependencies Roadmap

> **Document Type:** Operational Backlog & External Dependency Specification
> **Source of Truth:** Architecture Gap Analysis, Ecosystem Interfaces, Partner Contracts
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Branch:** `main` | **HEAD:** `1a0bd3b9ef624007cdb72e961ecb058966d5cffb`
> **Target Owners:** Ashwini Wadekar (Engineering & Ecosystem) & Riddhi (Product & UX)
> **Status:** OFFICIAL HANDOVER AUDIT

---

## 1. Prioritized Work Horizon Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 1. IMMEDIATE (Handover Day 1 & Day 2)                  â”‚
â”‚ â€¢ Production deployment of commit 1a0bd3b              â”‚
â”‚ â€¢ Live end-to-end walkthrough with Ashwini & Riddhi     â”‚
â”‚ â€¢ Google Cloud & Server Access Transfer Checklist       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 2. NEXT (Sprint 1: Weeks 1 - 2 Post-Handover)          â”‚
â”‚ â€¢ Google Cloud OAuth Verification submission            â”‚
â”‚ â€¢ Meta Developer Business Account setup for WhatsApp    â”‚
â”‚ â€¢ Provision Azure & GitHub OAuth App credentials        â”‚
â”‚ â€¢ Riddhi's comprehensive UX review & Interaction audit  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 3. LATER (Quarter 1 Roadmap: Month 1+)                 â”‚
â”‚ â€¢ Multi-modal OCR & vector document search             â”‚
â”‚ â€¢ Live TANTRA microservice network integration         â”‚
â”‚ â€¢ Real-time duplex audio WebSocket streaming client    â”‚
â”‚ â€¢ Native mobile app wrapper / Push notification relay  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## 2. Immediate Horizon (Handover Days 1 â€“ 2)

| Task / Item | Category | Responsible Owner | Dependency / Blocker | Current State |
|---|---|---|---|---|
| **Deploy Commit `1a0bd3b` to VM** | Infrastructure | Ashwini Wadekar | Push to `main` already completed; trigger or monitor automated CI/CD pipeline on production VM. | **READY TO DEPLOY** |
| **Verify Structured Email Draft Edit in Prod** | Technical Quality | Ashwini Wadekar | Requires production VM running `1a0bd3b`. Conduct live click test of "Edit Before Sending" -> Edit Body -> Click Send -> Confirm approval card. | **PENDING LIVE SMOKE TEST** |
| **Walkthrough & Access Verification** | Governance | Raj Prajapati / Ashwini / Riddhi | In-person walkthrough conducted; access transfer protocol established. | **COMPLETED IN PERSON** |
| **Review Ashwini Technical Walkthrough** | Engineering | Ashwini Wadekar | Critical modules reviewed: `backend/app/services/communication_service.py`, `companion/`, `InputBar.tsx`. | **COMPLETED & ACCEPTED** |
| **Review Riddhi Product & UX Walkthrough** | Product / UX | Riddhi | User journeys, guest boundaries, draft editing, and approval cards inspected. | **COMPLETED & ACCEPTED** |

---

## 3. Next Horizon (Sprint 1: Weeks 1 â€“ 2)

### 3.1 External Credential & Verification Dependencies

#### A. Google Cloud Trust & Safety OAuth Verification
- **Requirement:** Complete the Google Cloud Trust & Safety review for sensitive scopes (`gmail.send`, `gmail.compose`, `gmail.readonly`, `calendar.events`).
- **Required Assets:**
  - Public Privacy Policy URL on `mitra.blackholeinfiverse.com`.
  - Public Terms of Service URL.
  - YouTube walkthrough video demonstrating why each sensitive scope is requested and how the user triggers it.
  - Domain ownership verification via Google Search Console for `blackholeinfiverse.com`.
- **Target Owner:** Ashwini Wadekar (Technical Submission) / Raj Prajapati (Domain verification)

#### B. Meta Developer WhatsApp Cloud API Setup
- **Requirement:** Activate production WhatsApp messaging.
- **Required Steps:**
  - Create or link a verified Meta Business Manager account.
  - Register a dedicated phone number with WhatsApp Business Account (WABA).
  - Generate a permanent System User Access Token with `whatsapp_business_messaging` permissions.
  - Configure webhook endpoint `https://mitra.blackholeinfiverse.com/webhook/whatsapp` and subscribe to `messages` event.
  - Populate `WHATSAPP_CLOUD_ACCESS_TOKEN`, `WHATSAPP_CLOUD_PHONE_NUMBER_ID`, and `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in production `.env`.
- **Target Owner:** Ashwini Wadekar

#### C. Microsoft Azure App Registration & GitHub OAuth App
- **Requirement:** Enable Microsoft Outlook and GitHub login buttons.
- **Required Steps:**
  - In Azure Portal, create an App Registration for MITRA, configure redirect URI `https://mitra.blackholeinfiverse.com/api/oauth/microsoft/callback`, grant `Mail.ReadWrite`, `Mail.Send`, `User.Read`.
  - In GitHub Developer Settings, create an OAuth App, set callback URL `https://mitra.blackholeinfiverse.com/api/oauth/github/callback`.
  - Add client IDs and secrets to production VM `.env` and GitHub Actions secrets.
- **Target Owner:** Ashwini Wadekar

### 3.2 Product & UX Decisions (Owned by Riddhi)
- **Review Guest-to-User Conversion Flow:** Determine how and when to prompt guest users to create an account when they attempt email/calendar actions.
- **Draft Editor UI Ergonomics:** Evaluate whether the draft editor should be inline above the chat input or expand into a focused modal drawer.
- **Confirmation Card Visual Hierarchy:** Review `CommunicationConfirmationCard` to ensure the "Confirm & Send" button is visually distinct from secondary cancellation actions.
- **Empty States & First-Time Onboarding:** Design guided suggestions or starter prompts for first-time users.

---

## 4. Later Horizon (Roadmap: Month 1+)

### 4.1 Architecture & Technical Enhancements
- **Multi-Modal Document Processing:** Integrate vector embedding generation (e.g. OpenAI `text-embedding-3-small` or local embeddings) and MongoDB Atlas Vector Search for deep PDF document querying.
- **Live TANTRA Network Integration:** Upgrade `tantra_adapter.py` from an adapter/mock into a live HTTP/gRPC client connecting directly to the production TANTRA orchestration cluster once deployed.
- **Real-Time Duplex Audio Client:** Connect the frontend Web Audio API directly to the backend duplex WebSocket (`/ws/audio`) for hands-free voice conversations.
- **Push Notification Infrastructure:** Implement Web Push API / Service Worker notification delivery for reminders scheduled in `ReminderScheduler`.

### 4.2 Ecosystem Alignments
- **UniGuru v2 Full Pipeline:** Unify ontological reasoning across external BHIV knowledge graphs.
- **Capability Runtime Contract (Kanishk Integration):** Wire `capability_runtime_interface.py` to Kanishk's live capability execution host (`CAPABILITY_RUNTIME_URL`) once provisioned in staging.
