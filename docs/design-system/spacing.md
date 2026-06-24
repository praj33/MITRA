# Mitra — Design System: Spacing
**4px base unit. Every spacing value is a multiple of 4.**

---

## Base Unit
```
1 unit = 4px
All spacing values are multiples of 4px.
Exception: 2px for hairline gaps only.
```

## Scale
| Token | Value | Use |
|-------|-------|-----|
| `space-0.5` | 2px | Hairline gaps, icon-to-text in tight labels |
| `space-1` | 4px | Inline element gaps (icon + text), badge padding |
| `space-1.5` | 6px | Tight internal card padding |
| `space-2` | 8px | Gap between list items, inner card sections |
| `space-3` | 12px | Card internal padding (sm), gap between cards |
| `space-4` | 16px | Card internal padding (default), zone separators |
| `space-5` | 20px | Section padding, large card spacing |
| `space-6` | 24px | Between major sections |
| `space-8` | 32px | Large component separation |
| `space-10` | 40px | Panel padding |
| `space-12` | 48px | Top bar height |
| `space-16` | 64px | Input bar height |

## Application Rules
- **Cards always use `space-4` (16px) padding** — never less than 12px
- **List gaps always `space-1` (4px)** in sidebar, `space-2` (8px) in center
- **Between sections always `space-6` (24px)**
- **Icon-to-text gap always `space-1.5` (6px)**
- **Button padding: `space-2` vertical, `space-3` horizontal**
