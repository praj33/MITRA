# DEP — Design & Evidence Packet

## Metadata

| Field | Value |
|-------|-------|
| **Project** | MITRA — Universal AI Companion |
| **Ecosystem** | BHIV |
| **Author** | Raj Prajapati (praj33) |
| **Date** | July 28, 2026 |
| **Phase** | Phase 1 Convergence |
| **Status** | In Progress |

---

## Mission

Transform MITRA from a standalone companion into the canonical, persistent AI companion for the entire BHIV ecosystem.

## Constraints

1. MITRA is the Companion Layer — not intelligence, not execution
2. UniGuru is the Backend Intelligence Model
3. TANTRA is the Execution Runtime
4. Bucket is the Truth Layer
5. No duplicate implementations across products

## Deliverables

### Phase 1 — Canonical API Lock ✅
- JWT authentication (cross-compatible with Node.js frontend)
- Presence API (`/api/v1/presence`)
- Notifications API (`/api/v1/notifications`)
- Runtime API mounted (`/api/v1/sessions`, `/api/v1/attachments`, `/api/v1/intents`)

### Phase 4 — UniGuru Convergence ✅
- UniGuru set as primary LLM (was Groq)
- Fallback chain: UniGuru → Groq → OpenAI → Gemini

### Phase 2 — Universal Runtime (In Progress)
- Continuity Service created
- TANTRA client ready (awaiting endpoint)

### Phases 3, 5, 6 — Blocked
- Awaiting VM URLs (Gurukul, Samruddhi, SETU)
- Awaiting TANTRA endpoint (Ashmit)
- Awaiting Capability Runtime URL (Kanishk)
