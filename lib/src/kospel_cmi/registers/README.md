# Register System

This module handles encoding and decoding of heater register values.

## Register Format

The heater exposes registers as hexadecimal strings in **little-endian format**:

- **Register Format**: 4-character hex string (e.g., `"d700"`)
- **Byte Order**: Little-endian (bytes swapped)
  - `"d700"` means: bytes are `[0xd7, 0x00]` in memory
  - When read as big-endian: `0x00d7` = 215
- **Value Type**: Signed 16-bit integers (-32768 to 32767)

## Scaled Values

Temperatures and pressures are stored with scaling factors for precision:

- **Temperatures**: Stored ×10 (e.g., 22.5°C → 225 → `"00e1"`)
- **Pressure**: Stored ×100 (e.g., 5.00 bar → 500 → `"01f4"`)

This provides 0.1°C precision for temperatures and 0.01 bar precision for pressure.

## Flag Registers

Some registers use individual bits as flags (specific register addresses may vary per device/version):

### Register 0b55 (System Flags)

- Bit 3: Summer mode
- Bit 4: Water heater enabled
- Bit 5: Winter mode
- Bit 6: Party mode
- Bit 7: Vacation mode
- Bit 9: Manual mode

**Heater Mode** (register 0b55, bits 3, 5, 6, 7, 9) — six mutually exclusive modes:
- OFF: All mode bits cleared
- SUMMER: Bit 3=1
- WINTER: Bit 5=1
- PARTY: Bit 6=1
- VACATION: Bit 7=1
- MANUAL: Bit 9=1

### Register 0b51 (Component Status)

- Bit 0: Pump CO running
- Bit 1: Pump circulation running
- Bit 2: Valve position (0=CO, 1=DHW)
- Bit 7: CO heating circuit active (radiator icon)
- Bit 8: CWU heating circuit active (tap icon)

## Example Register Values

Register values may vary per device type / version. Currently the project includes only one `SETTINGS_REGISTRY` but may be extended with multiple configurations for various device types.

| Register | Description | Format | Example |
|----------|-------------|--------|---------|
| `0b31` | Room temperature setting | Temp (×10) | `"00e1"` = 22.5°C |
| `0b4b` | Room current temperature | Temp (×10) | `"00e6"` = 23.0°C |
| `0b2f` | Water temperature setting | Temp (×10) | `"01a4"` = 42.0°C |
| `0b4e` | Pressure | Pressure (×100) | `"01f4"` = 5.00 bar |
| `0b51` | Component status flags | Flags | `"0005"` (bits 0,2 set) |
| `0b55` | System flags | Flags | `"02a0"` (bits 5,7,9 set) |
| `0b8a` | Work mode (0=CO, 1=Heat Source, 2=Buffer) | Integer | `"0000"` = CO |
| `0b8d` | Manual temperature | Temp (×10) | `"00e1"` = 22.5°C |

## Common Register Mappings

### Temperature Registers (scaled ×10)

- `0b31`: Room temperature setting
- `0b4b`: Room current temperature
- `0b2f`: Water temperature setting
- `0b4a`: Water current temperature
- `0b4c`: Outside temperature
- `0b74`: Outside temperature off threshold
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

### Flag Registers

- `0b51`: Component status (pumps, valve)
- `0b55`: System flags (heater mode, water heater)

### Mode Registers

- `0b8a`: Work mode (0=CO, 1=Heat Source, 2=Buffer)
- `0b55`: Heater mode (bits 3, 5, 6, 7, 9 for OFF/SUMMER/WINTER/PARTY/VACATION/MANUAL)

### Vacation Mode Registers (tryb wakacje)

- `0b59`: Duration in hours (scaled ×10, e.g. 79.5 = 79.5 hours)
- `0b5a`: Indefinite flag (0xffff = "Do odwołania", until cancelled)
- `0b6c`: End time — minute (0–59)
- `0b6d`: End time — hour (0–23)
- `0b6e`: End time — day (1–31)
- `0b6f`: End time — month (1–12)
- `0b70`: End time — year (2 digits, e.g. 26 = 2026)

## Implementation

Register encoding/decoding is implemented in:
- `utils.py` - Core utilities (`reg_to_int`, `int_to_reg`, `set_bit`, `get_bit`)
- `decoders.py` - Decoder functions for various register types
- `encoders.py` - Encoder functions for various register types
- `enums.py` - Enum types for semantic values

## Read-Modify-Write Pattern

Flag bits require reading the current register value, modifying the specific bit, and writing back the entire register. This pattern is implemented in the encoder functions to preserve other bits in the register.

## Negative Values

Negative register values are normal for flag registers. The value `-32080` for register `0b55` means bits 8-15 are set, which is expected when multiple flags are enabled.
