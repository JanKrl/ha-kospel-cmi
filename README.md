# Kospel Heater Control Library

Python library for interacting with Kospel heaters via their HTTP API. Provides high-level abstractions for reading and writing heater settings without direct bit manipulation.

## Current Status

✅ **Home Assistant Integration Verified**: The integration has been successfully tested and verified to work in Home Assistant. The integration appears correctly in the Home Assistant UI and loads without errors.

The integration currently operates in **simulation mode** for safe testing without physical hardware. All layers (Transport, Data, Service, and Integration) are complete and functional.

## Overview

This project communicates with Kospel heaters through a REST API that exposes heater registers as hexadecimal values. The heater uses a register-based system where:
- **Registers** store 16-bit values as little-endian hex strings (e.g., `"d700"` = 215)
- **Flags** use individual bits within registers to store boolean settings
- **Values** are often scaled (temperatures ×10, pressure ×100)

The library abstracts away low-level bit operations and provides semantic APIs for working with heater settings.

## Architecture

The project follows a 4-layer architecture:

1. **Transport Layer (Client)**: `kospel/api.py` - Handles raw async I/O with the Kospel API, manages connection, retries, and error handling. Supports simulator mode for development.
2. **Data Layer (Parser)**: `registers/` - Interprets raw data into Python dataclasses/Pydantic models. Contains decoders, encoders, and utilities.
3. **Service Layer (Controller)**: `controller/api.py` - Abstracts complex logic, provides high-level methods like `set_heating_curve(curve_id)`.
4. **Integration Layer (Home Assistant)**: Home Assistant integration - Wraps the Service Layer into Home Assistant entities. ✅ **Verified working in Home Assistant**. See [INSTALLATION.md](INSTALLATION.md) for installation instructions.

**Note**: The first iteration uses **simulation mode only** - no actual heater hardware is accessed. The integration has been verified to work correctly in Home Assistant.

### Project Structure

```
hass-jupyter/
├── main.py                # Main application entry point (uses custom_components/kospel modules)
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
│       ├── strings.json   # UI strings
│       ├── logging_config.py  # Simplified logging for HA context
│       ├── kospel/        # Transport layer
│       │   ├── __init__.py
│       │   ├── api.py     # HTTP API calls with simulator support
│       │   └── simulator.py  # Simulator implementations
│       ├── controller/    # Service layer
│       │   ├── __init__.py
│       │   ├── api.py     # HeaterController class
│       │   └── registry.py  # SETTINGS_REGISTRY and SettingDefinition
│       └── registers/     # Data layer
│           ├── __init__.py
│           ├── decoders.py  # Decode functions (hex → Python values)
│           ├── encoders.py  # Encode functions (Python values → hex)
│           ├── utils.py     # Low-level utilities (register encoding/decoding)
│           └── enums.py     # Enums (HeaterMode, ManualMode, WaterHeaterEnabled, ValvePosition, PumpStatus)
├── data/                  # Mock state data
│   └── heater_mock_state.yaml
├── scripts/               # Utility scripts
│   └── check_registers.py
├── docs/                  # Documentation
│   ├── architecture.mermaid
│   └── status.md
├── README.md              # This file
└── INSTALLATION.md        # Home Assistant installation instructions
```

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

#### 1. `registers/utils.py` - Low-Level Utilities

Low-level functions for encoding/decoding heater register formats:

- **`reg_to_int(hex_val: str) -> int`**: Converts little-endian hex string to signed 16-bit integer
  - Example: `"d700"` → 215 (bytes swapped: `"00d7"` → 0x00d7 → 215)
- **`int_to_reg(value: int) -> str`**: Converts signed 16-bit integer to little-endian hex string
  - Example: 215 → `"d700"` (reverse of above)
- **`get_bit(value: int, bit_index: int) -> bool`**: Checks if bit is set (low-level utility)
- **`set_bit(value: int, bit_index: int, state: bool) -> int`**: Sets/clears bit (low-level utility)
- **`reg_address_to_int(address: str) -> int`**: Converts register address string to integer for sorting

#### 2. `custom_components/kospel/registers/decoders.py` - Decode Functions

Functions that convert hex register values to Python types:

- **`decode_scaled_temp(hex_val: str, bit_index: Optional[int]) -> float`**: Decodes temperature (scaled by 10)
  - Example: `"00e1"` (225) → 22.5°C
- **`decode_scaled_pressure(hex_val: str) -> float`**: Decodes pressure (scaled by 100)
  - Example: `"01f4"` (500) → 5.00 bar
- **`decode_heater_mode(hex_val: str, bit_index: Optional[int]) -> HeaterMode`**: Decodes heater mode from bits 3 and 5
- **`decode_map(true_value, false_value)`**: Factory function that creates a decoder mapping a boolean bit to enum values
- **`decode_bit_boolean(hex_val: str, bit_index: Optional[int]) -> bool`**: Decodes a single bit as boolean

#### 3. `custom_components/kospel/registers/encoders.py` - Encode Functions

Functions that convert Python values to hex register strings:

- **`encode_scaled_temp(value: float, register: str, bit_index: Optional[int], current_hex: Optional[str]) -> str`**: Encodes temperature (scaled by 10)
- **`encode_scaled_pressure(value: float, register: str, bit_index: Optional[int], current_hex: Optional[str]) -> str`**: Encodes pressure (scaled by 100)
- **`encode_heater_mode(value: HeaterMode, bit_index: Optional[int], current_hex: Optional[str]) -> str`**: Encodes heater mode to bits 3 and 5
- **`encode_map(true_value, false_value)`**: Factory function that creates an encoder mapping enum values to boolean bits

