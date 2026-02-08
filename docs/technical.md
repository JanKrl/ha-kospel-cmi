# Technical Specifications

This document provides a high-level technical understanding of the Kospel Heater Control Library, including architecture patterns, data formats, protocols, and implementation details.

## Overview

The Kospel Heater Control Library is a Python-based system for controlling Kospel electric heaters via their HTTP REST API. The system follows a strict 4-layer architecture that separates concerns between transport, data parsing, service logic, and integration layers.

**Key Characteristics:**
- **Async-first**: Built on `asyncio` and `aiohttp` for non-blocking I/O
- **Type-safe**: Strict type hinting throughout with no `Any` types
- **Registry-driven**: Settings defined declaratively in a central registry
- **Simulator-capable**: Full simulator implementation for offline development and testing
- **Protocol-based**: Uses Python Protocol types for decoder/encoder interfaces

## Architecture Patterns

### Layered Architecture

The system follows a strict 4-layer architecture with clear boundaries:

```
┌─────────────────────────────────────┐
│ Layer 4: Integration (Future)       │ ← Home Assistant entities
├─────────────────────────────────────┤
│ Layer 3: Service (Controller)       │ ← High-level business logic
├─────────────────────────────────────┤
│ Layer 2: Data (Parser)              │ ← Data transformation
├─────────────────────────────────────┤
│ Layer 1: Transport (Client)         │ ← HTTP communication
└─────────────────────────────────────┘
```

**Layer Separation Rules:**
- Each layer only communicates with adjacent layers
- No cross-layer dependencies
- Lower layers are unaware of higher layers
- Higher layers depend on lower layers

### Registry Pattern

The `SETTINGS_REGISTRY` is a central configuration that maps semantic setting names to their physical register locations and transformation logic. This pattern enables:

- **Declarative Configuration**: Settings defined in one place
- **Automatic Property Generation**: Dynamic properties on `HeaterController`
- **Type Safety**: Each setting has associated decode/encode functions
- **Read-only Enforcement**: Settings without encoders are automatically read-only

**Example Registry Entry:**
```python
"heater_mode": SettingDefinition(
    register="0b55",
    decode_function=decode_heater_mode,
    encode_function=encode_heater_mode
)
```

### Decorator Pattern

The `@with_simulator` decorator routes function calls to simulator implementations based on environment configuration:

```python
@with_simulator(simulator_read_register)
async def read_register(session, api_base_url, register):
    # Real implementation
```

This pattern enables:
- **Transparent Simulation**: No code changes needed to switch between real/simulator
- **Development Safety**: Test without physical hardware
- **Environment-based Routing**: Controlled via `SIMULATION_MODE` environment variable

### Protocol-based Type System

Python Protocols are used to define interfaces for decoders and encoders:

```python
class Decoder(Protocol[T]):
    def __call__(self, hex_val: str, bit_index: Optional[int] = None) -> Optional[T]: ...
```

This provides:
- **Structural Typing**: Functions that match the signature are compatible
- **Type Safety**: Type checkers can verify compatibility
- **Flexibility**: No inheritance required

## Data Formats

### Register Encoding

**Format**: 4-character hexadecimal string in little-endian byte order

**Internal Representation**: Signed 16-bit integer (-32768 to 32767)

