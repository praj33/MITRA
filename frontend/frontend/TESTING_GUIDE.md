# Testing Guide - Governance & Transparency Features

## How to Test Different Scenarios

This guide shows you exactly what messages to send to trigger different enforcement and safety validation states.

---

## 🔴 Test Case 1: Enforcement BLOCK

### Expected Behavior:
- Enforcement Decision: **BLOCK** (red badge)
- Safety Level: **BLOCKED** (red badge)
- Execution Status: **Skipped** (orange badge)
- Message: "Action blocked by enforcement policy"

### Test Messages:
```
block this content
please block this message
block me
```

**What to Look For:**
- ✅ Red BLOCK badge in Governance Layer
- ✅ Reason tag: "PROHIBITED"
- ✅ Trace ID displayed
- ✅ Execution status shows "Skipped (Enforcement)"
- ✅ No response generated
- ✅ Clear blocking message displayed

---

## 🟡 Test Case 2: Enforcement REWRITE

### Expected Behavior:
- Enforcement Decision: **REWRITE** (yellow badge)
- Safety Level: **SOFT RISK** (yellow badge)
- Execution Status: **Completed**
- Response marked as "Modified by Enforcement"

### Test Messages:
```
rewrite this text
please rewrite the content
rewrite message
```

**What to Look For:**
- ✅ Yellow REWRITE badge in Governance Layer
- ✅ Reason tag: "TONE"
- ✅ Trace ID displayed
- ✅ Safety shows "SOFT RISK" with confidence %
- ✅ Response has yellow border and "Modified by Enforcement" indicator
- ✅ Execution completes normally

---

## 🟠 Test Case 3: HIGH RISK Detection

### Expected Behavior:
- Enforcement Decision: **ALLOW** (green badge)
- Safety Level: **HIGH RISK** (orange badge)
- Execution Status: **Completed**
- Warning message displayed

### Test Messages:
```
this is unsafe content
risky behavior detected
unsafe message here
```

**What to Look For:**
- ✅ Green ALLOW badge (content allowed but monitored)
- ✅ Orange HIGH RISK badge with confidence %
- ✅ Warning: "High risk detected. Proceeding with caution."
- ✅ Execution completes but with caution indicator
- ✅ Response generated normally

---

## 🟢 Test Case 4: Normal Execution (ALLOW + SAFE)

### Expected Behavior:
- Enforcement Decision: **ALLOW** (green badge)
- Safety Level: **SAFE** (green badge)
- Execution Status: **Completed**
- Normal response flow

### Test Messages:
```
hello, how are you?
create a task to call John tomorrow
what is the weather today?
help me with something
summarize this text
```

**What to Look For:**
- ✅ Green ALLOW badge
- ✅ Reason tag: "POLICY OK"
- ✅ Green SAFE badge with confidence % (~98%)
- ✅ Normal execution flow
- ✅ Response generated without warnings
- ✅ Clean, standard UI display

---

## 🔵 Test Case 5: Task Creation Workflow

### Expected Behavior:
- Intent: "task_creation"
- Task created and displayed
- Normal governance flow

### Test Messages:
```
create a reminder to call mom
schedule a meeting with the team
add a task for tomorrow
create task to buy groceries
```

**What to Look For:**
- ✅ Intent detected: "task_creation"
- ✅ Task type displayed
- ✅ Governance layer shows ALLOW + SAFE
- ✅ Execution status: "Task Created"
- ✅ Task card appears at the end
- ✅ Task ID and details visible

---

## ⚠️ Test Case 6: Error Handling

### Expected Behavior:
- Error state displayed clearly
- Graceful error fallback
- User-friendly error message

### How to Trigger:
1. **Backend offline**: Stop the backend server
2. **Invalid request**: Send a very long message (if backend has limits)
3. **Network error**: Disconnect internet temporarily

**What to Look For:**
- ✅ Red error badge
- ✅ Clear error message
- ✅ Error details in execution panel
- ✅ No application crash
- ✅ User can try again

---

## 📋 Testing Checklist

Use this checklist to verify all features:

### Enforcement Visibility
- [ ] BLOCK scenario displays correctly
- [ ] REWRITE scenario displays correctly
- [ ] ALLOW scenario displays correctly
- [ ] Reason tags are 1-2 words (not verbose)
- [ ] Trace IDs are visible
- [ ] Governance layer is prominent

