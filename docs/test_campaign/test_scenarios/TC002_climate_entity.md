# TC002 - Climate Entity Tests

## Test Category: Climate Entity Functionality
**Priority:** High  
**Prerequisites:** Integration setup completed (TC001.3 passed)

---

## Overview

The Kospel Climate Entity provides main heater control through Home Assistant's climate interface. It supports:
- **HVAC Modes:** OFF, HEAT
- **Preset Modes:** winter, summer, off
- **Temperature Control:** Target temperature setting

### Entity Details
- **Entity ID:** `climate.kospel_heater`
- **Name:** Kospel Heater
- **Features:** Target Temperature, Preset Mode

---

## TC002.1 - Climate Entity Display

### Objective
Verify the climate entity displays correctly in the Home Assistant UI.

### Preconditions
1. Integration configured and entities created
2. Simulator has valid state data

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Overview dashboard | Dashboard loads |
| 2 | Add Climate card (if not present) | Climate card configuration opens |
| 3 | Select "Kospel Heater" entity | Entity selected |
| 4 | Save card | Climate card displays |
| 5 | Observe current temperature | Temperature value displayed (or N/A) |
| 6 | Observe target temperature | Target temperature displayed |
| 7 | Observe HVAC mode | Mode (Off/Heat) displayed |
| 8 | Observe preset | Preset mode displayed |

### Pass/Fail Criteria
- **Pass:** Climate entity displays with all attributes visible
- **Fail:** Entity missing, displays error, or attributes not visible

---

## TC002.2 - HVAC Mode - OFF to HEAT

### Objective
Verify changing HVAC mode from OFF to HEAT works correctly.

### Preconditions
1. Climate entity visible (TC002.1 passed)
2. Current HVAC mode is OFF

### Test Data Setup
Edit `simulation_state.yaml`:
```yaml
"0b55": "0000"  # Heater OFF (bits 3,5 both 0)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify current mode is OFF | Mode shows "Off" |
| 2 | Click on climate entity | Climate detail view opens |
| 3 | Change HVAC mode to HEAT | Mode selector appears |
| 4 | Confirm HEAT selection | UI shows pending change |
| 5 | Wait for coordinator refresh | Entity updates (within 30s) |
| 6 | Verify mode changed to HEAT | Mode shows "Heat" |
| 7 | Check simulator state file | Register 0b55 updated |

### Pass/Fail Criteria
- **Pass:** Mode changes to HEAT, state persists in simulator
- **Fail:** Mode doesn't change or reverts on refresh

### State Verification
After test, `0b55` register should have bit 5 set (Winter mode):
```yaml
"0b55": "0020"  # Winter mode (bit 5 = 1)
```

---

## TC002.3 - HVAC Mode - HEAT to OFF

### Objective
Verify changing HVAC mode from HEAT to OFF works correctly.

### Preconditions
1. Current HVAC mode is HEAT

### Test Data Setup
Edit `simulation_state.yaml`:
```yaml
"0b55": "0020"  # Winter mode (bit 5 = 1)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Verify current mode is HEAT | Mode shows "Heat" |
| 2 | Click on climate entity | Climate detail view opens |
| 3 | Change HVAC mode to OFF | Mode selector appears |
| 4 | Confirm OFF selection | UI shows pending change |
| 5 | Wait for coordinator refresh | Entity updates |
| 6 | Verify mode changed to OFF | Mode shows "Off" |
| 7 | Check simulator state file | Register 0b55 updated |

### Pass/Fail Criteria
- **Pass:** Mode changes to OFF, state persists
- **Fail:** Mode doesn't change or reverts

---

## TC002.4 - Preset Mode - Winter

### Objective
Verify setting winter preset mode works correctly.

