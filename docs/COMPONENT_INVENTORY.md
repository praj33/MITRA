# Mitra — Component Inventory
**Version:** v4.0 | Design System Foundation

---

## The 9 Card Primitives

All Mitra screens are assembled from these 9 reusable card types.  
No screen should need a custom layout that isn't built from these.

---

### 1. Conversation Card

**Purpose:** Represents a past or ongoing companion conversation in the sidebar list.

**Props:**
```typescript
interface ConversationCardProps {
  id: string
  title: string                          // first message truncated
  preview: string                        // last companion response preview
  timestamp: string                      // relative: "2m ago", "Yesterday"
  isActive: boolean                      // currently selected
  hasUnread?: boolean                    // unread indicator
  capabilityUsed?: string[]              // icons for capabilities used
}
```

**States:** default | hover | active | unread

**Variants:**
- `compact` — sidebar list (title + timestamp + dot)
- `expanded` — search results (title + preview + capabilities used)

**Responsive:** Hidden on mobile (drawer), list on tablet/desktop

---

### 2. Context Card

**Purpose:** Shows contextual information relevant to the current companion interaction. Lives in the right panel.

**Props:**
```typescript
interface ContextCardProps {
  title: string
  subtitle?: string
  content: React.ReactNode
  source?: string                        // "From calendar", "From notes"
  actions?: ActionItem[]
  isCollapsible?: boolean
}
```

**States:** default | loading | collapsed | error

**Variants:**
- `calendar` — shows event details (time, location, attendees)
- `task` — shows task with status chip and due date
- `note` — shows note content with edit action
- `contact` — shows contact card with quick-action buttons
- `document` — shows document title with open/summarize actions

---

### 3. Recommendation Card

**Purpose:** Proactive suggestions from companion — shown when companion detects an opportunity.

**Props:**
```typescript
interface RecommendationCardProps {
  title: string
  description: string
  confidence: 'high' | 'medium'          // controls visual weight
  actions: {
    primary: { label: string; onClick: () => void }
    secondary?: { label: string; onClick: () => void }
  }
  onDismiss: () => void
  icon?: string
}
```

**States:** default | accepted | dismissed | loading

**Variants:**
- `workflow` — "Ready to run your morning briefing?"
- `reminder` — "You have a meeting in 15 minutes"
- `followup` — "You haven't replied to John's email from 2 days ago"
- `suggestion` — "You usually draft your weekly summary on Fridays"

---

### 4. Notification Card

**Purpose:** System alerts, reminders, and time-sensitive information.

**Props:**
```typescript
interface NotificationCardProps {
  id: string
  type: 'reminder' | 'alert' | 'info' | 'success' | 'warning' | 'error'
  title: string
  body?: string
  timestamp: string
  isRead: boolean
  action?: { label: string; onClick: () => void }
  onDismiss: () => void
}
```

**States:** unread | read | dismissed | loading

**Color coding:** uses semantic tokens — success/warning/error/info

---

### 5. Action Card

**Purpose:** Shows the result of a capability invocation inline in the conversation thread.

**Props:**
```typescript
interface ActionCardProps {
  capability: 'email' | 'calendar' | 'whatsapp' | 'reminder' | 
              'task' | 'notes' | 'contacts' | 'browser' | 'document'
  status: 'success' | 'error' | 'loading' | 'pending_confirm'
  title: string
  summary: string
  result?: Record<string, any>           // capability-specific result data
  actions?: {
    confirm?: () => void                 // "Send this email"
    edit?: () => void                    // "Edit draft"
    retry?: () => void                   // on error
    undo?: () => void                    // on success
  }
  traceId?: string                       // Mitra safety trace
}
```

**States:** loading | success | error | pending_confirm | confirmed

**Variants (per capability):**
- `email` — shows To, Subject, preview body + Send/Edit buttons
- `calendar` — shows date, time, title + Schedule/Modify buttons
- `reminder` — shows time, message + Set/Modify buttons
- `task` — shows title, priority, due date + Create/Edit buttons

---

### 6. Timeline Card

**Purpose:** Shows a sequence of events, workflow steps, or conversation moments.

**Props:**
```typescript
interface TimelineCardProps {
  items: {
    id: string
    time: string
    title: string
    description?: string
    status: 'completed' | 'active' | 'pending' | 'failed'
    icon?: string
    capability?: string
  }[]
  title?: string
  showConnectors?: boolean
}
```

**States:** loading | populated | empty

**Use cases:**
- Workflow execution progress
- Morning briefing output
- Meeting preparation steps
- Conversation history summary

---

### 7. Status Card

**Purpose:** System health, connection status, and service availability at a glance.

