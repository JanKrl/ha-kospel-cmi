# Manual Test Campaign - Kospel Home Assistant Integration

## Lean Testing Approach

This test campaign uses a **state-file-driven** approach. Each test:
1. Starts with a known **initial state YAML** file
2. Performs an **action** (either in HA UI or by editing the state file)
3. Verifies the **expected state** by comparing the YAML file or HA UI

**Two-way testing**:
- **HA → State file**: Set value in Home Assistant UI, verify in `simulation_state.yaml`
- **State file → HA**: Edit `simulation_state.yaml`, verify value appears in Home Assistant UI

## Quick Start

### 1. Environment Setup

```bash
# Set environment variable
export SIMULATION_MODE=1

# State file location
<HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

### 2. Running a Test

1. Copy the **Initial State** YAML to `simulation_state.yaml`
2. Restart Home Assistant or wait for refresh (~30s)
3. Perform the **Action** (HA UI change or state file edit)
4. Compare `simulation_state.yaml` with **Expected State**
5. Mark test as **PASS** if states match, **FAIL** otherwise

## State File Location

```
<HA_CONFIG>/custom_components/kospel/data/simulation_state.yaml
```

## Base Initial States

Use these as starting points for tests.

### state_baseline.yaml - Default Test State
```yaml
"0b51": "0000"
"0b55": "0020"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
```

**Decoded values:**
| Register | Setting | Value |
|----------|---------|-------|
| 0b51 | Status | All idle, DHW valve |
| 0b55 | Mode | Winter (bit 5=1) |
| 0b66 | CWU Temp Economy | 40.0°C |
| 0b67 | CWU Temp Comfort | 42.0°C |
| 0b68 | Room Temp Economy | 22.0°C |
| 0b69 | Room Temp Comfort- | 21.0°C |
| 0b6a | Room Temp Comfort | 23.0°C |
| 0b6b | Room Temp Comfort+ | 24.0°C |
| 0b8a | Pressure | 5.00 bar |
| 0b8d | Manual Temperature | 22.5°C |

## Register Reference

### Register 0b55 - Control Flags
| Bit | Function | Value=1 | Value=0 |
|-----|----------|---------|---------|
| 3 | Summer Mode | Active | Inactive |
| 4 | Water Heater | Enabled | Disabled |
| 5 | Winter Mode | Active | Inactive |
| 9 | Manual Mode | Enabled | Disabled |

**Common 0b55 values:**
| Mode | Hex (LE) | Bits set |
|------|----------|----------|
| Off | `"0000"` | none |
| Winter | `"0020"` | 5 |
| Summer | `"0008"` | 3 |
| Winter + Water | `"0030"` | 4, 5 |
| Winter + Manual | `"0220"` | 5, 9 |
| Winter + Manual + Water | `"0230"` | 4, 5, 9 |

### Register 0b51 - Status Flags
| Bit | Function | Value=1 | Value=0 |
|-----|----------|---------|---------|
| 0 | Pump CO | Running | Idle |
| 1 | Pump Circulation | Running | Idle |
| 2 | Valve Position | CO | DHW |

**Common 0b51 values:**
| Status | Hex (LE) |
|--------|----------|
| All idle, DHW | `"0000"` |
| Pump CO running | `"0100"` |
| Pump Circ running | `"0200"` |
| Both pumps running | `"0300"` |
| All idle, CO valve | `"0400"` |

### Temperature Encoding (×10 scale)
| °C | Decimal | Hex (LE) |
|----|---------|----------|
| 20.0 | 200 | `"c800"` |
| 21.0 | 210 | `"d200"` |
| 22.0 | 220 | `"dc00"` |
| 22.5 | 225 | `"e100"` |
| 23.0 | 230 | `"e600"` |
| 24.0 | 240 | `"f000"` |
| 25.0 | 250 | `"fa00"` |
| 40.0 | 400 | `"9001"` |
| 42.0 | 420 | `"a401"` |

### Pressure Encoding (×100 scale)
| bar | Decimal | Hex (LE) |
|-----|---------|----------|
| 5.00 | 500 | `"f401"` |
| 5.04 | 504 | `"f801"` |
| 2.50 | 250 | `"fa00"` |

## Test Scenarios

| ID | Scenario | Document |
|----|----------|----------|
| TC001 | Integration Setup | [TC001_integration_setup.md](test_scenarios/TC001_integration_setup.md) |
| TC002 | Climate Entity | [TC002_climate_entity.md](test_scenarios/TC002_climate_entity.md) |
| TC003 | Sensor Entities | [TC003_sensor_entities.md](test_scenarios/TC003_sensor_entities.md) |
| TC004 | Switch Entities | [TC004_switch_entities.md](test_scenarios/TC004_switch_entities.md) |
| TC005 | Simulator | [TC005_simulator.md](test_scenarios/TC005_simulator.md) |

## Test Result Tracking

Simple pass/fail tracking - no extensive documentation needed:

```
Date: YYYY-MM-DD
Tester: Name

TC001: [P] [P] [P] [P] [P]
TC002: [P] [P] [F] [P] [P] [P] [P]
TC003: [P] [P] [P] [P] [P] [P] [P] [P]
TC004: [P] [P] [P] [P] [P] [P]
TC005: [P] [P] [P] [P] [P]

Failed tests: TC002.3 - Mode not changing
Notes: Investigate heater_mode encoding
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Value not updating in HA | Wait 30s for coordinator refresh |
| State file edit not reflected | Ensure file saved, wait for refresh |
| Entity shows "unavailable" | Check state file exists and is valid YAML |
| Wrong value displayed | Check encoding (little-endian, scaling) |
