# Mitra — Component Library
**Phase 3 Design System · Component-First Architecture**

---

## Philosophy

Every component in Mitra follows one rule:
> **Build once. Use everywhere. Extend never — compose instead.**

No screen should require a one-off layout or custom component.  
All screens are assembled from this library.

---

## Tier 1 — Primitives

The smallest, indivisible building blocks. Never composed from other components.

### `<Text />`
```tsx
<Text variant="heading" | "body-lg" | "body" | "body-sm" | "label" | "caption" | "overline" | "mono"
      color="primary" | "secondary" | "muted" | "brand" | "success" | "warning" | "error"
      weight="normal" | "medium" | "semibold" | "bold"
      truncate?: boolean
      lines?: number  // for multi-line truncation
/>
```

### `<Icon />`
```tsx
<Icon name={string}        // Lucide icon name
      size={12 | 14 | 16 | 20 | 24 | 32}
      color?: string       // defaults to text-secondary
      className?: string
/>
```

### `<Badge />`
```tsx
<Badge variant="default" | "brand" | "success" | "warning" | "error" | "info"
       size="sm" | "md"
       dot?: boolean       // show colored dot instead of background
/>
```

### `<Dot />` — Presence Indicator
```tsx
<Dot status="active" | "thinking" | "away" | "error"
     size="sm" | "md" | "lg"
     pulse?: boolean       // animate the dot
/>
```

### `<Avatar />`
```tsx
<Avatar src?: string
        name: string       // for fallback initials
        size={24 | 32 | 40 | 48}
        status?: "active" | "away"
/>
```

### `<Spinner />`
```tsx
<Spinner size="sm" | "md" | "lg"
         color?: "brand" | "muted"
/>
```

### `<Divider />`
```tsx
<Divider orientation="horizontal" | "vertical"
         className?: string
/>
```

---

## Tier 2 — Base Components

Composed from Tier 1 primitives. Functional UI atoms.

### `<Button />`
```tsx
<Button variant="primary" | "secondary" | "ghost" | "destructive"
        size="sm" | "md" | "lg"
        icon?: ReactNode
        iconPosition?: "left" | "right"
        loading?: boolean
        disabled?: boolean
        onClick: () => void
/>
```
**States:** default → hover → active (scale 0.97) → loading → disabled

### `<Input />`
```tsx
<Input label?: string
       placeholder?: string
       error?: string
       hint?: string
       icon?: ReactNode
       size="sm" | "md"
       disabled?: boolean
/>
```

### `<Textarea />`
```tsx
<Textarea label?: string
          maxRows?: number     // auto-grows up to maxRows
          placeholder?: string
/>
```

### `<Toggle />`
```tsx
<Toggle checked: boolean
        onChange: (v: boolean) => void
        label?: string
        disabled?: boolean
/>
```

### `<Select />` — via Radix UI
```tsx
<Select options: { value: string; label: string }[]
        value: string
        onChange: (v: string) => void
        placeholder?: string
        searchable?: boolean
/>
```

### `<Tooltip />` — via Radix UI
```tsx
<Tooltip content: string | ReactNode
         side?: "top" | "bottom" | "left" | "right"
         delay?: number
/>
```

### `<Popover />` — via Radix UI
```tsx
<Popover trigger: ReactNode
         content: ReactNode
         align?: "start" | "center" | "end"
/>
```

### `<Kbd />`
```tsx
<Kbd keys: string[]    // e.g. ["⌘", "K"]
/>
```

### `<Toast />`
```tsx
<Toast type="success" | "error" | "info" | "warning"
       title: string
       description?: string
       action?: { label: string; onClick: () => void }
       duration?: number   // ms, default 4000
/>
```

---

## Tier 3 — Card Primitives (Core System)

The 9 reusable cards that all screens are assembled from.  
Full specification: see [`COMPONENT_INVENTORY.md`](../COMPONENT_INVENTORY.md)

| Card | Import |
|------|--------|
| `<ConversationCard />` | `@/cards/ConversationCard` |
| `<ContextCard />` | `@/cards/ContextCard` |
| `<RecommendationCard />` | `@/cards/RecommendationCard` |
| `<NotificationCard />` | `@/cards/NotificationCard` |
| `<ActionCard />` | `@/cards/ActionCard` |
| `<TimelineCard />` | `@/cards/TimelineCard` |
| `<StatusCard />` | `@/cards/StatusCard` |
| `<KPICard />` | `@/cards/KPICard` |
| `<SystemCard />` | `@/cards/SystemCard` |

