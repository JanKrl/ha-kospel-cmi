# TC003 - Sensor Entity Tests

## Test Category: Sensor Entity Functionality
**Priority:** High  
**Prerequisites:** Integration setup completed (TC001.3 passed)

---

## Overview

The Kospel integration provides multiple sensor entities for monitoring heater status:

### Temperature Sensors (7)
| Sensor | Entity ID | Register | Description |
|--------|-----------|----------|-------------|
| Room Temperature Economy | `sensor.*_room_temperature_economy` | 0b68 | Economy mode room temp |
| Room Temperature Comfort | `sensor.*_room_temperature_comfort` | 0b6a | Comfort mode room temp |
| Room Temperature Comfort Plus | `sensor.*_room_temperature_comfort_plus` | 0b6b | Comfort+ mode room temp |
| Room Temperature Comfort Minus | `sensor.*_room_temperature_comfort_minus` | 0b69 | Comfort- mode room temp |
| CWU Temperature Economy | `sensor.*_cwu_temperature_economy` | 0b66 | Economy water temp |
| CWU Temperature Comfort | `sensor.*_cwu_temperature_comfort` | 0b67 | Comfort water temp |
| Manual Temperature | `sensor.*_manual_temperature` | 0b8d | Manual mode temp setting |

### Pressure Sensor (1)
| Sensor | Entity ID | Register | Description |
|--------|-----------|----------|-------------|
| Pressure | `sensor.*_pressure` | 0b8a | System pressure |

### Status Sensors (3)
| Sensor | Entity ID | Register | Bit | Description |
|--------|-----------|----------|-----|-------------|
| Pump CO | `sensor.*_pump_co` | 0b51 | 0 | Central heating pump status |
| Pump Circulation | `sensor.*_pump_circulation` | 0b51 | 1 | Circulation pump status |
| Valve Position | `sensor.*_valve_position` | 0b51 | 2 | Three-way valve position |

---

## TC003.1 - Temperature Sensor Display

### Objective
Verify all temperature sensors display correctly with proper units.

### Preconditions
1. Integration configured with valid simulator state

### Test Data Setup
Edit `simulation_state.yaml`:
```yaml
"0b68": "dc00"  # Room Temp Economy: 22.0°C (220)
"0b6a": "e600"  # Room Temp Comfort: 23.0°C (230)
"0b6b": "f000"  # Room Temp Comfort+: 24.0°C (240)
"0b69": "d200"  # Room Temp Comfort-: 21.0°C (210)
"0b66": "9001"  # CWU Temp Economy: 40.0°C (400)
"0b67": "a401"  # CWU Temp Comfort: 42.0°C (420)
"0b8d": "e100"  # Manual Temperature: 22.5°C (225)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Kospel device page | Device shows all entities |
| 2 | Verify Room Temp Economy sensor | Shows 22.0°C |
| 3 | Verify Room Temp Comfort sensor | Shows 23.0°C |
| 4 | Verify Room Temp Comfort+ sensor | Shows 24.0°C |
| 5 | Verify Room Temp Comfort- sensor | Shows 21.0°C |
| 6 | Verify CWU Temp Economy sensor | Shows 40.0°C |
| 7 | Verify CWU Temp Comfort sensor | Shows 42.0°C |
| 8 | Verify Manual Temperature sensor | Shows 22.5°C |
| 9 | Verify all show unit "°C" | Unit of measurement is Celsius |

### Pass/Fail Criteria
- **Pass:** All temperatures display correctly with °C unit
- **Fail:** Any temperature missing, incorrect, or wrong unit

---

## TC003.2 - Temperature Sensor Decimal Precision

### Objective
Verify temperature sensors display decimal values correctly.

### Test Data Setup
Edit `simulation_state.yaml`:
```yaml
"0b6a": "e500"  # 22.9°C (229)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Update simulator state with test value | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check Room Temp Comfort sensor | Shows 22.9°C |
| 4 | Verify decimal is displayed correctly | One decimal place shown |

### Pass/Fail Criteria
- **Pass:** Decimal value displays correctly (22.9)
- **Fail:** Value rounded incorrectly or no decimal shown

---

## TC003.3 - Temperature Sensor Negative Values

### Objective
Verify temperature sensors handle negative values correctly.

### Test Data Setup
Set a negative temperature (e.g., -5.0°C = -50):
```yaml
"0b6a": "ceFF"  # -50 in two's complement, little-endian
```
Note: -50 = 0xFFCE → little-endian = "ceff"

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Update simulator state with negative value | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check sensor display | Shows -5.0°C |
| 4 | Verify negative sign displayed | Minus sign visible |