**Encoding Process**:
1. Pack signed integer as 16-bit signed short
2. Unpack as unsigned 16-bit integer (handles two's complement)
3. Format as 4-digit lowercase hex string
4. Swap bytes for little-endian transmission

**Example**:
- Value: `215` (0x00D7)
- Packed: `[0xD7, 0x00]` (little-endian)
- Hex string: `"d700"` (transmitted format)
- Decoding: `"d700"` → swap → `"00d7"` → parse → `215`

**Negative Values**:
- Value: `-32080`
- Two's complement: `33456` (0x82B0)
- Hex string: `"b082"` (bytes swapped: `[0xB0, 0x82]`)

### Scaled Values

Temperatures and pressures are stored with scaling factors for precision:

- **Temperatures**: Stored ×10 (e.g., 22.5°C → 225 → `"00e1"`)
- **Pressure**: Stored ×100 (e.g., 5.00 bar → 500 → `"01f4"`)

This provides 0.1°C precision for temperatures and 0.01 bar precision for pressure.

### Flag Registers

Some registers use individual bits as boolean flags. Flags are accessed via bit manipulation:

**Register 0b55 (System Flags)**:
```
Bit 15  14  13  12  11  10  9   8   7   6   5   4   3   2   1   0
┌──────────────────────────────────────────────────────────────────┐
│                    │    │    │    │Win │Wat │Sum │              │
│                    │    │    │    │Ter │Hea │mer │              │
│                    │Man │    │    │(5) │(4) │(3) │              │
│                    │Mod │    │    │    │    │    │              │
│                    │(9) │    │    │    │    │    │              │
└──────────────────────────────────────────────────────────────────┘
```

**Bit Operations**:
- Read: `(value >> bit_index) & 1`
- Set: `value | (1 << bit_index)`
- Clear: `value & ~(1 << bit_index)`

**Read-Modify-Write Pattern**: Flag bits require reading the current register value, modifying the specific bit, and writing back the entire register.

## Communication Protocol

### HTTP API

**Base URL Format**: `http://<HEATER_IP>/api/dev/<DEVICE_ID>`

**Endpoints**:

1. **Read Single Register**:
   - `GET /api/dev/<DEVICE_ID>/<register>/1`
   - Response: `{"regs": {"0b55": "d700"}, "sn": "...", "time": "..."}`

2. **Read Multiple Registers**:
   - `GET /api/dev/<DEVICE_ID>/<start_register>/<count>`
   - Example: `GET /api/dev/65/0b00/256`
   - Response: `{"regs": {"0b00": "...", "0b01": "...", ...}}`

3. **Write Register**:
   - `POST /api/dev/<DEVICE_ID>/<register>`
   - Body: Hex string (e.g., `"d700"`)
   - Content-Type: `application/json`
   - Response: `{"status": "0"}` (0 = success)

**Request/Response Format**:
- All values are hex strings (4 characters)
- Little-endian byte order
- JSON encoding for requests and responses

### Error Handling

**Network Errors**:
- Timeout: 5 seconds (configurable)
- Connection errors: Returns `None` or empty dict
- HTTP errors: Logged and returns `None`/`False`

**Data Errors**:
- Invalid hex strings: Return default value (`0` or `"0000"`)
- Missing registers: Use default empty string `"0000"`
- Parsing errors: Logged and return `None`

**Application Errors**:
- Invalid settings: Raise `AttributeError` with helpful message
- Read-only settings: Raise `AttributeError` on write attempt
- Missing settings: Raise `AttributeError` with available options

## Implementation Details

### Async Programming

**Framework**: `asyncio` with `aiohttp`

**Session Management**:
- `aiohttp.ClientSession` passed explicitly (no global state)
- Session lifecycle managed by caller (context manager recommended)
- Supports connection pooling and keep-alive

**Function Signatures**:
```python
async def read_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str
) -> Optional[str]:
```

**Best Practices**:
- All I/O operations are async
- Use `async with` for session management
- Timeout all network operations (default 5s)
- Log errors with context

### Type System

**Type Hints**:
- All function parameters and return types explicitly typed
- Use `Optional[T]` for nullable returns
- Use `Protocol` for structural typing
- Avoid `Any` type (enforced by project rules)

**Type Variables**:
```python
T = TypeVar("T")
Decoder(Protocol[T]): ...
```

**Enum Types**:
- All semantic values use Enum classes
- Enums provide string representations via `.value`
- Type-safe comparisons

### State Management

**HeaterController State**:
- `_settings: Dict[str, Any]`: Decoded setting values
- `_pending_writes: Dict[str, Any]`: Modified settings awaiting save
- `_register_cache: Dict[str, str]`: Cached raw register values

**State Flow**:
1. `refresh()` → Fetch registers → Decode → Store in `_settings`
2. Property access → Return from `_settings`
3. Property write → Store in `_settings` and `_pending_writes`
4. `save()` → Encode pending writes → Write registers → Clear `_pending_writes`

### Batch Operations

**Reading**:
- Use `read_registers()` to fetch multiple registers in one API call
- Parse locally using `from_registers()` method
- Reduces network round-trips

**Writing**:
- Group writes by register address
- Read-modify-write pattern for registers with multiple settings
- Only write if value actually changed

### Simulator Implementation

**State Persistence**:
- In-memory dictionary: `Dict[str, str]` (register address → hex value)
- YAML file persistence: `data/heater_mock_state.yaml`
- Auto-save after each write operation
- Auto-load on first read in simulator mode

**Simulator Functions**:
- Mirror real API function signatures (without `session` and `api_base_url`)
- Maintain register state consistently
- Support all read/write operations
- Log operations for debugging

## Home Assistant Integration Requirements

### Import Rules: kospel-cmi-lib

The integration uses **kospel-cmi-lib** for heater communication. Imports use absolute paths to the installed package:

```python
# ✅ CORRECT: Absolute imports from kospel-cmi-lib (installed via manifest requirements)
from kospel_cmi.controller.api import HeaterController
from kospel_cmi.controller.registry import SETTINGS_REGISTRY
from kospel_cmi.kospel.api import read_registers
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend
from kospel_cmi.registers.enums import HeaterMode, ManualMode

# Within integration (same package): use relative imports
from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator
```

**Why Absolute Imports for kospel_cmi?**

kospel-cmi-lib is installed by Home Assistant when loading the integration (via `manifest.json` requirements). It is a top-level Python package, so absolute imports work correctly. Integration modules within `custom_components/kospel/` use relative imports (`.`) for each other.

**Files That Import from kospel_cmi**:
- `custom_components/kospel/__init__.py`
- `custom_components/kospel/coordinator.py`
- `custom_components/kospel/climate.py`, `sensor.py`, `switch.py`

**Common Mistakes**:

1. **Forgetting relative notation**: `from kospel.simulator import ...` instead of `from .simulator import ...`
2. **Wrong level of dots**: Using `.` when you need `..` or vice versa
3. **Mixing absolute and relative**: Some files use relative, others use absolute (inconsistent)

**Validation**:

Before deploying to Home Assistant, verify all imports:
```bash
# Search for absolute imports (should return no results)
grep -r "^from \(kospel\|controller\|registers\|logging_config\) import" custom_components/kospel/
grep -r "^import \(kospel\|controller\|registers\|logging_config\)" custom_components/kospel/
```

**Exception**: Files outside the integration directory (e.g., `main.py` in project root) can use absolute imports if the path is added to `sys.path`, but this is not applicable to Home Assistant integration files.

### Integration Structure

The integration follows Home Assistant's directory structure. Heater communication is provided by kospel-cmi-lib (installed via manifest requirements):

```
custom_components/kospel/
├── __init__.py          # Integration entry point
├── manifest.json        # Integration metadata (requirements: aiohttp, kospel-cmi-lib)
├── config_flow.py       # Configuration UI
├── coordinator.py       # Data update coordinator
├── climate.py           # Climate entities
├── sensor.py            # Sensor entities
├── switch.py            # Switch entities
├── const.py             # Constants
└── strings.json         # UI strings
```

**Key Points**:
- Heater communication (Transport, Data, Service layers) is in **kospel-cmi-lib**
- Integration imports from `kospel_cmi.*` (absolute imports to installed package)
- The `manifest.json` must include `kospel-cmi-lib==0.1.0a3` in requirements (explicit version required for pre-release)

### Testing Integration Imports

Before deploying, test that imports work correctly:

1. **Syntax Check**: Ensure Python can parse all files
   ```bash
   python3 -m py_compile custom_components/kospel/**/*.py
   ```

2. **Import Test**: Try importing the integration (outside Home Assistant context)
   ```python
   # This should work if structure is correct
   import sys
   sys.path.insert(0, 'custom_components')
   from kospel import async_setup
   ```

3. **Home Assistant Validation**: Use Home Assistant's configuration check
   - Go to Developer Tools > YAML > Check Configuration
   - Look for import errors in logs

## Design Decisions

### Why Registry Pattern?

**Problem**: Traditional approach requires manually defining properties for each setting.

**Solution**: Registry defines settings declaratively, properties generated automatically.

**Benefits**:
- Add new settings without code changes to `HeaterController`
- Single source of truth for register mappings
- Type safety through associated decode/encode functions

### Why Read-Modify-Write for Flags?

**Problem**: Flag bits share a register with other settings. Writing only the flag would overwrite other values.

**Solution**: Read current register value, modify specific bit(s), write back entire register.

**Implementation**: Encoders accept `current_hex` parameter and return modified hex string.

### Why Little-Endian?

**Constraint**: Heater firmware uses little-endian byte order (determined by reverse engineering).

**Impact**: All encoding/decoding must handle byte swapping correctly.

**Solution**: Centralized utilities in `registers/utils.py` handle byte order consistently.

### Why Scaled Values?

**Problem**: Limited precision with integer-only storage.

**Solution**: Store values scaled (temperatures ×10, pressure ×100).

**Benefits**:
- 0.1°C precision for temperatures
- 0.01 bar precision for pressure
- No floating-point storage issues

### Why Simulator Mode?

**Problem**: Development and testing require physical heater hardware.

**Solution**: Environment-variable controlled simulator mode with YAML state persistence.

**Benefits**:
- Develop without hardware
- Test all code paths
- Reproducible test scenarios
- Offline development

## Dependencies

### Runtime Dependencies

- **Python**: ≥3.14 (project); kospel-cmi-lib requires ≥3.10
- **aiohttp**: ≥3.13.3 (async HTTP client)
- **kospel-cmi-lib**: ≥0.1.0 (heater communication - Transport, Data, Service layers)

### Development Dependencies

- **pytest**: ≥8.0.0 (testing framework)
- **pytest-asyncio**: ≥0.23.0 (async test support)
- **pytest-cov**: ≥5.0.0 (coverage reporting)
- **pytest-mock**: ≥3.14.0 (mocking utilities)
- **aioresponses**: ≥0.7.6 (mock HTTP responses)
- **pyaml**: ≥25.7.0 (YAML parsing for mock state)
- **python-dotenv**: ≥1.2.1 (environment variable loading)
- **ruff**: ≥0.14.10 (linting and formatting)

### Dependency Management

- **Package Manager**: `uv` (modern Python package manager)
- **Lock File**: `uv.lock` (reproducible builds)

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── registers/               # Data layer tests
│   ├── test_utils.py       # Encoding/decoding
│   ├── test_decoders.py    # Decoder functions
│   └── test_encoders.py    # Encoder functions
├── kospel/                 # Transport layer tests
│   ├── test_api.py         # HTTP client
│   └── test_simulator.py   # Simulator implementation
├── controller/             # Service layer tests
│   └── test_api.py         # HeaterController
└── integration/            # Integration tests
    ├── test_api_communication.py
    └── test_mock_mode.py
```

### Testing Principles

1. **TDD Approach**: Write tests before or alongside implementation
2. **Layer Isolation**: Test each layer independently
3. **Mock External I/O**: Mock HTTP requests/responses
4. **Coverage Target**: ≥80% code coverage
5. **Async Testing**: Use `pytest-asyncio` for async functions

### Test Types

**Unit Tests**:
- Test individual functions in isolation
- Mock external dependencies
- Test edge cases and error conditions

**Integration Tests**:
- Test cross-layer functionality
- Use mock HTTP responses
- Test end-to-end workflows

**Simulator Mode Tests**:
- Verify simulator implementation consistency
- Test state persistence
- Verify simulator matches real API behavior

## Coding Standards

### Type Hinting

- **Strict Typing**: All functions must have complete type hints
- **No Any**: Avoid `Any` type unless absolutely necessary
- **Protocol Types**: Use for structural typing
- **Optional Returns**: Use `Optional[T]` for nullable returns

### Documentation

- **Google-style Docstrings**: All public classes and methods
- **Parameter Documentation**: Document all parameters and return values
- **Example Usage**: Include examples where helpful
- **Comments**: Explain *why*, not *what*

### Error Handling

- **Explicit Handling**: Never pass exceptions silently
- **Custom Exceptions**: Create domain-specific exceptions (future)
- **Logging**: Log errors with context
- **Return Values**: Use `None`/`False` for recoverable errors

### Code Style

- **PEP 8**: Follow Python style guide
- **Ruff**: Automated linting and formatting
- **Line Length**: 88 characters (Black-compatible)
- **Import Organization**: Standard library → third-party → local

## Performance Considerations

### Optimization Strategies

1. **Batch Operations**: Read multiple registers in one API call
2. **Caching**: Cache register values to avoid redundant reads
3. **Lazy Loading**: Only fetch registers when needed
4. **Change Detection**: Only write if value actually changed

### API Call Reduction

**Without Optimization**:
- Reading 5 settings = 5 separate API calls

**With Optimization**:
- Reading 5 settings = 1 batch API call + local parsing

**Example**:
```python
# Fetch all registers once
all_registers = await read_registers(session, api_base_url, "0b00", 256)

# Parse locally (no additional API calls)
heater.from_registers(all_registers)
```

### Memory Considerations

- **Register Cache**: Only cache registers in registry (not all 256)
- **State Persistence**: Mock state persisted to disk, not kept in memory indefinitely
- **Session Pooling**: Reuse HTTP connections via `aiohttp.ClientSession`

## Security Considerations

### Current Limitations

- **No Authentication**: Assumes local network access
- **No Encryption**: HTTP (not HTTPS) communication
- **No Input Validation**: Range checking not implemented (future)

### Recommendations

1. **Network Isolation**: Use on local network only
2. **Input Validation**: Add range checking for settings (future)
3. **HTTPS Support**: Implement if heater firmware supports it (future)

## Future Enhancements

### Planned Features

1. **Home Assistant Integration**: Layer 4 implementation (✅ **Completed and Verified** - integration working in Home Assistant)
2. **Custom Exceptions**: Domain-specific error types
3. **Input Validation**: Range checking for temperatures, pressures
4. **Connection Pooling**: Optimize HTTP connection reuse
5. **WebSocket Support**: Real-time updates if available
6. **Configuration File**: External config for connection settings

### Technical Debt

1. **Error Handling**: More specific exception types needed
2. **Type Hints**: Some areas could use more comprehensive types
3. **Documentation**: API reference could be auto-generated
4. **Testing**: Comprehensive test suite needed (TDD approach)

## References

- **Architecture Diagram**: See `docs/architecture.mermaid`
- **Detailed Architecture**: See `docs/ARCHITECTURE.md`
- **User Guide**: See `README.md`
- **Roadmap**: See `docs/roadmap.md`

