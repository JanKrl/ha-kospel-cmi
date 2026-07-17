# Technical Specifications

This document provides a high-level technical understanding of the Kospel Heater Control Library, including architecture patterns, data formats, protocols, and implementation details.

## Overview

The Kospel Heater Control Library is a Python-based system for controlling Kospel electric heaters via their HTTP REST API. The system follows a strict 3-layer architecture that separates concerns between transport, data parsing and service logic.

**Key Characteristics:**
- **Async-first**: Built on `asyncio` and `aiohttp` for non-blocking I/O
- **Type-safe**: Strict type hinting throughout with no `Any` types
- **Device-specific API**: Explicit properties and async setters on `EkcoM3`
- **Simulator-capable**: Full simulator implementation for offline development and testing
- **Protocol-based**: Uses Python Protocol types for decoder/encoder interfaces

## Architecture Patterns

### Layered Architecture

The system follows a strict 3-layer architecture with clear boundaries:

```
┌─────────────────────────────────────┐
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

### Device Class Pattern

> **See also**: For device class documentation, see [`../src/kospel_cmi/controller/README.md`](../src/kospel_cmi/controller/README.md).

`EkcoM3` is a device-specific class with explicit properties and async setters. Each setting is a property (read) or `set_*` method (write). Writes happen immediately; no `save()` or batching.

- **Explicit API**: All settings are explicit properties; IDE support and type safety
- **Immediate save**: Each setter writes to the device immediately
- **Device-specific**: One class per device type; add `KospelCmiPro` for new variants

**Usage:**
```python
controller = EkcoM3(backend=backend)
await controller.refresh()
mode = controller.heater_mode  # Read property
await controller.set_heater_mode(HeaterMode.WINTER)  # Write immediately
```

### Register Backend (Protocol)

Register read/write is abstracted behind a `RegisterBackend` Protocol. The controller depends only on this interface; it does not know whether data comes from HTTP or from a YAML file.

- **Protocol** (`kospel/backend.py`): `read_register(register)`, `read_registers(start_register, count)`, `write_register(register, hex_value)`. No session, URL, or mode parameters.
- **HttpRegisterBackend(session, api_base_url)**: implements the protocol via HTTP calls to the device.
- **YamlRegisterBackend(state_file: str)**: implements the protocol using a YAML state file; the file path is a required constructor parameter (no environment variable).
- **Construction**: The consumer creates backend and passes it to `EkcoM3(backend=...)`.
- **write_flag_bit**: Single implementation in `kospel/backend.py` as a **function** that takes the backend as first argument: `write_flag_bit(backend, register, bit_index, state)`. It is not a method on the backend; it uses `backend.read_register` and `backend.write_register`. One implementation for all backends.
- **Why Protocol**: The controller and `write_flag_bit` need “something that can read/write registers”. A Protocol lets any object with the right methods be used. Alternatives (e.g. passing three callables) would require the caller to build closures over `session`/`api_base_url` or `state_file`; the Protocol keeps that state inside the backend object and keeps the interface explicit.

This gives:
- **Single responsibility**: Controller logic is independent of transport.
- **Testability**: Tests can use a mock backend or `YamlRegisterBackend` with a temporary file.
- **No env-based routing**: No `simulation_mode` or env vars in the call chain.

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

> **See also**: For detailed register encoding/decoding reference, see [`../src/kospel_cmi/registers/README.md`](../src/kospel_cmi/registers/README.md).

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
│                    │Man │    │Vac │Par │Win │Wat │Sum │          │
│                    │(9) │    │(7) │(6) │(5) │(4) │(3) │          │
└──────────────────────────────────────────────────────────────────┘
```
Heater mode (bits 3, 5, 6, 7, 9): OFF, SUMMER, WINTER, PARTY, VACATION, MANUAL — mutually exclusive.

**Bit Operations**:
- Read: `(value >> bit_index) & 1`
- Set: `value | (1 << bit_index)`
- Clear: `value & ~(1 << bit_index)`

**Read-Modify-Write Pattern**: Flag bits require reading the current register value, modifying the specific bit, and writing back the entire register.

## Communication Protocol

> **See also**: For detailed HTTP API endpoint reference, see [`../src/kospel_cmi/kospel/README.md`](../src/kospel_cmi/kospel/README.md).

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

4. **Device Discovery** (no device_id required):
   - `GET /api/dev` — returns `{"status": "0", "sn": "...", "devs": ["65"]}`
   - `GET /api/dev/<DEVICE_ID>/info` — returns model info (`info.id`: 18=EKD.M3, 19=EKCO.M3, 65=C.MG3, 81=C.MW3)
   - See `kospel.discovery` module: `probe_device()`, `discover_devices()`

