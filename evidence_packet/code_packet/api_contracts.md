# API Contracts — Phase 1 Canonical Lock

---

## 1. Primary Conversation Endpoint
- **URL**: `POST /api/companion/chat`
- **Payload**:
```json
{
  "message": "What is on my schedule today?",
  "user_id": "user_123",
  "app_id": "gurukul",
  "platform": "web"
}
```

---

## 2. Authentication Handshake
- **URL**: `POST /api/companion/auth`
- **Payload**:
```json
{
  "app_id": "gurukul",
  "user_id": "user_123",
  "auth_token": "token_abc"
}
```

---

## 3. Cross-Application State Persistence
- **URL**: `POST /api/companion/state`
- **Payload**:
```json
{
  "user_id": "user_123",
  "app_id": "gurukul",
  "active_section": "calendar",
  "theme": "dark"
}
```

---

## 4. Governed Execution Endpoint
- **URL**: `POST /api/companion/execute`
- **Payload**:
```json
{
  "capability": "task_management",
  "intent": "create_task",
  "params": { "title": "Submit Assignment" },
  "user_id": "user_123"
}
```
