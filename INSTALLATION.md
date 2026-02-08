# Installation Instructions

This document provides detailed instructions for installing the Kospel Electric Heaters integration in Home Assistant.

## Prerequisites

- Home Assistant version 2024.1 or later
- Python 3.14 or later (required by the integration)
- Access to your Home Assistant configuration directory

## Manual Installation

### Step 1: Locate Home Assistant Configuration Directory

The configuration directory location varies by installation type:

- **Home Assistant OS**: `/config/`
- **Home Assistant Container**: Mounted volume (usually `/config/`)
- **Home Assistant Core**: The directory where your `configuration.yaml` is located
- **Home Assistant Supervised**: `/usr/share/hassio/homeassistant/`

### Step 2: Create Integration Directory

Create the integration directory in your Home Assistant configuration:

```bash
mkdir -p <config>/custom_components/kospel
```

Replace `<config>` with your actual Home Assistant configuration directory path.

### Step 3: Copy Integration Files

Copy the integration directory from this repository to your Home Assistant configuration:

```bash
cp -r custom_components/kospel <config>/custom_components/
```

**Note**: Home Assistant automatically installs the **kospel-cmi-lib** dependency via `manifest.json` requirements when loading the integration. No manual installation of library modules is needed.

### Step 4: Verify Directory Structure

Ensure your directory structure matches the following:

```
<config>/custom_components/kospel/
├── __init__.py
├── manifest.json
├── config_flow.py
├── coordinator.py
├── const.py
├── climate.py
├── sensor.py
├── switch.py
├── strings.json
├── data/              # Created at runtime when using YAML backend
│   └── state.yaml     # State file for file-based (development) backend
└── ...
```

Heater communication (Transport, Data, Service layers) is provided by **kospel-cmi-lib**, which Home Assistant installs automatically.

## Configuration: HTTP or YAML backend

When you add the Kospel integration (Settings → Devices & Services → Add Integration → Kospel Electric Heaters), you choose how to connect:

1. **Heater (HTTP)** – Connect to a real heater. Enter the heater IP address and device ID. The URL will be `http://[IP]/api/dev/[ID]`.
2. **File-based (development)** – Use a YAML file for state (no hardware). State is stored in the integration directory at `custom_components/kospel/data/state.yaml`. This file is created automatically when the integration runs. You can edit it to simulate different heater states.

Existing config entries that used the old "simulation mode" are automatically migrated to the YAML backend.

## File Locations and Logs

### Integration Directory

The integration files are located at:
```
<config>/custom_components/kospel/
```

### YAML backend state file (development mode)

When using the **File-based (development)** backend, the state file is located at:
```
<config>/custom_components/kospel/data/state.yaml
```

This file is created automatically when the integration runs. You can view and edit it to test different scenarios without a physical heater.

### Home Assistant Logs

Log location varies by installation type:

- **Home Assistant OS**: Available via Settings > System > Logs in the UI
- **Home Assistant Container**: Usually in the container logs (check with `docker logs`)
- **Home Assistant Core**: Check the console output or log file location specified in your configuration
- **Home Assistant Supervised**: Available via Supervisor > System > Logs in the UI

### Viewing Logs in Home Assistant UI

1. Go to **Settings** > **System** > **Logs**
2. The main log shows all Home Assistant activity
3. Integration-specific logs will include messages from the `custom_components.kospel` module

### Enable Debug Logging

To enable debug logging for the integration, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.kospel: debug
    kospel_cmi: debug
```

Then restart Home Assistant to apply the logging configuration.

## Verification

### Step 1: Check Integration Appears

1. Go to **Settings** > **Devices & Services**
2. Click **Add Integration** (bottom right, if on mobile use the "+" button)
3. Search for "Kospel Electric Heaters"
4. The integration should appear in the list

If it doesn't appear, check the Home Assistant logs for errors.

### Step 2: Verify Integration Loads

1. Check the Home Assistant logs for any errors
2. Look for messages containing `kospel` or `custom_components.kospel`
3. If simulation mode is enabled, you should see a message indicating simulation mode is active

### Step 3: Check Simulator State File

If using simulation mode:

1. After configuring the integration (see next section), check that the simulator state file was created:
   ```
   <config>/custom_components/kospel/data/simulation_state.yaml
   ```
2. The file should contain register state data in YAML format

### Step 4: Configure the Integration

1. Go to **Settings** > **Devices & Services**
2. Find **Kospel Electric Heaters** in your integrations list
3. Click **Configure** or click the integration card
4. Follow the configuration flow (in simulation mode, IP and device ID are optional)

## Configuration Flow

When configuring the integration:

- **In Simulation Mode**: IP address and device ID are optional (placeholder values will be used)
- A note will indicate that simulation mode is active
- No actual connection to heater hardware will be attempted

## Troubleshooting

### Integration Doesn't Appear

- Verify the directory structure is correct
- Check that all files are in the `custom_components/kospel/` directory
- Verify `manifest.json` is present and valid
- Check Home Assistant logs for import errors

### Integration Loads but Shows Errors

- Check Home Assistant logs for detailed error messages
- Ensure Home Assistant can install kospel-cmi-lib (check network connectivity)
- Ensure Python version 3.10 or later (kospel-cmi-lib requirement)
- Check that `aiohttp>=3.13.3` is available (usually included with Home Assistant)

### Simulation Mode Not Working

- Verify `SIMULATION_MODE` environment variable is set correctly
- Check that the environment variable is set before Home Assistant starts
- Verify the simulator state file location is writable
- Check logs for simulation mode status messages

## Next Steps

After installation:

1. Configure the integration via Settings > Devices & Services
2. Verify entities appear correctly
3. Test all functionality using the simulator
4. Once fully tested, you can proceed to connect to real hardware (future iterations)

## Support

For issues or questions:

1. Check the Home Assistant logs first
2. Verify all installation steps were followed correctly
3. Ensure simulation mode is set up correctly if testing without hardware
4. Review the project README.md for additional information

