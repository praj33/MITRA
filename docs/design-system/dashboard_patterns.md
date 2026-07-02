# Mitra — Dashboard Patterns
**Assembling screens from card primitives · Phase 3 Design System**

---

## Philosophy

Mitra screens are not designed page-by-page.  
They are **assembled from zones** using card primitives.

A new screen = pick a layout → fill zones with the right cards.

---

## Zone Grid Vocabulary

| Zone | CSS Grid Area | Purpose |
|------|--------------|---------|
| `topbar` | Fixed top | Status, identity, search |
| `sidebar` | Fixed left | Navigation, history |
| `center` | Flexible main | Primary attention — conversation, workflow |
| `context` | Fixed right | Capability results, suggestions |
| `input` | Fixed bottom | User input |

---

## Pattern 1 — Companion Conversation (Default)

**When:** User is in active conversation.

```
┌─────────────────────────────────────────────────────────────┐
│ TopBar: "● Active" · Gauri · 🔔3                            │
├──────────┬──────────────────────────────┬───────────────────┤
│ Sidebar  │ ConversationThread           │ ContextPanel      │
│          │                              │                   │
│ Nav      │ CompanionMessage (greeting)  │ ContextCard       │
│ Conv.    │ CompanionMessage (response)  │ (Today's calendar)│
│ List     │   └─ ActionCard (inline)     │                   │
│          │ CompanionMessage (latest)    │ ContextCard       │
│          │                              │ (Pending tasks)   │
│          │                              │                   │
│          │                              │ RecommendationCard│
├──────────┴──────────────────────────────┴───────────────────┤
│ InputBar: Ask Mitra anything...                    🎤  →    │
└─────────────────────────────────────────────────────────────┘
```

**Cards used:** `CompanionMessage`, `ActionCard` (inline), `ContextCard` ×2, `RecommendationCard`

---

## Pattern 2 — Workflow Running

**When:** User triggers a multi-step workflow (e.g. "morning briefing").

```
┌─────────────────────────────────────────────────────────────┐
│ TopBar: "● Working on morning briefing..."                  │
├──────────┬──────────────────────────────┬───────────────────┤
│ Sidebar  │ WorkflowProgress             │ ContextPanel      │
│          │                              │                   │
│ Nav      │ TimelineCard                 │ KPICard           │
│ (active  │  ✓ Calendar — 3 meetings     │ "3 meetings today"│
│  workflow│  ✓ Email — 2 unread          │                   │
│  highlight│ ● Tasks — loading...        │ KPICard           │
│          │  ○ Reminders — pending       │ "2 unread emails" │
│          │                              │                   │
│          │ [View Full Report]           │ StatusCard        │
│          │                              │ "All systems OK"  │
└──────────┴──────────────────────────────┴───────────────────┘
```

**Cards used:** `TimelineCard`, `KPICard` ×2, `StatusCard`  
**No InputBar** during workflow — replaced by workflow progress bar.

---

## Pattern 3 — Capability Result (Email Draft)

**When:** User says "Draft an email to John about the meeting."

```
Center panel — CompanionMessage:
┌────────────────────────────────────────────┐
│ [M] I've drafted this for you:             │
│ ┌──────────────────────────────────────┐   │
│ │ 📧 EMAIL DRAFT              ✓ Ready  │   │  ← ActionCard
│ │ To: john@example.com                │   │
│ │ Subject: Meeting Tomorrow           │   │
│ │ ─────────────────────────────────── │   │
│ │ Hi John, confirming our 3pm...      │   │
│ │                                     │   │
│ │ [Edit Draft]         [Send Now →]   │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘

Right panel — ContextPanel:
┌───────────────────┐
│ CONTEXT           │
│ ┌───────────────┐ │
│ │ 📧 Email Draft│ │  ← ContextCard (email variant)
│ │ john@ex.com   │ │
│ │ Meeting Tom.. │ │
│ │ [Edit] [Send] │ │
│ └───────────────┘ │
│ ┌───────────────┐ │
│ │ 📅 Calendar   │ │  ← ContextCard (calendar variant)
│ │ John — 3pm ✓ │ │
│ └───────────────┘ │
└───────────────────┘
```

**Cards used:** `ActionCard` (inline in center), `ContextCard` ×2 (in right panel)

---

## Pattern 4 — Knowledge Response (UniGuru)

**When:** User asks an educational question.

