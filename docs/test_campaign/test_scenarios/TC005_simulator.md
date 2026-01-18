# TC005 - Simulator Functionality Tests

## Test Category: Simulator System
**Priority:** High  
**Prerequisites:** `SIMULATION_MODE=1` environment variable set

---

## Overview

The simulator provides offline development and testing capability for the Kospel integration. Key features tested:

- State file creation and persistence
- Register read operations
- Register write operations
- Flag bit operations (read-modify-write)
- State file manual editing
- Environment variable configuration

---

## TC005.1 - Simulation Mode Detection

### Objective
Verify the integration correctly detects simulation mode from environment variable.

### Test Steps - Mode Enabled

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set environment variable `SIMULATION_MODE=1` | Variable set |
| 2 | Restart Home Assistant | HA restarts |
| 3 | Check logs for simulation mode indicator | "Simulation mode" or similar message appears |
| 4 | Configure integration | Config flow allows empty IP |
| 5 | Verify entities work without real heater | Entities functional |

### Test Steps - Mode Disabled

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Unset environment variable or set `SIMULATION_MODE=0` | Variable cleared |
| 2 | Restart Home Assistant | HA restarts |
| 3 | Check logs for real mode indicator | No simulation mode message |
| 4 | Try to configure without real IP | Config flow may require IP |

### Pass/Fail Criteria
- **Pass:** Simulation mode correctly detected based on environment
- **Fail:** Simulation mode not detected or incorrectly identified

---

## TC005.2 - State File Creation

### Objective
Verify the simulator creates state file automatically if it doesn't exist.

### Preconditions
1. `SIMULATION_MODE=1` set
2. State file does NOT exist

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Delete state file if it exists | File removed |
| 2 | Note expected location | `custom_components/kospel/data/simulation_state.yaml` |
| 3 | Configure and start integration | Integration starts |
| 4 | Wait for first data refresh | Coordinator fetches data |
| 5 | Check for state file | File created |
| 6 | Verify file is valid YAML | File parses without error |

### Pass/Fail Criteria
- **Pass:** State file created automatically in correct location
- **Fail:** State file not created or in wrong location

---

## TC005.3 - State File Persistence - Read Operations

### Objective
Verify simulator correctly reads values from state file.

### Preconditions
1. State file exists with known values

### Test Data Setup
Create `simulation_state.yaml`:
```yaml
"0b55": "0020"
"0b6a": "e600"
"0b8a": "f401"
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set known values in state file | File saved |
| 2 | Restart integration or wait for refresh | Data reloaded |
| 3 | Check heater mode (0b55 bit 5) | Shows Winter mode |
| 4 | Check room temperature (0b6a) | Shows 23.0°C |
| 5 | Check pressure (0b8a) | Shows 5.00 bar |

### Pass/Fail Criteria
- **Pass:** Simulator reads correct values from state file
- **Fail:** Values don't match state file or read fails

---

## TC005.4 - State File Persistence - Write Operations

### Objective
Verify simulator correctly writes values to state file.

### Preconditions
1. Integration configured and running
2. State file exists

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note current state file contents | Contents recorded |
| 2 | Change target temperature via UI | Temperature change initiated |
| 3 | Wait for save operation | Save completes |
| 4 | Open state file | File opens |
| 5 | Verify new value written | Register value updated |
| 6 | Close and reopen state file | No caching issues |
| 7 | Verify value persisted | Value still present |

### Pass/Fail Criteria
- **Pass:** Write operations persist to state file
- **Fail:** Values not written or not persisted

---

## TC005.5 - Manual State File Editing

### Objective
Verify manually edited state file values are reflected in Home Assistant.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note current temperature sensor value | Value recorded |
| 2 | Edit state file directly | New value set |
| 3 | Save state file | File saved |
| 4 | Wait for coordinator refresh | ~30 seconds (scan interval) |
| 5 | Check temperature sensor in HA | Shows new value |

### Test Data
Change `0b6a` from `"e600"` (23.0°C) to `"fa00"` (25.0°C)

### Pass/Fail Criteria
- **Pass:** Manual edits reflected after coordinator refresh
- **Fail:** Manual edits not reflected (known issue - see status.md)

### Notes
**Known Issue**: There may be a bug where manual YAML edits are not immediately reflected. Document behavior observed.

---

## TC005.6 - Flag Bit Operations - Single Bit

### Objective
Verify read-modify-write pattern works correctly for single bit operations.

### Test Data Setup
```yaml
"0b55": "0020"  # Winter mode, other bits clear
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set initial state | File saved |
| 2 | Turn on Manual Mode (bit 9) | Toggle switch |
| 3 | Check state file | Bit 9 set, bit 5 preserved |
| 4 | Expected value | "0220" |
| 5 | Turn on Water Heater (bit 4) | Toggle switch |
| 6 | Check state file | Bits 4, 5, 9 all set |
| 7 | Expected value | "0230" |

