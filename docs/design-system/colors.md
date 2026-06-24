# Mitra — Design System: Colors
**Full color token reference**

---

## Palette Decisions

| Decision | Rationale |
|----------|-----------|
| Near-black (#0A0A0F) not pure black | Pure black feels harsh; this reads as premium |
| Purple brand (#7C6FF7) | Intelligence, calm authority — not cold blue, not aggressive red |
| Amber for thinking state | Warm and alert — signals processing without alarm |
| No saturated backgrounds on cards | Cards read via border + elevation, not background color |
| 4-level surface scale | Creates real depth without shadows |

---

## Surface Colors
| Token | Value | Use |
|-------|-------|-----|
| `surface-primary` | `#0A0A0F` | Shell background |
| `surface-secondary` | `#111118` | Sidebar, panels |
| `surface-elevated` | `#18181F` | Cards, modals, tooltips |
| `surface-overlay` | `#1E1E28` | Hover states, skeleton loaders |

## Border Colors
| Token | Value | Use |
|-------|-------|-----|
| `border-subtle` | `#27272F` | Default card borders |
| `border-default` | `#3F3F50` | Input borders, interactive elements |
| `border-strong` | `#6B6B80` | Focused states, active indicators |

## Text Colors
| Token | Value | Use |
|-------|-------|-----|
| `text-primary` | `#F4F4F8` | Headings, primary content |
| `text-secondary` | `#A1A1B5` | Labels, descriptions |
| `text-muted` | `#6B6B80` | Timestamps, placeholders, disabled |

## Brand Colors
| Token | Value | Use |
|-------|-------|-----|
| `brand` | `#7C6FF7` | CTAs, active nav, companion indicator |
| `brand-hover` | `#A78BFA` | Hover state for brand elements |
| `brand-soft` | `#1E1A3F` | Brand-tinted backgrounds |
| `brand-glow` | `#7C6FF740` | Focus rings, subtle glow |

## Semantic Colors
| Token | Default | Soft BG | Use |
|-------|---------|---------|-----|
| `success` | `#34D399` | `#0F2D22` | Completed actions, online status |
| `warning` | `#FBBF24` | `#2D2208` | Thinking state, cautions |
| `error` | `#F87171` | `#2D1212` | Failures, blocked actions |
| `info` | `#60A5FA` | `#122040` | Informational states |

## Presence Colors (Companion Status)
| State | Color | Use |
|-------|-------|-----|
| `active` | `#34D399` | Companion ready |
| `thinking` | `#FBBF24` | Processing request |
| `away` | `#6B6B80` | Idle / disconnected |
| `error` | `#F87171` | Error state |
