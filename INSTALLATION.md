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

Copy all integration files from this repository to the integration directory:

```bash
# Copy entire integration directory (includes library modules)
cp -r custom_components/kospel <config>/custom_components/
```

Alternatively, you can copy files individually:

```bash
# Copy integration core files
cp custom_components/kospel/*.py <config>/custom_components/kospel/
cp custom_components/kospel/*.json <config>/custom_components/kospel/

# Copy library modules (kospel/, controller/, registers/)
cp -r custom_components/kospel/kospel <config>/custom_components/kospel/
cp -r custom_components/kospel/controller <config>/custom_components/kospel/
cp -r custom_components/kospel/registers <config>/custom_components/kospel/
```

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
├── logging_config.py # Simplified logging for HA context
├── kospel/           # Transport layer
│   ├── __init__.py
│   ├── api.py
│   └── simulator.py
├── controller/       # Service layer
│   ├── __init__.py
│   ├── api.py
│   └── registry.py
└── registers/        # Data layer
    ├── __init__.py
    ├── decoders.py
    ├── encoders.py
    ├── enums.py
    └── utils.py
```

## Environment Variable Setup (Simulation Mode)

**Important**: The first iteration of this integration uses **simulation mode only**. No actual heater hardware will be accessed. The integration has been verified to work correctly in Home Assistant.

### Setting Simulation Mode

The integration uses the `SIMULATION_MODE` environment variable to enable simulation mode. The exact method depends on your Home Assistant installation type:

#### Home Assistant OS / Supervised

Add to your `configuration.yaml`:

```yaml
system_health:
```

Then set the environment variable in the Home Assistant container/host system environment.

Alternatively, set it in the Home Assistant environment before starting:
- **Docker**: Use `-e SIMULATION_MODE=1` flag
- **Systemd**: Add to service file: `Environment=SIMULATION_MODE=1`
- **Shell**: `export SIMULATION_MODE=1` before starting Home Assistant

#### Home Assistant Core

Set as environment variable before starting Home Assistant:

```bash
export SIMULATION_MODE=1
```

Then start Home Assistant normally.

### Simulation State File

The simulator uses a YAML file to persist state. The default location is:

```
<config>/custom_components/kospel/data/simulation_state.yaml
```

This file is created automatically when the integration runs for the first time. The simulator will maintain heater state in this file, allowing you to test the integration without physical hardware.

You can manually edit this file to simulate different heater states for testing purposes.

## File Locations and Logs

### Integration Directory

The integration files are located at:
```
<config>/custom_components/kospel/
```

### Simulator State File

The simulator state file is located at:
```
<config>/custom_components/kospel/data/simulation_state.yaml
```

This file is created automatically when the integration runs. You can view and edit it to test different scenarios.

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
    kospel: debug
    controller: debug
    registers: debug
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
- Verify all library modules (kospel/, controller/, registers/) are copied correctly
- Ensure Python version is 3.14 or later
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

