# Governance & Transparency UX Features

## Overview

This sprint focused on **Clarity • Trust • Governance Awareness** - making the Assistant → Being transition VISIBLE + TRUSTABLE by showing Enforcement + Validator + Execution transparency.

## What Was Added

### Day 1: Enforcement Awareness UI

**Enforcement Decision Display:**
- **ALLOW** badge (green) - Action approved by enforcement
- **REWRITE** badge (yellow) - Action modified by enforcement
- **BLOCK** badge (red) - Action blocked by enforcement
- **Reason Tag** - Short 1-2 word policy reason (e.g., "POLICY OK", "PROHIBITED", "TONE")
- **Trace ID** - Short hash for audit trail

**Visibility:**
- Prominent governance layer section in execution pipeline
- Clear visual indicators with color coding
- System message: "All outputs are validated and enforced before user visibility"
- Shows when enforcement blocks, rewrites, or allows actions

### Day 2: Validator + Safety State Visibility

**Safety Label Display:**
- **SAFE** (green) - Content validated as safe
- **SOFT RISK** (yellow) - Low risk detected
- **HIGH RISK** (orange) - Elevated risk detected  
- **BLOCKED** (red) - Content blocked by validator
- **Confidence %** - Validation confidence score displayed

**Purpose:**
- Demonstrates that emotional output is validated before user sees it
- Clear badge format - NOT essay text
- Shows Akanksha Safety Layer (Behavior Validator) confirmation

### Day 3: Execution Transparency Polish

**Execution States:**
- **Executing** (blue, animated) - Action in progress
- **Completed** (green) - Action finished successfully
- **Failed** (red) - Action failed with error details
- **Skipped** (orange) - Skipped due to enforcement block

**Features:**
- Execution progress indicators in loading spinner
- Pipeline stage visualization (Input → Enforcement → Safety → Intent → Execution)
- Task queue clarity with status indicators
- Fault feedback with detailed error messages
- Graceful error fallback handling

### Day 4: Demo Hardening

**UI Stability:**
- Consistent visual hierarchy
- Predictable state transitions
- Clear status indicators
- No confusing UX distractions
- Removed unnecessary elements

## How Enforcement Appears

### In the UI

1. **Governance Layer Section** (Step 1.5 in pipeline):
   - Shield icon (🛡️) indicating governance
   - "Governance Layer — System-Controlled Decisions" header
   - Separate displays for Enforcement and Safety Validator

2. **Enforcement Badge**:
   - Color-coded decision badge (ALLOW/REWRITE/BLOCK)
   - Animated pulse for active decisions
   - Short reason tag
   - Trace ID for reference

3. **Impact Indicators**:
   - When BLOCKED: Red warning message, execution status shows "Skipped"
   - When REWRITE: Yellow indicator, response marked as "Modified by Enforcement"
   - When ALLOW: Green indicator, normal flow continues

## How Users Read Decisions

### Visual Hierarchy

```
Execution #1
├─ User Command
├─ Governance Layer (🛡️)
│  ├─ Enforcement Decision (Raj) → [ALLOW/REWRITE/BLOCK] + Reason + Trace ID
│  └─ Safety Validator (Akanksha) → [SAFE/SOFT RISK/HIGH RISK/BLOCKED] + Confidence %
├─ Detected Intent
├─ Execution Status → [Executing/Completed/Failed/Skipped]
├─ System Response (with rewrite indicator if applicable)
└─ Created Task (if applicable)
```

### Decision Flow

1. **User submits command** → Visible in pipeline
2. **Governance check** → Enforcement decision displayed prominently
3. **Safety validation** → Validator confirmation shown
4. **If BLOCKED** → Execution stops, clear "Skipped" status shown
5. **If ALLOWED** → Execution continues, completion shown
6. **If REWRITE** → Response marked as modified, original intent preserved

### Key Messages

- **"System is governed. Decisions are controlled."** - Visible in header
- **"All outputs are validated and enforced before user visibility"** - In governance section
- Clear visual distinction between user input, governance decisions, and system output

## Component Architecture

### EnforcementBadge Component
- Displays enforcement decision with visual prominence
- Converts long reasons to short tags (1-2 words)
- Shows trace ID for auditability
- Color-coded: Green (ALLOW), Yellow (REWRITE), Red (BLOCK)

### SafetyLabel Component
- Displays safety validation level
- Shows confidence percentage
- Color-coded risk levels
- Clear badge format

### StatusIndicator Component
- Execution status visualization
- Supports: Executing, Completed, Failed, Skipped, Pending
- Color-coded with icons
- Animated for active states

### CommandExecution Component
- Main pipeline visualization
- Step-by-step execution flow
- Governance layer prominently displayed
- Clear error handling
- Execution state clarity

## Backend Integration

### API Response Mapping

The frontend expects enforcement and safety data in the response:

```typescript
{
  enforcement: {
    decision: 'allow' | 'rewrite' | 'block',
    reason: string,
    trace_id: string
  },
  safety: {
    level: 'safe' | 'soft_risk' | 'high_risk' | 'blocked',
    confidence: number,
    score: number
  },
  execution: {
    status: 'executing' | 'completed' | 'failed' | 'skipped',
    stage: string,
    error: string
  }
}
```

### Coordination with Backend Teams

- **Nilesh (Decision Hub)**: Provides response + execution + workflow status
- **Raj (Enforcement Engine)**: Provides enforcement decision signal (allow/rewrite/block)
- **Akanksha (Behavior Validator)**: Provides validation confidence / safety confirmation
- **Sankalp (Emotional Engine)**: Provides conversational + emotional content

**Important**: Frontend only reads & displays states safely. No reverse control.

## Demo Scenarios

### Scenario 1: Enforcement Blocking
1. User enters command with prohibited content
2. Governance layer shows **BLOCK** with "PROHIBITED" reason
3. Safety shows **BLOCKED** status
4. Execution status: **Skipped**
5. Clear message: "Action blocked by enforcement policy"

### Scenario 2: Enforcement Rewrite
1. User enters command requiring tone adjustment
2. Governance layer shows **REWRITE** with "TONE" reason
3. Safety shows **SOFT RISK**
4. Execution completes
5. Response marked: "Modified by Enforcement"
6. Original intent preserved

### Scenario 3: Normal Execution
1. User enters allowed command
2. Governance layer shows **ALLOW** with "POLICY OK"
3. Safety shows **SAFE** with confidence %
4. Execution completes successfully
5. Normal response flow

### Scenario 4: High Risk Detection
1. User enters command with risk indicators
2. Governance shows **ALLOW** (content allowed but monitored)
3. Safety shows **HIGH RISK** with elevated score
4. Warning: "High risk detected. Proceeding with caution."
5. Execution completes with monitoring

## Testing Checklist

- [ ] Enforcement blocking displays correctly
- [ ] Enforcement rewrite shows modification indicator
- [ ] Safety validator displays all states (SAFE, SOFT RISK, HIGH RISK, BLOCKED)
- [ ] Confidence scores display correctly
- [ ] Trace IDs are visible and readable
- [ ] Execution states transition correctly
- [ ] Error states show clear messages
- [ ] Skipped executions due to enforcement are clear
- [ ] Response modification indicators work
- [ ] Governance message is always visible

## Deployment Notes

### Required Environment Variables
- `REACT_APP_API_URL`: Backend API URL
- `REACT_APP_API_KEY`: API authentication key

### Build Process
```bash
npm install
npm run build
```

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Responsive design for all screen sizes

## Future Enhancements

- Expandable trace details on click
- Governance policy explanation tooltips
- Safety score breakdown visualization
- Historical enforcement decision log
- User-facing policy documentation

