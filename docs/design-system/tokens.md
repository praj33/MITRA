# Mitra — Design System Foundation

## Design Philosophy

Mitra is a **premium operating surface**, not a chat application.  
Every visual decision should feel intentional, calm, and fast.

**Three principles:**
1. **Clarity over decoration** — if it doesn't carry information, remove it
2. **Hierarchy over beauty** — the most important thing must be obvious in 3 seconds
3. **Motion with purpose** — animate state, not decoration

---

## Design Tokens

All values are defined as CSS custom properties and Tailwind config extensions.

```typescript
// design-system/tokens.ts
export const tokens = {
  // ── COLORS ──────────────────────────────────────────────────────
  colors: {
    // Base surface
    background: {
      primary:    '#0A0A0F',   // main shell background
      secondary:  '#111118',   // sidebar, panels
      elevated:   '#18181F',   // cards, modals
      overlay:    '#1E1E28',   // hover states, dropdowns
    },
    // Borders
    border: {
      subtle:    '#27272F',    // card borders, dividers
      default:   '#3F3F50',    // interactive element borders
      strong:    '#6B6B80',    // focused/active borders
    },
    // Text
    text: {
      primary:   '#F4F4F8',    // headings, primary content
      secondary: '#A1A1B5',    // labels, metadata
      muted:     '#6B6B80',    // placeholders, disabled
      inverse:   '#0A0A0F',    // text on light backgrounds
    },
    // Brand (Mitra identity)
    brand: {
      primary:   '#7C6FF7',    // primary CTA, companion indicator
      secondary: '#A78BFA',    // hover state
      soft:      '#1E1A3F',    // brand-tinted backgrounds
      glow:      '#7C6FF740',  // subtle glow on focus
    },
    // Semantic
    success:  { default: '#34D399', soft: '#0F2D22' },
    warning:  { default: '#FBBF24', soft: '#2D2208' },
    error:    { default: '#F87171', soft: '#2D1212' },
    info:     { default: '#60A5FA', soft: '#122040' },
    // Companion presence states
    presence: {
      active:   '#34D399',   // companion responding
      thinking: '#FBBF24',   // processing
      away:     '#6B6B80',   // inactive
      error:    '#F87171',   // error state
    }
  },

  // ── TYPOGRAPHY ─────────────────────────────────────────────────
  typography: {
    family: {
      sans: 'Inter, system-ui, -apple-system, sans-serif',
      mono: 'JetBrains Mono, Fira Code, monospace',
    },
    scale: {
      '2xs': '10px',
      xs:    '11px',
      sm:    '12px',
      base:  '14px',
      md:    '15px',
      lg:    '16px',
      xl:    '18px',
      '2xl': '20px',
      '3xl': '24px',
      '4xl': '30px',
      '5xl': '36px',
    },
    weight: {
      normal:   '400',
      medium:   '500',
      semibold: '600',
      bold:     '700',
    },
    leading: {
      tight:   '1.2',
      snug:    '1.375',
      normal:  '1.5',
      relaxed: '1.625',
    },
    tracking: {
      tight:  '-0.025em',
      normal: '0em',
      wide:   '0.05em',
      wider:  '0.1em',  // used for CAPS labels only
    }
  },

  // ── SPACING ────────────────────────────────────────────────────
  spacing: {
    // Base unit: 4px
    px:  '1px',
    0.5: '2px',
    1:   '4px',
    1.5: '6px',
    2:   '8px',
    2.5: '10px',
    3:   '12px',
    3.5: '14px',
    4:   '16px',
    5:   '20px',
    6:   '24px',
    7:   '28px',
    8:   '32px',
    10:  '40px',
    12:  '48px',
    14:  '56px',
    16:  '64px',
    20:  '80px',
    24:  '96px',
  },

  // ── BORDER RADIUS ──────────────────────────────────────────────
  radius: {
    sm:   '6px',
    md:   '8px',
    lg:   '12px',
    xl:   '16px',
    '2xl':'20px',
    full: '9999px',
  },

  // ── SHADOW ─────────────────────────────────────────────────────
  shadow: {
    sm:    '0 1px 2px rgba(0,0,0,0.4)',
    md:    '0 4px 12px rgba(0,0,0,0.4)',
    lg:    '0 8px 24px rgba(0,0,0,0.5)',
    brand: '0 0 0 1px rgba(124,111,247,0.3), 0 4px 16px rgba(124,111,247,0.15)',
  },

  // ── ANIMATION ──────────────────────────────────────────────────
  motion: {
    duration: {
      instant:  '80ms',
      fast:     '150ms',
      normal:   '250ms',
      slow:     '400ms',
      slower:   '600ms',
    },
    easing: {
      default:    'cubic-bezier(0.4, 0, 0.2, 1)',
      spring:     'cubic-bezier(0.34, 1.56, 0.64, 1)',
      decelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
      accelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
    }
  },

  // ── GRID ───────────────────────────────────────────────────────
  layout: {
    sidebar:      '240px',
    sidebarSm:    '64px',   // icon-only collapsed
    contextPanel: '320px',
    inputBar:     '64px',
    topBar:       '48px',
    maxContent:   '800px',  // center panel max width
  }
}
```

