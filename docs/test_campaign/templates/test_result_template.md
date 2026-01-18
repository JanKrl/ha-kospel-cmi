# Test Result Template

## Instructions

Use this template to document individual test case results. Can be used for detailed results tracking or for tests that require extra documentation.

---

# Test Result Record

## Test Information

| Field | Value |
|-------|-------|
| **Test ID** | |
| **Test Name** | |
| **Test Category** | |
| **Priority** | Critical / High / Medium / Low |
| **Executed By** | |
| **Execution Date** | |
| **Session ID** | |

---

## Execution Environment

| Field | Value |
|-------|-------|
| Home Assistant Version | |
| Installation Type | OS / Container / Core / Supervised |
| Simulation Mode | Yes / No |
| Browser | |
| State File Used | Default / Custom: _______ |

---

## Pre-Conditions

### State Before Test
```yaml
# Simulator state file contents relevant to test
```

### Configuration
_Any specific configuration for this test_

---

## Test Execution

### Steps Executed

| Step # | Action | Expected | Actual | Status |
|--------|--------|----------|--------|--------|
| 1 | | | | ☐ P / ☐ F |
| 2 | | | | ☐ P / ☐ F |
| 3 | | | | ☐ P / ☐ F |
| 4 | | | | ☐ P / ☐ F |
| 5 | | | | ☐ P / ☐ F |

### Deviations from Procedure
_Document any deviations from the test procedure_

---

## Result

### Overall Result
☐ **PASS** - All steps completed successfully  
☐ **FAIL** - One or more steps failed  
☐ **BLOCKED** - Could not complete due to dependency/issue  
☐ **NOT RUN** - Test was skipped  

### Failure Details (if applicable)
| Field | Value |
|-------|-------|
| Failed Step | |
| Expected Result | |
| Actual Result | |
| Bug ID Created | |

---

## Evidence

### State After Test
```yaml
# Simulator state file contents after test
```

### Log Excerpts
```
# Relevant log entries during test
```

### Screenshots
_Reference or embed screenshots_

---

## Notes & Observations
_Any additional observations during test execution_

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | | | |
| Reviewer (if applicable) | | | |

---

# Example Completed Test Result

## Test Information

| Field | Value |
|-------|-------|
| **Test ID** | TC002.4 |
| **Test Name** | Preset Mode - Winter |
| **Test Category** | Climate Entity |
| **Priority** | High |
| **Executed By** | Test Engineer |
| **Execution Date** | 2026-01-18 |
| **Session ID** | TEST-2026-01-18-001 |

---

## Execution Environment

| Field | Value |
|-------|-------|
| Home Assistant Version | 2024.1.0 |
| Installation Type | Container |
| Simulation Mode | Yes |
| Browser | Chrome 120 |
| State File Used | Default |

---

## Pre-Conditions

### State Before Test
```yaml
"0b55": "0000"  # Heater OFF
```

### Configuration
Debug logging enabled for custom_components.kospel

---

## Test Execution

### Steps Executed

| Step # | Action | Expected | Actual | Status |
|--------|--------|----------|--------|--------|
| 1 | Click on climate entity | Detail view opens | Detail view opened | ☑ P |
| 2 | Open preset selection | Dropdown appears | Dropdown appeared | ☑ P |
| 3 | Select "winter" preset | Selection confirmed | Selected successfully | ☑ P |
| 4 | Wait for refresh | Entity updates | Updated in 5 seconds | ☑ P |
| 5 | Verify preset is "winter" | Shows "winter" | Shows "winter" | ☑ P |
| 6 | Verify HVAC mode is HEAT | Shows "Heat" | Shows "Heat" | ☑ P |
| 7 | Check simulator state | Bit 5 set in 0b55 | Value is "0020" | ☑ P |

### Deviations from Procedure
None - test executed as documented.

---

## Result

### Overall Result
☑ **PASS** - All steps completed successfully

---

## Evidence

### State After Test
```yaml
"0b55": "0020"  # Winter mode active
```

### Log Excerpts
```
2026-01-18 14:23:15 DEBUG [SIMULATOR] WRITE register 0b55: 0000 → 0020 (0 → 32)
2026-01-18 14:23:16 DEBUG [SIMULATOR] READ register 0b55: 0020 (32)
```

### Screenshots
climate_winter_preset.png - Climate card showing winter preset

---

## Notes & Observations
- UI response was fast (~2 seconds for UI update)
- Log messages clearly showed state transition
- Coordinator refresh occurred within expected interval

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tester | Test Engineer | 2026-01-18 | TE |
