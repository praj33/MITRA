# Mitra v4 — UX Foundation REVIEW PACKET
**Sprint:** Companion UX Foundation | **Date:** June 2026

---

## Entry Point

This sprint delivers the **foundational design system and UX architecture** for the Mitra v4 Universal Companion experience. It is not a collection of screens — it is the system all future screens are assembled from.

**Before this sprint:** No design system. One-off chat UI. No component standards.  
**After this sprint:** Reusable primitives, layout system, motion standards, component inventory, IA, wireframes.

---

## Information Architecture

See: [`docs/INFORMATION_ARCHITECTURE.md`](docs/INFORMATION_ARCHITECTURE.md)

**Summary:**
- Mitra is a **zoned operating surface**, not a page-routed app
- 4 fixed zones: Top Bar | Left Sidebar | Center Panel | Right Context Panel
- 4-tier attention hierarchy: critical info visible in 0–1s, full content in 5s
- 6 primary user flows: conversation, capability invocation, workflow, knowledge, onboarding, settings

---

## Design System Overview

See: [`docs/design-system/`](docs/design-system/)

| File | Contents |
|------|---------|
| `tokens.md` | Complete design token system (colors, type, spacing, radius, shadow, motion) |
| `colors.md` | Full color palette with semantic tokens and rationale |
| `typography.md` | Type scale, roles, do/don't rules |
| `spacing.md` | 4px base unit spacing system |
| `layout_rules.md` | CSS Grid specs for all 3 breakpoints |

**Tech stack confirmed:**
- React + TypeScript
- Tailwind CSS (extended with design tokens)
- CSS Grid (primary layout system)
- Zustand (state management)
- shadcn/ui + Radix UI (accessible primitives)
- Framer Motion (animation)

---

## Component Overview

See: [`docs/COMPONENT_INVENTORY.md`](docs/COMPONENT_INVENTORY.md)

**The 9 Card Primitives (all future screens assembled from these):**

| Card | Purpose |
|------|---------|
| ConversationCard | Past/active session in sidebar |
| ContextCard | Contextual info in right panel (calendar, tasks, notes) |
| RecommendationCard | Proactive companion suggestions |
| NotificationCard | Alerts, reminders, system messages |
| ActionCard | Capability execution results inline in thread |
| TimelineCard | Multi-step workflow progress |
| StatusCard | System/service health |
| KPICard | Quick metric displays |
| SystemCard | Rich companion output (knowledge, summaries, code) |

**Zustand store structure defined** — single source of truth for session, conversations, capability results, UI state.

---

## Wireframes

### Desktop (≥1280px)
- 3-panel CSS Grid layout
- Sidebar (240px) + Center (flexible) + Context Panel (320px)
- Input bar fixed at bottom, top bar fixed at top

### Tablet (768–1279px)
- 2-panel: collapsed sidebar (64px icon-only) + Center
- Context panel becomes slide-over drawer
- Sidebar expands to overlay on interaction

### Mobile (<768px)
- Single column + bottom navigation
- Sidebar becomes full-screen drawer
- Context panel becomes bottom sheet

---

## Layout Decisions

| Decision | Rationale |
|----------|-----------|
| CSS Grid over Flexbox for shell | Grid named areas make zone assignments explicit and maintainable |
| `overflow: hidden` on shell | Prevents global scroll — each zone manages its own scrolling |
| `100dvh` on mobile | Respects dynamic viewport height (mobile browser chrome) |
| Right panel 320px | Enough for 1 card + metadata, doesn't crowd center at 1280px |
| Sidebar 240px | Standard sidebar width; enough for conversation titles without wrapping |
| 48px top bar | Compact but touch-safe; consistent with Linear, Notion, Arc |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| `#0A0A0F` not pure black | Pure black feels harsh; near-black reads as premium |
| Purple brand `#7C6FF7` | Intelligence and calm authority — avoids both cold tech-blue and aggressive red |
| Inter typeface | Best screen readability at 11–15px; neutral, doesn't impose personality |
| 4-level surface scale | Creates depth without shadows; works on OLED displays |
| Section labels 10px UPPERCASE | Clear zone demarcation without visual weight |
| Cards via border, not background | Avoids color stacking issues in dark mode |
| Animation ≤250ms for UI | Never blocks the user; feels instantaneous |
| No cyberpunk effects | Mitra is calm and functional, not dramatic |

---

## Premium Experience Highlights

See: [`docs/PREMIUM_EXPERIENCE_GUIDE.md`](docs/PREMIUM_EXPERIENCE_GUIDE.md)

- Framer Motion patterns defined for all transition types
- Skeleton loading — no layout shift
- Empty states always show actionable content
- Error states always inline — no full-page errors
- R3F optional ambient layer defined (presence orb, state transitions)
- Companion errors surface as calm human language, never technical strings

---

## Known Risks

| Risk | Mitigation |
|------|-----------|
| Tailwind config can diverge from token definitions | Single `tokens.ts` file as source of truth; Tailwind config extends it |
| shadcn/ui components may not match design tokens | All shadcn components will be overridden with Mitra tokens via CSS variables |
| R3F ambient layer adds bundle weight | Lazy-loaded, tree-shaken; never in critical path |
| Mobile `100dvh` inconsistency on some browsers | Using `100dvh` with `min-height: 100vh` fallback |
| Zustand store can grow without discipline | Store split into domain slices (companion, capability, ui, workflow) |

---

## Future Recommendations

1. **Figma component library** — Translate all 9 card types into Figma components with auto-layout for design-dev parity
2. **Design token export** — Use Style Dictionary to export tokens to JSON, CSS, and Figma tokens
3. **Storybook** — Document all primitives and card types with Storybook for team reference
4. **Focus Mode** — Full-screen conversation mode with R3F ambient layer (defined, not built in this sprint)
5. **Light theme** — Token architecture already supports it; implement `light.ts` theme in next sprint
6. **Accessibility audit** — All Radix UI primitives are accessible by default; run axe-core audit before launch
