# Mitra Production Roadmap

**Current Version:** v4.0.0 | **Last Updated:** July 2026

---

## Completed Milestones

### ✅ M1 — Safety Pipeline (Complete)
- Deterministic Safety → Intelligence → Enforcement → Execution flow
- Bucket logging with integrity hashes
- Trace ID continuity across all stages
- Fail-closed security model

### ✅ M2 — Companion Architecture (Complete)
- CompanionOrchestrator as central brain
- Persistent sessions (MongoDB + in-memory fallback)
- Per-user memory (facts, preferences, history)
- Configurable personality engine (5 tone presets)
- Multi-provider LLM abstraction (Groq, OpenAI, Google, Mistral)

### ✅ M3 — Capability Hub (Complete)
- 11 modular capabilities registered via CapabilityRegistry
- BaseCapability interface for uniform execution
- Intent-based routing
- No hardcoded capabilities

### ✅ M4 — UniGuru Integration (Complete)
- Live UniGuru v2 API integration
- LLM fallback for educational queries
- Seamless user experience (appears as natural conversation)

### ✅ M5 — Cross-Platform Frontend (Complete)
- 3-tier responsive layout (mobile/tablet/desktop)
- Mobile: bottom nav, drawer sidebar, slide-over context
- Tablet: collapsed sidebar, overlay context
- Desktop: full 3-panel grid
- Safe area support for notched phones
- Touch-optimized tap targets

### ✅ M6 — Workflow Engine (Complete)
- 5 built-in workflows (morning briefing, meeting prep, email followup, weekly review, quick reminder)
- Custom workflow registration
- All steps route through capability interfaces
- Partial completion support

### ✅ M7 — Documentation (Complete)
- System architecture document
- Capability map
- Interface contracts
- Cross-platform interaction flows
- Integration guide
- Deployment guide
- Review packet with history

---

## Next Milestone: M8 — Production Hardening

**Target:** August 2026

### 8.1 — Real Capability Execution
- [ ] Connect EmailCapability to live Brevo API (draft + send)
- [ ] Connect CalendarCapability to Google Calendar API
- [ ] Connect WhatsApp to live Cloud API
- [ ] Connect Reminder to scheduled job runner (APScheduler or Celery)
- [ ] Connect Contacts to user address book (MongoDB collection)

### 8.2 — Authentication & Authorization
- [ ] JWT-based session tokens (replace API key auth for web)
- [ ] Per-user API rate limiting
- [ ] OAuth2 for Google Calendar integration
- [ ] Secure credential storage (AWS Secrets Manager / Vault)

### 8.3 — Observability
- [ ] Structured logging (JSON format) for Render/Datadog
- [ ] Error tracking (Sentry integration)
- [ ] Latency metrics per pipeline stage
- [ ] Capability success/failure dashboards
- [ ] Bucket audit daily summaries

### 8.4 — Performance
- [ ] Redis caching for session and memory
- [ ] LLM response streaming (SSE)
- [ ] Lazy-load frontend components
- [ ] CDN for static assets

---

## Future Milestone: M9 — Native Apps

**Target:** Q4 2026

### 9.1 — Mobile Apps
- [ ] React Native shell consuming web API
- [ ] Push notifications via Firebase
- [ ] Offline message queue
- [ ] Biometric auth

### 9.2 — Desktop Apps
- [ ] Electron wrapper for macOS/Windows
- [ ] System tray companion
- [ ] Native notification integration
- [ ] Keyboard shortcut engine

---

## Future Milestone: M10 — Advanced Intelligence

**Target:** Q1 2027

### 10.1 — Proactive Companion
- [ ] Time-based triggers (morning briefing auto-run)
- [ ] Context-aware suggestions based on user patterns
- [ ] Smart follow-up reminders
- [ ] Meeting preparation auto-trigger

### 10.2 — Multi-Agent
- [ ] Capability agents with independent execution contexts
- [ ] Agent-to-agent communication for complex workflows
- [ ] Parallel capability execution

### 10.3 — Advanced Memory
- [ ] Long-term memory summarization
- [ ] Fact verification and decay
- [ ] Cross-session topic threading
- [ ] Memory export/import

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM provider outage | High | Multi-provider fallback chain in LLMBridge |
| MongoDB downtime | Medium | In-memory fallback for sessions/memory |
| WhatsApp API rate limits | Medium | Queue-based sending with backoff |
| Render cold starts | Medium | Keep-alive health checks |
| iOS Safari viewport bugs | Low | `100dvh` with `100vh` fallback |
| Bundle size growth | Low | Lazy loading, tree shaking |