---

## Component Categories

### Tier 1 — Primitives (atoms)
Never composed from other components. Build everything else from these.

| Primitive | Description |
|-----------|-------------|
| `<Text>` | Typography with variant prop (heading, body, label, caption, mono) |
| `<Icon>` | Icon wrapper with size and color tokens |
| `<Badge>` | Status/label chips (success, warning, error, info, brand) |
| `<Dot>` | Presence indicator (active, thinking, away, error) |
| `<Divider>` | Horizontal or vertical separator |
| `<Avatar>` | User or companion avatar with fallback initials |
| `<Spinner>` | Loading indicator (3 sizes: sm, md, lg) |

### Tier 2 — Base Components (molecules)
Composed from primitives.

| Component | Description |
|-----------|-------------|
| `<Button>` | Primary, secondary, ghost, destructive variants |
| `<Input>` | Text field with label, error, hint states |
| `<Textarea>` | Multi-line input |
| `<Select>` | Dropdown via Radix UI Select |
| `<Toggle>` | Boolean switch |
| `<Tooltip>` | Hover label via Radix UI |
| `<Popover>` | Floating panel via Radix UI |

### Tier 3 — Card Primitives (the system core)
The 9 reusable card types that all screens are assembled from.

See `COMPONENT_INVENTORY.md` for full spec.

### Tier 4 — Layout Components (organisms)
| Component | Description |
|-----------|-------------|
| `<Shell>` | Root layout — top bar + sidebar + center + right panel |
| `<Sidebar>` | Left navigation + conversation list |
| `<TopBar>` | Header with companion status + user profile |
| `<InputBar>` | Fixed bottom input area |
| `<ContextPanel>` | Right panel container |
| `<ConversationThread>` | Scrollable message list |

---

## Theme Structure

```
/design-system
├── tokens.ts           ← all design tokens (single source of truth)
├── themes/
│   ├── dark.ts         ← dark theme (default)
│   └── light.ts        ← light theme (future)
├── typography.ts       ← text style definitions
├── motion.ts           ← animation definitions
└── index.ts            ← exports all
```

## Tailwind Config Extension

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          primary:    '#0A0A0F',
          secondary:  '#111118',
          elevated:   '#18181F',
          overlay:    '#1E1E28',
        },
        border: {
          subtle:  '#27272F',
          default: '#3F3F50',
          strong:  '#6B6B80',
        },
        brand: {
          DEFAULT:  '#7C6FF7',
          hover:    '#A78BFA',
          soft:     '#1E1A3F',
        },
        text: {
          primary:   '#F4F4F8',
          secondary: '#A1A1B5',
          muted:     '#6B6B80',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        '2xs': ['10px', { lineHeight: '1.4' }],
        xs:    ['11px', { lineHeight: '1.4' }],
        sm:    ['12px', { lineHeight: '1.5' }],
        base:  ['14px', { lineHeight: '1.5' }],
        md:    ['15px', { lineHeight: '1.5' }],
      },
      spacing: {
        sidebar:       '240px',
        'sidebar-sm':  '64px',
        context:       '320px',
        topbar:        '48px',
        inputbar:      '64px',
      },
      borderRadius: {
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      animation: {
        'fade-in':    'fadeIn 250ms cubic-bezier(0.4, 0, 0.2, 1)',
        'slide-up':   'slideUp 250ms cubic-bezier(0.0, 0.0, 0.2, 1)',
        'slide-right':'slideRight 250ms cubic-bezier(0.0, 0.0, 0.2, 1)',
        'pulse-dot':  'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:     { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp:    { from: { transform: 'translateY(8px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
        slideRight: { from: { transform: 'translateX(-8px)', opacity: '0' }, to: { transform: 'translateX(0)', opacity: '1' } },
        pulseDot:   { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.4' } },
      },
    }
  },
  plugins: [require('@tailwindcss/typography')],
}
```
