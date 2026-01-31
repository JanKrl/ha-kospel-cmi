"""
Registry of the heater registers. It contains list of known registers and information needed to decode and encode them.
"""

from dataclasses import dataclass
from typing import Optional, Any

from ..registers.decoders import (
    Decoder,
    decode_map,
    decode_heater_mode,
    decode_scaled_temp,
    decode_scaled_pressure,
)
from ..registers.encoders import (
    Encoder,
    encode_heater_mode,
    encode_map,
    encode_scaled_temp,
)
from ..registers.enums import ValvePosition, ManualMode, WaterHeaterEnabled, PumpStatus


@dataclass
class SettingDefinition:
    """Definition of a setting's register and bit location."""

    register: str
    # Function to decode the value from a register hex string
    decode_function: Decoder
    # Function to encode a value to a register hex string (None for read-only settings)
    encode_function: Optional[Encoder] = None
    # If specific bit index is needed, otherwise the whole register is decoded/encoded
    bit_index: Optional[int] = None

    @property
    def is_read_only(self) -> bool:
        """Derived property: read-only if no encode_function."""
        return self.encode_function is None

    def decode(self, hex_val: str) -> Any:
        """Decode the value from a register hex string.

        Args:
            hex_val (str): The hex value of the register

        Returns:
            Any: The decoded value
        """
        return self.decode_function(hex_val, self.bit_index)

    def encode(self, value: Any, current_hex: Optional[str] = None) -> Optional[str]:
        """Encode a value to a register hex string.

        Args:
            value: The value to encode
            current_hex: Optional current hex value (for read-modify-write operations)

        Returns:
            Optional[str]: The hex string to write, or None if encoding fails

        Raises:
            ValueError: If setting is read-only (no encode_function)
        """
        if self.encode_function is None:
            raise ValueError("Setting is read-only (no encode_function)")
        return self.encode_function(value, self.bit_index, current_hex)


# Settings registry mapping semantic names to register/bit locations
SETTINGS_REGISTRY = {
    "heater_mode": SettingDefinition(
        register="0b55",
        decode_function=decode_heater_mode,
        encode_function=encode_heater_mode,
    ),
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
    ),
    "is_water_heater_enabled": SettingDefinition(
        register="0b55",
        bit_index=4,
        decode_function=decode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        ),
        encode_function=encode_map(
            true_value=WaterHeaterEnabled.ENABLED,
            false_value=WaterHeaterEnabled.DISABLED,
        ),
    ),
    "is_pump_co_running": SettingDefinition(
        register="0b51",
        bit_index=0,
        decode_function=decode_map(
            true_value=PumpStatus.RUNNING,
            false_value=PumpStatus.IDLE,
        ),
        # Read-only: no encode_function
    ),
    "is_pump_circulation_running": SettingDefinition(
        register="0b51",
        bit_index=1,
        decode_function=decode_map(
            true_value=PumpStatus.RUNNING,
            false_value=PumpStatus.IDLE,
        ),
        # Read-only: no encode_function
    ),
    "valve_position": SettingDefinition(
        register="0b51",
        bit_index=2,
        decode_function=decode_map(
            true_value=ValvePosition.CO,
            false_value=ValvePosition.DHW,
        ),
        # Read-only: no encode_function
    ),
    "manual_temperature": SettingDefinition(
        register="0b8d",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "room_temperature_economy": SettingDefinition(
        register="0b68",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "room_temperature_comfort": SettingDefinition(
        register="0b6a",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "room_temperature_comfort_plus": SettingDefinition(
        register="0b6b",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "room_temperature_comfort_minus": SettingDefinition(
        register="0b69",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "cwu_temperature_economy": SettingDefinition(
        register="0b66",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "cwu_temperature_comfort": SettingDefinition(
        register="0b67",
        decode_function=decode_scaled_temp,
        encode_function=encode_scaled_temp,
    ),
    "pressure": SettingDefinition(
        register="0b8a",
        decode_function=decode_scaled_pressure,
        # Read-only: no encode_function
    ),
    "room_temperature": SettingDefinition(
        register="0b6d",
        decode_function=decode_scaled_temp,
        # Read-only: no encode_function
    ),
}
