# TC003 - Sensor Entity Tests

**Priority:** High  
**Direction:** State File → HA (sensors are read-only)

---

## Temperature Sensors

### TC003.1 - Temperature Sensors Display

**Initial State:** Use `state_baseline.yaml`
```yaml
"0b68": "dc00"  # Room Temp Economy: 22.0°C
"0b69": "d200"  # Room Temp Comfort-: 21.0°C
"0b6a": "e600"  # Room Temp Comfort: 23.0°C
"0b6b": "f000"  # Room Temp Comfort+: 24.0°C
"0b66": "9001"  # CWU Temp Economy: 40.0°C
"0b67": "a401"  # CWU Temp Comfort: 42.0°C
"0b8d": "e100"  # Manual Temperature: 22.5°C
```

**Action:** Check sensor values in HA after refresh

**Expected HA Values:**

| Sensor | Expected |
|--------|----------|
| Room Temp Economy | 22.0°C |
| Room Temp Comfort- | 21.0°C |
| Room Temp Comfort | 23.0°C |
| Room Temp Comfort+ | 24.0°C |
| CWU Temp Economy | 40.0°C |
| CWU Temp Comfort | 42.0°C |
| Manual Temperature | 22.5°C |

---

### TC003.2 - Temperature Change Detection

**Initial State:**
```yaml
"0b6a": "e600"  # 23.0°C
```

**Action:** Edit state file:
```yaml
"0b6a": "fa00"  # 25.0°C
```

Wait for HA refresh (30s)

**HA Verification:** Room Temp Comfort shows 25.0°C

---

### TC003.3 - Decimal Precision

**Initial State:**
```yaml
"0b6a": "e500"  # 229 = 22.9°C
```

**HA Verification:** Room Temp Comfort shows 22.9°C (one decimal place)

---

### TC003.4 - Negative Temperature

**Initial State:**
```yaml
"0b6a": "ceff"  # -50 = -5.0°C (two's complement)
```

**HA Verification:** Room Temp Comfort shows -5.0°C

---

## Pressure Sensor

### TC003.5 - Pressure Display

**Initial State:**
```yaml
"0b8a": "f401"  # 500 = 5.00 bar
```

**HA Verification:** Pressure sensor shows 5.00 bar

---

### TC003.6 - Pressure Change Detection

**Initial State:**
```yaml
"0b8a": "f401"  # 5.00 bar
```

**Action:** Edit state file:
```yaml
"0b8a": "f801"  # 504 = 5.04 bar
```

**HA Verification:** Pressure shows 5.04 bar

---

## Status Sensors

### TC003.7 - Pump CO Status

**Test A - Idle:**
```yaml
"0b51": "0000"  # bit 0 = 0
```
**HA Verification:** Pump CO shows "Idle"

**Test B - Running:**
```yaml
"0b51": "0100"  # bit 0 = 1
```
**HA Verification:** Pump CO shows "Running"

---

### TC003.8 - Pump Circulation Status

**Test A - Idle:**
```yaml
"0b51": "0000"  # bit 1 = 0
```
**HA Verification:** Pump Circulation shows "Idle"

**Test B - Running:**
```yaml
"0b51": "0200"  # bit 1 = 1
```
**HA Verification:** Pump Circulation shows "Running"

---

### TC003.9 - Valve Position

**Test A - DHW:**
```yaml
"0b51": "0000"  # bit 2 = 0
```
**HA Verification:** Valve Position shows "DHW"

**Test B - CO:**
```yaml
"0b51": "0400"  # bit 2 = 1
```
**HA Verification:** Valve Position shows "CO"

---

### TC003.10 - Combined Status Register

**Initial State:**
```yaml
"0b51": "0500"  # bits 0 and 2 set
```

**HA Verification:**
| Sensor | Expected |
|--------|----------|
| Pump CO | Running |
| Pump Circulation | Idle |
| Valve Position | CO |

---

### TC003.11 - Missing Register Default

**Initial State:** Use `state_minimal.yaml` (only 0b55 defined)

**HA Verification:** Pressure sensor shows 0.0 bar (default for missing register)

---

## Summary

| Test | Result |
|------|--------|
| TC003.1 | [ ] |
| TC003.2 | [ ] |
| TC003.3 | [ ] |
| TC003.4 | [ ] |
| TC003.5 | [ ] |
| TC003.6 | [ ] |
| TC003.7 | [ ] |
| TC003.8 | [ ] |
| TC003.9 | [ ] |
| TC003.10 | [ ] |
| TC003.11 | [ ] |

---

## Quick Reference: 0b51 Status Values

| Status | Hex | Bits |
|--------|-----|------|
| All idle, DHW | `"0000"` | - |
| Pump CO running | `"0100"` | 0 |
| Pump Circ running | `"0200"` | 1 |
| Both pumps | `"0300"` | 0, 1 |
| CO valve | `"0400"` | 2 |
| All running, CO | `"0700"` | 0, 1, 2 |

## Quick Reference: Temperature Encoding

| °C | Decimal | Hex (LE) |
|----|---------|----------|
| -5.0 | -50 | `"ceff"` |
| 20.0 | 200 | `"c800"` |
| 22.9 | 229 | `"e500"` |
| 23.0 | 230 | `"e600"` |
| 25.0 | 250 | `"fa00"` |
