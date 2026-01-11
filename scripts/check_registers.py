"""
Utility script, for development purposes, to discover and display all available registers from the heater API.

This script demonstrates how to check how many registers are available and
what their addresses are.

Usage:
    python check_registers.py
"""

import asyncio
import aiohttp
from typing import Dict, List, Tuple, Optional, Any
import api
from registers.registry import SETTINGS_REGISTRY
from registers.enums import HeaterMode, ValvePosition
from registers.utils import reg_to_int, reg_address_to_int
from logging_config import setup_logging, get_logger

logger = get_logger("check_registers")

# Configuration - adjust these to match your heater
HEATER_IP = "192.168.101.49:80"
DEVICE_ID = "65"
API_BASE_URL = f"http://{HEATER_IP}/api/dev/{DEVICE_ID}"
REGISTER_COUNT = 256  # Define how many registers to try to read from the heater


def _group_invalid_registers(
    invalid_registers: Dict[str, str],
) -> List[Tuple[str, Optional[str], int]]:
    """
    Group consecutive invalid registers into ranges (only within same prefix).

    Returns:
        List of tuples: (start_reg, end_reg, count) for ranges, or (reg, None, 1) for singles.
    """
    if not invalid_registers:
        return []

    # Group by prefix first (0b, 0c, 0d, etc.)
    by_prefix: Dict[str, List[str]] = {}
    for reg in invalid_registers.keys():
        prefix = reg[:2]
        if prefix not in by_prefix:
            by_prefix[prefix] = []
        by_prefix[prefix].append(reg)

    ranges: List[Tuple[str, Optional[str], int]] = []

    # Process each prefix group separately
    for prefix in sorted(by_prefix.keys()):
        sorted_invalid = sorted(by_prefix[prefix], key=reg_address_to_int)

        range_start: Optional[str] = None
        range_end: Optional[str] = None

        for i, reg in enumerate(sorted_invalid):
            reg_int = reg_address_to_int(reg)

            if range_start is None:
                # Start a new range
                range_start = reg
                range_end = reg
            else:
                prev_reg_int = reg_address_to_int(sorted_invalid[i - 1])
                # Only continue range if consecutive AND same prefix
                if reg_int == prev_reg_int + 1 and reg[:2] == range_start[:2]:
                    # Continue the range
                    range_end = reg
                else:
                    # End current range and start a new one
                    if range_start == range_end:
                        ranges.append((range_start, None, 1))
                    else:
                        count = (
                            reg_address_to_int(range_end)
                            - reg_address_to_int(range_start)
                            + 1
                        )
                        ranges.append((range_start, range_end, count))
                    range_start = reg
                    range_end = reg

        # Add the last range for this prefix
        if range_start is not None:
            if range_start == range_end:
                ranges.append((range_start, None, 1))
            else:
                count = (
                    reg_address_to_int(range_end) - reg_address_to_int(range_start) + 1
                )
                ranges.append((range_start, range_end, count))

    return ranges


def _format_parsed_value(value: Any) -> str:
    """Format a parsed value for display."""
    if isinstance(value, bool):
        return str(value)
    elif isinstance(value, (HeaterMode, ValvePosition)):
        return value.value
    elif isinstance(value, float):
        return f"{value:.1f}°C"
    else:
        return str(value)


def _get_parsed_values(reg: str, hex_val: str) -> str:
    """
    Get parsed values for a known register using SETTINGS_REGISTRY.

    Returns:
        Formatted string with parsed values, or empty string if not a known register.
    """
    # Get all settings that use this register
    settings_for_reg = [
        (name, defn) for name, defn in SETTINGS_REGISTRY.items() if defn.register == reg
    ]

    if not settings_for_reg:
        return ""

    parsed_parts = []

    # Parse each setting using its SettingDefinition.decode() method
    for setting_name, setting_def in settings_for_reg:
        try:
            parsed_value = setting_def.decode(hex_val)
            if parsed_value is not None:
                # Format the value appropriately
                if isinstance(parsed_value, dict):
                    # For dict values (like pump_status), format each key-value pair
                    for key, val in parsed_value.items():
                        if val is not None:
                            parsed_parts.append(f"{key}={val}")
                else:
                    # For single values, use the setting name
                    formatted = _format_parsed_value(parsed_value)
                    parsed_parts.append(f"{setting_name}={formatted}")
        except Exception:
            # Silently skip parsing errors
            pass

    # Format and return
    if parsed_parts:
        return " | " + " | ".join(parsed_parts)

    return ""


