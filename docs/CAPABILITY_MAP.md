# Mitra Capability Map

**Version:** v4.0.0 | **Last Updated:** July 2026

---

## Overview

Mitra's capabilities are modular, independently attachable interfaces registered at runtime via `CapabilityRegistry`. No capability is hardcoded. All capabilities extend `BaseCapability` and are invoked through a uniform `execute(intent, params, trace_id)` interface.

```
User Message → IntentFlow → CapabilityRegistry.resolve(intent) → Capability.execute() → CapabilityResult
```

---

## Capability Registry Architecture

```
┌─────────────────────────────────────────────────┐
│              CapabilityRegistry                  │
│  register() / unregister() / resolve(intent)    │
│                                                  │
│  Intent Map:                                     │
│    "draft_email"     → EmailCapability           │
│    "create_event"    → CalendarCapability         │
│    "send_whatsapp"   → WhatsAppCapability         │
│    "create_task"     → TaskCapability             │
│    "create_reminder" → ReminderCapability         │
│    "create_note"     → NotesCapability            │
│    "lookup_contact"  → ContactsCapability         │
│    "web_search"      → BrowserCapability          │
│    "send_notification"→ NotificationCapability    │
│    "upload_document" → DocumentCapability         │
│    "knowledge"       → UniGuruCapability          │
└─────────────────────────────────────────────────┘
```

---

## Capability Details

### 1. Email (`email_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/email_capability.py` |
| **Intents** | `draft_email`, `send_email`, `read_emails` |
| **Description** | Compose, read, search, and send emails |
| **Dependencies** | Brevo API (production), simulated (dev) |

### 2. Calendar (`calendar_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/calendar_capability.py` |
| **Intents** | `create_event`, `list_events`, `check_availability` |
| **Description** | Create, view, and manage calendar events |
| **Dependencies** | MongoDB (event store) |

### 3. WhatsApp (`whatsapp_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/whatsapp_capability.py` |
| **Intents** | `send_whatsapp`, `check_messages` |
| **Description** | Send WhatsApp messages via Cloud API |
| **Dependencies** | WhatsApp Cloud API (production), simulated (dev) |

### 4. Task (`task_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/task_capability.py` |
| **Intents** | `create_task`, `list_tasks`, `update_task` |
| **Description** | Create, update, and track tasks |
| **Dependencies** | MongoDB (task store) |

### 5. Reminder (`reminder_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/reminder_capability.py` |
| **Intents** | `create_reminder`, `list_reminders`, `cancel_reminder` |
| **Description** | Set, list, and cancel time-based reminders |
| **Dependencies** | MongoDB (reminder store) |

### 6. Notes (`notes_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/notes_capability.py` |
| **Intents** | `create_note`, `list_notes`, `search_notes` |
| **Description** | Create and retrieve notes with search |
| **Dependencies** | MongoDB (notes store) |

### 7. Contacts (`contacts_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/contacts_capability.py` |
| **Intents** | `lookup_contact`, `add_contact`, `list_contacts` |
| **Description** | Look up and manage contact records |
| **Dependencies** | MongoDB (contacts store) |

### 8. Browser (`browser_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/browser_capability.py` |
| **Intents** | `web_search`, `summarize_page` |
| **Description** | Search the web and summarize pages |
| **Dependencies** | LLM Bridge (search synthesis) |

### 9. Notification (`notification_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/notification_capability.py` |
| **Intents** | `send_notification`, `list_notifications` |
| **Description** | Send notifications across channels |
| **Dependencies** | Push notification service |

### 10. Document (`document_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/document_capability.py` |
| **Intents** | `upload_document`, `summarize_document`, `search_document` |
| **Description** | Upload, read, and summarize documents |
| **Dependencies** | LLM Bridge (summarization) |

### 11. UniGuru (`uniguru_capability.py`)
| Property | Value |
|----------|-------|
| **Module** | `app/capabilities/uniguru_capability.py` |
| **Intents** | `uniguru`, `knowledge`, `explain`, `learn`, `study`, `educational` |
| **Description** | Knowledge retrieval and educational conversations |
| **Dependencies** | UniGuru v2 API (`uniguru-v2.onrender.com`) with LLM fallback |

---

## Adding a New Capability

```python
# 1. Create capability file: app/capabilities/my_capability.py
from app.capabilities.base_capability import BaseCapability, CapabilityResult

class MyCapability(BaseCapability):
    @property
    def name(self) -> str: return "my_capability"
    
    @property
    def description(self) -> str:
        return "What this capability does."
    
    @property
    def supported_intents(self) -> list:
        return ["my_intent_1", "my_intent_2"]
    
    async def execute(self, intent, params, trace_id=None) -> CapabilityResult:
        # Implementation here
        return CapabilityResult(
            capability=self.name, intent=intent,
            status="success", summary="Done.",
            data={"result": "..."},
            trace_id=trace_id,
        )

# 2. Register in app/capabilities/__init__.py
from app.capabilities.my_capability import MyCapability
capability_registry.register(MyCapability())
```

No other code changes required. The capability is automatically discoverable via `CapabilityRegistry.list_capabilities()` and routable via `CapabilityRegistry.resolve(intent)`.

---

## Workflow Integration

Capabilities are composable into multi-step workflows via `WorkflowEngine`:

| Workflow | Steps | Capabilities Used |
|----------|-------|-------------------|
| `morning_briefing` | 4 | calendar, email, task, reminder |
| `meeting_prep` | 3 | calendar, notes, reminder |
| `email_followup` | 2 | email |
| `weekly_review` | 4 | task, notes, calendar, email |
| `quick_reminder` | 1 | reminder |

Custom workflows can be registered at runtime via `workflow_engine.register_workflow()`.

---

## Base Capability Interface

```python
class BaseCapability(ABC):
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str: ...
    @property
    def supported_intents(self) -> List[str]: ...
    
    async def execute(self, intent: str, params: Dict, trace_id: str = None) -> CapabilityResult: ...
    def can_handle(self, intent: str) -> bool: ...
```

## CapabilityResult Schema

```python
@dataclass
class CapabilityResult:
    capability: str       # "email", "calendar", etc.
    intent: str           # "draft_email", "create_event", etc.
    status: str           # "success" | "error" | "pending" | "not_found"
    summary: str          # Human-readable one-line summary
    data: Dict[str, Any]  # Capability-specific payload
    actions: List[Dict]   # Follow-up action suggestions
    error: Optional[str]  # Error message if status == "error"
    trace_id: Optional[str]
```
