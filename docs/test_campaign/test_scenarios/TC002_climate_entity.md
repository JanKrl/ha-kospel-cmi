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
| TC002.1 | HA → File | [ ] |
| TC002.2 | HA → File | [ ] |
| TC002.3 | HA → File | [ ] |
| TC002.4 | HA → File | [ ] |
| TC002.5 | HA → File | [ ] |
| TC002.6 | HA → File | [ ] |
| TC002.7 | HA → File | [ ] |
| TC002.8 | File → HA | [ ] |
| TC002.9 | File → HA | [ ] |
| TC002.10 | HA → File | [ ] |

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
