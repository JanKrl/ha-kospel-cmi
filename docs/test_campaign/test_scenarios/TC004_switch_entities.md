# TC004 - Switch Entity Tests

## Test Category: Switch Entity Functionality
**Priority:** High  
**Prerequisites:** Integration setup completed (TC001.3 passed)

---

## Overview

The Kospel integration provides two switch entities for controlling heater operation:

| Switch | Entity ID | Register | Bit | Function |
|--------|-----------|----------|-----|----------|
| Manual Mode | `switch.*_manual_mode` | 0b55 | 9 | Enable/disable manual temperature control |
| Water Heater | `switch.*_water_heater` | 0b55 | 4 | Enable/disable domestic hot water heating |

Both switches operate on the same register (0b55) but control different bits using the read-modify-write pattern.

---

## TC004.1 - Manual Mode Switch Display

### Objective
Verify the Manual Mode switch displays correctly in Home Assistant UI.

### Preconditions
1. Integration configured and entities created
2. Simulator has valid state data

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Kospel device page | Device shows all entities |
| 2 | Locate Manual Mode switch | Switch entity visible |
| 3 | Verify switch name | Shows "Manual Mode" |
| 4 | Verify switch state is displayed | Shows ON or OFF |

### Pass/Fail Criteria
- **Pass:** Switch displays with correct name and state
- **Fail:** Switch missing or displays error

---

## TC004.2 - Manual Mode Switch - Turn ON

### Objective
Verify turning on Manual Mode switch works correctly.

### Preconditions
1. Manual Mode switch visible
2. Switch is currently OFF

### Test Data Setup
Edit `simulation_state.yaml` (ensure bit 9 is 0):
```yaml
"0b55": "0020"  # Winter mode, manual mode OFF
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify switch shows OFF | Switch state is OFF |
| 2 | Click/toggle the switch | Switch interaction occurs |
| 3 | Observe UI feedback | Switch shows pending state |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify switch is now ON | Switch state is ON |
| 6 | Check simulator state file | Bit 9 set in register 0b55 |

### Pass/Fail Criteria
- **Pass:** Switch turns ON, state persists in simulator
- **Fail:** Switch doesn't change or reverts

### Expected State Change
Before: `"0b55": "0020"` (bit 9 = 0)
After: `"0b55": "0220"` (bit 9 = 1)

---

## TC004.3 - Manual Mode Switch - Turn OFF

### Objective
Verify turning off Manual Mode switch works correctly.

### Preconditions
1. Manual Mode switch visible
2. Switch is currently ON

### Test Data Setup
Edit `simulation_state.yaml` (ensure bit 9 is 1):
```yaml
"0b55": "0220"  # Winter mode, manual mode ON
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify switch shows ON | Switch state is ON |
| 2 | Click/toggle the switch | Switch interaction occurs |
| 3 | Observe UI feedback | Switch shows pending state |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify switch is now OFF | Switch state is OFF |
| 6 | Check simulator state file | Bit 9 cleared in register 0b55 |

### Pass/Fail Criteria
- **Pass:** Switch turns OFF, state persists in simulator
- **Fail:** Switch doesn't change or reverts

### Expected State Change
Before: `"0b55": "0220"` (bit 9 = 1)
After: `"0b55": "0020"` (bit 9 = 0)

---

## TC004.4 - Water Heater Switch Display

### Objective
Verify the Water Heater switch displays correctly in Home Assistant UI.

### Preconditions
1. Integration configured and entities created
2. Simulator has valid state data

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Kospel device page | Device shows all entities |
| 2 | Locate Water Heater switch | Switch entity visible |
| 3 | Verify switch name | Shows "Water Heater" |
| 4 | Verify switch state is displayed | Shows ON or OFF |

### Pass/Fail Criteria
- **Pass:** Switch displays with correct name and state
- **Fail:** Switch missing or displays error

---

## TC004.5 - Water Heater Switch - Turn ON

### Objective
Verify turning on Water Heater switch works correctly.

### Preconditions
1. Water Heater switch visible
2. Switch is currently OFF

