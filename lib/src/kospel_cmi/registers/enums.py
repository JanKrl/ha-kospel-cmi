from enum import Enum, IntEnum


class HeaterMode(Enum):
    """Heater operating mode.

    All six modes are mutually exclusive per the manufacturer UI.
    Stored in register 0b55: bit 3=SUMMER, bit 5=WINTER, bit 6=PARTY,
    bit 7=VACATION, bit 9=MANUAL. OFF = all mode bits cleared.
    """

    OFF = "off"
    SUMMER = "summer"  # Water only
    WINTER = "winter"  # Water + radiators
    PARTY = "party"  # Temporary comfort boost
    VACATION = "vacation"  # Reduced heating when away
    MANUAL = "manual"  # Manual temperature override


class WaterHeaterEnabled(Enum):
    """Water heater enabled."""

    ENABLED = "Water heater enabled"  # Water heater is enabled
    DISABLED = "Water heater disabled"  # Water heater is disabled


class ValvePosition(Enum):
    """Valve position."""

    DHW = "DHW"  # Domestic Hot Water
    CO = "CO"  # Central Heating


class HeatingStatus(Enum):
    """Heating circuit status matching manufacturer UI icons."""

    RUNNING = "running"  # Red: circuit active, power > 0 (or cwu in summer)
    IDLE = "idle"  # Green: circuit active, not heating
    DISABLED = "disabled"  # Grey: circuit inactive


class HeatingCircuitActive(Enum):
    """Raw bit value for heating circuit active (0b51 bits 7, 8)."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class CwuMode(IntEnum):
    """CWU (domestic hot water) mode — which temperature source is active.

    Stored in register 0b30. Values: 0=economy (0b66), 1=anti-freeze,
    2=comfort (0b67).
    """

    ECONOMY = 0  # Uses cwu_temperature_economy (0b66)
    ANTI_FREEZE = 1  # Anti-freeze protection
    COMFORT = 2  # Uses cwu_temperature_comfort (0b67)



# Firmware value for room_mode (0b32) when heater_mode=MANUAL.
# Tells firmware to use manual_temperature (0b8d) as the target.
ROOM_MODE_MANUAL = 64


# Registry for resolving enum paths from YAML
# (e.g. "WaterHeaterEnabled.ENABLED" -> WaterHeaterEnabled.ENABLED)
ENUM_REGISTRY: dict[str, type[Enum]] = {
    "HeaterMode": HeaterMode,
    "WaterHeaterEnabled": WaterHeaterEnabled,
    "ValvePosition": ValvePosition,
    "HeatingStatus": HeatingStatus,
    "HeatingCircuitActive": HeatingCircuitActive,
}
