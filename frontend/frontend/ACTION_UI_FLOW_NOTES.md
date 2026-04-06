# Action UI Flow Notes
**Demo-Ready UX Documentation**  
**Date: January 22, 2026**

---

## Overview
This document details the visual flow and interaction patterns of the AI Assistant, showing how actions and outcomes are presented to users in a calm, understandable way.

---

## Core Interaction Flows

### Flow 1: Simple Question-Answer
**User Action:** Asks a question  
**Example:** "What's the weather like today?"

**UI Flow:**
1. **User types** → Message appears in input field with visual feedback
2. **User sends** → 
   - Toast notification: "Message sent" (green, 2s)
   - User message bubble appears (blue, right-aligned)
   - Loading state appears below
3. **Loading states** (sequential):
   - "Reading your message..."
   - "Understanding what you need..."
   - "Working on it..."
4. **Response appears:**
   - Intent card (blue box): "Got it: Get Information"
   - Main response text (clear, readable)
   - Completion indicator: ✓ "All set" (small green checkmark)
   - Next step hint: "Is there anything else I can help you with?"
   - Timestamp: "Just now"

**User Outcome:** ✅ Clear answer + knows conversation is ready for next input

---

### Flow 2: Task Creation
**User Action:** Requests task creation  
**Example:** "Remind me to call Mom tomorrow at 3pm"

**UI Flow:**
1. **Message sent** → Toast: "Message sent"
2. **User bubble** appears (blue, right)
3. **Loading states:**
   - "Reading your message..."
   - "Understanding what you need..."
   - "Working on it..."
4. **Response appears:**
   - Intent card: "Got it: Set a Reminder • Personal Task"
   - Main response: "I've created a reminder for you to call Mom tomorrow at 3pm."
   - **Task Created Section** (prominent):
     - ✓ Green checkmark icon in circle
     - "Task Created" label (green, bold)
     - **Action Card** (liquid glass style):
       - Status: "Pending" with yellow ⏳ icon
       - Description: "Call Mom tomorrow at 3pm"
       - Created timestamp
       - Next step hint: "You can start working on this task when you're ready."
   - Next step suggestion: "What would you like to do next? You can ask me to create more tasks, answer questions, or help with anything else."

**User Outcome:** ✅ Sees task was created, knows its status, has clear next steps

---

### Flow 3: Blocked Request (Safety)
**User Action:** Requests prohibited content  
**Example:** "How do I hack into someone's account?"

**UI Flow:**
1. **Message sent** → Toast: "Message sent"
2. **User bubble** appears
3. **Loading states:**
   - "Reading your message..."
   - "Reviewing content..."
   - "Double-checking..."
