# UX Translation Map
**Phase C: Demo-Ready Human-Grade Assistant UX**  
**Owner: Chandragupta Maurya**  
**Date: January 22, 2026**

---

## Purpose
This document maps all engineering artifacts to human-readable UX language for the AI Assistant demo. The goal: **Any first-time user instantly understands what the assistant did and what happens next** in under 60 seconds.

---

## Core UX Principles Applied

### 1. **Calm Technology**
- No cognitive overload
- Information appears only when needed
- Consistent, predictable interactions

### 2. **Explain Without Exposing**
- Users understand outcomes without seeing internals
- No trace IDs, enforcement labels, or system statuses
- Actions are clear, not technical

### 3. **Reassuring by Default**
- Errors don't panic
- Failures provide next steps
- Success is obvious and encouraging

---

## Translation Tables

### A. Intent Translation
**System Internal** → **User-Facing**

| System Value | User Sees |
|-------------|-----------|
| `question` | "Ask a question" |
| `task_creation` | "Create a task" |
| `schedule` | "Schedule something" |
| `reminder` | "Set a reminder" |
| `information` | "Get information" |
| `unknown` | "General request" |

**Implementation:** `utils/translations.ts` → `translateIntent()`

---

### B. Task Type Translation
**System Internal** → **User-Facing**

| System Value | User Sees |
|-------------|-----------|
| `work_task` | "Work Task" |
| `personal_task` | "Personal Task" |
| `quick_note` | "Quick Note" |
| `_` (underscore) | " " (space, title case) |

**Implementation:** `utils/translations.ts` → `translateTaskType()`

---

### C. Action Status Translation
**System Internal** → **User-Facing**

| System Status | User Sees | Icon | Color |
|--------------|-----------|------|-------|
| `executed` | "Done!" | ✓ | Green |
| `completed` | "Done!" / "I've created a task for you" | ✓ | Green |
| `executing` | "Working on it..." | ⟳ | Blue (animated) |
| `pending` | "Processing..." | ⏳ | Yellow (animated) |
| `skipped` | "I can't do that" | ⊘ | Orange |
| `failed` | "Something went wrong" | ✗ | Red |

**Implementation:** `utils/translations.ts` → `translateActionStatus()`  
**Component:** `StatusIndicator.tsx`

---

### D. Enforcement Decision Translation
**System Internal** → **User-Facing**

| Enforcement | User Message | When Shown |
|------------|-------------|-----------|
| `allow` | *(No message)* | Normal flow |
| `rewrite` | "I rephrased this to keep things safe and clear." | Inline, yellow card |
| `block` | "I can't help with that request. Let me know if there's something else I can do." | Inline, red card |

**Implementation:** `ChatMessage.tsx` lines 131-145

---

### E. Safety Level Translation
**System Internal** → **User-Facing**

| Safety Level | User Message | Badge Label | Color |
|-------------|-------------|-------------|-------|
| `safe` | *(No message)* | — | — |
| `soft_risk` | "I'm being careful with this response." | "Caution" | Yellow |
| `high_risk` | "I'm being careful with this response." | "Warning" | Orange |
| `blocked` | "I can't provide that content." | "Not Available" | Red |

**Implementation:** `ChatMessage.tsx` lines 147-160, `SafetyLabel.tsx`

---

### F. Loading Stage Translation
**System Internal** → **User-Facing**

| Backend Stage | User Sees |
|--------------|-----------|
| `input` | "Reading your message..." |
| `enforcement` | "Checking..." |
| `safety` | "Making sure it's safe..." |
| `intent` | "Understanding..." |
| `execution` | "Working on it..." |
| *(default)* | "Thinking..." |

**Implementation:** `LoadingSpinner.tsx` lines 8-14

---

### G. Timestamp Translation
**System Internal** → **User-Facing**

| Time Difference | User Sees |
|----------------|-----------|
| < 1 minute | "Just now" |
| < 60 minutes | "5 minutes ago" |
| < 24 hours | "3 hours ago" |
| < 7 days | "2 days ago" |
| 7+ days | "Jan 15, 3:45 PM" |