```
Center panel:
┌────────────────────────────────────────────┐
│ [M] Here's how quantum entanglement works: │
│ ┌──────────────────────────────────────┐   │
│ │ 📚 KNOWLEDGE                         │   │  ← SystemCard (knowledge variant)
│ │ Quantum Entanglement                │   │
│ │ ─────────────────────────────────── │   │
│ │ When two particles become...        │   │
│ │ [Expand ↓]                         │   │
│ │                                     │   │
│ │ Follow-up:                          │   │
│ │ [What about superposition?]         │   │
│ │ [Real-world examples?]              │   │
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

**Cards used:** `SystemCard` (knowledge variant)  
Right panel: empty state or related suggestions.

---

## Pattern 5 — Notification Center

**When:** User navigates to Notifications section.

```
Center panel:
┌────────────────────────────────────────────┐
│ NOTIFICATIONS                    [Mark All]│
│ ┌──────────────────────────────────────┐   │
│ │ 🔔 TODAY                             │   │
│ │ ● Meeting starts in 15 min   2m ago  │   │  ← NotificationCard
│ │ ● 3 new emails from Kanishk  8m ago  │   │  ← NotificationCard
│ │                                      │   │
│ │ EARLIER                              │   │
│ │ ○ Weekly summary ready      1h ago   │   │  ← NotificationCard (read)
│ │ ○ Reminder: Call mom        2h ago   │   │  ← NotificationCard (read)
│ └──────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

**Cards used:** `NotificationCard` ×N  
Right panel: shows `StatusCard` for companion status.

---

## Pattern 6 — Intelligence Dashboard (UniGuru Hub)

**When:** User navigates to Intelligence section.

```
┌─────────────────────────────────────────────────────────────┐
│ TopBar: "📊 Intelligence"                                   │
├──────────┬──────────────────────────────┬───────────────────┤
│ Sidebar  │ [Search knowledge base...]   │ ContextPanel      │
│          │                              │                   │
│ Nav      │ RECENT SESSIONS              │ KPICard           │
│          │ ┌──────────────────────────┐ │ "12 topics studied│
│          │ │ Quantum Computing  2d ago│ │  this week"       │
│          │ │ ML Fundamentals   5d ago │ │                   │
│          │ └──────────────────────────┘ │ SystemCard        │
│          │                              │ (suggested topics)│
│          │ SUGGESTED TODAY              │                   │
│          │ ┌──────────────────────────┐ │                   │
│          │ │ 💡 Continue: Quantum...  │ │                   │  ← RecommendationCard
│          │ │ [Continue] [Dismiss]     │ │                   │
│          │ └──────────────────────────┘ │                   │
└──────────┴──────────────────────────────┴───────────────────┘
```

**Cards used:** `ConversationCard` (for sessions), `RecommendationCard`, `KPICard`, `SystemCard`

---

## Responsive Pattern Adaptations

### Desktop (≥1280px) — All 3 panels visible
Use all patterns as documented above.

### Tablet (768–1279px) — 2 panels (sidebar collapsed, no context panel by default)
- `ContextPanel` → becomes slide-over drawer, triggered by ActionCard button
- `Sidebar` → icon-only (64px), taps expand to overlay
- Patterns 1–6 adapt: right panel content moves into center panel as expandable sections

### Mobile (<768px) — Single panel + bottom nav
- Center panel takes full width
- `ContextPanel` → bottom sheet, triggered by tapping ActionCard
- `Sidebar` → full-screen drawer from left
- `InputBar` height increases to 72px for touch targets
- `KPICard` → compact row layout (2 KPIs per row instead of stacked)

---

## Dashboard Zones — Quick Reference

| Need to show | Use card | Goes in zone |
|---|---|---|
| Companion response | `CompanionMessage` | Center |
| Capability result (inline) | `ActionCard` | Center (inside message) |
| Capability result (detail) | `ContextCard` | Right panel |
| Proactive suggestion | `RecommendationCard` | Right panel or center |
| System alert | `NotificationCard` | Center (notifications view) |
| Workflow steps | `TimelineCard` | Center |
| Quick metric | `KPICard` | Right panel |
| Knowledge answer | `SystemCard` | Center |
| Service health | `StatusCard` | Right panel (bottom) |
| Past conversation | `ConversationCard` | Sidebar list |

---

## Composition Anti-Patterns

❌ **Never do this:**
- Custom one-off layout for a new screen
- Nested cards (card inside a card)
- Scrolling the entire shell — only zones scroll internally
- Using `position: fixed` inside a card
- Hardcoding colors inside a component — always use tokens
- Building a screen without checking this pattern library first

✅ **Always do this:**
- Pick a pattern from this doc and assemble from cards
- Check `COMPONENT_INVENTORY.md` for the right card
- Use token values — never raw hex colors in components
- Test all 3 breakpoints before shipping a screen
