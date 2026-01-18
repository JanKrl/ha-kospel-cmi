# Environment Setup Procedure

## Purpose
This document provides step-by-step instructions for setting up the test environment for manual testing of the Kospel Home Assistant integration.

---

## Prerequisites

### Hardware Requirements
- Computer with Home Assistant access
- Web browser for Home Assistant UI

### Software Requirements
- Home Assistant 2024.1 or later
- Python 3.14 or later (included with HA)
- Text editor for YAML file editing

### Access Requirements
- Admin access to Home Assistant
- Access to Home Assistant configuration directory
- Ability to set environment variables

---

## Step 1: Install Home Assistant (if needed)

If you don't have Home Assistant installed, follow the official installation guide:
https://www.home-assistant.io/installation/

For testing purposes, we recommend:
- **Home Assistant Container (Docker)** - Most flexible for testing
- **Home Assistant OS** - Easiest setup

---

## Step 2: Locate Configuration Directory

Find your Home Assistant configuration directory:

| Installation Type | Location |
|-------------------|----------|
| Home Assistant OS | `/config/` |
| Home Assistant Container | Mounted volume (typically `/config/`) |
| Home Assistant Core | Directory containing `configuration.yaml` |
| Home Assistant Supervised | `/usr/share/hassio/homeassistant/` |

---

## Step 3: Copy Integration Files

### Option A: Full Directory Copy (Recommended)

```bash
# From the project root directory
cp -r custom_components/kospel <HA_CONFIG>/custom_components/
```

### Option B: Manual File Copy

Ensure you copy all necessary files:

```
custom_components/kospel/
├── __init__.py
├── manifest.json
├── config_flow.py
├── coordinator.py
├── const.py
├── climate.py
├── sensor.py
├── switch.py
├── strings.json
├── logging_config.py
├── kospel/
│   ├── __init__.py
│   ├── api.py
│   └── simulator.py
├── controller/
│   ├── __init__.py
│   ├── api.py
│   └── registry.py
└── registers/
    ├── __init__.py
    ├── decoders.py
    ├── encoders.py
    ├── enums.py
    └── utils.py
```

---

## Step 4: Set Environment Variables

### For Docker/Container Installation

Add to docker-compose.yml:
```yaml
environment:
  - SIMULATION_MODE=1
```

Or use docker run:
```bash
docker run ... -e SIMULATION_MODE=1 ...
```

### For Home Assistant OS

Set in container environment before starting.

### For Home Assistant Core

```bash
export SIMULATION_MODE=1
# Then start Home Assistant
```

### For Systemd Service

Add to service file:
```ini
[Service]
Environment=SIMULATION_MODE=1
```

---

## Step 5: Configure Debug Logging (Optional but Recommended)

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.kospel: debug
    custom_components.kospel.kospel: debug
    custom_components.kospel.controller: debug
    custom_components.kospel.coordinator: debug
```

---

## Step 6: Create Initial Simulator State (Optional)

Create the data directory and initial state file:

```bash
mkdir -p <HA_CONFIG>/custom_components/kospel/data
```

Create `simulation_state.yaml` with test data:

```yaml
"0b51": "0000"
"0b55": "0030"
"0b66": "9001"
"0b67": "a401"
"0b68": "dc00"
"0b69": "d200"
"0b6a": "e600"
"0b6b": "f000"
"0b8a": "f401"
"0b8d": "e100"
```

---

## Step 7: Restart Home Assistant

Restart Home Assistant to apply changes:

### Via UI
1. Settings > System > Restart
2. Confirm restart

### Via Command Line
```bash
# Docker
docker restart homeassistant

# Systemd
sudo systemctl restart home-assistant@homeassistant.service

# Core
# Stop and start your HA process
```

---

## Step 8: Verify Installation

### Check Integration Appears
1. Navigate to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "Kospel Electric Heaters"
4. Integration should appear in search results

### Check Logs for Errors
1. Navigate to Settings > System > Logs
2. Search for "kospel"
3. Verify no ERROR level messages

---

## Step 9: Configure Integration

1. Click "Add Integration"
2. Search and select "Kospel Electric Heaters"
3. In simulation mode, IP and device ID are optional
4. Complete configuration
5. Verify integration appears in integrations list

---

## Step 10: Verify Entities Created

1. Click on the Kospel integration
2. Verify device appears
3. Click on device
4. Verify all entities are listed:
   - 1 Climate entity
   - 7 Temperature sensors
   - 1 Pressure sensor
   - 3 Status sensors
   - 2 Switches

---

## Environment Checklist

Use this checklist to verify environment is ready:

| Item | Status | Notes |
|------|--------|-------|
| Home Assistant installed and accessible | ☐ | |
| Integration files copied to correct location | ☐ | |
| `SIMULATION_MODE=1` environment variable set | ☐ | |
| Debug logging configured (optional) | ☐ | |
| Home Assistant restarted | ☐ | |
| Integration appears in "Add Integration" | ☐ | |
| Integration configured successfully | ☐ | |
| All entities created | ☐ | |
| No errors in logs | ☐ | |
| Simulator state file created | ☐ | |

---

## Troubleshooting

### Integration Not Found

1. Verify files are in correct location
2. Check `manifest.json` exists and is valid
3. Check logs for import errors
4. Restart Home Assistant

### Import Errors in Logs

1. Verify all subdirectories have `__init__.py`
2. Verify all library modules copied (kospel/, controller/, registers/)
3. Check for Python version compatibility

### Simulation Mode Not Active

1. Verify environment variable is set correctly
2. Check variable is visible to Home Assistant process
3. Restart Home Assistant after setting variable

### State File Not Created

1. Check data directory exists with write permissions
2. Verify path: `custom_components/kospel/data/`
3. Check logs for file I/O errors

---

## Reset Environment

To reset the test environment:

1. Remove integration from Home Assistant
2. Delete state file: `rm custom_components/kospel/data/simulation_state.yaml`
3. Restart Home Assistant
4. Re-configure integration

---

## Contact

For issues with environment setup, refer to:
- INSTALLATION.md
- Project README.md
- Home Assistant documentation
