# Mitra v4 — UX Foundation REVIEW PACKET
**Sprint:** Companion UX Foundation | **Date:** June 2026

---

## Entry Point

This sprint delivers the **foundational design system and UX architecture** for the Mitra v4 Universal Companion experience. It is not a collection of screens — it is the system all future screens are assembled from.

**Before this sprint:** No design system. One-off chat UI. No component standards.  
**After this sprint:** Reusable primitives, layout system, motion standards, component inventory, IA, wireframes.

---

## Design System Overview

See: `docs/design-system/`

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

See: `docs/COMPONENT_INVENTORY.md`

**The 9 Card Primitives (all future screens assembled from these):**

| Card | Purpose |
|------|---------|
| ConversationCard | Past/active session in sidebar |
| ContextCard | Contextual info in right panel |
| RecommendationCard | Proactive companion suggestions |
| NotificationCard | Alerts, reminders, system messages |
| ActionCard | Capability execution results inline |
| TimelineCard | Multi-step workflow progress |
| StatusCard | System/service health |
| KPICard | Quick metric displays |
| SystemCard | Rich companion output |

---

## Verification

- Frontend production build: ✅ Passed
- Design system tokens: ✅ Complete
- Component inventory: ✅ 9 card types defined
- Layout rules: ✅ 3 breakpoints specified
