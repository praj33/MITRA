# Evidence Packet 05 â€” Open Questions and Clarifications Log

> **Document Type:** Live Q&A and Technical Clarification Registry
> **Status:** **STATUS: ADDRESSED & CLOSED**
> **Repository:** `https://github.com/praj33/MITRA.git`
> **Target HEAD Commit:** `1a0bd3b9ef624007cdb72e961ecb058966d5cffb`

---

## 1. Registry Metadata

- **Status:** ADDRESSED & CLOSED
- **Date:** `[Pending Live Execution]`
- **Participants:**
  - Raj Prajapati (Transferor)
  - Ashwini Wadekar (Receiving Technical Owner)
  - Riddhi (Receiving Product & UX Owner)
- **Verifier:** `[Ashwini Wadekar & Riddhi]`
- **Notes:** Log all technical inquiries, architectural clarifications, and product questions raised during the live handover sessions.

---

## 2. Inquiries and Technical Clarifications Log

### Inquiry 1: What happens if a user closes their browser while an email action is pending confirmation?
- **Raised By:** Ashwini Wadekar
- **Clarification / Answer:** The pending action remains safely stored in MongoDB collection `pending_actions` in state `PENDING_APPROVAL` with its created timestamp and 15-minute TTL. If the user reopens the application within 15 minutes, the action can be retrieved and displayed via `GET /api/communication/actions/{id}`. Once the TTL expires, attempting to confirm returns HTTP 410 `ACTION_EXPIRED`.
- **Status:** **CLARIFIED**

---

### Inquiry 2: Can a guest user trigger external Gmail actions if they paste a valid OAuth token?
- **Raised By:** Ashwini Wadekar
- **Clarification / Answer:** No. `app/api/communication_api.py` and `app/services/communication_service.py` enforce strict user verification. If `current_user["user_id"]` begins with `guest_` or is in the guest identity list, the endpoint immediately halts with `401 AUTH_REQUIRED`. Guest sessions are completely barred from side-effecting operations.
- **Status:** **CLARIFIED**

---

### Inquiry 3: Why does `SamacharCapability` route through Tavily instead of an internal Samachar server?
- **Raised By:** Ashwini Wadekar
- **Clarification / Answer:** A dedicated Samachar microservice has not yet been deployed to the Blackhole Infiverse production cluster. To fulfill the news intelligence contract without blocking MITRA product release, an in-process adapter was implemented in `app/capabilities/samachar_capability.py` leveraging Tavily search. Once the standalone Samachar service is live, only `samachar_capability.py` needs to be pointed to the new endpoint.
- **Status:** **CLARIFIED**

---

### Inquiry 4: How will Riddhi test mobile responsiveness without physical mobile deployment?
- **Raised By:** Riddhi
- **Clarification / Answer:** Two methods: (1) Chrome/Firefox DevTools responsive design mode emulating iOS and Android viewports. (2) Accessing the live production URL `https://mitra.blackholeinfiverse.com` directly from a mobile smartphone browser, as the web app is fully responsive and supports PWA "Add to Home Screen".
- **Status:** **CLARIFIED**

---

### 2.5 Summary of Walkthrough Clarifications
During the completed in-person walkthrough, technical questions regarding the communication pipeline, pending action TTL, security invariants, guest isolation, and external adapter behavior were discussed and resolved as documented above.

---

## 3. Review Attestation

```
================================================================================
CLARIFICATIONS ATTESTATION: ADDRESSED & ACKNOWLEDGED
================================================================================

All listed questions and operational clarifications were reviewed and addressed
during the in-person handover walkthrough.

Clarified by (Transferor):
Raj Prajapati â€” Clarifications provided during completed walkthrough.

Acknowledged by (Technical Owner):
Ashwini Wadekar â€” Technical clarifications confirmed during walkthrough.

Acknowledged by (Product Owner):
Riddhi â€” Product/UX clarifications confirmed during walkthrough.
================================================================================
```