#### 4. `custom_components/kospel/controller/api.py` - High-Level API

Main module providing a high-level API for reading and writing heater settings:

**Class: `HeaterController`**
- Constructor: `HeaterController(session, api_base_url, registry=SETTINGS_REGISTRY)`
- Loads settings into a cached object
- Modify multiple settings, then write all at once with `save()`
- Two initialization methods:
  - `refresh()`: Loads from heater via API calls (complete implementation)
  - `from_registers(registers)`: Loads from already-fetched register data (more efficient)

**Dynamic Properties:**
- All settings from `SETTINGS_REGISTRY` are accessible as dynamic properties
- Writable settings: `heater_mode`, `is_manual_mode_enabled`, `is_water_heater_enabled`, `manual_temperature`, etc.
- Read-only settings: `valve_position`, `is_pump_co_running`, `is_pump_circulation_running`, `pressure`, etc.

**Methods:**
- `refresh()`: Load all settings from the heater (makes a single API call)
- `from_registers(registers)`: Load from already-fetched register data
- `save()`: Write all pending changes to the heater
- `get_setting(name)`: Explicit getter for a setting
- `set_setting(name, value)`: Explicit setter for a setting
- `get_all_settings()`: Get all current settings
- `print_settings()`: Display current settings

#### 5. `custom_components/kospel/controller/registry.py` - Settings Registry

The `SETTINGS_REGISTRY` is a central registry that maps semantic setting names to their register locations and parsing logic. It serves as the single source of truth for how settings are stored in heater registers.

**SettingDefinition:**
- `register`: Register address (e.g., `"0b55"`)
- `decode_function`: Function to decode value from hex string
- `encode_function`: Optional function to encode value to hex string (None for read-only)
- `bit_index`: Optional bit index for flag-based settings
- `is_read_only`: Derived property (True if encode_function is None)

#### 6. `custom_components/kospel/kospel/api.py` - Transport Layer

Low-level API functions for communicating with the heater:

- **`read_register(session, api_base_url, register) -> Optional[str]`**: Read a single register
- **`read_registers(session, api_base_url, start_register, count) -> Dict[str, str]`**: Read multiple registers in batch
- **`write_register(session, api_base_url, register, hex_value) -> bool`**: Write a single register
- **`write_flag_bit(session, api_base_url, register, bit_index, state) -> bool`**: Write a single flag bit (read-modify-write)
- **`is_simulation_mode() -> bool`**: Check if simulation mode is enabled

All functions support simulator mode via the `@with_simulator` decorator, which routes calls to `kospel/simulator.py` when `SIMULATION_MODE` environment variable is set.

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

**Note**: The library modules (`kospel/`, `controller/`, `registers/`) are now located in `custom_components/kospel/`. When using them in `main.py` or other scripts, you need to add the path to `sys.path`:

```python
import asyncio
import aiohttp
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add custom_components/kospel to path to import library modules
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "kospel"))

from controller.api import HeaterController
from registers.enums import HeaterMode
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
from controller.api import HeaterController
from registers.enums import HeaterMode

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
from controller.api import HeaterController
from kospel.api import read_registers

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
- Routes all API calls to `custom_components/kospel/kospel/simulator.py` implementations
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

The `SETTINGS_REGISTRY` is a central registry in `controller/registry.py` that maps semantic setting names to their register locations and parsing logic. It serves as the single source of truth for how settings are stored in heater registers.

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

2. **Create decode function** in `registers/decoders.py` (if needed):
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

4. **Add enum** in `registers/enums.py` (if needed):
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

This project includes comprehensive test coverage following TDD principles. The test suite covers all three architecture layers with unit tests, integration tests, and coverage reporting.

### Running Tests

**Install test dependencies:**
```bash
uv sync --all-groups
```

Or to sync only the dev group:
```bash
uv sync --extra dev
```

**Note:** After syncing, you can run tests with `uv run pytest` or activate the virtual environment with `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows) and use `pytest` directly.

**Run all tests:**
```bash
uv run pytest
```

**Run tests with verbose output:**
```bash
uv run pytest -v
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
uv run pytest --cov=kospel --cov=registers --cov=controller --cov-report=html --cov-report=term
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
├── conftest.py                    # Shared fixtures and test configuration
├── registers/                     # Data layer tests
│   ├── test_utils.py             # Register encoding/decoding tests
│   ├── test_decoders.py          # Decoder function tests
│   └── test_encoders.py          # Encoder function tests
├── kospel/                       # Transport layer tests
│   ├── test_api.py               # HTTP API client tests
│   └── test_simulator.py         # Simulator implementation tests
├── controller/                    # Service layer tests
│   └── test_api.py               # HeaterController tests
└── integration/                   # Integration tests
    ├── test_api_communication.py # End-to-end API tests
    └── test_mock_mode.py         # Simulator mode integration tests
```

### Test Coverage

The project aims for ≥80% code coverage across all layers. Coverage reports are generated using `pytest-cov` and include:

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
    uv sync --group dev
    uv run pytest --cov=kospel --cov=registers --cov=controller --cov-report=xml
    uv run pytest --cov-report=term --cov-report=html
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

## License

[Add your license here]
