# TC001 - Integration Setup and Configuration

## Test Category: Installation & Setup
**Priority:** Critical  
**Prerequisites:** Home Assistant instance available, `SIMULATION_MODE=1` environment variable set

---

## TC001.1 - Integration Discovery

### Objective
Verify the Kospel integration appears in the Home Assistant integration list.

### Preconditions
1. Integration files copied to `custom_components/kospel/`
2. Home Assistant restarted after file copy
3. `SIMULATION_MODE=1` environment variable is set

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Devices & Services | Page loads successfully |
| 2 | Click "Add Integration" button | Integration search dialog appears |
| 3 | Type "Kospel" in search field | "Kospel Electric Heaters" appears in results |
| 4 | Observe integration icon/name | Integration displays correctly |

### Pass/Fail Criteria
- **Pass:** Integration appears in search results with correct name
- **Fail:** Integration not found or displays incorrect name

### Notes
- If integration doesn't appear, check Home Assistant logs for import errors
- Verify all files are present in `custom_components/kospel/`

---

## TC001.2 - Config Flow - Simulation Mode

### Objective
Verify the configuration flow works correctly in simulation mode.

### Preconditions
1. `SIMULATION_MODE=1` environment variable is set
2. Integration discovered (TC001.1 passed)

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click "Kospel Electric Heaters" in integration list | Config flow dialog opens |
| 2 | Observe simulation mode indicator | Note indicates simulation mode is active |
| 3 | Leave IP address field empty or use placeholder | Field accepts empty/placeholder value |
| 4 | Leave Device ID field empty or use placeholder | Field accepts empty/placeholder value |
| 5 | Click "Submit" button | Configuration completes successfully |
| 6 | Observe integration card | Integration shows as configured |

### Pass/Fail Criteria
- **Pass:** Config flow completes, integration is added
- **Fail:** Config flow fails or requires real IP/device values in simulation mode

### Test Data
- IP Address: (leave empty or use "192.168.1.1")
- Device ID: (leave empty or use "65")

---

## TC001.3 - Entity Creation Verification

### Objective
Verify all expected entities are created after integration setup.

### Preconditions
1. Integration configured (TC001.2 passed)
2. Home Assistant has completed data refresh

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Devices & Services | Page loads |
| 2 | Click on "Kospel Electric Heaters" integration | Integration detail page opens |
| 3 | Click on the device | Device page shows entities |
| 4 | Verify Climate entity exists | "Kospel Heater" climate entity present |
| 5 | Verify Temperature sensors exist | All 7 temperature sensors present |
| 6 | Verify Pressure sensor exists | Pressure sensor present |
| 7 | Verify Status sensors exist | Pump CO, Pump Circulation, Valve Position sensors present |
| 8 | Verify Switch entities exist | Manual Mode, Water Heater switches present |

### Expected Entities

#### Climate (1)
- Kospel Heater

#### Sensors (11)
| Sensor Name | Type | Unit |
|-------------|------|------|
| Room Temperature Economy | Temperature | °C |
| Room Temperature Comfort | Temperature | °C |
| Room Temperature Comfort Plus | Temperature | °C |
| Room Temperature Comfort Minus | Temperature | °C |
| CWU Temperature Economy | Temperature | °C |
| CWU Temperature Comfort | Temperature | °C |
| Manual Temperature | Temperature | °C |
| Pressure | Pressure | bar |
| Pump CO | Status | - |
| Pump Circulation | Status | - |
| Valve Position | Status | - |

#### Switches (2)
| Switch Name | Function |
|-------------|----------|
| Manual Mode | Enable/disable manual temperature control |
| Water Heater | Enable/disable water heating |

### Pass/Fail Criteria
- **Pass:** All 14 entities are present (1 climate + 11 sensors + 2 switches)
- **Fail:** Any entity is missing

---

## TC001.4 - Integration Restart Resilience

### Objective
Verify the integration survives Home Assistant restart.

