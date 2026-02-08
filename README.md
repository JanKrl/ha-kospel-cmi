# Kospel Heater Home Assistant Integration

Home Assistant integration for Kospel electric heaters. Uses the [kospel-cmi-lib](https://pypi.org/project/kospel-cmi-lib/) library for heater communication via their HTTP API.

## Current Status

✅ **Home Assistant Integration Verified**: The integration has been successfully tested and verified to work in Home Assistant. The integration appears correctly in the Home Assistant UI and loads without errors.

During configuration you can choose **HTTP** (real heater device) or **YAML** (file-based, for development). For YAML, state is stored in `custom_components/kospel/data/state.yaml`. The integration uses [kospel-cmi-lib 0.1.0a2](https://pypi.org/project/kospel-cmi-lib/0.1.0a2/) with its backend-based API.

## Overview

This project communicates with Kospel heaters through a REST API that exposes heater registers as hexadecimal values. The heater uses a register-based system where:
- **Registers** store 16-bit values as little-endian hex strings (e.g., `"d700"` = 215)
- **Flags** use individual bits within registers to store boolean settings
- **Values** are often scaled (temperatures ×10, pressure ×100)

The library abstracts away low-level bit operations and provides semantic APIs for working with heater settings.

## Architecture

The integration uses the external **kospel-cmi-lib** library for heater communication (Transport, Data, and Service layers) and provides the Home Assistant integration layer:

1. **Layers 1–3 (kospel-cmi-lib)**: Transport (HTTP API, simulator), Data (decoders, encoders, registers), Service (HeaterController, SETTINGS_REGISTRY)
2. **Integration Layer (this repo)**: Home Assistant entities (climate, sensor, switch), config flow, coordinator. ✅ **Verified working in Home Assistant**. See [INSTALLATION.md](INSTALLATION.md) for installation instructions.

**Note**: You can run without hardware by choosing the **YAML (file-based)** backend during setup; state is stored in the integration's `data/state.yaml`.

### Project Structure

```
home-assistant-kospel/
├── main.py                # Standalone demo (uses kospel-cmi-lib)
├── logging_config.py      # Logging configuration module
├── custom_components/     # Home Assistant integration
│   └── kospel/            # Kospel integration package
│       ├── __init__.py    # Integration entry point
│       ├── manifest.json  # Integration metadata
│       ├── config_flow.py # Configuration UI
│       ├── coordinator.py # Data update coordinator
│       ├── climate.py     # Climate entity
│       ├── sensor.py      # Sensor entities
│       ├── switch.py      # Switch entities
│       ├── const.py       # Constants
│       └── strings.json   # UI strings
├── scripts/               # Utility scripts
│   └── check_registers.py # Register discovery (uses kospel-cmi-lib)
├── docs/                  # Documentation
│   ├── architecture.mermaid
│   ├── technical.md
│   └── status.md
├── README.md              # This file
└── INSTALLATION.md        # Home Assistant installation instructions
```

Heater communication (Transport, Data, Service layers) is provided by **kospel-cmi-lib** (installed via `manifest.json` requirements).

### System Architecture

```
┌─────────────────┐
│  main.py        │  ← Application entry point
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HeaterController│  ← Service Layer (controller/api.py)
│                 │
│  - refresh()     │
│  - save()        │
│  - Dynamic props │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  kospel/api.py  │  ← Transport Layer
│                 │
│  - read_register │
│  - write_register│
│  - Mock support  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ registers/      │  ← Data Layer
│                 │
│  - decoders.py  │  (decode functions)
│  - encoders.py  │  (encode functions)
│  - registry.py  │  (SETTINGS_REGISTRY)
│  - utils.py     │  (encoding/decoding)
│  - enums.py     │  (HeaterMode, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Heater HTTP API│  ← External system
│                 │
│  GET /api/dev/  │
│  POST /api/dev/ │
└─────────────────┘
```

### Key Components

The Transport, Data, and Service layers are provided by **kospel-cmi-lib**. Import from `kospel_cmi`:

- **`kospel_cmi.controller.api.HeaterController`** - High-level API: `HeaterController(backend=...)`, `refresh()`, `save()`, `from_registers()`, dynamic properties for all settings
- **`kospel_cmi.kospel.backend`** - `HttpRegisterBackend(session, api_base_url)`, `YamlRegisterBackend(state_file=...)` for transport
- **`kospel_cmi.controller.registry.SETTINGS_REGISTRY`** - Maps setting names to register locations and decode/encode logic
- **`kospel_cmi.kospel.api`** - `read_register`, `read_registers`, `write_register`, `write_flag_bit`
- **`kospel_cmi.registers.enums`** - `HeaterMode`, `ManualMode`, `WaterHeaterEnabled`, `PumpStatus`, `ValvePosition`

## Heater API Protocol

### Register System

The heater exposes registers as hexadecimal strings in **little-endian format**:

- **Register Format**: 4-character hex string (e.g., `"d700"`)
- **Byte Order**: Little-endian (bytes swapped)
  - `"d700"` means: bytes are `[0xd7, 0x00]` in memory
  - When read as big-endian: `0x00d7` = 215
- **Value Type**: Signed 16-bit integers (-32768 to 32767)

### Flag Registers

Some registers use individual bits as flags:

**Register 0b55** (Flags):
- Bit 3: Summer mode
- Bit 4: Water heater enabled
- Bit 5: Winter mode
- Bit 9: Manual mode enabled

**Register 0b51** (Component Status):
- Bit 0: Pump CO running
- Bit 1: Pump circulation running
- Bit 2: Valve position (0=CO, 1=DHW)

**Heater Mode Logic** (register 0b55, bits 3 & 5):
- Summer: Bit 3=1, Bit 5=0
- Winter: Bit 3=0, Bit 5=1
- Off: Bit 3=0, Bit 5=0

### API Endpoints

**Base URL**: `http://<HEATER_IP>/api/dev/<DEVICE_ID>`

**Read Register**:
- `GET /api/dev/<DEVICE_ID>/<register>/<count>`
- Example: `GET /api/dev/65/0b55/1`
- Response: `{"regs": {"0b55": "d700"}, "sn": "...", "time": "..."}`

**Write Register**:
- `POST /api/dev/<DEVICE_ID>/<register>`
- Body: Hex string (e.g., `"d700"`)
- Response: `{"status": "0"}` on success

**Read Multiple Registers**:
- `GET /api/dev/<DEVICE_ID>/0b00/256` (reads 256 registers starting from 0b00)
- Response: `{"regs": {"0b00": "...", "0b01": "...", ...}}`

### Example Register Values

| Register | Description | Format | Example |
|----------|-------------|--------|---------|
| `0b31` | Room temperature setting | Temp (×10) | `"00e1"` = 22.5°C |
| `0b4b` | Room current temperature | Temp (×10) | `"00e6"` = 23.0°C |
| `0b2f` | Water temperature setting | Temp (×10) | `"01a4"` = 42.0°C |
| `0b4e` | Pressure | Pressure (×100) | `"01f4"` = 5.00 bar |
| `0b51` | Component status flags | Flags | `"0005"` (bits 0,2 set) |
| `0b55` | System flags | Flags | `"02a0"` (bits 5,7,9 set) |
| `0b8a` | Heater mode priority | Integer | `"0000"` = CO Priority |
| `0b8d` | Manual temperature | Temp (×10) | `"00e1"` = 22.5°C |

## Usage Examples

### Basic Usage

```python
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

from kospel_cmi.controller.api import HeaterController
from kospel_cmi.registers.enums import HeaterMode
from logging_config import setup_logging

async def main():
    load_dotenv()
    setup_logging()
    
    heater_ip = os.getenv("HEATER_IP")
    device_id = os.getenv("DEVICE_ID")
    api_base_url = f"http://{heater_ip}/api/dev/{device_id}"

    async with aiohttp.ClientSession() as session:
        heater = HeaterController(session, api_base_url)
        await heater.refresh()
        
        print(f"Heater Mode: {heater.heater_mode}")
        print(f"Manual Mode: {heater.is_manual_mode_enabled}")
        print(f"Water Heater: {heater.is_water_heater_enabled}")
        heater.print_settings()

asyncio.run(main())
```

### Setting Heater Mode

```python
import asyncio
import aiohttp
from kospel_cmi.controller.api import HeaterController
from kospel_cmi.registers.enums import HeaterMode, ManualMode

async def main():
    async with aiohttp.ClientSession() as session:
        heater = HeaterController(session, "http://192.168.1.1/api/dev/65")
        await heater.refresh()
        
        # Modify settings
        heater.heater_mode = HeaterMode.WINTER
        heater.manual_temperature = 22.0
        heater.is_manual_mode_enabled = ManualMode.ENABLED
        
        # Write all changes at once
        success = await heater.save()
        print(f"Settings saved: {success}")

asyncio.run(main())
```

### Using from_registers for Efficiency

```python
import asyncio
import aiohttp
from kospel_cmi.controller.api import HeaterController
from kospel_cmi.kospel.api import read_registers

async def main():
    async with aiohttp.ClientSession() as session:
        api_base_url = "http://192.168.1.1/api/dev/65"
        
        # Fetch register data once
        all_registers = await read_registers(session, api_base_url, "0b00", 256)
        
        # Parse settings from fetched data (no additional API calls)
        heater = HeaterController(session, api_base_url)
        heater.from_registers(all_registers)
        
        print(f"Mode: {heater.heater_mode}")
        print(f"Manual mode: {heater.is_manual_mode_enabled}")

asyncio.run(main())
```

### Simulator Mode

The library supports simulator mode for development without a physical heater:

```bash
# Enable simulator mode
export SIMULATION_MODE=1
export SIMULATION_STATE_FILE=simulation_state.yaml

# Run your application
python main.py
```

Simulator mode:
- Routes all API calls to kospel-cmi-lib simulator implementations
- Maintains register state in memory
- Persists state to a YAML file (default: `data/heater_mock_state.yaml`)
- Allows testing without network connectivity

## Configuration

### Heater Connection

Configure the heater connection using environment variables:

```bash
export HEATER_IP="192.168.101.49:80"
export DEVICE_ID="65"
```

Or use a `.env` file:

```env
HEATER_IP=192.168.101.49:80
DEVICE_ID=65
```

The `api_base_url` is constructed as: `http://{HEATER_IP}/api/dev/{DEVICE_ID}`

### Logging

The library uses Python's standard `logging` module for uniform logging throughout the project. Logging is configured via `logging_config.py` and supports both console and file output with independent log levels.

#### Initialization

Initialize logging at the start of your application:

```python
from logging_config import setup_logging

# Initialize logging (should be called once at startup)
setup_logging()
```

#### Environment Variables

Configure logging behavior using environment variables:

- **`LOG_LEVEL_CONSOLE`**: Log level for console output (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **`LOG_LEVEL_FILE`**: Log level for file output (default: `DEBUG`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **`LOG_FILE`**: Path to log file (default: `logs/hass-jupyter.log`)
- **`LOG_FORMAT`**: Optional custom log format string (default: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`)

#### Example Configuration

```bash
# Set console to INFO level, file to DEBUG level
export LOG_LEVEL_CONSOLE=INFO
export LOG_LEVEL_FILE=DEBUG
export LOG_FILE=logs/heater.log

# Run your application
python main.py
```

#### Log Levels

- **`DEBUG`**: Detailed diagnostic information (register values, mock operations, parsing details)
- **`INFO`**: General informational messages (mode changes, successful operations, refresh/save completion)
- **`WARNING`**: Warning messages (file I/O issues, missing registers, non-critical errors)
- **`ERROR`**: Error messages (API failures, parsing errors, write failures)
- **`CRITICAL`**: Critical errors (should not occur in normal operation)

#### Log Files

Log files are automatically rotated when they reach 10MB, keeping up to 5 backup files. The `logs/` directory is created automatically if it doesn't exist.

#### Using Loggers in Your Code

Get a logger for your module:

```python
from logging_config import get_logger

logger = get_logger("your_module_name")

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

## SETTINGS_REGISTRY

The `SETTINGS_REGISTRY` is provided by **kospel-cmi-lib** (`kospel_cmi.controller.registry`). It maps semantic setting names to their register locations and parsing logic. It serves as the single source of truth for how settings are stored in heater registers.

### Purpose

- **Centralized Configuration**: All register-to-setting mappings are defined in one place
- **Reusable Parsing**: Settings can be parsed from already-fetched register data without additional API calls
- **Type Safety**: Associates each setting with its proper decode/encode functions and data type
- **Dynamic Properties**: `HeaterController` automatically exposes all registry settings as properties

### Structure

Each entry in `SETTINGS_REGISTRY` maps a semantic name to a `SettingDefinition`:

```python
"setting_name": SettingDefinition(
    register="0b55",              # Register address (e.g., "0b55", "0b51")
    bit_index=3,                  # Optional: bit index for flag bits
    decode_function=decode_function, # Function to decode value from hex string
    encode_function=encode_function, # Optional: function to encode value to hex string
    is_read_only=False            # Derived property (True if encode_function is None)
)
```

### SettingDefinition Fields

- **`register`** (str): The register address where the setting is stored (e.g., `"0b55"`)
- **`bit_index`** (int, optional): For flag-based settings, the bit index within the register. Omitted for full-register values (like temperatures)
- **`decode_function`** (Decoder): Function that takes `(hex_val: str, bit_index: Optional[int])` and returns the decoded value
- **`encode_function`** (Encoder, optional): Function that takes `(value, register, bit_index, current_hex)` and returns hex string. None for read-only settings
- **`is_read_only`** (bool): Derived property (True if encode_function is None)

### Example Registry Entries

**Flag-based setting** (single bit):
```python
"is_manual_mode_enabled": SettingDefinition(
    register="0b55",
    bit_index=9,
    decode_function=decode_map(
        true_value=ManualMode.ENABLED,
        false_value=ManualMode.DISABLED,
    ),
    encode_function=encode_map(
        true_value=ManualMode.ENABLED,
        false_value=ManualMode.DISABLED,
    ),
)
```

**Full register value** (temperature):
```python
"manual_temperature": SettingDefinition(
    register="0b8d",
    decode_function=decode_scaled_temp,
    encode_function=encode_scaled_temp
)
```

**Multi-bit setting** (heater mode):
```python
"heater_mode": SettingDefinition(
    register="0b55",
    decode_function=decode_heater_mode,
    encode_function=encode_heater_mode
)
```

**Read-only status** (pump running):
```python
"is_pump_co_running": SettingDefinition(
    register="0b51",
    bit_index=0,
    decode_function=decode_map(
        true_value=PumpStatus.RUNNING,
        false_value=PumpStatus.IDLE,
    ),
    # Read-only: no encode_function
)
```

### Usage

The registry is used internally by:

1. **`HeaterController.from_registers()`**: Decodes settings from already-fetched register data
2. **`HeaterController.save()`**: Encodes settings to register values before writing
3. **`HeaterController.__getattr__()`**: Provides dynamic property access to all registry settings
4. **`HeaterController.__setattr__()`**: Validates and stores pending writes for registry settings

### Current Registry Contents

The registry currently includes:
- **Mode settings**: `heater_mode`, `is_manual_mode_enabled`, `is_water_heater_enabled`
- **Status (read-only)**: `is_pump_co_running`, `is_pump_circulation_running`, `valve_position`, `pressure`
- **Temperature settings**: `manual_temperature`, `room_temperature_*`, `cwu_temperature_*`

See `controller/registry.py` for the complete list.

## Development Guidelines

### Adding New Settings

1. **Add to `SETTINGS_REGISTRY`** in `controller/registry.py`:
   ```python
   "new_setting": SettingDefinition(
       register="0bXX",
       bit_index=Y,  # If it's a flag bit (omit for full register values)
       decode_function=decode_new_setting_from_reg,
       encode_function=encode_new_setting_to_reg  # Omit for read-only
   )
   ```

2. **Create decode function** in kospel-cmi-lib's `registers/decoders.py` (if needed):
   ```python
   def decode_new_setting_from_reg(reg_hex: str, bit_index: Optional[int] = None) -> Optional[Type]:
       """Decode the setting value from a register hex string."""
       # For flag bits, use decode_bit_boolean or decode_map
       # For full register values, use decode_scaled_temp, decode_scaled_pressure, etc.
   ```

3. **Create encode function** in `registers/encoders.py` (if writable):
   ```python
   def encode_new_setting_to_reg(value: Type, register: str, bit_index: Optional[int], current_hex: Optional[str]) -> Optional[str]:
       """Encode the setting value to a register hex string."""
       # Use read-modify-write pattern for flag bits
       # Use int_to_reg for full register values
   ```

4. **Add enum** in kospel-cmi-lib's `registers/enums.py` (if needed):
   ```python
   class NewSetting(Enum):
       VALUE1 = "Value 1"
       VALUE2 = "Value 2"
   ```

**Note**: Once added to `SETTINGS_REGISTRY`, the setting will automatically be available as a dynamic property on `HeaterController`!

### Best Practices

- **Use high-level API**: Prefer `HeaterController` class over direct register manipulation
- **Batch operations**: Use `HeaterController` class when modifying multiple settings
- **Avoid redundant calls**: Use `from_registers()` when you already have register data
- **Error handling**: Check return values and handle `None` results appropriately
- **Simulator mode**: Use simulator mode for development and testing

## Common Register Mappings

### Temperature Registers (scaled ×10)
- `0b31`: Room temperature setting
- `0b4b`: Room current temperature
- `0b2f`: Water temperature setting
- `0b4a`: Water current temperature
- `0b4c`: Outside temperature
- `0b48`: Inlet temperature
- `0b49`: Outlet temperature
- `0b44`: Factor
- `0b8d`: Manual temperature
- `0b68`: Room temperature economy
- `0b69`: Room temperature comfort minus
- `0b6a`: Room temperature comfort
- `0b6b`: Room temperature comfort plus
- `0b66`: CWU temperature economy
- `0b67`: CWU temperature comfort

### Pressure/Flow Registers
- `0b4e`: Pressure (scaled ×100)
- `0b4f`: Flow rate (l/min, scaled ×10)
- `0b8a`: Pressure (scaled ×100)

### Flag Registers
- `0b51`: Component status (pumps, valve)
- `0b55`: System flags (modes, manual mode, water heater)

### Mode Registers
- `0b8a`: Heater mode priority (0=CO, 1=Heat Source, 2=Buffer)
- `0b55`: Heater mode (bits 3,5 for summer/winter/off)

## Testing

This project includes integration tests that verify the Home Assistant integration works with kospel-cmi-lib. Unit tests for the library layers are in the kospel-cmi-lib repository.

### Running Tests

**Install test dependencies:**
```bash
uv sync --all-groups
```

Or to sync only the dev group:
```bash
uv sync --extra dev
```

**Note:** After syncing, run tests with `uv run python -m pytest tests/`.

**Run all tests:**
```bash
uv run python -m pytest tests/
```

**Run tests with verbose output:**
```bash
uv run python -m pytest tests/ -v
```

**Run specific test modules:**
```bash
uv run pytest tests/registers/          # Data layer tests
uv run pytest tests/kospel/             # Transport layer tests
uv run pytest tests/controller/         # Service layer tests
uv run pytest tests/integration/        # Integration tests
```

**Run tests matching a pattern:**
```bash
uv run pytest -k "test_decode"          # Run all decode-related tests
uv run pytest -k "test_heater_controller"  # Run HeaterController tests
```

**Run tests with coverage:**
```bash
uv run python -m pytest tests/ --cov=custom_components.kospel --cov-report=html --cov-report=term
```

**View HTML coverage report:**
```bash
# After running coverage, open htmlcov/index.html in your browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures (uses kospel_cmi)
└── integration/                   # Integration tests
    ├── test_api_communication.py # End-to-end API tests (HeaterController)
    └── test_mock_mode.py         # Simulator mode integration tests
```

Tests for Transport, Data, and Service layers are in the **kospel-cmi-lib** repository.

### Test Coverage

Coverage reports are generated using `pytest-cov` and include:

- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test cross-layer functionality and end-to-end workflows
- **Simulator Mode Tests**: Verify simulator implementation consistency with real API

### Writing Tests

When adding new features, follow these testing principles:

1. **TDD Approach**: Write tests before or alongside implementation
2. **Comprehensive Coverage**: Test happy paths, edge cases, and error conditions
3. **Layer Separation**: Tests respect layer boundaries
4. **Type Safety**: Test with proper types and type validation
5. **Error Handling**: Test all error paths and exception handling
6. **Async Testing**: Use `pytest-asyncio` for async function tests

### Test Fixtures

The `tests/conftest.py` file provides shared fixtures:

- `api_base_url` - Standard API base URL
- `mock_session` - Mock aiohttp session
- `sample_registers` - Sample register data for testing
- `heater_controller` - HeaterController instance
- `heater_controller_with_registers` - Pre-loaded controller instance
- `enable_mock_mode` / `disable_mock_mode` - Simulator mode fixtures

### Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install uv
  uses: astral-sh/setup-uv@v3
  
- name: Run tests
  run: |
    uv sync --all-groups
    uv run python -m pytest tests/ --cov=custom_components.kospel --cov-report=xml --cov-report=term
```

## Troubleshooting

### Common Issues

**Negative register values**: Normal for flags registers. The value `-32080` for register `0b55` means bits 8-15 are set, which is expected when multiple flags are enabled.

**Setting changes not taking effect**: Some settings may require additional flags to be set. Check the heater documentation or JS source for dependencies.

**API timeouts**: Ensure the heater IP is correct and reachable. Default timeout is 5 seconds (configurable in code).

**Import errors**: Make sure you're importing from the correct modules:
- `HeaterController` from `controller.api`
- `HeaterMode`, `ManualMode`, etc. from `registers.enums`
- API functions from `kospel.api`

**Simulator mode not working**: Ensure `SIMULATION_MODE` environment variable is set to `1`, `true`, `yes`, or `on`.

**Test failures**: 
- Ensure all test dependencies are installed: `uv sync --group dev`
- Check that test fixtures are properly configured
- Verify environment variables are not interfering with tests

## References

This library was reverse-engineered from JavaScript code used in the heater's web interface. Key findings:

- Register encoding uses little-endian byte order
- Flag bits are used for boolean settings within registers
- Temperature and pressure values are scaled for precision
- Read-Modify-Write pattern is required for setting flag bits

## Installation (HACS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=JanKrl&repository=ha-kospel-cmi&category=integration)

If your Home Assistant instance is [linked to My Home Assistant](https://my.home-assistant.io/), click the badge above to open this repository in HACS and install from there. Otherwise add the repo manually:

1. In HACS go to **Integrations** → **⋮** → **Custom repositories**.
2. Add repository URL: `https://github.com/JanKrl/ha-kospel-cmi`
3. Select category **Integration** and click **Add**.
4. Search for **Kospel Electric Heaters**, install, then restart Home Assistant.
5. Add the integration via **Settings** → **Devices & services** → **Add integration** → **Kospel Electric Heaters**.

See [INSTALLATION.md](INSTALLATION.md) for manual installation and configuration details.

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for the full text.