### Preconditions
1. Climate entity visible
2. Current preset is not "winter"

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on climate entity | Detail view opens |
| 2 | Open preset selection | Preset dropdown/list appears |
| 3 | Select "winter" preset | Preset selection confirmed |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify preset changed to "winter" | Preset shows "winter" |
| 6 | Verify HVAC mode is HEAT | HVAC mode should be "Heat" |
| 7 | Check simulator state | Bit 5 set, bit 3 cleared in 0b55 |

### Pass/Fail Criteria
- **Pass:** Preset changes to winter, heater mode updated
- **Fail:** Preset doesn't change or heater mode incorrect

### Expected State
```yaml
"0b55": "0020"  # Winter: bit 5=1, bit 3=0
```

---

## TC002.5 - Preset Mode - Summer

### Objective
Verify setting summer preset mode works correctly.

### Preconditions
1. Climate entity visible
2. Current preset is not "summer"

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on climate entity | Detail view opens |
| 2 | Open preset selection | Preset dropdown/list appears |
| 3 | Select "summer" preset | Preset selection confirmed |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify preset changed to "summer" | Preset shows "summer" |
| 6 | Verify HVAC mode is HEAT | HVAC mode should be "Heat" |
| 7 | Check simulator state | Bit 3 set, bit 5 cleared in 0b55 |

### Pass/Fail Criteria
- **Pass:** Preset changes to summer, heater mode updated
- **Fail:** Preset doesn't change or heater mode incorrect

### Expected State
```yaml
"0b55": "0008"  # Summer: bit 3=1, bit 5=0
```

---

## TC002.6 - Preset Mode - Off

### Objective
Verify setting "off" preset mode works correctly.

### Preconditions
1. Climate entity visible
2. Current preset is not "off"

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on climate entity | Detail view opens |
| 2 | Open preset selection | Preset dropdown/list appears |
| 3 | Select "off" preset | Preset selection confirmed |
| 4 | Wait for coordinator refresh | Entity updates |
| 5 | Verify preset changed to "off" | Preset shows "off" |
| 6 | Verify HVAC mode is OFF | HVAC mode should be "Off" |
| 7 | Check simulator state | Both bits 3,5 cleared in 0b55 |

### Pass/Fail Criteria
- **Pass:** Preset changes to off, heater mode is OFF
- **Fail:** Preset doesn't change or HVAC mode incorrect

### Expected State
```yaml
"0b55": "0000"  # Off: bit 3=0, bit 5=0
```

---

## TC002.7 - Target Temperature - Set Valid Value

### Objective
Verify setting target temperature works correctly.

### Preconditions
1. Climate entity visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click on climate entity | Detail view opens |
| 2 | Note current target temperature | Value recorded |
| 3 | Adjust temperature to 22.5°C | Temperature slider/input used |
| 4 | Confirm temperature change | UI shows new value |
| 5 | Wait for coordinator refresh | Entity updates |
| 6 | Verify target temperature is 22.5°C | Target shows 22.5°C |
| 7 | Check simulator state (0b8d register) | Value should be scaled ×10 |

### Pass/Fail Criteria
- **Pass:** Temperature changes and persists
- **Fail:** Temperature doesn't change or wrong value stored

### Expected State
22.5°C scaled by 10 = 225 (0x00E1 in big-endian, "e100" in little-endian):
```yaml
"0b8d": "e100"
```

---

## TC002.8 - Target Temperature - Minimum Value

### Objective
Verify setting temperature to minimum value works correctly.

### Preconditions
1. Climate entity visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Adjust temperature to minimum (e.g., 5°C) | Temperature adjusted |
| 2 | Wait for coordinator refresh | Entity updates |
| 3 | Verify temperature is at minimum | Value shows correctly |
| 4 | Check simulator state | Correct scaled value stored |

### Pass/Fail Criteria
- **Pass:** Minimum temperature accepted and stored
- **Fail:** Temperature rejected or incorrect value stored

---

## TC002.9 - Target Temperature - Maximum Value

### Objective
Verify setting temperature to maximum value works correctly.

