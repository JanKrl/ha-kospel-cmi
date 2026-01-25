# TC002 - Climate Entity Tests

**Priority:** High  
**Entity:** `climate.kospel_heater`

---

## HA → State File Tests

### TC002.1 - Set Preset: Winter

**Initial State:**
```yaml
"0b55": "0000"  # Off
```

**Action:** In HA, set Climate preset to "winter"

**Expected State:**
```yaml
"0b55": "0020"  # bit 5 = 1
```

**HA Verification:** HVAC mode shows "Heat", Preset shows "winter"

---

### TC002.2 - Set Preset: Summer

**Initial State:**
```yaml
"0b55": "0020"  # Winter
```

**Action:** In HA, set Climate preset to "summer"

**Expected State:**
```yaml
"0b55": "0008"  # bit 3 = 1
```

**HA Verification:** HVAC mode shows "Heat", Preset shows "summer"

---

### TC002.3 - Set Preset: Off

**Initial State:**
```yaml
"0b55": "0020"  # Winter
```

**Action:** In HA, set Climate preset to "off"

**Expected State:**
```yaml
"0b55": "0000"  # bits 3,5 = 0
```

**HA Verification:** HVAC mode shows "Off", Preset shows "off"

---

### TC002.4 - Set HVAC Mode: OFF to HEAT

**Initial State:**
```yaml
"0b55": "0000"  # Off
```

**Action:** In HA, set HVAC mode to "Heat"

**Expected State:**
```yaml
"0b55": "0020"  # Winter mode (default for HEAT)
```

---

### TC002.5 - Set HVAC Mode: HEAT to OFF

**Initial State:**
```yaml
"0b55": "0020"  # Winter
```

**Action:** In HA, set HVAC mode to "Off"

**Expected State:**
```yaml
"0b55": "0000"
```

---

### TC002.6 - Set Target Temperature: 25.0°C

**Initial State:**
```yaml
"0b8d": "e100"  # 22.5°C
```

**Action:** In HA Climate, set temperature to 25.0°C

**Expected State:**
```yaml
"0b8d": "fa00"  # 250 = 25.0°C
```

---

### TC002.7 - Set Target Temperature: 20.0°C

**Initial State:**
```yaml
"0b8d": "e100"  # 22.5°C
```

**Action:** In HA Climate, set temperature to 20.0°C

**Expected State:**
```yaml
"0b8d": "c800"  # 200 = 20.0°C
```

---

## State File → HA Tests

### TC002.8 - Read Heater Mode from State

**Initial State:**
```yaml
"0b55": "0008"  # Summer mode
```

**Action:** Wait for HA refresh (30s) or restart HA

**HA Verification:** Climate shows Preset "summer", HVAC "Heat"

---

### TC002.9 - Read Target Temperature from State

**Initial State:**
```yaml
"0b8d": "0801"  # 264 = 26.4°C
```

**Action:** Wait for HA refresh (30s)

**HA Verification:** Climate target temperature shows 26.4°C

---

### TC002.10 - Mode Preserved with Feature Toggles

**Initial State:**
```yaml
"0b55": "0020"  # Winter only
```

**Action:** In HA, turn ON Manual Mode switch

**Expected State:**
```yaml
"0b55": "0220"  # Winter + Manual (bit 5 and bit 9)
```

**Verification:** Winter mode preserved (bit 5 still set)

---

## Summary

| Test | Direction | Result |
|------|-----------|--------|
| TC002.1 | HA → File | [P] |
| TC002.2 | HA → File | [F] |
| TC002.3 | HA → File | [F] |
| TC002.4 | HA → File | [F] |
| TC002.5 | HA → File | [F] |
| TC002.6 | HA → File | [P] |
| TC002.7 | HA → File | [P] |
| TC002.8 | File → HA | [F] |
| TC002.9 | File → HA | [F] |
| TC002.10 | HA → File | [F] |

### Notes

### TC002.1
Register value changed correctly but HVAC mode shows "off", not "heating"

### TC002.2
Register value changed to 0820 and was not enclosed in quote signs. HVAC is "off"

### TC002.3
In test setup register value was set to "0020" but Home Assistant shows preset "off".
Logs:
Decoded settings: heater_mode (0b55): 0020 → HeaterMode.OFF | is_manual_mode_enabled (0b55): 0020 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0020 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0

### TC002.4
When changed HVAC mode to "heat" preset remained at "off". Result register value '2000' with quote signs.
Logs:
2026-01-25 13:09:36.480 DEBUG (MainThread) [custom_components.kospel.controller.api] Set heater_mode = HeaterMode.WINTER (pending write)
2026-01-25 13:09:36.481 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 13:09:36.481 DEBUG (MainThread) [custom_components.kospel.registers.encoders] Encoding heater mode to Winter: 2000 (32) → 2000 (32)
2026-01-25 13:09:36.481 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded heater_mode: 2000 → 2000
2026-01-25 13:09:36.481 DEBUG (MainThread) [custom_components.kospel.controller.api] Register 0b55 unchanged, skipping write
2026-01-25 13:09:36.481 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully

### TC002.5
No logs were produced, no register value changed.

### TC002.6
Register value is not quoted

### TC002.7
After setting initial register value for the test, the value is not updated in Home Assistant. But logs show correctly decoded value:
Decoded settings: heater_mode (0b55): 0020 → HeaterMode.OFF | is_manual_mode_enabled (0b55): 0020 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0020 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
Then, after setting new value in UI, register is updated correctly.

### TC002.8
Home Assistant UI shows HVAC off and preset winter.
Logs:
Decoded settings: heater_mode (0b55): 0008 → HeaterMode.OFF | is_manual_mode_enabled (0b55): 0008 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0008 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): c800 → 20.0 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0

### TC002.9
Correct decoded value is shown in logs but is not visible in UI. Manual temperature entity is sensor.manual_temperature and value remained at 22.5

#### TC002.10
Value change appers in logs and in state file but in Home Assistant it shows manual mode disabled.
Logs:
2026-01-25 13:32:25.275 DEBUG (MainThread) [custom_components.kospel.controller.api] Set is_manual_mode_enabled = ManualMode.ENABLED (pending write)
2026-01-25 13:32:25.275 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 13:32:25.275 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded is_manual_mode_enabled: 0020 → 0022
2026-01-25 13:32:25.276 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 13:32:25.304 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b55: 0020 → 0022 (8192 → 8704)
2026-01-25 13:32:25.304 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b55: 0020 → 0022
2026-01-25 13:32:25.304 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully

---

## Quick Reference: 0b55 Mode Values

| Mode | Hex | Bits |
|------|-----|------|
| Off | `"0000"` | - |
| Summer | `"0008"` | 3 |
| Winter | `"0020"` | 5 |
| Summer + Water | `"0018"` | 3, 4 |
| Winter + Water | `"0030"` | 4, 5 |
| Winter + Manual | `"0220"` | 5, 9 |
| Winter + Manual + Water | `"0230"` | 4, 5, 9 |

## Quick Reference: Temperature Encoding

| °C | Hex (LE) |
|----|----------|
| 20.0 | `"c800"` |
| 22.5 | `"e100"` |
| 25.0 | `"fa00"` |
| 26.4 | `"0801"` |
