"""
This module contains tools to encode human-readable values to heater register hex format.

Encoders convert Python values (enums, bools, floats) to hex strings that can be written to registers.
"""

import logging
from typing import Optional, Protocol, Any, Callable
from .utils import int_to_reg, reg_to_int, set_bit
from .enums import HeaterMode

logger = logging.getLogger(__name__)


class Encoder(Protocol):
    """Encoder takes a value and converts it to a hex string for writing to a register.

    Args:
        value: The value to encode (enum, bool, float, etc.)
        register: Register address (e.g., "0b55")
        bit_index: Optional bit index for bit-based settings
        current_hex: Optional current hex value of the register (for read-modify-write)

    Returns:
        Optional[str]: Hex string to write, or None if encoding fails
    """

    def __call__(
        self,
        value: Any,
        bit_index: Optional[int] = None,
        current_hex: Optional[str] = None,
    ) -> Optional[str]: ...


def encode_heater_mode(
    value: HeaterMode,
    bit_index: Optional[int] = None,
    current_hex: Optional[str] = None,
) -> Optional[str]:
    """Encode heater mode to hex string for register 0b55.

    Heater mode is stored in register 0b55 using bits 3, 5, 6, 7, 9:
    - SUMMER: bit 3=1, others 0
    - WINTER: bit 5=1, others 0
    - PARTY: bit 5=1 AND bit 6=1 (sub-mode of winter, per UI)
    - VACATION: bit 5=1 AND bit 7=1 (sub-mode of winter, per UI)
    - MANUAL: bit 5=1 AND bit 9=1 (sub-mode of winter, per UI)
    - OFF: all mode bits 0

    Uses read-modify-write pattern to preserve other flag bits in the register.

    Args:
        value: HeaterMode enum value
        bit_index: Ignored (not used for heater mode)
        current_hex: Current hex value of register 0b55 (required for read-modify-write)

    Returns:
        Hex string to write, or None if current_hex is not provided
    """
    if current_hex is None:
        logger.warning(
            "encode_heater_mode: current_hex is required for read-modify-write"
        )
        return None

    SUMMER_BIT = 3
    WINTER_BIT = 5
    PARTY_BIT = 6
    VACATION_BIT = 7
    MANUAL_BIT = 9
    MODE_BITS = (SUMMER_BIT, WINTER_BIT, PARTY_BIT, VACATION_BIT, MANUAL_BIT)

    try:
        # Validate hex string format
        if len(current_hex) != 4:
            logger.error(
                f"encode_heater_mode: invalid hex string length: {current_hex}"
            )
            return None
        int(current_hex, 16)  # Validate hex format

        current_int = reg_to_int(current_hex)
        new_int = current_int

        # Clear all mode bits first
        for bit in MODE_BITS:
            new_int = set_bit(new_int, bit, False)

        # Set the bit for the chosen mode
        if value == HeaterMode.SUMMER:
            new_int = set_bit(new_int, SUMMER_BIT, True)
        elif value == HeaterMode.WINTER:
            new_int = set_bit(new_int, WINTER_BIT, True)
        elif value == HeaterMode.PARTY:
            new_int = set_bit(new_int, WINTER_BIT, True)
            new_int = set_bit(new_int, PARTY_BIT, True)
        elif value == HeaterMode.VACATION:
            new_int = set_bit(new_int, WINTER_BIT, True)
            new_int = set_bit(new_int, VACATION_BIT, True)
        elif value == HeaterMode.MANUAL:
            # Manual is sub-mode of winter: UI requires both bit 5 and bit 9
            new_int = set_bit(new_int, WINTER_BIT, True)
            new_int = set_bit(new_int, MANUAL_BIT, True)
        elif value == HeaterMode.OFF:
            pass  # all bits already cleared

        logger.debug(
            f"Encoding heater mode to {value.value}: "
            f"{current_hex} ({current_int}) → {int_to_reg(new_int)} ({new_int})"
        )

        return int_to_reg(new_int)
    except (ValueError, TypeError) as e:
        logger.error(f"Error encoding heater mode: {e}")
        return None


