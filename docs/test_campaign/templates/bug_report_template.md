# Bug Report Template

## Instructions

Copy this template for each bug found during testing. Save as `BUG_XXX_short_description.md` in the `results/` folder.

---

# Bug Report

## Bug ID
**BUG-XXX**

## Summary
_One line description of the bug_

## Severity

| Level | Description |
|-------|-------------|
| ☐ Critical | Integration fails to load or crashes |
| ☐ High | Major feature completely broken |
| ☐ Medium | Feature partially working or incorrect values |
| ☐ Low | Minor issues, cosmetic problems |

## Priority for Sprint

| Level | Description |
|-------|-------------|
| ☐ P1 | Must fix this sprint |
| ☐ P2 | Should fix this sprint |
| ☐ P3 | Backlog |

---

## Bug Details

### Related Test Case
_Test ID where bug was discovered (e.g., TC002.3)_

### Environment
- **Home Assistant Version:** 
- **Installation Type:** (OS/Container/Core/Supervised)
- **Simulation Mode:** Yes/No
- **Date Discovered:** 

### Steps to Reproduce

1. _Step 1_
2. _Step 2_
3. _Step 3_
4. _..._

### Expected Result
_What should happen_

### Actual Result
_What actually happens_

---

## Technical Details

### Affected Components
- [ ] Climate Entity
- [ ] Sensor Entities
- [ ] Switch Entities
- [ ] Coordinator
- [ ] Simulator
- [ ] Config Flow
- [ ] Other: _____________

### Affected Registers
_List any registers involved (e.g., 0b55, 0b8d)_

### Simulator State (if applicable)
```yaml
# State before bug occurred
"0bXX": "XXXX"
```

### Log Output
```
# Relevant log entries (ERROR, WARNING, DEBUG)
_Paste log snippets here_
```

### Screenshots
_Attach or reference any screenshots_

---

## Analysis

### Root Cause (if known)
_Analysis of what might be causing the bug_

### Suggested Fix (if known)
_Ideas for how to fix_

### Related Issues
_Links to related bugs or known issues_

---

## Additional Notes
_Any other relevant information_

---

## Status

| Status | Date | Notes |
|--------|------|-------|
| ☐ New | | |
| ☐ Confirmed | | |
| ☐ In Progress | | |
| ☐ Fixed | | |
| ☐ Verified | | |
| ☐ Closed | | |
| ☐ Won't Fix | | |

---

## Reported By
**Name:** 
**Date:** 
**Session ID:** 

---

# Example Bug Report

## Bug ID
**BUG-001**

## Summary
Manual Mode switch state reverts to OFF after coordinator refresh

## Severity
☑ High - Major feature completely broken

## Priority for Sprint
☑ P1 - Must fix this sprint

---

## Bug Details

### Related Test Case
TC004.2 - Manual Mode Switch - Turn ON

### Environment
- **Home Assistant Version:** 2024.1.0
- **Installation Type:** Container
- **Simulation Mode:** Yes
- **Date Discovered:** 2026-01-18

### Steps to Reproduce

1. Ensure Manual Mode switch is OFF
2. Click the Manual Mode switch to turn ON
3. Observe switch shows ON briefly
4. Wait for coordinator refresh (30 seconds)
5. Observe switch reverts to OFF

### Expected Result
Manual Mode switch should remain ON after coordinator refresh

### Actual Result
Manual Mode switch reverts to OFF after coordinator refresh

---

## Technical Details

### Affected Components
- [x] Switch Entities
- [x] Coordinator
- [x] Simulator

### Affected Registers
0b55 (bit 9 - Manual Mode flag)

### Simulator State (if applicable)
```yaml
# State before toggle
"0b55": "0020"

# State immediately after toggle (correct)
"0b55": "0220"

# State after refresh (incorrect - reverted)
"0b55": "0020"
```

### Log Output
```
2026-01-18 10:30:15 DEBUG custom_components.kospel [SIMULATOR] WRITE register 0b55: 0020 → 0220
2026-01-18 10:30:45 DEBUG custom_components.kospel [SIMULATOR] READ register 0b55: 0020 (32)
```

### Screenshots
_N/A_

---

## Analysis

### Root Cause (if known)
Possibly the state file is being re-read on each refresh, overwriting in-memory changes. Or there's a race condition between write and read operations.

### Suggested Fix (if known)
Investigate state file write timing and ensure writes are committed before next read.

### Related Issues
Possibly related to known issue: "Simulator State Not Reading Manual YAML Edits"

---

## Additional Notes
This is a blocking issue for switch functionality testing.

---

## Status
☑ New - 2026-01-18

---

## Reported By
**Name:** Test Engineer
**Date:** 2026-01-18
**Session ID:** TEST-2026-01-18-001
