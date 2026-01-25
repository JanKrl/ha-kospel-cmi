# TC005 - Simulator Tests

**Priority:** High  
**State File:** `<config>/custom_components/kospel/data/simulation_state.yaml`

---

## TC005.1 - Simulation Mode Detection

**Precondition:** `SIMULATION_MODE=1` environment variable set

**Action:** Check HA logs after starting integration

**Expected:** Logs show simulator routing messages (no HTTP errors)

---

## TC005.2 - State File Auto-Creation

**Precondition:** Delete state file if exists

**Action:** Configure integration → Wait for first refresh

**Expected:** State file created at `data/simulation_state.yaml`

---

## TC005.3 - State File Read

**Initial State:** Create file manually:
```yaml
"0b55": "0020"
"0b6a": "e600"
"0b8a": "f401"
```

**Action:** Restart integration or wait for refresh

**HA Verification:**
| Entity | Expected |
|--------|----------|
| Heater Mode | Winter |
| Room Temp Comfort | 23.0°C |
| Pressure | 5.00 bar |

---

## TC005.4 - State File Write

**Initial State:**
```yaml
"0b8d": "e100"  # 22.5°C
```

**Action:** In HA, set Climate temperature to 25.0°C

**Expected State:**
```yaml
"0b8d": "fa00"  # 25.0°C written
```

---

## TC005.5 - Bit Operations Preserve Other Bits

**Initial State:**
```yaml
"0b55": "0020"  # Winter (bit 5)
```

**Action:** Turn ON Manual Mode (bit 9)

**Expected State:**
```yaml
"0b55": "0220"  # Both bits 5 and 9 set
```

**Verification:** Bit 5 preserved during bit 9 operation

---

## TC005.6 - State Persistence After Restart

**Initial State:** Set via HA actions:
```yaml
"0b55": "0230"
"0b8d": "fa00"
```

**Action:** Restart Home Assistant

**Expected:** After restart:
- State file unchanged
- HA entities show same values

---

## TC005.7 - Manual State Edit Reflected

**Initial State:**
```yaml
"0b6a": "e600"  # 23.0°C
```

**Action:** Edit file directly:
```yaml
"0b6a": "fa00"  # 25.0°C
```

Wait for HA refresh (30s)

**HA Verification:** Room Temp Comfort shows 25.0°C

---

## TC005.8 - Missing Register Returns Default

**Initial State:** Use `state_minimal.yaml` (only 0b55)

**Action:** Check sensors in HA

**HA Verification:** 
- Pressure shows 0.0 bar
- Temperatures show 0.0°C
- No errors in logs

---

## TC005.9 - State File YAML Format

**Action:** After several operations, check state file format

**Expected:**
- Keys quoted: `"0b55":`
- Values quoted: `"0020"`
- Valid YAML syntax

**Example:**
```yaml
"0b51": "0000"
"0b55": "0020"
"0b8a": "f401"
```

---

## Summary

| Test | Result |
|------|--------|
| TC005.1 | [ ] |
| TC005.2 | [ ] |
| TC005.3 | [ ] |
| TC005.4 | [ ] |
| TC005.5 | [ ] |
| TC005.6 | [ ] |
| TC005.7 | [ ] |
| TC005.8 | [ ] |
| TC005.9 | [ ] |

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `SIMULATION_MODE` | Enable simulation | `1`, `true`, `yes`, `on` |
| `SIMULATION_STATE_FILE` | Custom file path | `custom_state.yaml` |

## State File Location

Default: `<config>/custom_components/kospel/data/simulation_state.yaml`
