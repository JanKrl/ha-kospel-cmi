"""
This module contains tools to decode human-readable values from heater registers (stored in raw hex format).

A register value can represent a single value (like temperature of pressure) or be a bitmask of boolean values.
"""

from typing import Optional, Protocol, TypeVar, Callable
from .enums import HeaterMode
from .utils import reg_to_int, get_bit


T = TypeVar("T")


class Decoder(Protocol[T]):
    """Decoder takes raw hex value of a register and returns readable value.
    Some decoders like single-bit flags may require bit_index.

    All decoders must accept bit_index parameter (even if they ignore it)
    to maintain compatibility with the registry system.

    Args:
        hex_val: Hex string from register
        bit_index: Optional bit index (required for some decoders, ignored for others)

    Returns:
        Optional[T]: Readable value (may be dict, string, bool, float, etc. depending on decoder)
                        None: If decoding fails
    """

    def __call__(
        self, hex_val: str, bit_index: Optional[int] = None
    ) -> Optional[T]: ...


def decode_map(
    true_value: T, false_value: T
) -> Callable[[str, Optional[int]], Optional[T]]:
    """Returns a decoder function that maps a boolean bit to specific Enum state.

    Args:
        true_value: Value to return if bit is 1
        false_value: Value to return if bit is 0
    """

    def _decoder(hex_val: str, bit_index: Optional[int] = None) -> Optional[T]:
        raw_bool = decode_bit_boolean(hex_val, bit_index)
        if raw_bool is None:
            return None
        return true_value if raw_bool else false_value

    return _decoder


def decode_heater_mode(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[HeaterMode]:
    """Decode heater mode from register 0b55 hex string.

    Args:
        hex_val: Hex string from register 0b55
        bit_index: Ignored
    """
    SUMMER_BIT = 3
    WINTER_BIT = 5

    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        # Validate hex string
        int(hex_val, 16)
        flags_0b55 = reg_to_int(hex_val)
        is_summer = get_bit(flags_0b55, SUMMER_BIT)
        is_winter = get_bit(flags_0b55, WINTER_BIT)

        if is_summer:
            return HeaterMode.SUMMER
        elif is_winter:
            return HeaterMode.WINTER
        else:
            return HeaterMode.OFF
    except (ValueError, TypeError):
        return None


def decode_bit_boolean(hex_val: str, bit_index: Optional[int] = None) -> Optional[bool]:
    """Generic decoder to get a boolean value from a register hex string, at specific bit index.

    Args:
        hex_val: Hex string from register
        bit_index: Bit index of boolean value (required)
    """
    if bit_index is None:
        raise ValueError("Bit index is required for boolean value decoding")

    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        # Validate hex string
        int(hex_val, 16)
        regiser_int = reg_to_int(hex_val)
        return get_bit(regiser_int, bit_index)
    except (ValueError, TypeError):
        return None


def decode_scaled_temp(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[float]:
    """Decode temperature value (scaled by 10).

    Args:
        hex_val: Hex string from register
        bit_index: Ignored
    """
    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        # Validate hex string
        int(hex_val, 16)
        return reg_to_int(hex_val) / 10.0
    except (ValueError, TypeError):
        return None


def decode_scaled_pressure(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[float]:
    """Decode pressure value (scaled by 100).

    Args:
        hex_val: Hex string from register
        bit_index: Ignored
    """
    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        # Validate hex string
        int(hex_val, 16)
        return reg_to_int(hex_val) / 100.0
    except (ValueError, TypeError):
        return None