**Request/Response Format**:
- All values are hex strings (4 characters)
- Little-endian byte order
- JSON encoding for requests and responses

### Error Handling

**HTTP layer (`kospel.api`)**:
- **Transport**: Network failures, HTTP error status, or non-JSON responses raise `KospelConnectionError` (chained from the underlying exception where applicable).
- **Single read (`read_register`)**: Missing register in the JSON `regs` object raises `RegisterMissingError`. Values that are not valid 4-character hex raise `RegisterValueInvalidError`.
- **Batch read (`read_registers`)**: Partial `regs` payloads are allowed (the device may omit addresses). Every **present** value is validated; invalid hex raises `RegisterValueInvalidError`.
- **Write (`write_register`)**: Failures raise `KospelConnectionError` or `KospelWriteError` (e.g. device `status` not `"0"`). No boolean success return.

**YAML simulator (`kospel.simulator`)**:
- Unchanged lenient behavior: missing registers still surface as `"0000"` for offline use. Write failures when persisting the file raise `KospelWriteError`.

**Controller (`EkcoM3`)**:
- **`refresh()`**: On backend failure, the previous register cache is left unchanged. On success, the cache is replaced by the batch response map, which may still be **partial** (device may omit keys) unless strict mode applies.
- **`strict_refresh`**: Pass `strict_refresh=True` to `EkcoM3`. Then each successful `read_registers` must include every address in **`EkcoM3.REQUIRED_REGISTERS`** (the union of registers used by public read-only properties). If any are missing, **`IncompleteRegisterRefreshError`** is raised (with **`missing_registers`**) and the **cache is not updated**. Default is `strict_refresh=False` (partial cache allowed).
- **Reading properties**: Accessing a register that was never loaded into the cache raises `RegisterMissingError` (call `refresh()` or `from_registers()` with the needed keys first).
- **Setters**: Raise on write failure (same types as the backend) instead of returning `False`.

**Application-level validation**:
- Invalid enum/range arguments may raise `ValueError` or `TypeError` with a clear message (e.g. max power index out of dynamically queried bounds).

## Implementation Details

### Async Programming

**Framework**: `asyncio` with `aiohttp`

**Session Management**:
- `aiohttp.ClientSession` passed explicitly (no global state)
- When using `HttpRegisterBackend`, call `EkcoM3.aclose()` when done, or use `async with EkcoM3(backend=...)` to release the session automatically
- Supports connection pooling and keep-alive

**Function Signatures**:
```python
async def read_register(
    session: aiohttp.ClientSession,
    api_base_url: str,
    register: str
) -> str:
```

**Best Practices**:
- All I/O operations are async
- Use `async with` for session management
- Timeout all network operations (default 5s)
- Log errors with context
- **File I/O in async code**: Never use synchronous `open()` or `Path.read_text()`/`write_text()` inside async functions. Use `aiofiles` instead:
  - `async with aiofiles.open(path, "r", encoding="utf-8") as f: content = await f.read()`
  - `async with aiofiles.open(path, "a", encoding="utf-8") as f: await f.write(data)`
  - Reference implementation: `kospel/simulator.py` (_load_registers, _save_registers)

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

**EkcoM3 State**:
- `_registers: Dict[str, str]`: Cached raw register values

**State Flow**:
1. `refresh()` → Fetch registers → Store in `_registers`
2. Property access → Decode from `_registers` on demand
3. `set_*()` → Encode → Write register immediately → Update `_registers`

### Batch Operations

**Reading**:
- Use `read_registers()` to fetch multiple registers in one API call
- Parse locally using `from_registers()` method
- Reduces network round-trips

**Writing**:
- Group writes by register address
- Read-modify-write pattern for registers with multiple settings
- Only write if value actually changed

### Dynamic Hardware Capabilities

Certain settings on Kospel devices, such as the maximum power limit and the pump lift options, depend entirely on the specific physical hardware unit connected.
- **Max Power Limit:** Instead of a static enum of options, the device reports the length of available power settings in register `0b35` and uses subsequent registers (`0b36`, `0b37`, etc.) to provide the specific kW value options. The currently selected index is stored in `0b62`.
- **Stateless Integration:** Because these hardware capabilities never change during runtime, and because `refresh()` fetches 256 registers starting at `0b00` (which inherently captures these arrays), the library derives these lists dynamically on the fly from the cached register snapshot rather than performing any custom initialization queries or maintaining separate metadata state.

### YAML / simulator (function module)

**Layout**: `kospel/simulator.py` is a **function module** like `api.py`: no classes, only async functions that take `state_file` as the first parameter.