### Safety Validation
- [ ] SAFE level displays with confidence %
- [ ] SOFT RISK displays correctly
- [ ] HIGH RISK displays with warning
- [ ] BLOCKED displays correctly
- [ ] Confidence scores show properly
- [ ] Badges are simple (not essay text)

### Execution Transparency
- [ ] Executing state shows during processing
- [ ] Completed state shows after success
- [ ] Failed state shows on errors
- [ ] Skipped state shows when blocked
- [ ] Pipeline stages visible in loading
- [ ] Error messages are clear

### UI/UX Quality
- [ ] Visual hierarchy is clear
- [ ] Color coding consistent
- [ ] No confusing elements
- [ ] Predictable behavior
- [ ] Smooth transitions
- [ ] Responsive layout

---

## 🎬 Demo Script (3-5 minutes)

### Step 1: Normal Flow (30 seconds)
1. Send: "Hello, how can you help me?"
2. Show: ALLOW + SAFE badges
3. Explain: "Normal execution with governance check passing"

### Step 2: Enforcement Block (45 seconds)
1. Send: "block this message"
2. Show: BLOCK + BLOCKED badges
3. Show: Execution skipped
4. Explain: "Content blocked by enforcement policy with trace ID for audit"

### Step 3: Enforcement Rewrite (45 seconds)
1. Send: "rewrite this content"
2. Show: REWRITE + SOFT RISK badges
3. Show: Modified response indicator
4. Explain: "Content modified by enforcement engine to comply with policy"

### Step 4: High Risk Detection (45 seconds)
1. Send: "this is unsafe content"
2. Show: ALLOW + HIGH RISK badges
3. Show: Warning message
4. Explain: "Content allowed but flagged as high risk with monitoring"

### Step 5: Task Creation (45 seconds)
1. Send: "create a task to call John tomorrow"
2. Show: Full pipeline including task creation
3. Explain: "Complete workflow with governance, validation, and execution"

### Step 6: Error Handling (30 seconds)
1. Show error state (or trigger one)
2. Explain: "Graceful error handling with clear user feedback"

---

## 🔍 Verification Points

After each test, verify:

1. **Governance Layer Visible**: Can you see the governance section?
2. **Decisions Clear**: Are enforcement and safety decisions obvious?
3. **Trace IDs Present**: Can you see trace IDs for audit?
4. **States Correct**: Does execution status match the scenario?
5. **Messages Clear**: Are user-facing messages concise and understandable?
6. **No Confusion**: Is it obvious what happened and why?

---

## 🐛 Troubleshooting Test Cases

### If BLOCK doesn't trigger:
- ✅ Check backend is running
- ✅ Verify message contains "block" keyword
- ✅ Check browser console for errors
- ✅ Verify API response contains enforcement data

### If REWRITE doesn't trigger:
- ✅ Message must contain "rewrite" keyword
- ✅ Check backend response structure
- ✅ Verify enforcement decision in response

### If HIGH RISK doesn't trigger:
- ✅ Message must contain "unsafe" or "risk" keyword
- ✅ Check safety level in API response
- ✅ Verify confidence score display

### If Task Creation doesn't work:
- ✅ Message should clearly indicate task intent
- ✅ Check intent detection in pipeline
- ✅ Verify task object in response

---

## 📊 Expected Response Structure

Each API response should contain:

```json
{
  "status": "success",
  "result": {
    "enforcement": {
      "decision": "allow" | "rewrite" | "block",
      "reason": "policy_check_passed" | "prohibited_content" | "tone_adjustment",
      "trace_id": "enf-12345678"
    },
    "safety": {
      "level": "safe" | "soft_risk" | "high_risk" | "blocked",
      "confidence": 0.98,
      "score": 0.02
    },
    "response": "Assistant response text",
    "type": "passive" | "intelligence" | "workflow"
  }
}
```

---

## ✅ Success Criteria

Your testing is successful when:

1. ✅ All 6 test cases work correctly
2. ✅ Governance decisions are always visible
3. ✅ Safety validation shows for every request
4. ✅ Execution states are clear and accurate
5. ✅ Error handling is graceful
6. ✅ UI is stable and predictable
7. ✅ Demo script runs smoothly

**Happy Testing! 🚀**