async def main():
    """Discover and display all available registers."""
    print("=" * 80)
    print("  REGISTER DISCOVERY TOOL")
    print("=" * 80)
    print(f"\nConnecting to heater at {API_BASE_URL}...")
    print(
        "Reading all available registers (starting from 0b00, max 256 registers)...\n"
    )

    logger.info(f"Starting register discovery for {API_BASE_URL}")

    async with aiohttp.ClientSession() as session:
        logger.debug(f"Reading {REGISTER_COUNT} registers starting from 0b00")
        all_registers = await api.read_registers(
            session, API_BASE_URL, "0b00", REGISTER_COUNT
        )

        if not all_registers:
            logger.error("Could not read any registers from heater")
            print("ERROR: Could not read any registers!")
            print("This might indicate:")
            print("  - Network connectivity issue")
            print("  - Incorrect API base URL")
            print("  - Heater is not responding")
            return

        # Separate valid and invalid registers (ffff = -1 typically indicates invalid/unavailable)
        valid_registers = {}
        invalid_registers = {}

        logger.debug("Separating valid and invalid registers")
        for reg, hex_val in all_registers.items():
            int_val = reg_to_int(hex_val)
            if hex_val.lower() == "ffff" or int_val == -1:
                invalid_registers[reg] = hex_val
            else:
                valid_registers[reg] = hex_val

        # Display summary
        logger.info(
            f"Discovered {len(all_registers)} registers: "
            f"{len(valid_registers)} valid, {len(invalid_registers)} invalid"
        )
        print(f"✓ Successfully discovered {len(all_registers)} registers")
        print(f"  - Valid registers: {len(valid_registers)}")
        print(f"  - Invalid/unavailable registers: {len(invalid_registers)} (ffff)\n")

        # Sort registers by address for better readability
        sorted_all_regs = sorted(
            all_registers.items(), key=lambda x: reg_address_to_int(x[0])
        )

        # Group invalid registers into ranges
        logger.debug(f"Grouping {len(invalid_registers)} invalid registers into ranges")
        invalid_ranges = _group_invalid_registers(invalid_registers)
        logger.debug(f"Created {len(invalid_ranges)} invalid register ranges")

        # Create a mapping from register to its range info for quick lookup
        invalid_range_map: Dict[str, Tuple[str, Optional[str], int]] = {}
        for range_start, range_end, count in invalid_ranges:
            if range_end is None:
                invalid_range_map[range_start] = (range_start, None, 1)
            else:
                # Map all registers in the range to the range info
                # Preserve the prefix (first 2 chars) from range_start
                prefix = range_start[:2]
                start_int = reg_address_to_int(range_start)
                end_int = reg_address_to_int(range_end)
                for reg_int in range(start_int, end_int + 1):
                    reg_str = f"{prefix}{reg_int:02x}"
                    invalid_range_map[reg_str] = (range_start, range_end, count)

        # Create a set of all invalid register addresses for quick lookup
        invalid_set = set(invalid_registers.keys())

        # Display register list
        print("Available registers:")
        print("-" * 100)
        print(
            f"{'Register':<12} {'Hex Value':<12} {'Int Value':<12} {'Parsed Values':<60}"
        )
        print("-" * 100)

        # Track which ranges we've already displayed
        displayed_ranges = set()

        # Display all registers, showing ranges for invalid ones
        for reg, hex_val in sorted_all_regs:
            if reg in invalid_set:
                # Check if this is the start of a range we haven't displayed yet
                if reg in invalid_range_map:
                    range_start, range_end, count = invalid_range_map[reg]
                    range_key = (range_start, range_end)

                    if range_key not in displayed_ranges:
                        if range_end is None:
                            # Single invalid register
                            int_val = reg_to_int(hex_val)
                            parsed = _get_parsed_values(reg, hex_val)
                            print(f"{reg:<12} {hex_val:<12} {int_val:<12} {parsed}")
                        else:
                            # Range of invalid registers
                            range_display = f"{range_start}-{range_end}"
                            print(
                                f"{range_display:<12} {'ffff':<12} {'-1 (invalid)':<12} [{count} registers]"
                            )
                        displayed_ranges.add(range_key)
            else:
                # Valid register - display normally with parsed values
                int_val = reg_to_int(hex_val)
                parsed = _get_parsed_values(reg, hex_val)
                print(f"{reg:<12} {hex_val:<12} {int_val:<12} {parsed}")

        print("-" * 100)
        print(f"\nTotal: {len(all_registers)} registers available")

        # Show register range
        if sorted_all_regs:
            first_reg = sorted_all_regs[0][0]
            last_reg = sorted_all_regs[-1][0]
            print(f"Range: {first_reg} to {last_reg}")

        print("\n" + "=" * 80)
        print("Discovery complete!")
        print("=" * 80)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
