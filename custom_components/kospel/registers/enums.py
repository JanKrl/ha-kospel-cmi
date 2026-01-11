from enum import Enum


class HeaterMode(Enum):
    """Heater operating mode."""

    SUMMER = "Summer"  # In summer mode only water is heated
    WINTER = "Winter"  # In winter mode both water and radiators are heated
    OFF = "Off"  # The heater is off


class ManualMode(Enum):
    """Manual mode."""

    ENABLED = "Manual mode"  # Manual mode is enabled
    DISABLED = "Auto mode"  # Manual mode is disabled


class WaterHeaterEnabled(Enum):
    """Water heater enabled."""

    ENABLED = "Water heater enabled"  # Water heater is enabled
    DISABLED = "Water heater disabled"  # Water heater is disabled


class ValvePosition(Enum):
    """Valve position."""

    DHW = "DHW"  # Domestic Hot Water
    CO = "CO"  # Central Heating


class PumpStatus(Enum):
    """Pump status."""

    RUNNING = "Running"
    IDLE = "Idle"