def encode_bit_boolean(
    value: bool,
    bit_index: Optional[int],
    current_hex: Optional[str] = None,
) -> Optional[str]:
    """Encode a boolean value to a single bit in a register.

    Args:
        value: Boolean value to encode
        bit_index: Bit index to modify (required)
        current_hex: Current hex value of the register (required for read-modify-write)

    Returns:
        Hex string to write, or None if bit_index or current_hex is not provided
    """
    if bit_index is None:
        logger.error("encode_bit_boolean: bit_index is required")
        return None

    if current_hex is None:
        logger.warning(
            "encode_bit_boolean: current_hex is required for read-modify-write"
        )
        return None

    try:
        # Validate hex string format
        if len(current_hex) != 4:
            logger.error(
                f"encode_bit_boolean: invalid hex string length: {current_hex}"
            )
            return None
        int(current_hex, 16)  # Validate hex format

        current_int = reg_to_int(current_hex)
        new_int = set_bit(current_int, bit_index, value)
        return int_to_reg(new_int)
    except (ValueError, TypeError) as e:
        logger.error(f"Error encoding bit boolean: {e}")
        return None


def encode_map(
    true_value: Any, false_value: Any
) -> Callable[[Any, str, Optional[int], Optional[str]], Optional[str]]:
    """Returns an encoder function that maps an Enum or bool value to a boolean bit.

    Args:
        true_value: Enum value that represents True (e.g., WaterHeaterEnabled.ENABLED)
        false_value: Enum value that represents False (e.g., WaterHeaterEnabled.DISABLED)

    Returns:
        Encoder function that converts enum/bool to bit
    """

    def _encoder(
        value: Any,
        bit_index: Optional[int],
        current_hex: Optional[str] = None,
    ) -> Optional[str]:
        if bit_index is None:
            logger.error("encode_map: bit_index is required")
            return None

        if current_hex is None:
            logger.warning("encode_map: current_hex is required for read-modify-write")
            return None

        # Convert enum to boolean
        # Check if value matches one of the enum values
        if value == true_value or value == false_value:
            bool_value = value == true_value
        elif isinstance(value, bool):
            bool_value = value
        else:
            logger.error(f"encode_map: unsupported value type {type(value)}")
            return None

        return encode_bit_boolean(bool_value, bit_index, current_hex)

    return _encoder


def encode_scaled_x10(
    value: float,
    bit_index: Optional[int],
    current_hex: Optional[str] = None,
) -> Optional[str]:
    """Encode value scaled by 10 (value × 10 stored in register).

    Use for temperatures (°C), durations (hours), and any value with 0.1 precision.

    Args:
        value: Float value (e.g. 22.5°C, 79.5 h)
        bit_index: Ignored
        current_hex: Ignored (not needed for full register write)

    Returns:
        Hex string to write
    """
    try:
        scaled_val = int(value * 10)
        return int_to_reg(scaled_val)
    except Exception as e:
        logger.error(f"Error encoding scaled_x10: {e}")
        return None


def encode_scaled_x100(
    value: float,
    bit_index: Optional[int],
    current_hex: Optional[str] = None,
) -> Optional[str]:
    """Encode value scaled by 100 (value × 100 stored in register).

    Use for pressure (bar), flow, and any value with 0.01 precision.

    Args:
        value: Float value (e.g. 5.00 bar)
        bit_index: Ignored
        current_hex: Ignored (not needed for full register write)

    Returns:
        Hex string to write
    """
    try:
        scaled_val = int(value * 100)
        return int_to_reg(scaled_val)
    except Exception as e:
        logger.error(f"Error encoding scaled_x100: {e}")
        return None


def encode_raw_int(
    value: int,
    bit_index: Optional[int],
    current_hex: Optional[str] = None,
) -> Optional[str]:
    """Encode raw 16-bit signed integer to hex string.

    Use for registers that store integer values (e.g. duration, timestamps).
    Value -1 (0xffff) often means \"indefinite\" or \"until cancelled\".

    Args:
        value: Integer value (-32768 to 32767)
        bit_index: Ignored
        current_hex: Ignored (not needed for full register write)

    Returns:
        Hex string to write
    """
    if not isinstance(value, int):
        logger.error(f"Error encoding raw int: expected int, got {type(value).__name__}")
        return None
    try:
        return int_to_reg(value)
    except Exception as e:
        logger.error(f"Error encoding raw int: {e}")
        return None


# Registry for config loader: maps YAML encoder names to encoder functions.
# "map" is special—built from params at load time via encode_map().
ENCODER_REGISTRY: dict[str, Callable[..., Optional[str]]] = {
    "heater_mode": encode_heater_mode,
    "scaled_x10": encode_scaled_x10,
    "scaled_x100": encode_scaled_x100,
    "raw_int": encode_raw_int,
}