**Props:**
```typescript
interface StatusCardProps {
  title: string
  status: 'operational' | 'degraded' | 'unavailable' | 'loading'
  services?: {
    name: string
    status: 'ok' | 'warn' | 'error'
    latency?: number
  }[]
  lastChecked?: string
  compact?: boolean
}
```

**Variants:**
- `companion` — Mitra companion status (LLM provider, safety engine)
- `capabilities` — capability service statuses
- `system` — overall system health

---

### 8. KPI Card

**Purpose:** Quick metric displays for intelligence dashboards and workflow summaries.

**Props:**
```typescript
interface KPICardProps {
  label: string
  value: string | number
  unit?: string
  trend?: {
    direction: 'up' | 'down' | 'flat'
    value: string
    label: string
  }
  size?: 'sm' | 'md' | 'lg'
  color?: 'default' | 'brand' | 'success' | 'warning' | 'error'
}
```

**Use cases:**
- "5 emails today" (inbox count)
- "3 meetings" (calendar summary)
- "12 tasks pending" (task count)
- "2 unread notifications"

---

### 9. System Card

**Purpose:** Companion-generated structured output — rich responses beyond plain text.

**Props:**
```typescript
interface SystemCardProps {
  type: 'knowledge' | 'summary' | 'comparison' | 'list' | 'code' | 'table'
  title?: string
  content: React.ReactNode
  source?: string
  expandable?: boolean
  copyable?: boolean
  followups?: string[]                   // suggested follow-up questions
}
```

**Variants:**
- `knowledge` — UniGuru educational response with sections
- `summary` — condensed document/email/conversation summary
- `list` — structured list from companion
- `code` — code block with syntax highlighting
- `comparison` — side-by-side comparison

---

## Component State Matrix

| Component | Loading | Empty | Error | Hover | Active | Disabled |
|-----------|---------|-------|-------|-------|--------|---------|
| ConversationCard | ✅ | ✅ | — | ✅ | ✅ | — |
| ContextCard | ✅ | ✅ | ✅ | — | — | — |
| RecommendationCard | ✅ | — | — | ✅ | ✅ | ✅ |
| NotificationCard | — | — | — | ✅ | ✅ | — |
| ActionCard | ✅ | — | ✅ | ✅ | — | — |
| TimelineCard | ✅ | ✅ | ✅ | — | — | — |
| StatusCard | ✅ | — | ✅ | — | — | — |
| KPICard | ✅ | — | — | — | — | — |
| SystemCard | — | — | — | — | — | — |

---

## Component File Structure

```
frontend/frontend/src/
├── design-system/
│   ├── tokens.ts              ← design tokens
│   ├── themes/
│   │   └── dark.ts
│   └── index.ts
├── primitives/
│   ├── Text.tsx
│   ├── Icon.tsx
│   ├── Badge.tsx
│   ├── Dot.tsx
│   ├── Avatar.tsx
│   ├── Divider.tsx
│   ├── Spinner.tsx
│   └── index.ts
├── components/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Textarea.tsx
│   ├── Toggle.tsx
│   └── index.ts
├── cards/
│   ├── ConversationCard.tsx
│   ├── ContextCard.tsx
│   ├── RecommendationCard.tsx
│   ├── NotificationCard.tsx
│   ├── ActionCard.tsx
│   ├── TimelineCard.tsx
│   ├── StatusCard.tsx
│   ├── KPICard.tsx
│   ├── SystemCard.tsx
│   └── index.ts
├── layouts/
│   ├── Shell.tsx              ← root layout
│   ├── Sidebar.tsx
│   ├── TopBar.tsx
│   ├── ContextPanel.tsx
│   ├── InputBar.tsx
│   └── ConversationThread.tsx
└── patterns/
    ├── CompanionMessage.tsx   ← message + inline action card
    ├── WorkflowProgress.tsx   ← timeline pattern
    ├── CapabilityResult.tsx   ← action card pattern
    └── KnowledgeResponse.tsx  ← system card pattern
```

---

## Zustand Store Structure

```typescript
// stores/companion.store.ts
interface CompanionStore {
  // Session
  session: CompanionSession | null
  setSession: (session: CompanionSession) => void

  // Conversations
  conversations: Conversation[]
  activeConversationId: string | null
  setActiveConversation: (id: string) => void
  addMessage: (conversationId: string, message: Message) => void

  // Capabilities
  activeCapabilityResult: ActionCardProps | null
  setCapabilityResult: (result: ActionCardProps | null) => void

  // UI state
  isSidebarOpen: boolean
  isContextPanelOpen: boolean
  toggleSidebar: () => void
  toggleContextPanel: () => void

  // Companion status
  companionStatus: 'active' | 'thinking' | 'away' | 'error'
  setCompanionStatus: (status: CompanionStore['companionStatus']) => void
}
```
