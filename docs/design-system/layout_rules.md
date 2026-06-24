# Mitra — Layout Architecture
**CSS Grid-First | Low-Scroll | Dashboard Zoning**

---

## Core Grid System

All layouts use CSS Grid as the foundation. No flexbox for page-level structure.

### Desktop Grid (≥1280px)
```css
.mitra-shell {
  display: grid;
  grid-template-columns: 240px 1fr 320px;
  grid-template-rows: 48px 1fr 64px;
  grid-template-areas:
    "topbar  topbar  topbar"
    "sidebar center  context"
    "sidebar input   input";
  height: 100vh;
  overflow: hidden; /* prevents global scroll — each zone scrolls internally */
}
```

### Tablet Grid (768px–1279px)
```css
.mitra-shell {
  display: grid;
  grid-template-columns: 64px 1fr;   /* collapsed sidebar = icon-only */
  grid-template-rows: 48px 1fr 64px;
  grid-template-areas:
    "topbar  topbar"
    "sidebar center"
    "sidebar input";
  height: 100vh;
  overflow: hidden;
}

/* Context panel becomes a slide-over drawer */
.context-panel {
  position: fixed;
  right: 0;
  top: 48px;
  bottom: 64px;
  width: 320px;
  transform: translateX(100%);  /* hidden by default */
  transition: transform 300ms cubic-bezier(0.0, 0.0, 0.2, 1);
}
.context-panel.open { transform: translateX(0); }
```

### Mobile Grid (<768px)
```css
.mitra-shell {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 48px 1fr 60px 64px;
  grid-template-areas:
    "topbar"
    "center"
    "bottomnav"
    "input";
  height: 100dvh; /* dynamic viewport height — respects mobile browsers */
  overflow: hidden;
}

/* Sidebar becomes full-screen drawer */
.sidebar {
  position: fixed;
  inset: 0;
  z-index: 50;
  transform: translateX(-100%);
  transition: transform 250ms cubic-bezier(0.0, 0.0, 0.2, 1);
}
.sidebar.open { transform: translateX(0); }
```

---

## Zone Specifications

### Top Bar (48px, `grid-area: topbar`)
```
┌─────────────────────────────────────────────────────────────────┐
│  [≡] Mitra           ● Active      [🔔 3]    [Search]  [Avatar] │
│  hamburger logo      companion     notifs    cmd+K     user     │
└─────────────────────────────────────────────────────────────────┘
```
- Left: hamburger (mobile only) + Mitra wordmark
- Center: companion status dot + "Active" / "Thinking..." / "Away"
- Right: notification bell (badge count) + search trigger + user avatar
- Never scrolls. Always visible.

### Left Sidebar (240px desktop, 64px tablet, drawer mobile)
```
┌──────────────────┐
│ [M] Mitra        │ ← logo, collapses to icon on tablet
│──────────────────│
│ [💬] Chats       │ ← primary nav
│ [⚡] Capabilities│
│ [🔄] Workflows   │
│ [📊] Intelligence│
│──────────────────│
│ TODAY            │ ← section label (CAPS, muted, 10px)
│ ● Planning sess… │ ← active conversation (brand dot)
│   Morning brief… │
│   Email draft    │
│ EARLIER          │
│   Weekly review  │
│   Study plan     │
│──────────────────│
│ [⚙️] Settings    │ ← pinned bottom
│ [👤] Profile     │
└──────────────────┘
```

**Scroll behavior:** Only the conversation list section scrolls. Nav and bottom items are fixed within the sidebar.