4. **Response appears:**
   - **Red warning card** (prominent, at top):
     - "I can't help with that request. Let me know if there's something else I can do."
   - No intent card (doesn't show understanding for blocked content)
   - Status: ⊘ "I can't help with that" (orange)
   - Soft redirect: "Let me know if there's something else I can do for you."
   - **Optional details** (hidden by default):
     - Button: "Show details"
     - If clicked → Shows "Content Review: Blocked • PROHIBITED"
     - If clicked → Shows "Safety Status: Not Available"

**User Outcome:** ✅ Clear refusal without shame, alternative path offered, no technical jargon

---

### Flow 4: Rewritten Request (Content Adjustment)
**User Action:** Ambiguous or risky phrasing  
**Example:** "Tell me how to kill this process"

**UI Flow:**
1. **Message sent** → Toast: "Message sent"
2. **User bubble** appears with original message
3. **Loading states:**
   - "Reading your message..."
   - "Reviewing content..."
4. **Response appears:**
   - **Yellow info card** (top):
     - "I rephrased this to keep things safe and clear."
   - Intent card: "Got it: Get Information"
   - Main response: Explains how to terminate a software process
   - Completion: ✓ "All set"
   - Next step hint
   - **Optional details** (hidden):
     - "Show details" → "Content Review: Rephrased • TONE"

**User Outcome:** ✅ Understands adjustment was made, gets helpful answer, no confusion

---

### Flow 5: Execution Failure
**User Action:** Requests action that fails  
**Example:** "Send an email to john@example.com"

**UI Flow:**
1. **Message sent** → Toast: "Message sent"
2. **User bubble** appears
3. **Loading states:**
   - "Reading your message..."
   - "Understanding what you need..."
   - "Working on it..."
4. **Response appears:**
   - Intent card: "Got it: Task Creation"
   - Main response: "I tried to send that email, but ran into an issue."
   - **Status indicator** (visible):
     - ✗ "Couldn't complete that" (red)
   - **Error explanation** (calm):
     - "What happened: Email service unavailable"
   - Next step hint: "Please try again, or let me know if you need help with something else."

**User Outcome:** ✅ Knows what failed, why it failed, and has path forward—no panic

---

### Flow 6: Processing/Pending State
**User Action:** Submits complex request  
**Example:** "Analyze this data and create a report"

**UI Flow:**
1. **Message sent** → Toast: "Message sent"
2. **User bubble** appears
3. **Extended loading** (shows progress):
   - "Reading your message..."
   - "Understanding what you need..."
   - "Working on it..." (may stay here longer)
4. **If still processing:**
   - Response bubble shows:
     - Intent card
     - Main response text
     - Status: ⟳ "Working on it..." (blue, animated)
5. **When complete:**
   - Status updates to: ✓ "All set" (green)

**User Outcome:** ✅ Knows system is working, can see progress, not left wondering

---

## Visual Design Elements

### Message Bubbles
| Element | Style | Purpose |
|---------|-------|---------|
| User messages | Blue background, right-aligned, rounded corners | Clear distinction from assistant |
| Assistant messages | White/glass effect, left-aligned, liquid glass blur | Calm, premium feel |
| Timestamps | Small, gray, subtle | Context without clutter |

### Status Indicators
| Status | Icon | Color | Animation | Meaning |
|--------|------|-------|-----------|---------|
| Completed | ✓ | Green | None | Success, done |
| Executing | ⟳ | Blue | Rotating | In progress |
| Pending | ⏳ | Yellow | Pulse | Waiting |
| Skipped | ⊘ | Orange | None | Can't do that |
| Failed | ✗ | Red | None | Error occurred |

### Action Cards (Tasks)
- **Container:** Liquid glass with blur effect
- **Border:** Subtle, adaptive to dark/light mode
- **Hover:** Blue glow on border
- **Content:**
  - Status badge (top-left)
  - Description (prominent, readable font)
  - Timestamps (small, bottom)
  - Next step hint (contextual, italic)

### Confirmation Elements
| Element | When Shown | Style |
|---------|-----------|-------|
| Toast notification | Message sent | Green, top-center, auto-dismiss (2s) |
| Task created banner | Task successfully created | Green checkmark + label |
| Action summary | General response complete | Small green checkmark |
| Error message | Failure occurs | Red card with calm explanation |

---

## Loading State Progression

### Normal Flow (0.5-2s total)
```
User sends message
  ↓
"Message sent" toast (2s)
  ↓
"Reading your message..." (0.3s)
  ↓
"Understanding what you need..." (0.5s)
  ↓
"Working on it..." (0.7s)
  ↓
Response appears
```

### With Safety Check (1-3s total)
```
User sends message
  ↓
"Message sent" toast
  ↓
"Reading your message..."
  ↓
"Reviewing content..." ← Safety layer
  ↓
"Double-checking..." ← Safety confirmation
  ↓
Response appears (may include safety card)
```

### Long-Running Process (3s+)
```
User sends message
  ↓
"Message sent" toast
  ↓
Initial loading stages...
  ↓
"Working on it..." (stays animated)
  ↓
(User sees pulsing indicator)
  ↓
Eventually completes or shows status
```

---

## Empty State

**First Visit (No Messages):**
- Large chat bubble icon (blue)
- Heading: "Start a conversation"
- Subtext: "Start a conversation with your AI assistant. I'm here to help with questions, tasks, and more."
- Input ready below

**User Outcome:** ✅ Knows what to do immediately

---

## Error Handling Patterns

### Network Error
- Red card with ✗ icon
- Message: "Couldn't complete that"
- Explanation: "I ran into an issue processing your request."
- Next step: "Please try again, or let me know if you need help with something else."

### Timeout
- Yellow card with ⏳ icon
- Message: "Taking longer than expected"
- Explanation: "This is taking a while. I'm still working on it."
- Next step: (No action needed, continues processing)

### Backend Error
- Red card
- Message: "Couldn't complete that"
- Explanation: Shows error (simplified, not technical)
- Next step: Suggests retry or alternative

**Philosophy:** Every error state has:
1. What happened (simple)
2. Why (if helpful)
3. What to do next (always)

---

## Mobile Responsiveness

### Mobile-Specific Adjustments
- Message bubbles: 85% max width (was 75%)
- Touch targets: Minimum 44px for buttons
- Font size: Slightly larger (16px minimum for readability)
- Toast: Full width on mobile with padding
- Action cards: Full width, no hover states (tap-focused)

### Tablet
- Same as desktop but with medium breakpoint
- Better touch targets
- Slightly larger spacing

---

## Accessibility Features

### Keyboard Navigation
- `Enter` to send message
- `Shift+Enter` for new line
- Clear indication shown below input

### Screen Reader Support
- Status indicators have ARIA labels
- Loading states announced
- Error messages clearly labeled
- Toast notifications announced

### Color Contrast
- All text meets WCAG AA standards
- Status colors distinct even for color-blind users
- Icons supplement color (not color alone)

---

## Demo Scenarios (Testing Checklist)

### ✅ Scenario 1: Happy Path
1. User: "What's 2+2?"
2. Assistant responds immediately
3. Clear answer, completion indicator
4. Ready for next input

### ✅ Scenario 2: Task Creation
1. User: "Remind me to buy milk"
2. Loading → Task created card appears
3. Status shows "Pending"
4. Next step hint clear

### ✅ Scenario 3: Blocked Content
1. User: Asks prohibited question
2. Red safety card appears
3. No shame, alternative offered
4. Details hidden unless requested

### ✅ Scenario 4: Error Recovery
1. User: Makes request
2. Backend fails
3. Error shown calmly
4. Retry path clear

### ✅ Scenario 5: Long Response
1. User: Complex query
2. Loading persists
3. Progress visible
4. Eventually completes

---

## Key UX Principles Demonstrated

### 1. **Clarity**
- Every action has a clear outcome
- Status always visible when relevant
- Next steps always suggested

### 2. **Calm**
- No panic-inducing language
- Soft colors, gentle animations
- Errors are supportive, not accusatory

### 3. **Progressive Disclosure**
- Advanced details hidden by default
- Power users can access if needed
- Default view is clean

### 4. **Feedback Loop**
- Message sent confirmation
- Loading states show progress
- Completion explicitly marked

### 5. **No Dead Ends**
- Every state has next action
- Errors suggest recovery
- Always ready for new input

---

## Success Metrics

**A user should:**
1. ✅ Understand what happened in < 3 seconds
2. ✅ Know what to do next without thinking
3. ✅ Feel calm and in control at all times
4. ✅ Never see technical jargon
5. ✅ Never be left wondering "did it work?"

---

## Screenshots Locations (for Demo)

*Note: Actual screenshots would be captured during live testing. For now, the UI is described in detail above.*

**Recommended screenshots to capture:**
1. Empty state (first load)
2. Simple Q&A flow (complete interaction)
3. Task creation with action card
4. Blocked request with safety card
5. Error state with recovery hint
6. Loading state progression
7. Mobile view (responsive)
8. Dark mode comparison

---

**Document Status:** Complete  
**Last Updated:** January 22, 2026  
**Owner:** Chandragupta Maurya