# Phase 9: React Dashboard Manual Validation Guide

This document specifies the exact steps for manually validating the React Dashboard for the Meeting Intelligent System (Member 4).

---

## 1. Launching the Dashboard

From the project root:
```powershell
cd frontend
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 2. Validation Checklist

### A. Dashboard Header & Initial Ingestion
- [ ] **Meeting Header**: Confirmed display of `Meeting: ES2002a`.
- [ ] **Subtitle**: Confirmed display of `Post-Extraction Intelligence & Multi-Perspective Presentation Layer (Member 4)`.
- [ ] **Role Switcher**: All four supported roles (`Manager`, `Developer`, `Intern`, `Default`) are available and clickable.
- [ ] **Default Selection**: Dashboard boots with `Manager` role active by default.

### B. Dynamic Executive Headline
- [ ] **Manager Headline**: Displays `"32 action items tracked, including 1 high-priority item(s), 7 item(s) flagged for review, and 1 with explicit deadlines."`
- [ ] **Switch to Developer**: Headline dynamically changes to implementation deliverables and dependency focus.
- [ ] **Switch to Intern**: Headline dynamically changes to task clarity and ownership guidance.
- [ ] **Switch to Default**: Headline displays canonical meeting view description.

### C. Summary Cards Verification (Derived from Loaded Data)
Verify the 8 metric cards display the exact canonical values without hardcoding:
- [ ] **Total Tasks**: `32`
- [ ] **High Priority**: `1`
- [ ] **Med Priority**: `1`
- [ ] **Low Priority**: `30`
- [ ] **Auto Accepted**: `25`
- [ ] **Needs Review**: `7`
- [ ] **Review Req.**: `0`
- [ ] **Decisions**: `9`

### D. Distribution Visualizations
- [ ] **Priority Distribution**: Bar visually partitions into High (1), Medium (1), and Low (30).
- [ ] **Confidence Calibration**: Bar reflects High (25) and Medium (7) calibration distribution.
- [ ] **Human Review Triage**: Bar reflects Auto (25) and Recommended (7).

### E. Multi-Criteria Filter Controls
- [ ] **Priority Filter**: Select `HIGH` $\to$ displays exactly 1 item (`norm_act_031`).
- [ ] **Review Filter**: Select `Review Recommended` $\to$ displays exactly 7 items (`norm_act_006`, `007`, `008`, `011`, `012`, `013`, `030`).
- [ ] **Deadline Filter**: Select `With Deadline` $\to$ displays exactly 1 item (`norm_act_031`).
- [ ] **Search Box**: Type `"mascot"` $\to$ displays all mascot-related tasks across topics 10, 16, 17, 18.
- [ ] **Reset Button**: Clicking `Reset` restores table to all 32 items.

---

## 3. Representative Case Inspection (Click Row to Open Drawer)

### Case A: Topic 40 Working Remote Design (`norm_act_031`)
1. Click the first item in Manager view (`Work on the actual working design of the remote control`).
2. Verify Drawer contents:
   - **Task**: `"Work on the actual working design of the remote control"`
   - **Responsible**: `SPEAKER_00`
   - **Deadline**: `30 minutes` (highlighted)
   - **Priority**: `HIGH (0.7150)`
   - **Confidence**: `HIGH (0.9600)`
   - **Review Status**: `Auto Accepted`
   - **Priority Decomposition Table**: Shows ranked factors ($w_i \times v_i$ mathematical table) with `deadline_urgency (+0.2375)`, `assignment_clarity (+0.1275)`, `context_quality (+0.1000)`.
   - **Evidence Traces**: Verbatim quote `"Right, so it is to wrap up."` and `"The next meeting is going to be in 30 minutes."` from `SPEAKER_03` with timestamps `976.58–1019.12s`.

### Case B: Topic 10 Beagle Mascot (`norm_act_006`)
1. Filter by `Review Recommended` and click `Discuss and finalize the design of the Beagle mascot`.
2. Verify Drawer contents:
   - **Priority**: `LOW (0.2650)`
   - **Confidence**: `HIGH (0.7950)`
   - **Review Status**: `Review Recommended`
   - **Warning Box**: `⚠ Conflicting Decisions Detected` — Topic 10 contains competing design proposals in dialogue context.
   - **Reason Code**: `CONFLICTING_DECISIONS`.
   - **Linked Decisions**: Shows the 3 competing mascot proposals extracted from Topic 10.

### Case C: Topic 16 Animal Mascot (`norm_act_011`)
1. Click `Discuss and finalize the physical design of the animal mascot` (Topic 16).
2. Verify Drawer contents:
   - **Priority**: `LOW (0.2450)`
   - **Confidence**: `MEDIUM (0.7050)`
   - **Review Status**: `Review Recommended`
   - **Reason Codes**: `MEDIUM_CONFIDENCE`, `WEAK_DIALOGUE_GROUNDING`.
   - **Limiting Evidence**: Zero lexical corroboration in dialogue turns.

### Case D: Topic 39 Remote Control Form Factor (`norm_act_030`)
1. Click `Discuss and refine the design of the remote control to improve its current form factor` (Topic 39).
2. Verify Drawer contents:
   - **Priority**: `LOW (0.2450)`
   - **Confidence**: `MEDIUM (0.7350)`
   - **Review Status**: `Review Recommended`
   - **Reason Codes**: `MEDIUM_CONFIDENCE`, `WEAK_DIALOGUE_GROUNDING`.

---

## 4. Invariance & Integrity Guarantee
- Confirm that filtering, role switching, or searching never alters priority, confidence, or review scores.
- Confirm zero fabricated values, names, or deadlines.