- `read_register(state_file, register) -> str`
- `read_registers(state_file, start_register, count) -> Dict[str, str]`
- `write_register(state_file, register, hex_value) -> None` (raises `KospelWriteError` on persist failure)

Each call loads from or saves to the YAML file. `YamlRegisterBackend` in `backend.py` holds `state_file` and delegates to these functions.

**State persistence**:
- YAML file path is passed explicitly (no environment variable)
- Load on each read; save after each write
- Same contract as HTTP: controller code is identical for both backends


## Import Rules: Relative Imports Only

This section applies when **embedding or vendoring** this library inside a Home Assistant custom integration. The integration's own code must use relative imports within its package. The kospel-cmi-lib itself uses normal absolute imports (e.g. `from kospel_cmi import probe_device`).

**Critical Requirement**: All imports within a Home Assistant custom integration **must** use relative imports (with `.` notation). 

**Correct Import Patterns**:

```python
# ✅ CORRECT: Relative imports within integration
from .kospel.backend import HttpRegisterBackend, YamlRegisterBackend
from .controller.device import EkcoM3
from ..logging_config import get_logger

controller = EkcoM3(backend=...)

# ❌ INCORRECT: Absolute imports
from kospel.backend import HttpRegisterBackend
from controller.device import EkcoM3
from logging_config import get_logger
```

**Import Path Rules**:

1. **Same Package**: Use single dot (`.`) for modules in the same directory
   ```python
   from .backend import RegisterBackend  # kospel/backend.py from kospel/api.py
   ```

2. **Parent Package**: Use double dot (`..`) to go up one level
   ```python
   from ..registers.utils import reg_to_int  # registers/utils.py from kospel/api.py
   ```

3. **Sibling Package**: Use `..` to go up, then specify the sibling path
   ```python
   from ..kospel.api import read_registers  # kospel/api.py from controller/api.py
   ```

**Common Mistakes**:

1. **Forgetting relative notation**: `from kospel.backend import ...` instead of `from .backend import ...`
2. **Wrong level of dots**: Using `.` when you need `..` or vice versa
3. **Mixing absolute and relative**: Some files use relative, others use absolute (inconsistent)


## Design Decisions

### Why Registry Pattern?

**Problem**: Traditional approach requires manually defining properties for each setting.

**Solution**: Registry defines settings declaratively, properties generated automatically.

**Benefits**:
- Add new settings by adding properties and setters to `EkcoM3`
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

### Why Register Backend Abstraction?

**Problem**: Development and testing require physical heater hardware; mixing transport and “simulation mode” in the same functions led to complex parameter passing and env checks.

**Solution**: A `RegisterBackend` Protocol with two implementations—`HttpRegisterBackend(session, api_base_url)` and `YamlRegisterBackend(state_file: str)`. The controller receives a backend at construction; no environment variables or `simulation_mode` in the call chain.

**Benefits**:
- Develop without hardware by using `YamlRegisterBackend(state_file="...")`
- Controller logic identical for HTTP and YAML
- Single place for `write_flag_bit` (function using any backend)
- Configuration via constructor parameters only (URL or state file path)

## Dependencies

### Dependency Management

- **Package Manager**: `uv` (modern Python package manager)
- **Lock File**: `uv.lock` (reproducible builds)

## Workflow and Standards

For implementation details regarding:
- **Testing Strategy** (TDD, Integration, Simulator testing)
- **Coding Standards** (Type Hinting, Documentation, Error Handling, Code Style)

Please refer to the [Development Guide](development.md) which serves as the single source of truth for the project's development workflow.

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

- **Register Cache**: Cache raw register values in `_registers` (up to 256)
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

1. **Input Validation**: Range checking for temperatures, pressures
2. **Connection Pooling**: Optimize HTTP connection reuse
3. **Device type recognition**: Recognize heater device type

### Technical Debt

1. **Type Hints**: Some areas could use more comprehensive types
2. **Documentation**: API reference could be auto-generated
3. **Testing**: Comprehensive test suite needed (TDD approach)

## References

- **Architecture Diagram**: See [`architecture.md`](architecture.md)
- **User Guide**: See [`../README.md`](../README.md)
- **Development Guide**: See [`development.md`](development.md)

### Module Documentation

Detailed module-specific documentation is co-located with the code:

- **[kospel/](../src/kospel_cmi/kospel/README.md)** - HTTP API endpoints and protocol
- **[registers/](../src/kospel_cmi/registers/README.md)** - Register encoding, decoding, and mappings
- **[controller/](../src/kospel_cmi/controller/README.md)** - EkcoM3 device class

