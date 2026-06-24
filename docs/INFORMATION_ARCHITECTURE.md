# Mitra — Information Architecture
**Version:** v4.0 | **Sprint:** Companion UX Foundation | **Owner:** Raj Prajapati

---

## 1. Navigation Structure

Mitra has **no page routing** in the traditional sense. It is a **zoned operating surface** — one persistent shell, multiple attention zones that update contextually.

### Primary Navigation (persistent, left sidebar)
```
[M]  Mitra Logo / Home (resets to companion greeting)
───────────────────────────────
[💬] Conversations     — active sessions, history
[⚡] Capabilities      — Email, Calendar, WhatsApp, Tasks, Notes, Docs
[🔄] Workflows         — named multi-step automation
[🔔] Notifications     — system alerts, reminders, follow-ups
[📊] Intelligence      — UniGuru / Knowledge layer
[──] ─────────────────
[⚙️] Settings          — personality config, capabilities, integrations
[👤] Profile           — user identity, preferences
```

### Secondary Navigation (contextual, within panels)
- Capability sub-tabs (e.g. Email: Inbox / Drafts / Sent)
- Workflow filters (Active / Scheduled / History)
- Conversation filters (Today / This Week / All)

---

## 2. Primary User Flows

### Flow A — Companion Conversation (core loop)
```
User types message
    → Companion interprets intent
    → If simple: responds inline as text
    → If capability: shows Action Card + result card in right panel
    → Logs to conversation history
    → Memory updated
```

### Flow B — Capability Invocation
```
User says "schedule a meeting tomorrow at 3pm"
    → IntentFlow classifies → calendar intent
    → Capability Hub routes to CalendarCapability
    → Mitra passes through safety gate (Mitra control plane)
    → ExecutionService runs CalendarExecutor
    → Result shown as Calendar Card in right panel
    → Companion confirms inline: "Done — meeting added for tomorrow 3pm"
```

### Flow C — Workflow Execution
```
User says "morning briefing"
    → WorkflowEngine finds 'morning_briefing' workflow
    → Runs steps: Calendar → Email → Tasks
    → Each result shown as timeline cards in center panel
    → Companion summarizes: "Here's your morning — 2 meetings, 3 emails, 5 tasks"
```

### Flow D — Knowledge Query (UniGuru)
```
User asks "explain quantum entanglement simply"
    → KnowledgeRouter detects educational intent
    → Routes to UniGuruCapability
    → Response shown as Context Card with expandable sections
    → Follow-up questions suggested inline
```

---

## 3. Information Zones

The Mitra operating surface is divided into **4 fixed zones**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOP BAR (48px)  — Companion status, user name, quick actions       │
├──────────┬────────────────────────────────────┬─────────────────────┤
│          │                                    │                     │
│   LEFT   │         CENTER PANEL               │   RIGHT CONTEXT     │
│ SIDEBAR  │       (primary attention)           │      PANEL          │
│  (240px) │    Conversation thread             │     (320px)         │
│          │    Active workflow                 │  Capability results │
│  Nav     │    Intelligence output             │  Smart suggestions  │
│  Conv.   │                                    │  System status      │
│  List    │                                    │  Timeline           │
│          │                                    │                     │
├──────────┴────────────────────────────────────┴─────────────────────┤
│  INPUT BAR (64px) — Message input, voice, attachment, capability    │
└─────────────────────────────────────────────────────────────────────┘
```

| Zone | Purpose | Max Scroll | Update Frequency |
|------|---------|-----------|-----------------|
| Top Bar | Status, identity | Never | On state change |
| Left Sidebar | Navigation, history | Minimal | On new conversation |
| Center Panel | Primary interaction | Moderate | Every message |
| Right Panel | Capability context | Minimal | On capability invoke |
| Input Bar | User input | Never | Always visible |

---

## 4. Attention Hierarchy

Information visible within **3–5 seconds** of opening Mitra:

```
TIER 1 (instant, 0–1s): Companion greeting, current time/date, 
                          companion status indicator
TIER 2 (fast, 1–3s):    Last conversation summary, pending reminders,
                          today's first calendar event
TIER 3 (scan, 3–5s):    Capability shortcuts, workflow status,
                          notification count
TIER 4 (explore, 5s+):  Full conversation history, all capabilities,
                          settings, profile
```

---

## 5. Screen Relationships

```
COMPANION HOME
    ├── Conversation Thread (live, persistent)
    │       └── Inline Capability Cards (calendar, email, task results)
    ├── Capability Hub
    │       ├── Email View
    │       ├── Calendar View  
    │       ├── Task Board
    │       ├── Notes
    │       ├── Contacts
    │       └── Documents
    ├── Workflow Center
    │       ├── Active Workflows
    │       ├── Workflow Builder
    │       └── Workflow History
    ├── Intelligence (UniGuru)
    │       ├── Knowledge Search
    │       ├── Learning Sessions
    │       └── Document Analysis
    └── Settings
            ├── Personality Config
            ├── Capability Toggles
            └── Integration Management
```

---

## 6. Content Priority per Zone

### Left Sidebar — Priority Order
1. Active conversation (highlighted)
2. Today's conversations
3. Recent conversations (last 7 days)
4. Pinned conversations
5. Navigation icons (always visible)

### Center Panel — Priority Order
1. Companion response (latest)
2. Active workflow progress
3. User message (just sent)
4. Conversation history (above)

### Right Panel — Priority Order
1. Active capability result (just returned)
2. Today's calendar events
3. Pending tasks (due today)
4. Smart suggestions from companion
5. System status

---

## 7. Empty States

| Zone | Empty State Content |
|------|-------------------|
| No conversations | Companion greeting + 3 suggested quick starts |
| No capability results | "Ask me to help with email, calendar, or tasks" |
| No workflows | "You haven't set up any workflows yet. Try 'morning briefing'" |
| No notifications | Minimal icon, no text clutter |

---

## 8. Error States

All errors handled **inline** — never full-page errors.

| Error | Handling |
|-------|---------|
| Capability failed | Action Card shows error state with retry |
| LLM unavailable | Companion responds: "I'm having trouble right now, try again in a moment" |
| Safety block | Companion explains gently, no technical jargon |
| Network offline | Subtle status indicator in top bar, input disabled with message |