### Preconditions
1. Climate entity visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Adjust temperature to maximum (e.g., 30°C) | Temperature adjusted |
| 2 | Wait for coordinator refresh | Entity updates |
| 3 | Verify temperature is at maximum | Value shows correctly |
| 4 | Check simulator state | Correct scaled value stored |

### Pass/Fail Criteria
- **Pass:** Maximum temperature accepted and stored
- **Fail:** Temperature rejected or incorrect value stored

---

## TC002.10 - Current Temperature Display

### Objective
Verify current temperature is displayed from simulator state.

### Preconditions
1. Climate entity visible

### Test Data Setup
Set `room_temperature_comfort` (register 0b6a) in simulator state:
```yaml
"0b6a": "e200"  # 22.6°C (226 / 10)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set test value in simulator state | File updated |
| 2 | Force coordinator refresh (wait or trigger) | Data refreshed |
| 3 | Observe current temperature in climate card | Shows 22.6°C |

### Pass/Fail Criteria
- **Pass:** Current temperature displays correctly from simulator
- **Fail:** Wrong value or "unavailable" displayed

---

## TC002.11 - Entity Availability

### Objective
Verify climate entity shows correct availability status.

### Preconditions
1. Climate entity visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | With integration running, check entity status | Entity shows "available" |
| 2 | Check coordinator `last_update_success` | Should be True |
| 3 | Entity should respond to commands | Commands are accepted |

### Pass/Fail Criteria
- **Pass:** Entity is available when coordinator succeeds
- **Fail:** Entity unavailable despite successful updates

---

## TC002.12 - Rapid Mode Changes

### Objective
Verify system handles rapid consecutive mode changes correctly.

### Preconditions
1. Climate entity visible

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Change preset to "winter" | Change initiated |
| 2 | Immediately change preset to "summer" | Change initiated |
| 3 | Immediately change preset to "off" | Change initiated |
| 4 | Wait for all operations to complete | System stabilizes |
| 5 | Verify final state is "off" | Preset shows "off" |
| 6 | Check simulator state consistency | Register reflects "off" |
| 7 | Check logs for errors | No errors related to rapid changes |

### Pass/Fail Criteria
- **Pass:** System handles rapid changes without errors
- **Fail:** System crashes, shows errors, or state is inconsistent

---

## Summary Checklist

| Test ID | Test Name | Priority | Result | Notes |
|---------|-----------|----------|--------|-------|
| TC002.1 | Climate Entity Display | High | | |
| TC002.2 | HVAC Mode - OFF to HEAT | Critical | | |
| TC002.3 | HVAC Mode - HEAT to OFF | Critical | | |
| TC002.4 | Preset Mode - Winter | High | | |
| TC002.5 | Preset Mode - Summer | High | | |
| TC002.6 | Preset Mode - Off | High | | |
| TC002.7 | Target Temperature - Set Valid Value | High | | |
| TC002.8 | Target Temperature - Minimum Value | Medium | | |
| TC002.9 | Target Temperature - Maximum Value | Medium | | |
| TC002.10 | Current Temperature Display | High | | |
| TC002.11 | Entity Availability | Medium | | |
| TC002.12 | Rapid Mode Changes | Medium | | |

---

## Test Data Reference

### Register 0b55 - Heater Mode Flags

| Bit | Function | Value 1 | Value 0 |
|-----|----------|---------|---------|
| 3 | Summer Mode | Summer active | Summer inactive |
| 4 | Water Heater | Enabled | Disabled |
| 5 | Winter Mode | Winter active | Winter inactive |
| 9 | Manual Mode | Enabled | Disabled |

### Mode Combinations
| Heater Mode | Bit 3 | Bit 5 | Example Hex |
|-------------|-------|-------|-------------|
| OFF | 0 | 0 | "0000" |
| WINTER | 0 | 1 | "0020" |
| SUMMER | 1 | 0 | "0008" |

### Register 0b8d - Manual Temperature
- Scaled by 10
- Example: 22.5°C = 225 = 0x00E1 → "e100" (little-endian)