### Preconditions
1. Integration configured and entities created (TC001.3 passed)
2. Access to restart Home Assistant

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Note current entity states | Record all entity values |
| 2 | Navigate to Developer Tools > YAML | YAML config page opens |
| 3 | Click "Restart Home Assistant" | Restart confirmation appears |
| 4 | Confirm restart | Home Assistant begins restart |
| 5 | Wait for Home Assistant to restart | Home Assistant becomes available |
| 6 | Navigate to Kospel integration | Integration page loads |
| 7 | Verify all entities still exist | All 14 entities present |
| 8 | Verify entity states | States match or are refreshed from simulator |

### Pass/Fail Criteria
- **Pass:** Integration and entities survive restart
- **Fail:** Integration fails to load or entities are missing after restart

---

## TC001.5 - Integration Removal

### Objective
Verify the integration can be cleanly removed.

### Preconditions
1. Integration configured (TC001.2 passed)

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to Settings > Devices & Services | Page loads |
| 2 | Click on "Kospel Electric Heaters" integration | Integration detail page opens |
| 3 | Click the three-dot menu | Menu opens |
| 4 | Click "Delete" | Confirmation dialog appears |
| 5 | Confirm deletion | Integration is removed |
| 6 | Verify integration is removed from list | Integration no longer in list |
| 7 | Search for Kospel entities in Developer Tools > States | No Kospel entities found |

### Pass/Fail Criteria
- **Pass:** Integration removed cleanly, no orphan entities
- **Fail:** Integration removal fails or leaves orphan entities

---

## TC001.6 - Logs Verification

### Objective
Verify integration logs correctly and provides useful information.

### Preconditions
1. Integration configured (TC001.2 passed)
2. Debug logging enabled for `custom_components.kospel`

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Enable debug logging (see configuration.yaml) | Debug logging enabled |
| 2 | Restart Home Assistant | Home Assistant restarts |
| 3 | Navigate to Settings > System > Logs | Log viewer opens |
| 4 | Filter/search for "kospel" | Kospel-related logs appear |
| 5 | Verify simulation mode message | Log shows simulation mode is active |
| 6 | Verify no error messages | No ERROR level messages present |
| 7 | Verify coordinator updates logged | Data refresh operations logged |

### Expected Log Messages
- `[SIMULATOR] READ register...` messages (in DEBUG mode)
- Coordinator update messages
- Simulation mode indicator

### Pass/Fail Criteria
- **Pass:** Appropriate log messages present, no unexpected errors
- **Fail:** Missing log messages or unexpected errors

### Debug Logging Configuration
Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.kospel: debug
```

---

## TC001.7 - Error Handling - Missing State File

### Objective
Verify the integration handles missing simulator state file gracefully.

### Preconditions
1. Integration NOT yet configured
2. `SIMULATION_MODE=1` environment variable is set
3. No simulator state file exists

### Test Steps

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Delete simulator state file if it exists | File removed |
| 2 | Configure integration (repeat TC001.2) | Config flow completes |
| 3 | Verify entities have default values | Entities show 0.0 or default states |
| 4 | Check logs for warnings | Warning about missing state file (acceptable) |
| 5 | Verify no crash or failure | Integration continues operating |
| 6 | Verify state file is created | `simulation_state.yaml` file created |

### Pass/Fail Criteria
- **Pass:** Integration handles missing state file gracefully
- **Fail:** Integration crashes or shows errors to user

---

## Summary Checklist

| Test ID | Test Name | Priority | Result | Notes |
|---------|-----------|----------|--------|-------|
| TC001.1 | Integration Discovery | Critical | | |
| TC001.2 | Config Flow - Simulation Mode | Critical | | |
| TC001.3 | Entity Creation Verification | Critical | | |
| TC001.4 | Integration Restart Resilience | High | | |
| TC001.5 | Integration Removal | Medium | | |
| TC001.6 | Logs Verification | Medium | | |
| TC001.7 | Error Handling - Missing State File | Medium | | |