### Card Composition Rules
1. All cards use `bg-surface-elevated border border-border-subtle rounded-lg`
2. Default padding: `p-4` (16px)
3. Card titles: `text-sm font-semibold text-text-primary`
4. Card metadata: `text-xs text-text-muted`
5. Max width in center panel: `680px`
6. Cards never have colored backgrounds — only border-left accents for semantic meaning

### Card Border-Left Accents
```css
.card-brand   { border-left: 3px solid #7C6FF7; }  /* capability result */
.card-success { border-left: 3px solid #34D399; }  /* confirmed action */
.card-warning { border-left: 3px solid #FBBF24; }  /* pending action */
.card-error   { border-left: 3px solid #F87171; }  /* failed action */
```

---

## Tier 4 — Layout Components

High-level structure components. Used once per app.

### `<Shell />`
Root layout grid. Manages the 4-zone operating surface.
```tsx
<Shell>
  <Shell.TopBar />
  <Shell.Sidebar />
  <Shell.Center />
  <Shell.ContextPanel />
  <Shell.InputBar />
</Shell>
```

### `<Sidebar />`
```tsx
<Sidebar collapsed?: boolean      // icon-only mode (tablet)
         onCollapse: () => void
>
  <Sidebar.Nav />
  <Sidebar.ConversationList />
  <Sidebar.Footer />
</Sidebar>
```

### `<TopBar />`
```tsx
<TopBar companionStatus: "active" | "thinking" | "away" | "error"
        userName: string
        notificationCount?: number
        onSearch: () => void
/>
```

### `<ContextPanel />`
```tsx
<ContextPanel open?: boolean
              onClose: () => void
>
  {/* accepts any card composition */}
</ContextPanel>
```

### `<InputBar />`
```tsx
<InputBar onSend: (message: string) => void
          disabled?: boolean
          placeholder?: string
          onAttach?: () => void
          onVoice?: () => void
/>
```

### `<ConversationThread />`
```tsx
<ConversationThread messages: Message[]
                    isLoading?: boolean
                    onActionConfirm?: (action: string) => void
/>
```

---

## Tier 5 — Patterns

Composed from cards + layout components. Named, reusable interaction patterns.

### `<CompanionMessage />`
A complete companion turn: avatar + message text + optional ActionCard inline.
```tsx
<CompanionMessage role="assistant" | "user"
                  content: string
                  timestamp: string
                  capabilityResult?: ActionCardProps
                  suggestedActions?: string[]
/>
```

### `<WorkflowProgress />`
Shows a TimelineCard with live step progress.
```tsx
<WorkflowProgress workflowName: string
                  steps: WorkflowStep[]
                  currentStep: number
                  status: "running" | "completed" | "failed"
/>
```

### `<CapabilityResult />`
An ActionCard variant specialized for right-panel display.
```tsx
<CapabilityResult capability: string
                  result: CapabilityResultData
                  onConfirm?: () => void
                  onEdit?: () => void
                  onDismiss?: () => void
/>
```

### `<KnowledgeResponse />`
A SystemCard specialized for UniGuru educational output.
```tsx
<KnowledgeResponse query: string
                   answer: string
                   source?: string
                   followups?: string[]
                   onFollowup?: (q: string) => void
/>
```

### `<EmptyState />`
```tsx
<EmptyState icon?: ReactNode
            title: string
            description?: string
            action?: { label: string; onClick: () => void }
/>
```

### `<SkeletonCard />`
```tsx
<SkeletonCard lines?: number   // default 3
              showAvatar?: boolean
              className?: string
/>
```

---

## shadcn/ui Primitives Used

These are used as base implementations, overridden with Mitra tokens:

| shadcn Component | Mitra Override |
|-----------------|---------------|
| `Button` | Full style override with brand tokens |
| `Input` | Border and focus tokens applied |
| `Select` | Dropdown styled to dark surface |
| `Dialog` | Backdrop blur + surface-elevated |
| `Popover` | surface-elevated + border-subtle |
| `Tooltip` | 11px, surface-overlay |
| `Toast` | Slide-in from top-right, auto-dismiss |
| `Sheet` | Used for mobile sidebar drawer |

---

## Component Rules

### Do
- Export all components from their index file
- Always accept `className` prop for extension
- Always define `displayName` for React DevTools
- Use `forwardRef` for all interactive components
- Co-locate component tests with component files

### Don't
- Don't use `!important` overrides
- Don't embed data-fetching inside card components
- Don't use inline styles — use Tailwind classes only
- Don't create page-specific components — create patterns instead
- Don't use `any` in TypeScript — define proper interfaces