### Pass/Fail Criteria
- **Pass:** Single bit operations preserve other bits
- **Fail:** Other bits cleared during single bit operation

---

## TC005.7 - Batch Read Operations

### Objective
Verify simulator correctly handles batch register reads.

### Test Data Setup
Multiple registers in state file:
```yaml
"0b55": "0020"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b66": "9001"
"0b67": "a401"
"0b8a": "f401"
"0b8d": "e100"
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set multiple registers in state file | File saved |
| 2 | Trigger coordinator refresh | Data loaded |
| 3 | Verify all sensors have correct values | All values match |
| 4 | Check logs for batch read | "READ registers" message with count |

### Pass/Fail Criteria
- **Pass:** All registers read correctly in batch
- **Fail:** Some registers missing or incorrect

---

## TC005.8 - Default Values for Missing Registers

### Objective
Verify simulator returns default values for registers not in state file.

### Test Data Setup
State file with only one register:
```yaml
"0b55": "0020"
```

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set minimal state file | File saved |
| 2 | Trigger coordinator refresh | Data loaded |
| 3 | Check sensor for missing register (e.g., pressure) | Shows 0.0 |
| 4 | Verify no errors in logs | No errors for missing registers |

### Pass/Fail Criteria
- **Pass:** Missing registers return "0000" default
- **Fail:** Errors for missing registers or wrong default

---

## TC005.9 - State File Custom Location

### Objective
Verify custom state file location via environment variable.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set `SIMULATION_STATE_FILE=custom_test.yaml` | Variable set |
| 2 | Delete default state file if exists | File removed |
| 3 | Restart Home Assistant | HA restarts |
| 4 | Configure integration | Integration configured |
| 5 | Check for state file at custom location | `data/custom_test.yaml` created |

### Pass/Fail Criteria
- **Pass:** Custom state file location used
- **Fail:** Default location used instead

---

## TC005.10 - Concurrent Read/Write Operations

### Objective
Verify simulator handles concurrent operations without corruption.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set initial state | State established |
| 2 | Rapidly change multiple settings | Multiple writes initiated |
| 3 | Wait for all operations to complete | Operations complete |
| 4 | Check state file integrity | Valid YAML, all values correct |
| 5 | Check for warnings in logs | No corruption warnings |

### Pass/Fail Criteria
- **Pass:** No state corruption from concurrent operations
- **Fail:** State file corrupted or values lost

---

## TC005.11 - State File Format Validation

### Objective
Verify state file uses correct YAML format.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Perform several operations | State file updated |
| 2 | Open state file | File opens |
| 3 | Verify all keys are quoted | Keys like "0b55" properly quoted |
| 4 | Verify values are quoted | Values like "0020" properly quoted |
| 5 | Verify sorted order | Keys in alphabetical order |

### Expected Format
```yaml
"0b55": "0020"
"0b6a": "e600"
"0b8a": "f401"
```

### Pass/Fail Criteria
- **Pass:** YAML format correct with quoted strings
- **Fail:** Unquoted keys/values or incorrect format

---

## TC005.12 - Large Register Count Handling

### Objective
Verify simulator handles large batch reads efficiently.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Observe coordinator refresh timing | Time recorded |
| 2 | Check logs for register count | Shows 256 registers read |
| 3 | Verify refresh completes in reasonable time | < 5 seconds |
| 4 | Verify no timeout errors | No timeout messages |

### Pass/Fail Criteria
- **Pass:** Large batch reads complete efficiently
- **Fail:** Timeouts or excessive delays

---

## TC005.13 - State Recovery After Crash

### Objective
Verify state persists and recovers after Home Assistant restart.

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set specific state values via UI | Values set |
| 2 | Verify state file updated | File shows new values |
| 3 | Force stop Home Assistant | HA stops |
| 4 | Start Home Assistant | HA starts |
| 5 | Check state file still exists | File present |
| 6 | Check entity values in HA | Values match pre-restart state |

### Pass/Fail Criteria
- **Pass:** State persists across restarts
- **Fail:** State lost or corrupted after restart

---

## TC005.14 - Debug Logging in Simulator

### Objective
Verify simulator provides useful debug logging.

### Preconditions
1. Debug logging enabled for integration

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Enable debug logging | Logging configured |
| 2 | Perform read operation (coordinator refresh) | Read occurs |
| 3 | Check logs for `[SIMULATOR] READ` message | Message present |
| 4 | Verify register and value logged | Address and hex value shown |
| 5 | Perform write operation (change setting) | Write occurs |
| 6 | Check logs for `[SIMULATOR] WRITE` message | Message present |
| 7 | Verify old and new values logged | State change shown |

### Expected Log Format
```
[SIMULATOR] READ register 0b55: 0020 (32)
[SIMULATOR] WRITE register 0b8d: e100 → fa00 (225 → 250)
```

### Pass/Fail Criteria
- **Pass:** Debug logs provide useful information
- **Fail:** Missing or uninformative log messages

---

## Summary Checklist

| Test ID | Test Name | Priority | Result | Notes |
|---------|-----------|----------|--------|-------|
| TC005.1 | Simulation Mode Detection | Critical | | |
| TC005.2 | State File Creation | Critical | | |
| TC005.3 | State File Persistence - Read | Critical | | |
| TC005.4 | State File Persistence - Write | Critical | | |
| TC005.5 | Manual State File Editing | High | | Known issue |
| TC005.6 | Flag Bit Operations - Single Bit | High | | |
| TC005.7 | Batch Read Operations | High | | |
| TC005.8 | Default Values for Missing Registers | Medium | | |
| TC005.9 | State File Custom Location | Low | | |
| TC005.10 | Concurrent Read/Write Operations | Medium | | |
| TC005.11 | State File Format Validation | Medium | | |
| TC005.12 | Large Register Count Handling | Medium | | |
| TC005.13 | State Recovery After Crash | High | | |
| TC005.14 | Debug Logging in Simulator | Low | | |

---

## Test Data Reference

### State File Location
- Default: `<config>/custom_components/kospel/data/simulation_state.yaml`
- Custom: Controlled by `SIMULATION_STATE_FILE` environment variable

### Sample Complete State File
```yaml
"0b51": "0000"  # Status: all idle, DHW valve
"0b55": "0030"  # Winter mode, water heater enabled
"0b66": "9001"  # CWU temp economy: 40.0°C
"0b67": "a401"  # CWU temp comfort: 42.0°C
"0b68": "dc00"  # Room temp economy: 22.0°C
"0b69": "d200"  # Room temp comfort-: 21.0°C
"0b6a": "e600"  # Room temp comfort: 23.0°C
"0b6b": "f000"  # Room temp comfort+: 24.0°C
"0b8a": "f401"  # Pressure: 5.00 bar
"0b8d": "e100"  # Manual temp: 22.5°C
```

### Environment Variables
| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `SIMULATION_MODE` | Enable/disable simulation | `1`, `true`, `yes`, `on` |
| `SIMULATION_STATE_FILE` | Custom state file path | `custom_state.yaml` |