**Implementation:** `utils/translations.ts` → `formatFriendlyTimestamp()`

---

## What Users NEVER See

### ❌ Hidden System Internals

1. **Trace IDs**  
   - Where: `EnforcementBadge.tsx` line 77 (commented out)
   - Why: Debugging artifacts with no user value

2. **Risk Scores / Confidence Percentages**  
   - Where: `SafetyLabel.tsx` lines 36-48 (commented out)
   - Why: Creates anxiety, adds no actionable insight

3. **Raw `final_decision` values**  
   - Example: `bhiv_core`, `task_created_and_summary_generated`
   - Always translated to human language

4. **Backend stage names**  
   - Example: `enforcement`, `intentflow`, `decision_hub`
   - Hidden behind friendly loading messages

5. **Technical labels in UI**  
   - ~~"Safety Check"~~ → Hidden in advanced details
   - ~~"Safety Assessment"~~ → Hidden in advanced details
   - ~~"Enforcement Badge"~~ → Shown only if user clicks "Show advanced details"

---

## UX Flow Examples

### Example 1: Normal Task Creation

**User Input:**  
> "Remind me to buy groceries tomorrow"

**What Happens Behind the Scenes:**
- Intent detection: `reminder`
- Task creation: `personal_task`
- Decision: `task_created_and_summary_generated`

**What User Sees:**
1. **Loading:** "Thinking... → Understanding..."
2. **Response bubble:**
   - *"I understand you want to set a reminder • Personal Task"* (subtle, italic)
   - **"I've created a reminder for you to buy groceries tomorrow."**
   - Task card with status "Pending" (green dot + ✓)
   - *"What would you like to do next? You can ask me to create more tasks, answer questions, or help with anything else."*
3. **Timestamp:** "Just now"

**User Outcome:** ✅ Clear, reassuring, next steps obvious

---

### Example 2: Blocked Request

**User Input:**  
> "How do I hack into my neighbor's WiFi?"

**What Happens Behind the Scenes:**
- Enforcement: `block`
- Reason: `prohibited_content`
- Safety: `blocked`

**What User Sees:**
1. **Loading:** "Thinking... → Checking..."
2. **Response bubble with red card:**
   - **"I can't help with that request. Let me know if there's something else I can do."**
3. **NO enforcement trace IDs**
4. **NO safety scores**
5. **Optional:** User can click "Show advanced details" to see:
   - Safety Check: Badge "Blocked" + "PROHIBITED"
   - Safety Assessment: Dot + "Not Available"

**User Outcome:** ✅ Clear refusal, no shame, alternative offered

---

### Example 3: Rewritten Request

**User Input:**  
> "Tell me how to kill this process"

**What Happens Behind the Scenes:**
- Enforcement: `rewrite`
- Rewritten to: "How do I terminate a software process?"
- Reason: `tone_adjustment`

**What User Sees:**
1. **Response bubble with yellow card:**
   - **"I rephrased this to keep things safe and clear."**
   - Main response explains how to end a process
2. **NO trace IDs**
3. **Optional advanced details:** Safety Check badge "Rephrased" + "TONE"

**User Outcome:** ✅ User understands adjustment, gets helpful answer

---

### Example 4: Execution Failure

**User Input:**  
> "Send an email to john@example.com"

**What Happens Behind the Scenes:**
- Execution: `failed`
- Error: `Email service unavailable`

**What User Sees:**
1. **Response bubble with soft red:**
   - "I tried to send that email, but ran into an issue."
   - Status indicator: ✗ "Something went wrong"
   - **"Here's what happened: Email service unavailable"**
   - *"Is there anything else I can help you with?"* (next step hint)

**User Outcome:** ✅ Knows what failed, why, and has a path forward

---

## Component Inventory

### Components Following UX Standards ✅

