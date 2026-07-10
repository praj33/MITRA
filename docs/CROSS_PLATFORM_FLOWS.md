# Mitra Cross-Platform Interaction Flows

**Version:** v4.0.0 | **Last Updated:** July 2026

---

## Overview

Mitra delivers a consistent companion experience across all screen sizes and platforms. The shared experience layer ensures that regardless of device, users interact with the same companion identity, memory, and capabilities.

---

## Platform Matrix

| Platform | Interface | Layout | Navigation | Companion Access |
|----------|-----------|--------|-----------|------------------|
| **Desktop** (≥1024px) | Web (React) | 3-panel grid | Expanded sidebar | Always visible |
| **Tablet** (768–1023px) | Web (React) | 2-panel + overlay | Icon sidebar | Toggle context |
| **Mobile** (<768px) | Web (React) | Single column | Bottom nav + drawers | Hamburger + drawers |
| **WhatsApp** | Webhook | Chat thread | N/A | Direct messaging |
| **Telegram** | Webhook | Chat thread | N/A | Direct messaging |
| **Email** | Webhook | Inbox | N/A | Reply-based |
| **Telephony** | Webhook | Voice | N/A | Voice commands |

---

## Shared Experience Layer

All platforms share:
1. **Identity** — Same user_id, same companion name and personality
2. **Memory** — Facts, preferences, and conversation history persist across devices
3. **Capabilities** — Same 11 capabilities available on all platforms
4. **Safety Pipeline** — Every input goes through Safety → Enforcement regardless of channel
5. **Trace Continuity** — All interactions are logged with deterministic trace IDs

```
┌─────────────────────────────────────────────────────┐
│                  Shared Backend API                  │
│  CompanionOrchestrator → CapabilityRegistry          │
│  SessionManager → CompanionMemory → PersonalityEngine│
│  LLMBridge → WorkflowEngine                          │
└─────────────────┬──────────────────┬────────────────┘
                  │                  │
    ┌─────────────▼──┐    ┌────────▼──────────┐
    │  Web Frontend   │    │  Inbound Channels  │
    │  (React SPA)    │    │  WhatsApp/Telegram  │
    │  Desktop/Tablet │    │  Email/Telephony    │
    │  Mobile         │    │                     │
    └────────────────┘    └─────────────────────┘
```

---

## Flow 1: Conversational Chat (Web)

```
User types → InputBar.onSend()
  → CompanionService.chat(user_id, message)
    → POST /api/companion/chat
      → companion_orchestrator.process_message()
        → IntentFlow.classify(message)
        → IF capability match:
            → capability_registry.execute(intent, params)
            → CapabilityResult returned inline
        → ELSE:
            → personality_engine.build_system_prompt()
            → session_manager.get_history() (last 20 turns)
            → llm_bridge.call_llm_with_messages()
        → companion_memory.log_capability_use()
        → session_manager.add_turn()
      → CompanionResponse returned
  → Zustand store.addMessage()
  → ConversationCard rendered with animation
```

### Mobile-Specific Behavior
- Enter key creates newline (send via button)
- Input textarea uses 16px font (prevents iOS zoom)
- Quick actions visible via ⚡ toggle
- Bottom navigation for section switching

---

## Flow 2: Capability Execution (Web)

```
User: "Draft an email to John about tomorrow's meeting"
  → IntentFlow classifies: intent = "draft_email"
  → CapabilityRegistry.resolve("draft_email") → EmailCapability
  → EmailCapability.execute(intent="draft_email", params={...})
  → CapabilityResult {
      capability: "email",
      status: "success",
      summary: "Email draft created.",
      data: { draft_id: "...", preview: "..." }
    }
  → Rendered as ActionCard inline in conversation thread
  → Context panel updated with capability result
```

---

## Flow 3: Workflow Execution (Web)

```
User: "Run my morning briefing"
  → IntentFlow classifies: intent = "workflow:morning_briefing"
  → WorkflowEngine.run("morning_briefing", user_id)
    → Step 1: CalendarCapability.execute("list_events")
    → Step 2: EmailCapability.execute("read_emails")
    → Step 3: TaskCapability.execute("list_tasks")
    → Step 4: ReminderCapability.execute("list_reminders") [optional]
  → WorkflowResult {
      status: "completed",
      steps_completed: 4/4,
      summary: "3 events today | 5 unread emails | 10 pending tasks"
    }
  → Rendered as multi-step summary in conversation
```

---

## Flow 4: Inbound WhatsApp Message

```
WhatsApp Cloud API → POST /webhook/whatsapp
  → inbound_gateway.process_message()
    → Normalize to canonical payload
    → assistant_orchestrator.process()
      → Safety → Intelligence → Enforcement → Execution
    → Response sent back via WhatsApp Cloud API
  → Bucket logs entire trace
```

---

## Flow 5: Inbound Telegram Message

```
Telegram Bot API → POST /webhook/telegram
  → telegram_handler.handle()
    → inbound_gateway.process_message()
    → Same pipeline as WhatsApp
  → Response sent via Telegram Bot API
```

---

## Flow 6: Inbound Email

```
Email service → POST /webhook/email
  → email_handler.handle()
    → Parse subject + body
    → inbound_gateway.process_message()
    → Same pipeline
  → Response sent as reply email
```

---

## Flow 7: Voice/Telephony

```
Telephony service → POST /webhook/telephony
  → Audio STT → text
  → inbound_gateway.process_message()
  → Same pipeline
  → Response → TTS → Audio reply
```

---

## Responsive Behavior Summary

### Desktop (≥1024px)
- Full sidebar with labels (220px)
- Center conversation panel (flexible)
- Right context panel (280px)
- Keyboard shortcuts (⌘K search, Enter send)

### Tablet (768–1023px)
- Collapsed icon-only sidebar (64px)
- Full-width center panel
- Context panel as fixed overlay (triggered by button)
- Same keyboard shortcuts

### Mobile (<768px)
- No inline sidebar (hamburger → full-height drawer)
- Full-width conversation
- Bottom navigation bar (6 tabs)
- Context panel as slide-over sheet (right)
- Touch-optimized: 36px min tap targets
- Safe area insets for notched phones
- `100dvh` for mobile browser chrome

---

## Client Adapters

Prepared adapter specifications for future native implementations:

| Adapter | Location | Status |
|---------|----------|--------|
| Web | `client_adapters/web_adapter.md` | ✅ Active (React SPA) |
| Android | `client_adapters/android_adapter.md` | 📋 Spec ready |
| iOS | `client_adapters/ios_adapter.md` | 📋 Spec ready |
| macOS | `client_adapters/macos_adapter.md` | 📋 Spec ready |
| Windows | `client_adapters/windows_adapter.md` | 📋 Spec ready |

All native adapters consume the same REST API and share the same companion session.
