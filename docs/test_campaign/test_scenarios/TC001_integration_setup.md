# TC001 - Integration Setup

**Priority:** Critical  
**Prerequisites:** `SIMULATION_MODE=1` environment variable set

---

## TC001.1 - Integration Discovery

**Action:** Settings → Devices & Services → Add Integration → Search "Kospel"

**Expected:** "Kospel Electric Heaters" appears in search results

---

## TC001.2 - Config Flow

**Initial State:** Use `state_baseline.yaml`

**Action:** Click "Kospel Electric Heaters" → Submit (leave IP/Device ID default)

**Expected:** Integration added successfully, shows in integrations list

---

## TC001.3 - Entity Verification

**Initial State:** Use `state_baseline.yaml`

**Action:** Click Kospel integration → View device entities

**Expected Entities (14 total):**

| Type | Entity | Expected Value |
|------|--------|----------------|
| Climate | Kospel Heater | Mode: Heat, Preset: winter |
| Sensor | Room Temp Economy | 22.0°C |
| Sensor | Room Temp Comfort | 23.0°C |
| Sensor | Room Temp Comfort+ | 24.0°C |
| Sensor | Room Temp Comfort- | 21.0°C |
| Sensor | CWU Temp Economy | 40.0°C |
| Sensor | CWU Temp Comfort | 42.0°C |
| Sensor | Manual Temperature | 22.5°C |
| Sensor | Pressure | 5.00 bar |
| Sensor | Pump CO | Idle |
| Sensor | Pump Circulation | Idle |
| Sensor | Valve Position | DHW |
| Switch | Manual Mode | OFF |
| Switch | Water Heater | OFF |

---

## TC001.4 - Restart Resilience

**Initial State:** Integration configured with `state_baseline.yaml`

**Action:** Settings → System → Restart Home Assistant

**Expected:** After restart, integration loads, all 14 entities present with same values

---

## TC001.5 - Integration Removal

**Action:** Settings → Devices & Services → Kospel → Delete

**Expected:** Integration removed, no orphan entities in Developer Tools → States

---

## Summary

| Test | Result |
|------|--------|
| TC001.1 | [ ] |
| TC001.2 | [ ] |
| TC001.3 | [ ] |
| TC001.4 | [ ] |
| TC001.5 | [ ] |