### Test Data Setup
Edit `simulation_state.yaml` (ensure bit 4 is 0):
```yaml
"0b55": "0020"  # Winter mode, water heater OFF
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify switch shows OFF | Switch state is OFF |
| 2 | Click/toggle the switch | Switch interaction occurs |
| 3 | Observe UI feedback | Switch shows pending state |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify switch is now ON | Switch state is ON |
| 6 | Check simulator state file | Bit 4 set in register 0b55 |

### Pass/Fail Criteria
- **Pass:** Switch turns ON, state persists in simulator
- **Fail:** Switch doesn't change or reverts

### Expected State Change
Before: `"0b55": "0020"` (bit 4 = 0)
After: `"0b55": "0030"` (bit 4 = 1)

---

## TC004.6 - Water Heater Switch - Turn OFF

### Objective
Verify turning off Water Heater switch works correctly.

### Preconditions
1. Water Heater switch visible
2. Switch is currently ON

### Test Data Setup
Edit `simulation_state.yaml` (ensure bit 4 is 1):
```yaml
"0b55": "0030"  # Winter mode, water heater ON
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify switch shows ON | Switch state is ON |
| 2 | Click/toggle the switch | Switch interaction occurs |
| 3 | Observe UI feedback | Switch shows pending state |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify switch is now OFF | Switch state is OFF |
| 6 | Check simulator state file | Bit 4 cleared in register 0b55 |

### Pass/Fail Criteria
- **Pass:** Switch turns OFF, state persists in simulator
- **Fail:** Switch doesn't change or reverts

### Expected State Change
Before: `"0b55": "0030"` (bit 4 = 1)
After: `"0b55": "0020"` (bit 4 = 0)

---

## TC004.7 - Both Switches Operate Independently

### Objective
Verify both switches can be controlled independently without affecting each other.

### Preconditions
1. Both switches visible
2. Both switches currently OFF

### Test Data Setup
```yaml
"0b55": "0020"  # Winter mode, both manual and water heater OFF
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify both switches OFF | Manual: OFF, Water: OFF |
| 2 | Turn ON Manual Mode switch | Manual mode toggled |
| 3 | Wait for refresh | Data updated |
| 4 | Verify Manual Mode is ON | Manual: ON |
| 5 | Verify Water Heater still OFF | Water: OFF |
| 6 | Turn ON Water Heater switch | Water heater toggled |
| 7 | Wait for refresh | Data updated |
| 8 | Verify both switches are ON | Manual: ON, Water: ON |
| 9 | Turn OFF Manual Mode | Manual mode toggled |
| 10 | Wait for refresh | Data updated |
| 11 | Verify Manual is OFF, Water still ON | Manual: OFF, Water: ON |

### Pass/Fail Criteria
- **Pass:** Switches operate independently without affecting each other
- **Fail:** Toggling one switch affects the other

### State Progression
| Step | Register | Manual (bit 9) | Water (bit 4) |
|------|----------|----------------|---------------|
| Start | 0020 | 0 | 0 |
| After 3 | 0220 | 1 | 0 |
| After 7 | 0230 | 1 | 1 |
| After 10 | 0030 | 0 | 1 |

---

## TC004.8 - Switch State Persistence After Heater Mode Change

### Objective
Verify switch states persist when heater mode is changed via climate entity.

### Preconditions
1. Both switches visible
2. Manual Mode ON, Water Heater ON

### Test Data Setup
```yaml
"0b55": "0230"  # Winter mode, manual ON, water heater ON
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify initial states | Manual: ON, Water: ON, Mode: Winter |
| 2 | Change heater preset to "summer" via climate entity | Preset change |
| 3 | Wait for refresh | Data updated |
| 4 | Verify Manual Mode switch | Still ON |
| 5 | Verify Water Heater switch | Still ON |
| 6 | Verify heater mode changed | Mode: Summer |
| 7 | Check register value | Bits 4, 9 still set (bits 3, 5 changed) |

### Pass/Fail Criteria
- **Pass:** Switch states preserved when mode changes
- **Fail:** Switch states reset when mode changes

### Expected State Change
Before: `"0b55": "0230"` (winter + manual + water)
After: `"0b55": "0218"` (summer + manual + water)

---

## TC004.9 - Rapid Switch Toggling

### Objective
Verify system handles rapid consecutive switch toggles correctly.

### Preconditions
1. Manual Mode switch visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Toggle Manual Mode ON | Switch toggled |
| 2 | Immediately toggle OFF | Switch toggled |
| 3 | Immediately toggle ON | Switch toggled |
| 4 | Wait for all operations to complete | System stabilizes |
| 5 | Verify final state matches last toggle | Switch is ON |
| 6 | Check simulator state consistency | Register reflects ON state |
| 7 | Check logs for errors | No errors from rapid operations |

### Pass/Fail Criteria
- **Pass:** System handles rapid toggles without errors
- **Fail:** System errors, crashes, or state is inconsistent