### Pass/Fail Criteria
- **Pass:** Negative temperature displays correctly
- **Fail:** Wrong value or missing negative sign

---

## TC003.4 - Pressure Sensor Display

### Objective
Verify pressure sensor displays correctly with proper units.

### Test Data Setup
Edit `simulation_state.yaml`:
```yaml
"0b8a": "f401"  # 500 = 5.00 bar (scaled ×100)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to pressure sensor | Sensor visible |
| 2 | Verify pressure value | Shows 5.00 bar |
| 3 | Verify unit of measurement | Shows "bar" |
| 4 | Check device class | Device class is "pressure" |

### Pass/Fail Criteria
- **Pass:** Pressure displays as 5.00 bar
- **Fail:** Wrong value, wrong unit, or missing

---

## TC003.5 - Pressure Sensor Precision

### Objective
Verify pressure sensor displays two decimal places correctly.

### Test Data Setup
```yaml
"0b8a": "f801"  # 504 = 5.04 bar
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Update simulator state | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check pressure display | Shows 5.04 bar |

### Pass/Fail Criteria
- **Pass:** Pressure shows with 0.01 precision (5.04)
- **Fail:** Precision lost or incorrect rounding

---

## TC003.6 - Pump CO Status Sensor

### Objective
Verify Pump CO status sensor displays correctly.

### Test Data Setup - Pump Running
```yaml
"0b51": "0100"  # Bit 0 = 1 (Pump CO running)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set bit 0 = 1 in simulator state | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check Pump CO sensor | Shows "Running" |
| 4 | Set bit 0 = 0 in simulator state | File saved |
| 5 | Wait for coordinator refresh | Data updated |
| 6 | Check Pump CO sensor | Shows "Idle" |

### Pass/Fail Criteria
- **Pass:** Pump status toggles between "Running" and "Idle"
- **Fail:** Wrong status or doesn't update

---

## TC003.7 - Pump Circulation Status Sensor

### Objective
Verify Pump Circulation status sensor displays correctly.

### Test Data Setup - Pump Running
```yaml
"0b51": "0200"  # Bit 1 = 1 (Pump Circulation running)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set bit 1 = 1 in simulator state | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check Pump Circulation sensor | Shows "Running" |
| 4 | Set bit 1 = 0 in simulator state | File saved |
| 5 | Wait for coordinator refresh | Data updated |
| 6 | Check Pump Circulation sensor | Shows "Idle" |

### Pass/Fail Criteria
- **Pass:** Pump status toggles between "Running" and "Idle"
- **Fail:** Wrong status or doesn't update

---

## TC003.8 - Valve Position Sensor

### Objective
Verify Valve Position sensor displays correctly.

### Test Data Setup - DHW Position
```yaml
"0b51": "0000"  # Bit 2 = 0 (DHW position)
```

### Test Data Setup - CO Position
```yaml
"0b51": "0400"  # Bit 2 = 1 (CO position)
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set bit 2 = 0 in simulator state | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check Valve Position sensor | Shows "DHW" |
| 4 | Set bit 2 = 1 in simulator state | File saved |
| 5 | Wait for coordinator refresh | Data updated |
| 6 | Check Valve Position sensor | Shows "CO" |

### Pass/Fail Criteria
- **Pass:** Valve position toggles between "DHW" and "CO"
- **Fail:** Wrong position or doesn't update

---

## TC003.9 - Combined Status Register Test

### Objective
Verify multiple status bits work correctly together.

### Test Data Setup
```yaml
"0b51": "0500"  # Bits 0 and 2 set: Pump CO running + CO valve position
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set combined value in simulator | File saved |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check Pump CO | Shows "Running" |
| 4 | Check Pump Circulation | Shows "Idle" |
| 5 | Check Valve Position | Shows "CO" |

### Pass/Fail Criteria
- **Pass:** All three sensors show correct values from same register
- **Fail:** Any sensor shows incorrect value

---

## TC003.10 - Sensor Unavailability Handling

### Objective
Verify sensors handle unavailable states gracefully.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Delete a register from simulator state | Register removed |
| 2 | Wait for coordinator refresh | Data updated |
| 3 | Check corresponding sensor | Shows 0 or default value (not error) |
| 4 | Verify no crash or exception | System continues operating |

### Pass/Fail Criteria
- **Pass:** Missing register results in default value, not error
- **Fail:** Sensor shows error or causes exception

---

## TC003.11 - Sensor Device Class Verification

