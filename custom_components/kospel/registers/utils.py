"""
Low-level utility functions for encoding/decoding heater register formats.

This module handles the conversion between Python data types and the heater's
register format (little-endian hex strings representing signed 16-bit integers).

Important: The bit manipulation functions (get_bit, set_bit) are low-level
utilities and should not be used directly in application code.
"""

import logging
import struct

logger = logging.getLogger(__name__)


def int_to_reg(value: int) -> str:
    """
    Converts a signed 16-bit integer to the heater's little-endian hex string.

    This is the inverse of reg_to_int(). Converts a Python integer to the format
    expected by the heater API (little-endian hex string).

    Process:
    1. Convert signed int to unsigned 16-bit representation
    2. Format as 4-digit hex string
    3. Swap bytes for little-endian transmission

    Example:
        215 -> pack as signed -> unpack as unsigned -> 0x00D7 -> "00d7" -> "d700"

    Args:
        value: Signed 16-bit integer (-32768 to 32767)

    Returns:
        4-character hex string in little-endian format
    """
    try:
        # 1. Pack as signed short, then unpack as unsigned to get 16-bit representation
        # This handles negative values correctly (two's complement conversion)
        unsigned_val = struct.unpack("H", struct.pack("h", value))[0]
        # 2. Format as 4-digit hex string (lowercase, zero-padded)
        hex_str = f"{unsigned_val:04x}"
        # 3. Swap bytes for little-endian transmission
        # "00d7" -> "d700" (bytes swapped)
        return hex_str[2:] + hex_str[:2]
    except (ValueError, TypeError, struct.error) as e:
        logger.error(f"Error encoding int value '{value}': {e}")
        return "0000"


def reg_to_int(hex_val: str) -> int:
    """
    Converts the heater's little-endian hex string to a signed 16-bit integer.
    e.g., "d700" -> 0x00d7 -> 215
    """
    try:
        # 1. Swap the bytes (little-endian): "d700" -> "00d7"
        swapped_hex = hex_val[2:] + hex_val[:2]

        # 2. Convert to an unsigned integer
        unsigned_val = int(swapped_hex, 16)

        # 3. Interpret as a signed 16-bit integer
        # 'h' is format for signed short (16-bit)
        return struct.unpack("h", struct.pack("H", unsigned_val))[0]
    except (ValueError, TypeError, struct.error) as e:
        logger.error(f"Error decoding hex value '{hex_val}': {e}")
        return 0


def get_bit(value: int, bit_index: int) -> bool:
    """
    Checks if a specific bit is set in an integer.

    Note: This is a low-level utility function. For application code,
    prefer using the settings API in settings.py instead of direct bit manipulation.
    """
    return (value & (1 << bit_index)) != 0


def set_bit(value: int, bit_index: int, state: bool) -> int:
    """
    Sets or clears a specific bit in an integer.

    Note: This is a low-level utility function. For application code,
    prefer using the settings API in settings.py instead of direct bit manipulation.
    """
    if state:
        return value | (1 << bit_index)  # Set bit
    else:
        return value & ~(1 << bit_index)  # Clear bit


def reg_address_to_int(address: str) -> int:
    """
    Converts a register address string (e.g., '0b51') to integer (i.e. for sorting).
    """
    return int(address[2:], 16)
