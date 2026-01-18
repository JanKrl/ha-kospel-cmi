# Test Execution Checklist

## Purpose
This checklist guides testers through the manual test campaign execution process.

---

## Pre-Execution Checklist

Before starting test execution, verify:

| Item | Status | Notes |
|------|--------|-------|
| Environment setup complete | ☐ | See environment_setup.md |
| Test scenarios reviewed | ☐ | All TC001-TC005 documents |
| Bug report template available | ☐ | See templates/bug_report_template.md |
| Test session log ready | ☐ | See templates/test_session_log.md |
| State file backup created | ☐ | Optional but recommended |
| Debug logging enabled | ☐ | Recommended for debugging |

---

## Test Execution Order

Execute tests in the following order for best results:

### Phase 1: Foundation Tests (Must Pass to Continue)

| Priority | Test Suite | Critical Tests |
|----------|------------|----------------|
| 1 | TC001 - Integration Setup | TC001.1, TC001.2, TC001.3 |
| 2 | TC005 - Simulator | TC005.1, TC005.2, TC005.3 |

**Stop Point**: If Phase 1 tests fail, stop and resolve issues before continuing.

### Phase 2: Read-Only Tests

| Priority | Test Suite | Tests |
|----------|------------|-------|
| 3 | TC003 - Sensors | All sensor display tests |
| 4 | TC002 - Climate | TC002.1, TC002.10 (display only) |

### Phase 3: Write Operation Tests

| Priority | Test Suite | Tests |
|----------|------------|-------|
| 5 | TC004 - Switches | All switch tests |
| 6 | TC002 - Climate | Mode and temperature change tests |
| 7 | TC005 - Simulator | Write persistence tests |

### Phase 4: Advanced Tests

| Priority | Test Suite | Tests |
|----------|------------|-------|
| 8 | TC001 | Restart, removal tests |
| 9 | All | Edge cases, rapid operations |

---

## Quick Test Matrix

Use this matrix to track progress:

### TC001 - Integration Setup

| ID | Test Name | Pri | Result | Bugs |
|----|-----------|-----|--------|------|
| TC001.1 | Integration Discovery | Crit | ☐ P / ☐ F | |
| TC001.2 | Config Flow - Simulation | Crit | ☐ P / ☐ F | |
| TC001.3 | Entity Creation | Crit | ☐ P / ☐ F | |
| TC001.4 | Restart Resilience | High | ☐ P / ☐ F | |
| TC001.5 | Integration Removal | Med | ☐ P / ☐ F | |
| TC001.6 | Logs Verification | Med | ☐ P / ☐ F | |
| TC001.7 | Missing State File | Med | ☐ P / ☐ F | |

### TC002 - Climate Entity

| ID | Test Name | Pri | Result | Bugs |
|----|-----------|-----|--------|------|
| TC002.1 | Display | High | ☐ P / ☐ F | |
| TC002.2 | OFF to HEAT | Crit | ☐ P / ☐ F | |
| TC002.3 | HEAT to OFF | Crit | ☐ P / ☐ F | |
| TC002.4 | Preset - Winter | High | ☐ P / ☐ F | |
| TC002.5 | Preset - Summer | High | ☐ P / ☐ F | |
| TC002.6 | Preset - Off | High | ☐ P / ☐ F | |
| TC002.7 | Set Temperature | High | ☐ P / ☐ F | |
| TC002.8 | Min Temperature | Med | ☐ P / ☐ F | |
| TC002.9 | Max Temperature | Med | ☐ P / ☐ F | |
| TC002.10 | Current Temp Display | High | ☐ P / ☐ F | |
| TC002.11 | Availability | Med | ☐ P / ☐ F | |
| TC002.12 | Rapid Mode Changes | Med | ☐ P / ☐ F | |

### TC003 - Sensor Entities

| ID | Test Name | Pri | Result | Bugs |
|----|-----------|-----|--------|------|
| TC003.1 | Temp Sensor Display | High | ☐ P / ☐ F | |
| TC003.2 | Decimal Precision | Med | ☐ P / ☐ F | |
| TC003.3 | Negative Values | Med | ☐ P / ☐ F | |
| TC003.4 | Pressure Display | High | ☐ P / ☐ F | |
| TC003.5 | Pressure Precision | Med | ☐ P / ☐ F | |
| TC003.6 | Pump CO Status | High | ☐ P / ☐ F | |
| TC003.7 | Pump Circ Status | High | ☐ P / ☐ F | |
| TC003.8 | Valve Position | High | ☐ P / ☐ F | |
| TC003.9 | Combined Status | High | ☐ P / ☐ F | |
| TC003.10 | Unavailable Handling | Med | ☐ P / ☐ F | |
| TC003.11 | Device Class | Med | ☐ P / ☐ F | |
| TC003.12 | State Class | Med | ☐ P / ☐ F | |
| TC003.13 | Real-time Updates | High | ☐ P / ☐ F | |

### TC004 - Switch Entities