### Objective
Verify sensors have correct device classes for Home Assistant integration.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Developer Tools > States | States page opens |
| 2 | Find temperature sensors | Sensors listed |
| 3 | Check `device_class` attribute | Should be "temperature" |
| 4 | Find pressure sensor | Sensor listed |
| 5 | Check `device_class` attribute | Should be "pressure" |
| 6 | Check `unit_of_measurement` for all | Correct units assigned |

### Expected Device Classes
| Sensor Type | Device Class | Unit |
|-------------|--------------|------|
| Temperature | temperature | °C |
| Pressure | pressure | bar |
| Status | None | - |

### Pass/Fail Criteria
- **Pass:** All sensors have correct device classes
- **Fail:** Wrong or missing device classes

---

## TC003.12 - Sensor State Class Verification

### Objective
Verify sensors have correct state classes for statistics/graphs.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Developer Tools > States | States page opens |
| 2 | Find temperature/pressure sensors | Sensors listed |
| 3 | Check `state_class` attribute | Should be "measurement" |

### Pass/Fail Criteria
- **Pass:** Measurement sensors have `state_class: measurement`
- **Fail:** Missing or incorrect state class

---

## TC003.13 - Real-time Sensor Updates

### Objective
Verify sensors update in real-time when simulator state changes.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open sensor in HA UI | Sensor value visible |
| 2 | Note current value | Value recorded |
| 3 | Edit simulator state file | New value set |
| 4 | Wait for coordinator scan interval | Data refreshes |
| 5 | Verify sensor shows new value | Value updated |

### Pass/Fail Criteria
- **Pass:** Sensor updates within coordinator scan interval
- **Fail:** Sensor doesn't update or takes too long

---

## Summary Checklist

| Test ID | Test Name | Priority | Result | Notes |
|---------|-----------|----------|--------|-------|
| TC003.1 | Temperature Sensor Display | High | | |
| TC003.2 | Temperature Sensor Decimal Precision | Medium | | |
| TC003.3 | Temperature Sensor Negative Values | Medium | | |
| TC003.4 | Pressure Sensor Display | High | | |
| TC003.5 | Pressure Sensor Precision | Medium | | |
| TC003.6 | Pump CO Status Sensor | High | | |
| TC003.7 | Pump Circulation Status Sensor | High | | |
| TC003.8 | Valve Position Sensor | High | | |
| TC003.9 | Combined Status Register Test | High | | |
| TC003.10 | Sensor Unavailability Handling | Medium | | |
| TC003.11 | Sensor Device Class Verification | Medium | | |
| TC003.12 | Sensor State Class Verification | Medium | | |
| TC003.13 | Real-time Sensor Updates | High | | |

---

## Test Data Reference

### Temperature Encoding (scaled ×10)
| Temperature | Decimal Value | Hex (BE) | Hex (LE) |
|-------------|---------------|----------|----------|
| 15.0°C | 150 | 0096 | 9600 |
| 20.0°C | 200 | 00C8 | c800 |
| 22.5°C | 225 | 00E1 | e100 |
| 25.0°C | 250 | 00FA | fa00 |
| 40.0°C | 400 | 0190 | 9001 |
| -5.0°C | -50 | FFCE | ceff |

### Pressure Encoding (scaled ×100)
| Pressure | Decimal Value | Hex (BE) | Hex (LE) |
|----------|---------------|----------|----------|
| 1.50 bar | 150 | 0096 | 9600 |
| 2.50 bar | 250 | 00FA | fa00 |
| 5.00 bar | 500 | 01F4 | f401 |
| 5.04 bar | 504 | 01F8 | f801 |

### Status Register 0b51
| Bit | Function | Value 1 | Value 0 |
|-----|----------|---------|---------|
| 0 | Pump CO | Running | Idle |
| 1 | Pump Circulation | Running | Idle |
| 2 | Valve Position | CO | DHW |

### Status Register Test Values
| State | Bit 2 | Bit 1 | Bit 0 | Hex (LE) |
|-------|-------|-------|-------|----------|
| All idle, DHW | 0 | 0 | 0 | "0000" |
| Pump CO running, DHW | 0 | 0 | 1 | "0100" |
| Pump Circ running, DHW | 0 | 1 | 0 | "0200" |
| Both pumps, DHW | 0 | 1 | 1 | "0300" |
| All idle, CO | 1 | 0 | 0 | "0400" |
| Pump CO running, CO | 1 | 0 | 1 | "0500" |
| All running, CO | 1 | 1 | 1 | "0700" |