| Component | Purpose | Human-Friendly? | Notes |
|-----------|---------|----------------|-------|
| `App.tsx` | Main chat interface | ✅ Yes | Clean, no artifacts |
| `ChatMessage.tsx` | Message display | ✅ Yes | Translates all internals |
| `StatusIndicator.tsx` | Status badges | ✅ Yes | Icons + friendly labels |
| `ActionCard.tsx` | Task display | ✅ Yes | Next-step hints included |
| `NextStepHint.tsx` | Guidance messages | ✅ Yes | Calm, helpful suggestions |
| `LoadingSpinner.tsx` | Loading states | ✅ Yes | Friendly stage messages |
| `MessageInput.tsx` | User input | ✅ Yes | Simple, iOS-style |
| `translations.ts` | Translation layer | ✅ Yes | Central UX translation logic |

### Components with Advanced Details (Toggle) 🔒

| Component | What It Shows | Visibility |
|-----------|--------------|-----------|
| `EnforcementBadge.tsx` | Safety check decisions | Hidden by default, user can toggle |
| `SafetyLabel.tsx` | Safety assessment | Hidden by default, user can toggle |

**Philosophy:** Power users can access details, but default UX is clean.

---

## Design Language: iOS-Inspired Calm

### Visual Elements
- **Liquid glass effects** (`backdrop-blur-xl`)
- **Soft shadows** (`shadow-ios`, `shadow-ios-lg`)
- **Rounded corners** (`rounded-3xl`, `rounded-2xl`)
- **Gentle animations** (pulse, spin, smooth transitions)
- **Subtle borders** (white/20%, gray-700/30%)

### Color Semantics
| Color | Meaning | Use Case |
|-------|---------|----------|
| Blue (`iosBlue-500`) | System action, active | User messages, processing |
| Green | Success, completed | Done status, checkmarks |
| Yellow | Caution, pending | Waiting, rewritten content |
| Orange | Skipped, soft warning | Can't do that |
| Red | Error, blocked | Failures, prohibited content |
| Gray | Neutral, inactive | Timestamps, metadata |

### Typography
- Font family: `SF Pro` (`font-sf`)
- Hierarchy: Clear heading/body separation
- Line height: `leading-relaxed` for readability

---

## Validation Checklist

### ✅ Day 1 (Completed)
- [x] Audit all components for engineering artifacts
- [x] Document translation mappings
- [x] Confirm trace IDs are hidden
- [x] Confirm risk scores are hidden
- [x] Validate friendly loading messages
- [x] Validate status translations
- [x] Create UX_TRANSLATION_MAP.md

### 🚧 Day 2 (In Progress)
- [ ] Enhance action & outcome visibility
- [ ] Add confirmation messages where missing
- [ ] Test all error paths for calm handling
- [ ] Screenshot action flows
- [ ] Document interaction patterns

### 📅 Day 3 (Planned)
- [ ] Test on desktop (Chrome, Firefox, Safari)
- [ ] Test on mobile (iOS Safari, Android Chrome)
- [ ] Test on slow network (throttling)
- [ ] Verify loading states persist correctly
- [ ] Ensure no UI dead ends
- [ ] Create demo readiness checklist
- [ ] Record walkthrough video

---

## Success Metrics

**A user should be able to:**
1. Send a message and understand what the assistant is doing **in under 3 seconds**
2. See an outcome and know what happened **without reading docs**
3. Encounter an error and know what to do next **without panic**
4. Navigate the entire interface **without confusion**

**Demo readiness means:**
- Zero engineering jargon visible
- Every status has a clear icon + label
- Every action has a next step
- Every error is calm and actionable

---

## Contact & Coordination

**This UX work integrates with:**
- **Sankalp** (Response Intelligence) — Defines allowed content display
- **Nilesh** (Backend Orchestration) — Provides `/api/assistant` responses
- **Chandresh** (Action Execution) — Returns success/failure for actions
- **Akanksha Parab** (Safety Layer) — Ensures emotional/content safety
- **Yash Lokare** (Frontend Support) — Assists with UI implementation

**Owner:** Chandragupta Maurya  
**Goal:** Demo-safe AI Assistant for real humans in 60 seconds or less

---

**Last Updated:** January 22, 2026  
**Status:** Day 1 Complete ✅