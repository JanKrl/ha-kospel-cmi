# TC004 - Switch Entity Tests

**Priority:** High  
**Entities:** Manual Mode (bit 9), Water Heater (bit 4)

Both switches operate on register **0b55**.

---

## HA → State File Tests

### TC004.1 - Manual Mode: OFF → ON

**Initial State:**
```yaml
"0b55": "0020"  # Winter, Manual OFF
```

**Action:** In HA, turn ON Manual Mode switch

**Expected State:**
```yaml
"0b55": "0220"  # bit 9 set (Winter preserved)
```

---

### TC004.2 - Manual Mode: ON → OFF

**Initial State:**
```yaml
"0b55": "0220"  # Winter + Manual
```

**Action:** In HA, turn OFF Manual Mode switch

**Expected State:**
```yaml
"0b55": "0020"  # bit 9 cleared (Winter preserved)
```

---

### TC004.3 - Water Heater: OFF → ON

**Initial State:**
```yaml
"0b55": "0020"  # Winter, Water OFF
```

**Action:** In HA, turn ON Water Heater switch

**Expected State:**
```yaml
"0b55": "0030"  # bit 4 set (Winter preserved)
```

---

### TC004.4 - Water Heater: ON → OFF

**Initial State:**
```yaml
"0b55": "0030"  # Winter + Water
```

**Action:** In HA, turn OFF Water Heater switch

**Expected State:**
```yaml
"0b55": "0020"  # bit 4 cleared (Winter preserved)
```

---

### TC004.5 - Both Switches Independent

**Initial State:**
```yaml
"0b55": "0020"  # Winter only
```

**Actions (sequential):**
1. Turn ON Manual Mode
2. Verify: `"0b55": "0220"`
3. Turn ON Water Heater
4. Verify: `"0b55": "0230"`
5. Turn OFF Manual Mode
6. Verify: `"0b55": "0030"` (Water still ON)

---

## State File → HA Tests

### TC004.6 - Read Manual Mode from State

**Test A - Manual OFF:**
```yaml
"0b55": "0020"  # bit 9 = 0
```
**HA Verification:** Manual Mode switch shows OFF

**Test B - Manual ON:**
```yaml
"0b55": "0220"  # bit 9 = 1
```
**HA Verification:** Manual Mode switch shows ON

---

### TC004.7 - Read Water Heater from State

**Test A - Water OFF:**
```yaml
"0b55": "0020"  # bit 4 = 0
```
**HA Verification:** Water Heater switch shows OFF

**Test B - Water ON:**
```yaml
"0b55": "0030"  # bit 4 = 1
```
**HA Verification:** Water Heater switch shows ON

---

### TC004.8 - Switches Preserve Mode on Preset Change

**Initial State:**
```yaml
"0b55": "0230"  # Winter + Manual + Water
```

**Action:** In HA Climate, change preset to "summer"

**Expected State:**
```yaml
"0b55": "0218"  # Summer + Manual + Water (bits 3, 4, 9)
```

**Verification:** Manual and Water switches remain ON

---

## Summary

| Test | Direction | Result |
|------|-----------|--------|
| TC004.1 | HA → File | [ ] |
| TC004.2 | HA → File | [ ] |
| TC004.3 | HA → File | [ ] |
| TC004.4 | HA → File | [ ] |
| TC004.5 | HA → File | [ ] |
| TC004.6 | File → HA | [ ] |
| TC004.7 | File → HA | [ ] |
| TC004.8 | HA → File | [ ] |

---

## Quick Reference: 0b55 Values

| Configuration | Hex | Bits |
|---------------|-----|------|
| Winter only | `"0020"` | 5 |
| Winter + Water | `"0030"` | 4, 5 |
| Winter + Manual | `"0220"` | 5, 9 |
| Winter + Manual + Water | `"0230"` | 4, 5, 9 |
| Summer only | `"0008"` | 3 |
| Summer + Water | `"0018"` | 3, 4 |
| Summer + Manual | `"0208"` | 3, 9 |
| Summer + Manual + Water | `"0218"` | 3, 4, 9 |

## Bit Position Reference

| Bit | Value | Hex |
|-----|-------|-----|
| 3 (Summer) | 8 | 0x08 |
| 4 (Water) | 16 | 0x10 |
| 5 (Winter) | 32 | 0x20 |
| 9 (Manual) | 512 | 0x200 |