### Center Panel (flexible, primary attention zone)
```
┌────────────────────────────────────────┐
│  [Avatar] Good morning, Gauri.         │ ← companion greeting (top)
│  Today's 14 Jun · 3 meetings           │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ 👤 "Prepare me for my 3pm call" │  │ ← user message card
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ [M] Here's what I found:        │  │ ← companion response
│  │ ┌────────────────────────────┐  │  │
│  │ │ 📅 ACTION: Calendar        │  │  │ ← inline Action Card
│  │ │ 3:00 PM — Product Review   │  │  │
│  │ │ 4 attendees · Zoom link    │  │  │
│  │ │ [View] [Prep Notes]        │  │  │
│  │ └────────────────────────────┘  │  │
│  └──────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

**Scroll behavior:** Conversation thread scrolls vertically. Companion greeting stays at top (sticky). Input bar stays at bottom (fixed via grid).

### Right Context Panel (320px desktop, drawer on tablet/mobile)
```
┌────────────────────┐
│ CONTEXT            │ ← section label
│ ┌────────────────┐ │
│ │ 📅 Today       │ │ ← Context Card: calendar
│ │ 9:00 Standup   │ │
│ │ 3:00 PM Review │ │
│ │ 5:00 1:1       │ │
│ └────────────────┘ │
│ ┌────────────────┐ │
│ │ ✅ Tasks (5)   │ │ ← Context Card: tasks
│ │ ○ Send report  │ │
│ │ ○ Review PR    │ │
│ └────────────────┘ │
│                    │
│ SUGGESTIONS        │
│ ┌────────────────┐ │
│ │ 💡 Follow up   │ │ ← Recommendation Card
│ │ with Alex?     │ │
│ │ [Yes] [Dismiss]│ │
│ └────────────────┘ │
└────────────────────┘
```

### Input Bar (64px, `grid-area: input`)
```
┌──────────────────────────────────────────────────────────────┐
│  [+]  Ask Mitra anything...                      [🎤]  [→]   │
│  add  placeholder                               voice  send   │
└──────────────────────────────────────────────────────────────┘
```
- Left: attachment/capability quick-add
- Center: text input (grows vertically up to 3 lines, then scrolls)
- Right: voice input + send
- Always visible, never scrolled behind

### Mobile Bottom Nav (60px, mobile only)
```
┌─────────────────────────────────────────┐
│   💬        ⚡        🔄        👤      │
│  Chats  Capabilities  Workflows  Profile │
└─────────────────────────────────────────┘
```

---

## Spacing Discipline

### Card Spacing
All cards use consistent internal spacing:
```
card-sm:  padding: 12px (p-3)
card-md:  padding: 16px (p-4) — default for all 9 card types
card-lg:  padding: 20px (p-5) — Knowledge, System cards
```

### Between Cards
```
conversation-list gap: 4px  (gap-1)
context-panel gap:    8px   (gap-2)
capability results:   12px  (gap-3)
```

### Section Spacing
```
zone-to-zone:    16px border (divider)
section-label:   top 20px, bottom 8px
within-section:  8px between items
```

---

## Scrolling Rules

| Zone | Scrollable | Scroll Direction |
|------|-----------|-----------------|
| Top Bar | ❌ Never | — |
| Sidebar Nav Icons | ❌ Never | — |
| Sidebar Conversation List | ✅ Yes | Vertical |
| Center Thread | ✅ Yes | Vertical |
| Right Panel | ✅ Yes (if content overflows) | Vertical |
| Input Bar | ❌ Never | — |
| Bottom Nav | ❌ Never | — |

**Maximum conversation visible without scroll:** 5–7 messages (goal: 3 visible at all times)

---

## Information Hierarchy Rules

1. **Companion message always left-aligned** — user message right-aligned (clear reading flow)
2. **Most recent message always visible** — auto-scroll on new message
3. **Action Cards always visually separated** — border-left 3px brand accent
4. **Section labels always UPPERCASE, 10px, muted** — clear zone demarcation
5. **Timestamps always muted, 11px** — never compete with content
6. **Capability icons always 16px** — consistent visual language
7. **Loading states always match card dimensions** — no layout shift

---

## Comprehension Speed Targets

| Information | Target Visibility |
|-------------|------------------|
| Is Mitra active/available? | 0–1 second (status dot in top bar) |
| What's my next meeting? | 1–3 seconds (top of right panel) |
| What did Mitra just do? | 0–2 seconds (Action Card in thread) |
| How many unread notifications? | 0–1 second (badge on bell icon) |
| What's my last conversation? | 2–4 seconds (sidebar list) |
