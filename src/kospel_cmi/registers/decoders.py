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
    to support both full-register and bit-index decoders.

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

    Bits: 3=SUMMER, 5=WINTER, 6=PARTY, 7=VACATION, 9=MANUAL.
    Priority order: MANUAL > PARTY > VACATION > SUMMER > WINTER > OFF.

    Args:
        hex_val: Hex string from register 0b55
        bit_index: Ignored
    """
    MANUAL_BIT = 9
    PARTY_BIT = 6
    VACATION_BIT = 7
    SUMMER_BIT = 3
    WINTER_BIT = 5

    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        # Validate hex string
        int(hex_val, 16)
        flags_0b55 = reg_to_int(hex_val)

        if get_bit(flags_0b55, MANUAL_BIT):
            return HeaterMode.MANUAL
        if get_bit(flags_0b55, PARTY_BIT):
            return HeaterMode.PARTY
        if get_bit(flags_0b55, VACATION_BIT):
            return HeaterMode.VACATION
        if get_bit(flags_0b55, SUMMER_BIT):
            return HeaterMode.SUMMER
        if get_bit(flags_0b55, WINTER_BIT):
            return HeaterMode.WINTER
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
        register_int = reg_to_int(hex_val)
        return get_bit(register_int, bit_index)
    except (ValueError, TypeError):
        return None


def decode_scaled_x10(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[float]:
    """Decode value scaled by 10 (stored as value × 10 in register).

    Use for temperatures (°C), durations (hours), and any value with 0.1 precision.
    E.g. 22.5°C → 225 → \"00e1\", 79.5 h → 795 → \"1b03\".

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


def decode_scaled_x100(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[float]:
    """Decode value scaled by 100 (stored as value × 100 in register).

    Use for pressure (bar), flow, and any value with 0.01 precision.
    E.g. 5.00 bar → 500 → "01f4".

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


def decode_raw_int(
    hex_val: str, bit_index: Optional[int] = None
) -> Optional[int]:
    """Decode raw 16-bit signed integer from register.

    Use for registers that store integer values (e.g. duration, timestamps).
    Value 0xffff (-1) often means \"indefinite\" or \"until cancelled\".

    Args:
        hex_val: Hex string from register
        bit_index: Ignored
    """
    try:
        if hex_val is None or len(hex_val) != 4:
            return None
        int(hex_val, 16)
        return reg_to_int(hex_val)
    except (ValueError, TypeError):
        return None


# Registry for config loader: maps YAML decoder names to decoder functions.
# "map" is special—built from params at load time via decode_map().
DECODER_REGISTRY: dict[str, Callable[..., Optional[object]]] = {
    "heater_mode": decode_heater_mode,
    "scaled_x10": decode_scaled_x10,
    "scaled_x100": decode_scaled_x100,
    "raw_int": decode_raw_int,
}
