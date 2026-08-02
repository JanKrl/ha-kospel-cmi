# Kospel Schedules (Programator)

This document describes how schedules for Central Heating (CO), Domestic Hot Water (CWU), and Circulation are stored in the Kospel C.MI registers. This information was reverse-engineered from the C.MI web UI.

## Architecture

The system uses a day-to-program mapping architecture. Instead of setting times for each day directly, the user defines up to 8 "Daily Programs" (Program 1 to Program 8). Then, each day of the week is assigned one of these Program IDs (1-8).

There are three independent schedule types:
1. **CH (CO)**: Central Heating
   - *Note: If the device is configured in Buffer Mode (`0b8a` = 2), this schedule is repurposed and functions as the "Buffer Tank Schedule" (Programator Bufora).*
2. **DHW (CWU)**: Domestic Hot Water
3. **Circulation**: DHW Circulation Pump

## Day-to-Program Mapping Registers

These registers store a value from `1` to `8`, representing the selected Daily Program ID for that day.

| Day | CH (CO) | DHW (CWU) | Circulation |
| :--- | :--- | :--- | :--- |
| **Monday** | `0c94` | `0d16` | `0d98` |
| **Tuesday** | `0c95` | `0d17` | `0d99` |
| **Wednesday**| `0c96` | `0d18` | `0d9a` |
| **Thursday** | `0c97` | `0d19` | `0d9b` |
| **Friday** | `0c98` | `0d1a` | `0d9c` |
| **Saturday** | `0c99` | `0d1b` | `0d9d` |
| **Sunday** | `0c9a` | `0d1c` | `0d9e` |

## Program Definitions

A Daily Program defines up to 5 time slots for a 24-hour period. Each time slot consists of a start time, a stop time, and an associated temperature preset mode. 

In the device memory, each Daily Program occupies exactly **15 registers**:
- **Registers 1-10**: 5 pairs of (start time, stop time). Times are stored as minutes from midnight (e.g., 08:00 is `480`). If a time slot is empty/unused, the value is `65535` (`0xffff`).
- **Registers 11-15**: 5 values representing the temperature preset ID for each of the 5 time slots. If a time slot is empty, the value is `65535` (`0xffff`).

### Program Base Addresses

The start address for a given Program `N` (where `N` is `1` to `8`) is calculated as follows:

| Schedule Type | Start Address Formula (Decimal) | Base Address for Prog 1 (Hex) |
| :--- | :--- | :--- |
| **CH (CO)** | `3100 + 15 * (N - 1)` | `0c1c` |
| **DHW (CWU)** | `3230 + 15 * (N - 1)` | `0c9e` |
| **Circulation** | `3360 + 15 * (N - 1)` | `0d20` |

*Note: For the Circulation schedule, the web UI only writes the first 10 registers (start/stop times) and does not use temperature presets, but 15 registers are still allocated per program in the address space.*

### Temperature Preset IDs

The preset IDs map to the following operational modes:

**CH (CO) Presets:**
- `0`: Antifreeze (`Ochrona przed zamarzaniem`, `pzam`) ❄️
- `1`: Economy (`Ekonomiczny`, `eko`) 🍃
- `2`: Comfort (`Komfort`, `conf`) 🌡️
- `3`: Comfort Plus (`Komfort+`, `confp`) 🌡️+
- `4`: Comfort Minus (`Komfort-`, `confm`) 🌡️-

**DHW (CWU) Presets:**
- `0`: Off (`Wyłączone`) 🔌
- `1`: Economy (`Ekonomiczny`, `eko`) 🍃
- `2`: Comfort (`Komfort`, `conf`) 🌡️

**Circulation Presets:**
- `0`: Off (`Wyłączone`) 🔌
- `1`: On (`Włączone`) ⚡

## Time Slot Validation (Overlaps & Separation)
The integration and frontend cards perform strict validation on time slots before allowing them to be saved:
1. **No Overlaps or Collisions**: Time slots within the same Daily Program must be separated by at least 1 minute (`next_start > current_stop`).
2. **Valid Durations**: The `stop` time must be strictly greater than the `start` time (`stop > start`).
3. **Empty Spaces / Non-Contiguous Slots**: Time slots do not need to cover the full 24 hours continuously; unassigned gap periods revert to the background preset (Off / Antifreeze).

## Frontend Lovelace Cards
For detailed documentation on custom Lovelace cards, theme integration, style guides, and developer conventions, see [docs/frontend.md](frontend.md).
