"""Constants for the Kospel integration."""

from datetime import timedelta

from homeassistant.helpers.entity import DeviceInfo

DOMAIN = "kospel"

# Configuration keys
CONF_HEATER_IP = "heater_ip"
CONF_DEVICE_ID = "device_id"
CONF_SIMULATION_MODE = "simulation_mode"

# Update intervals
SCAN_INTERVAL = timedelta(seconds=30)

# Simulation mode constants
SIMULATION_MODE_ENV_VAR = "SIMULATION_MODE"


def get_device_info(entry_id: str) -> DeviceInfo:
    """Return DeviceInfo for the heater device.

    Used by all entities to attach to the same device in the device registry.
    Device name is translatable via strings.json under device.heater.name.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Kospel Heater",
        manufacturer="Kospel",
        model="Electric Heater",
        translation_key="heater",
    )