---

## TC004.10 - Switch Entity Availability

### Objective
Verify switch entities show correct availability status.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | With integration running, check switch status | Switches show "available" |
| 2 | Verify switches respond to commands | Toggle commands accepted |
| 3 | Check coordinator `last_update_success` | Should be True |

### Pass/Fail Criteria
- **Pass:** Switches available and responsive
- **Fail:** Switches unavailable or unresponsive

---

## TC004.11 - Switch Icon Display

### Objective
Verify switches display appropriate icons in Home Assistant UI.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | View Manual Mode switch | Switch icon visible |
| 2 | Verify ON state icon | Icon indicates ON state |
| 3 | Verify OFF state icon | Icon indicates OFF state |
| 4 | View Water Heater switch | Switch icon visible |
| 5 | Verify icon changes with state | Icon reflects current state |

### Pass/Fail Criteria
- **Pass:** Icons display and reflect switch states
- **Fail:** Icons missing or don't reflect state

---

## TC004.12 - Concurrent Switch Operations

### Objective
Verify both switches can be operated concurrently without issues.

### Preconditions
1. Both switches visible and OFF

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Turn ON Manual Mode switch | Operation initiated |
| 2 | Before refresh completes, turn ON Water Heater | Second operation initiated |
| 3 | Wait for both operations to complete | Both complete |
| 4 | Verify both switches are ON | Manual: ON, Water: ON |
| 5 | Check simulator state | Both bits set correctly |
| 6 | Check logs for race conditions | No errors or warnings |

### Pass/Fail Criteria
- **Pass:** Both operations succeed without conflicts
- **Fail:** One or both operations fail, or state is inconsistent

---

## Summary Checklist

| Test ID | Test Name | Priority | Result | Notes |
|---------|-----------|----------|--------|-------|
| TC004.1 | Manual Mode Switch Display | High | | |
| TC004.2 | Manual Mode Switch - Turn ON | Critical | | |
| TC004.3 | Manual Mode Switch - Turn OFF | Critical | | |
| TC004.4 | Water Heater Switch Display | High | | |
| TC004.5 | Water Heater Switch - Turn ON | Critical | | |
| TC004.6 | Water Heater Switch - Turn OFF | Critical | | |
| TC004.7 | Both Switches Operate Independently | High | | |
| TC004.8 | Switch State Persistence After Mode Change | High | | |
| TC004.9 | Rapid Switch Toggling | Medium | | |
| TC004.10 | Switch Entity Availability | Medium | | |
| TC004.11 | Switch Icon Display | Low | | |
| TC004.12 | Concurrent Switch Operations | Medium | | |

---

## Test Data Reference

### Register 0b55 - Shared Control Register

| Bit | Function | Value 1 | Value 0 |
|-----|----------|---------|---------|
| 3 | Summer Mode | Active | Inactive |
| 4 | Water Heater | Enabled | Disabled |
| 5 | Winter Mode | Active | Inactive |
| 9 | Manual Mode | Enabled | Disabled |

### Common Test Configurations

| Configuration | Bit 9 | Bit 5 | Bit 4 | Bit 3 | Hex (LE) |
|---------------|-------|-------|-------|-------|----------|
| Winter only | 0 | 1 | 0 | 0 | "0020" |
| Winter + Water | 0 | 1 | 1 | 0 | "0030" |
| Winter + Manual | 1 | 1 | 0 | 0 | "0220" |
| Winter + Manual + Water | 1 | 1 | 1 | 0 | "0230" |
| Summer only | 0 | 0 | 0 | 1 | "0008" |
| Summer + Water | 0 | 0 | 1 | 1 | "0018" |
| Summer + Manual | 1 | 0 | 0 | 1 | "0208" |
| Summer + Manual + Water | 1 | 0 | 1 | 1 | "0218" |
| Off | 0 | 0 | 0 | 0 | "0000" |
| Off + Manual | 1 | 0 | 0 | 0 | "0200" |
| Off + Water | 0 | 0 | 1 | 0 | "0010" |
| Off + Manual + Water | 1 | 0 | 1 | 0 | "0210" |

### Bit Position Calculation
- Bit 3: 2³ = 8 = 0x08
- Bit 4: 2⁴ = 16 = 0x10
- Bit 5: 2⁵ = 32 = 0x20
- Bit 9: 2⁹ = 512 = 0x200

Example: Winter + Manual + Water = 0x20 + 0x200 + 0x10 = 0x230 → LE: "3002" → "0230"
