# Mitra — Premium Experience Guide
**Motion, Transitions, Feedback, Loading, Empty, Error Systems**

---

## Motion Principles

### The 3 Rules
1. **Motion communicates state, not decoration.** Every animation must answer: "What changed?"
2. **Motion should never block the user.** Animations run at 150–250ms. Never longer for UI transitions.
3. **Motion has direction and origin.** Elements slide from where they came from. Panels slide from their edge.

### When to Animate
| Trigger | Animation | Duration |
|---------|-----------|---------|
| New message arrives | Fade in + slide up 8px | 250ms |
| Capability result appears | Context panel slides in from right | 300ms |
| Sidebar opens (mobile) | Slide from left | 250ms |
| Card appears | Fade in + scale from 0.96 | 200ms |
| Notification appears | Slide down from top | 200ms |
| Modal opens | Fade in + scale from 0.95 | 200ms |
| Companion thinking | Dot pulse animation | Loop |
| Page/zone transition | Crossfade | 150ms |
| Button click feedback | Scale 0.97 on press | 80ms |

### When NOT to Animate
- Typing in input fields
- Scrolling
- Text content changes
- Background data fetching
- Color/theme changes

---

## Framer Motion Patterns

### Standard Card Entry
```typescript
const cardVariants = {
  hidden:  { opacity: 0, y: 8, scale: 0.98 },
  visible: { 
    opacity: 1, y: 0, scale: 1,
    transition: { duration: 0.25, ease: [0.0, 0.0, 0.2, 1] }
  }
}

// Usage
<motion.div variants={cardVariants} initial="hidden" animate="visible">
  <ConversationCard {...props} />
</motion.div>
```

### Staggered List Entry
```typescript
const listVariants = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.04 } }
}

const itemVariants = {
  hidden:  { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.2 } }
}

// Usage: wraps conversation list, notification list
<motion.ul variants={listVariants} initial="hidden" animate="visible">
  {items.map(item => (
    <motion.li key={item.id} variants={itemVariants}>
      <ConversationCard {...item} />
    </motion.li>
  ))}
</motion.ul>
```

### Context Panel Slide-In
```typescript
const contextPanelVariants = {
  hidden:  { x: 32, opacity: 0 },
  visible: { 
    x: 0, opacity: 1,
    transition: { duration: 0.3, ease: [0.0, 0.0, 0.2, 1] }
  },
  exit: { 
    x: 32, opacity: 0,
    transition: { duration: 0.2 }
  }
}

// Usage: AnimatePresence wrapping ContextPanel
<AnimatePresence mode="wait">
  {isContextPanelOpen && (
    <motion.aside variants={contextPanelVariants} initial="hidden" 
                  animate="visible" exit="exit">
      <ContextPanel />
    </motion.aside>
  )}
</AnimatePresence>
```

### Companion Thinking Indicator
```typescript
// Three dots with staggered pulse
const dotVariants = {
  pulse: {
    scale: [1, 1.3, 1],
    opacity: [0.5, 1, 0.5],
    transition: { duration: 1.2, repeat: Infinity, ease: 'easeInOut' }
  }
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-1 items-center px-3 py-2">
      {[0, 0.15, 0.3].map((delay, i) => (
        <motion.span key={i}
          className="w-1.5 h-1.5 rounded-full bg-brand"
          variants={dotVariants}
          animate="pulse"
          transition={{ delay }}
        />
      ))}
    </div>
  )
}
```

---

## Loading States

### Skeleton Cards
All cards have a skeleton variant for loading states.
Skeleton uses `bg-surface-overlay animate-pulse` pattern.

```typescript
// Skeleton pattern — consistent across all cards
function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="p-4 rounded-lg bg-surface-elevated border border-border-subtle space-y-3">
      <div className="h-3 bg-surface-overlay rounded animate-pulse w-2/3" />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} 
          className={`h-2.5 bg-surface-overlay rounded animate-pulse ${
            i === lines - 1 ? 'w-1/2' : 'w-full'
          }`} 
        />
      ))}
    </div>
  )
}
```

### Global Loading Indicator
- Top bar shows a 2px brand-colored progress bar
- Companion status dot changes to `thinking` (amber pulse)
- Input bar disabled during companion response

---

## Empty States

**Rule:** Never show "Nothing here" — always show what the user can do.

### Conversation Thread (first session)
```
[Mitra avatar]
Good morning, [Name].
I'm ready when you are.

[Quick start suggestions — 3 chips:]
"What's on my calendar today?" 
"Check my emails"
"Set a reminder"
```

### Capability Panel (no result yet)
```
[Subtle icon for the capability]
Ask me to help with [capability name]
[small text: "e.g. 'schedule a meeting tomorrow at 2pm'"]
```

### Notification Panel (all clear)
```
[Small checkmark icon]
You're all caught up.
```

### Workflow Center (no workflows)
```
[Workflow icon]
No workflows yet.
[Button: "Try 'morning briefing'"]
```

---

## Error States

### Inline Error (card-level)
```typescript
// All cards receive error state
function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg 
                    bg-error-soft border border-error/20 text-sm">
      <Icon name="alert-circle" className="text-error shrink-0" size={16} />
      <span className="text-text-secondary">{message}</span>
      {onRetry && (
        <button onClick={onRetry} 
          className="ml-auto text-error hover:text-error/80 text-xs font-medium">
          Retry
        </button>
      )}
    </div>
  )
}
```

### Companion Error (safety block)
The companion responds with a calm, human message — never exposes technical error:
```
"I can't help with that particular request. 
 Is there something else I can help you with?"
```
Never shows: "BLOCKED by Mitra policy" or any internal system language.

### Network Offline
- Top bar shows a subtle amber indicator: `● Reconnecting...`
- Input bar shows: `"You're offline — messages will send when you reconnect"`
- No full-page error overlay

### Capability Failure
Action Card shows error state with:
- Red border-left accent
- Error icon
- Short message: "Couldn't create the event. Calendar may be unavailable."
- Retry button

---

## R3F Ambient Concepts (Optional Enhancement)

**Rule:** The product must work 100% without these. They are ambient enhancement only.

### Presence Orb (companion status)
A soft, breathing 3D sphere next to the companion avatar.
- Calm pulse when idle
- Faster ripple when thinking
- Steady glow when responding
- Implemented as a small `<Canvas>` (48×48px), not full-screen

### State Transition Particles
Subtle particle field that briefly activates during:
- Session start
- Workflow completion
- Major capability success

Implementation: `<Canvas>` absolutely positioned behind the top bar, opacity 0.15, z-index -1.

### Focus Mode Ambient
When user enters "focus mode" (fullscreen conversation):
- Background dims slightly
- A very subtle noise texture appears
- Canvas renders a slow, drifting gradient field
- Removed immediately on exit

**Never use R3F for:**
- Cards, lists, or any interactive UI
- Navigation or transitions
- Loading states
- Anything that affects layout

---

## Feedback Systems

### Micro-feedback (button press)
```typescript
// Scale feedback on all interactive elements
className="active:scale-[0.97] transition-transform duration-75"
```

### Success Confirmation
- Action Card border briefly turns success-green (300ms)
- Companion confirms inline in text
- No modal, no full-screen overlay

### Capability in Progress
- Action Card shows loading skeleton
- Companion status dot shows amber (thinking)
- Input bar placeholder: "Working on it..."

### Copy Feedback
- Copy button icon changes to checkmark for 1500ms
- No toast notification for simple copies

### Toast Notifications
Used sparingly — only for:
- Background workflow completions
- Errors that happened outside the current view
- "Undo" opportunities

Toast position: top-right, 320px wide, auto-dismiss at 4s
