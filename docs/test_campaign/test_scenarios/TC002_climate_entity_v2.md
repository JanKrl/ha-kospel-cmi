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
"0b55": "2000"  # bit 5 = 1 (little-endian)
```

**HA Verification:** HVAC mode shows "Heat", Preset shows "winter"

---

### TC002.2 - Set Preset: Summer

**Initial State:**
```yaml
"0b55": "2000"  # Winter (little-endian)
```

**Action:** In HA, set Climate preset to "summer"

**Expected State:**
```yaml
"0b55": "0800"  # bit 3 = 1 (little-endian)
```

**HA Verification:** HVAC mode shows "Heat", Preset shows "summer"

---

### TC002.3 - Set Preset: Off

**Initial State:**
```yaml
"0b55": "2000"  # Winter (little-endian)
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
"0b55": "2000"  # Winter mode (default for HEAT, little-endian)
```

---

### TC002.5 - Set HVAC Mode: HEAT to OFF

**Initial State:**
```yaml
"0b55": "2000"  # Winter (little-endian)
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
"0b55": "0800"  # Summer mode (little-endian)
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
"0b55": "2000"  # Winter only (little-endian)
```

**Action:** In HA, turn ON Manual Mode switch

**Expected State:**
```yaml
"0b55": "2002"  # Winter + Manual (bit 5 and bit 9, little-endian)
```

**Verification:** Winter mode preserved (bit 5 still set)

---

## Summary

| Test | Direction | Result |
|------|-----------|--------|
| TC002.1 | HA → File | [P] |
| TC002.2 | HA → File | [P] |
| TC002.3 | HA → File | [F] |
| TC002.4 | HA → File | [?] |
| TC002.5 | HA → File | [F] |
| TC002.6 | HA → File | [?] |
| TC002.7 | HA → File | [?] |
| TC002.8 | File → HA | [F] |
| TC002.9 | File → HA | [F] |
| TC002.10 | HA → File | [P] |

### Notes

### TC002.1
Result state:
0b55: '2000'

Logs:
2026-01-25 18:00:55.687 DEBUG (MainThread) [custom_components.kospel.controller.api] Set heater_mode = HeaterMode.WINTER (pending write)
2026-01-25 18:00:55.687 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:00:55.688 DEBUG (MainThread) [custom_components.kospel.registers.encoders] Encoding heater mode to Winter: 0000 (0) → 2000 (32)
2026-01-25 18:00:55.688 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded heater_mode: 0000 → 2000
2026-01-25 18:00:55.688 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:00:55.720 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b55: 0000 → 2000 (0 → 32)
2026-01-25 18:00:55.720 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b55: 0000 → 2000
2026-01-25 18:00:55.720 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated heater_mode = HeaterMode.WINTER after write
2026-01-25 18:00:55.720 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_manual_mode_enabled = ManualMode.DISABLED after write
2026-01-25 18:00:55.721 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_water_heater_enabled = WaterHeaterEnabled.DISABLED after write
2026-01-25 18:00:55.721 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:00:55.721 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:00:55.722 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:00:57.717 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:00:57.718 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:00:57.718 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:00:57.718 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:00:57.718 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully
2026-01-25 18:00:57.718 DEBUG (MainThread) [custom_components.kospel.coordinator] Finished fetching kospel data in 1.997 seconds (success: True)

### TC002.2
Result state:
0b55: 0800

Logs:
2026-01-25 18:03:29.435 DEBUG (MainThread) [custom_components.kospel.controller.api] Set heater_mode = HeaterMode.SUMMER (pending write)
2026-01-25 18:03:29.436 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:03:29.436 DEBUG (MainThread) [custom_components.kospel.registers.encoders] Encoding heater mode to Summer: 2000 (32) → 0800 (8)
2026-01-25 18:03:29.436 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded heater_mode: 2000 → 0800
2026-01-25 18:03:29.437 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:03:29.469 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b55: 2000 → 0800 (32 → 8)
2026-01-25 18:03:29.469 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b55: 2000 → 0800
2026-01-25 18:03:29.469 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated heater_mode = HeaterMode.SUMMER after write
2026-01-25 18:03:29.470 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_manual_mode_enabled = ManualMode.DISABLED after write
2026-01-25 18:03:29.470 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_water_heater_enabled = WaterHeaterEnabled.DISABLED after write
2026-01-25 18:03:29.470 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:03:29.470 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:03:29.471 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:03:31.483 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:03:31.483 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:03:31.484 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 0800 → HeaterMode.SUMMER | is_manual_mode_enabled (0b55): 0800 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0800 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:03:31.484 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:03:31.485 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

### TC002.3
After manually changing state file register '0b55' to '2000' the next refresh from API resulted in the following logs:
2026-01-25 18:06:08.449 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:06:08.450 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:06:10.389 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:06:10.390 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:06:10.390 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:06:10.390 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:06:10.390 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

but the UI kept showing preset "summer".
After that the preset was set to "off". This resulted in no logs being produced and no value change in state file. Then, I set register value to '0000' which generated the following logs in next refresh:
2026-01-25 18:10:16.449 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:10:16.450 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:10:18.379 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:10:18.379 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:10:18.379 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 0000 → HeaterMode.OFF | is_manual_mode_enabled (0b55): 0000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:10:18.380 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:10:18.380 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

but UI still shows "summer".

### TC002.4
Result state:
0b55: '2000'

Logs:
2026-01-25 18:13:21.385 DEBUG (MainThread) [custom_components.kospel.controller.api] Set heater_mode = HeaterMode.WINTER (pending write)
2026-01-25 18:13:21.386 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:13:21.386 DEBUG (MainThread) [custom_components.kospel.registers.encoders] Encoding heater mode to Winter: 0000 (0) → 2000 (32)
2026-01-25 18:13:21.386 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded heater_mode: 0000 → 2000
2026-01-25 18:13:21.387 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:13:21.416 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b55: 0000 → 2000 (0 → 32)
2026-01-25 18:13:21.416 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b55: 0000 → 2000
2026-01-25 18:13:21.416 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated heater_mode = HeaterMode.WINTER after write
2026-01-25 18:13:21.417 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_manual_mode_enabled = ManualMode.DISABLED after write
2026-01-25 18:13:21.417 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_water_heater_enabled = WaterHeaterEnabled.DISABLED after write
2026-01-25 18:13:21.417 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:13:21.417 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:13:21.418 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:13:23.377 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:13:23.378 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:13:23.378 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): e100 → 22.5 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:13:23.379 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:13:23.379 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

Additional comment:
Seems like there are no logs related to HAVOC setting change.

### TC002.5
There are no logs on change to OFF.

### TC002.6
Result state:
0b8d: fa00

Logs:
2026-01-25 18:16:43.118 DEBUG (MainThread) [custom_components.kospel.controller.api] Set manual_temperature = 25.0 (pending write)
2026-01-25 18:16:43.118 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:16:43.119 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded manual_temperature: e100 → fa00
2026-01-25 18:16:43.119 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:16:43.148 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b8d: e100 → fa00 (225 → 250)
2026-01-25 18:16:43.148 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b8d: e100 → fa00
2026-01-25 18:16:43.149 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated manual_temperature = 25.0 after write
2026-01-25 18:16:43.149 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:16:43.149 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:16:43.150 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:16:45.109 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:16:45.109 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:16:45.110 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): fa00 → 25.0 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:16:45.110 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:16:45.110 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

Additional comment:
Entity sensor.manual_temperature did not change. It's value remained at 22.5

### TC002.7
Result state:
0b8d: c800

Logs:
2026-01-25 18:19:08.956 DEBUG (MainThread) [custom_components.kospel.controller.api] Set manual_temperature = 20.0 (pending write)
2026-01-25 18:19:08.956 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:19:08.956 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded manual_temperature: e100 → c800
2026-01-25 18:19:08.957 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:19:08.986 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b8d: e100 → c800 (225 → 200)
2026-01-25 18:19:08.987 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b8d: e100 → c800
2026-01-25 18:19:08.987 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated manual_temperature = 20.0 after write
2026-01-25 18:19:08.987 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:19:08.988 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:19:08.988 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:19:10.936 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:19:10.936 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:19:10.937 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): c800 → 20.0 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:19:10.937 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:19:10.937 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

Additional comment:
Entity sensor.manual_temperature did not change. It's value remained at 22.5

### TC002.8
Logs:
2026-01-25 18:20:12.450 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:20:12.450 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:20:13.807 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:20:13.807 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:20:13.807 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 0800 → HeaterMode.SUMMER | is_manual_mode_enabled (0b55): 0800 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0800 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): c800 → 20.0 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:20:13.807 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:20:13.808 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

Additional comment:
UI shows preset "off" and HAVOC "off".

### TC002.9
Climate widget shows set temperature 20.0 and ensor.manual_temperature shows 22.5

#### TC002.10
Seems like the test instruction is incorrect. Setting register value to '0020' results in the following log:
2026-01-25 18:23:23.449 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:23:23.450 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:23:24.952 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:23:24.952 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:23:24.953 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 0020 → HeaterMode.OFF | is_manual_mode_enabled (0b55): 0020 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 0020 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): 0801 → 26.4 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:23:24.953 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:23:24.953 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

But then, when I set the register to '2000' the logs show:
2026-01-25 18:24:26.450 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:24:26.450 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:24:28.381 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:24:28.381 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:24:28.382 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2000 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2000 → ManualMode.DISABLED | is_water_heater_enabled (0b55): 2000 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): 0801 → 26.4 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:24:28.382 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:24:28.382 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

When I switched manual mode to ON:
2026-01-25 18:25:22.545 DEBUG (MainThread) [custom_components.kospel.controller.api] Set is_manual_mode_enabled = ManualMode.ENABLED (pending write)
2026-01-25 18:25:22.546 INFO (MainThread) [custom_components.kospel.controller.api] Saving 1 setting(s) to API
2026-01-25 18:25:22.546 DEBUG (MainThread) [custom_components.kospel.controller.api] Encoded is_manual_mode_enabled: 2000 → 2002
2026-01-25 18:25:22.547 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing write_register to simulator implementation
2026-01-25 18:25:22.579 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] WRITE register 0b55: 2000 → 2002 (32 → 544)
2026-01-25 18:25:22.579 INFO (MainThread) [custom_components.kospel.controller.api] Successfully wrote register 0b55: 2000 → 2002
2026-01-25 18:25:22.579 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated heater_mode = HeaterMode.WINTER after write
2026-01-25 18:25:22.579 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_manual_mode_enabled = ManualMode.ENABLED after write
2026-01-25 18:25:22.580 DEBUG (MainThread) [custom_components.kospel.controller.api] Updated is_water_heater_enabled = WaterHeaterEnabled.DISABLED after write
2026-01-25 18:25:22.580 INFO (MainThread) [custom_components.kospel.controller.api] All settings saved successfully
2026-01-25 18:25:22.580 INFO (MainThread) [custom_components.kospel.controller.api] Refreshing heater settings from API
2026-01-25 18:25:22.581 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] Routing read_registers to simulator implementation
2026-01-25 18:25:24.500 DEBUG (MainThread) [custom_components.kospel.kospel.simulator] [SIMULATOR] READ registers 0b00 to 0bff (256 registers)
2026-01-25 18:25:24.500 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoding settings from 256 registers
2026-01-25 18:25:24.501 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded settings: heater_mode (0b55): 2002 → HeaterMode.WINTER | is_manual_mode_enabled (0b55): 2002 → ManualMode.ENABLED | is_water_heater_enabled (0b55): 2002 → WaterHeaterEnabled.DISABLED | is_pump_co_running (0b51): 0000 → PumpStatus.IDLE | is_pump_circulation_running (0b51): 0000 → PumpStatus.IDLE | valve_position (0b51): 0000 → ValvePosition.DHW | manual_temperature (0b8d): 0801 → 26.4 | room_temperature_economy (0b68): dc00 → 22.0 | room_temperature_comfort (0b6a): e600 → 23.0 | room_temperature_comfort_plus (0b6b): f000 → 24.0 | room_temperature_comfort_minus (0b69): d200 → 21.0 | cwu_temperature_economy (0b66): 9001 → 40.0 | cwu_temperature_comfort (0b67): a401 → 42.0 | pressure (0b8a): f401 → 5.0
2026-01-25 18:25:24.501 DEBUG (MainThread) [custom_components.kospel.controller.api] Decoded 14 settings
2026-01-25 18:25:24.501 INFO (MainThread) [custom_components.kospel.controller.api] Heater settings refreshed successfully

Register state:
0b55: '2002'

---

## Quick Reference: 0b55 Mode Values

| Mode | Hex (Little-Endian) | Bits |
|------|---------------------|------|
| Off | `"0000"` | - |
| Summer | `"0800"` | 3 |
| Winter | `"2000"` | 5 |
| Summer + Water | `"1800"` | 3, 4 |
| Winter + Water | `"3000"` | 4, 5 |
| Winter + Manual | `"2200"` | 5, 9 |
| Winter + Manual + Water | `"2300"` | 4, 5, 9 |

## Quick Reference: Temperature Encoding

| °C | Hex (LE) |
|----|----------|
| 20.0 | `"c800"` |
| 22.5 | `"e100"` |
| 25.0 | `"fa00"` |
| 26.4 | `"0801"` |