| ID | Test Name | Pri | Result | Bugs |
|----|-----------|-----|--------|------|
| TC004.1 | Manual Mode Display | High | ☐ P / ☐ F | |
| TC004.2 | Manual Mode ON | Crit | ☐ P / ☐ F | |
| TC004.3 | Manual Mode OFF | Crit | ☐ P / ☐ F | |
| TC004.4 | Water Heater Display | High | ☐ P / ☐ F | |
| TC004.5 | Water Heater ON | Crit | ☐ P / ☐ F | |
| TC004.6 | Water Heater OFF | Crit | ☐ P / ☐ F | |
| TC004.7 | Independent Operation | High | ☐ P / ☐ F | |
| TC004.8 | State After Mode Change | High | ☐ P / ☐ F | |
| TC004.9 | Rapid Toggling | Med | ☐ P / ☐ F | |
| TC004.10 | Availability | Med | ☐ P / ☐ F | |
| TC004.11 | Icon Display | Low | ☐ P / ☐ F | |
| TC004.12 | Concurrent Operations | Med | ☐ P / ☐ F | |

### TC005 - Simulator

| ID | Test Name | Pri | Result | Bugs |
|----|-----------|-----|--------|------|
| TC005.1 | Mode Detection | Crit | ☐ P / ☐ F | |
| TC005.2 | State File Creation | Crit | ☐ P / ☐ F | |
| TC005.3 | Read Operations | Crit | ☐ P / ☐ F | |
| TC005.4 | Write Operations | Crit | ☐ P / ☐ F | |
| TC005.5 | Manual Editing | High | ☐ P / ☐ F | Known issue |
| TC005.6 | Flag Bit Operations | High | ☐ P / ☐ F | |
| TC005.7 | Batch Read | High | ☐ P / ☐ F | |
| TC005.8 | Default Values | Med | ☐ P / ☐ F | |
| TC005.9 | Custom Location | Low | ☐ P / ☐ F | |
| TC005.10 | Concurrent Operations | Med | ☐ P / ☐ F | |
| TC005.11 | File Format | Med | ☐ P / ☐ F | |
| TC005.12 | Large Count Handling | Med | ☐ P / ☐ F | |
| TC005.13 | State Recovery | High | ☐ P / ☐ F | |
| TC005.14 | Debug Logging | Low | ☐ P / ☐ F | |

---

## During Test Execution

### For Each Test

1. **Read** the test scenario completely before starting
2. **Prepare** any required test data
3. **Execute** steps exactly as written
4. **Observe** actual results
5. **Compare** to expected results
6. **Record** result (Pass/Fail)
7. **Document** any deviations or observations
8. **Create bug report** if test fails

### When a Test Fails

1. Stop and verify the failure
2. Check logs for error details
3. Try to reproduce the failure
4. Create a bug report with:
   - Steps to reproduce
   - Expected vs actual result
   - Log snippets
   - Screenshots if applicable
5. Note bug ID in test matrix
6. Continue with remaining tests (unless blocker)

### Common Issues During Execution

| Issue | Action |
|-------|--------|
| Entity not updating | Wait for coordinator refresh (30s) |
| Value shows "unavailable" | Check simulator state file |
| UI not responding | Refresh browser page |
| Test data not applied | Verify state file saved correctly |
| Unexpected error in logs | Document and continue |

---

## Post-Execution Tasks

### Immediate

- [ ] Complete all test result entries
- [ ] Create bug reports for all failures
- [ ] Save all logs and screenshots
- [ ] Document any blocked tests

### Analysis

- [ ] Count Pass/Fail/Blocked for each category
- [ ] Identify patterns in failures
- [ ] Classify bugs by severity
- [ ] Prioritize bugs for sprint planning

### Reporting

- [ ] Complete test session log
- [ ] Calculate pass rate
- [ ] Summarize key findings
- [ ] Provide sprint planning recommendations

---

## Test Session Summary Template

Fill in after completing test session:

```
Test Session Summary
====================

Date: ____________
Tester: ____________
Duration: ____________

Results Summary:
- Total Tests: 57
- Passed: ____
- Failed: ____
- Blocked: ____
- Not Run: ____

Pass Rate: _____%

Critical Issues Found: ____
High Priority Issues: ____
Medium Priority Issues: ____
Low Priority Issues: ____

Key Findings:
1. ____________
2. ____________
3. ____________

Recommendations for Sprint Planning:
1. ____________
2. ____________
3. ____________

Blocking Issues (must fix before hardware testing):
1. ____________
```

---

## Emergency Procedures

### If Home Assistant Crashes

1. Check logs for crash reason
2. Restart Home Assistant
3. Document the crash
4. Create high-priority bug report
5. Try to reproduce

### If State File Corrupted

1. Delete state file
2. Restart integration
3. Re-create test data
4. Continue testing

### If Integration Won't Load

1. Check Home Assistant logs
2. Verify all files present
3. Check for Python errors
4. Try removing and re-adding integration
5. If unresolvable, create critical bug report
