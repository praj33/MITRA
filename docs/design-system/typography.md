# Mitra — Design System: Typography
**Reference for all text treatments across the Mitra operating surface**

---

## Font Stack

```css
--font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
```

### Why Inter
- Designed for screen readability at small sizes
- Excellent for UI: variable font with optical sizing
- Widely available via Google Fonts
- Neutral — does not impose personality on the content

### Why JetBrains Mono
- Best readability for code blocks in responses
- Ligatures improve scan speed for code
- Consistent weight across sizes

---

## Type Scale

| Name | Size | Weight | Line Height | Use Case |
|------|------|--------|-------------|---------|
| `h1` | 30px | 700 | 1.2 | Page titles (settings, onboarding) |
| `h2` | 24px | 600 | 1.2 | Section headers |
| `h3` | 20px | 600 | 1.3 | Card titles (knowledge, system) |
| `h4` | 18px | 600 | 1.3 | Panel headers |
| `h5` | 16px | 600 | 1.4 | Sub-sections |
| `body-lg` | 15px | 400 | 1.6 | Companion responses (primary reading) |
| `body` | 14px | 400 | 1.5 | Default UI text, inputs, descriptions |
| `body-sm` | 13px | 400 | 1.5 | Secondary information, card descriptions |
| `label` | 12px | 500 | 1.4 | Form labels, button text |
| `caption` | 11px | 400 | 1.4 | Timestamps, metadata, helper text |
| `overline` | 10px | 600 | 1.4 | Section labels (always UPPERCASE) |
| `mono` | 13px | 400 | 1.6 | Code blocks, trace IDs, technical data |

---

## Typography Roles

### Companion Response Text
```
font-size:   15px (body-lg)
font-weight: 400
line-height: 1.625 (relaxed)
color:       text-primary (#F4F4F8)
max-width:   680px
```
Rationale: Companion responses are the primary reading surface. Relaxed line-height improves long-form readability.

### User Message Text
```
font-size:   14px (body)
font-weight: 400
line-height: 1.5
color:       text-primary
```

### Section Labels (overlines)
```
font-size:     10px
font-weight:   600
letter-spacing: 0.08em
text-transform: uppercase
color:         text-muted (#6B6B80)
```
Examples: "TODAY", "CONTEXT", "SUGGESTIONS", "RECENT"

### Card Titles
```
font-size:   14px
font-weight: 600
line-height: 1.4
color:       text-primary
```

### Metadata / Timestamps
```
font-size:   11px
font-weight: 400
color:       text-muted
```

### Button Labels
```
font-size:   13px
font-weight: 500
letter-spacing: 0.01em
```

---

## Spacing Between Text Elements

```
heading → body:         8px
body → body (new para): 12px
section → section:      24px
label → input:          4px
caption below element:  4px
```

---

## Do / Don't

### Do
- Use `body-lg` (15px) for companion responses
- Use `overline` style for all section labels
- Use `caption` for timestamps and metadata
- Use `mono` for code, trace IDs, technical values
- Keep line lengths between 55–75 characters in center panel

### Don't
- Don't use more than 3 type sizes on the same card
- Don't use regular weight for button labels
- Don't use UPPERCASE for anything except `overline` labels
- Don't mix font families within a single card
- Don't use font-size below 10px anywhere
