"""Constants for the Kospel integration."""

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from homeassistant.helpers.entity import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

DOMAIN = "kospel"

# Configuration keys
CONF_BACKEND_TYPE = "backend_type"
CONF_HEATER_IP = "heater_ip"
CONF_DEVICE_ID = "device_id"
CONF_SERIAL_NUMBER = "serial_number"
CONF_SIMULATION_MODE = "simulation_mode"  # Deprecated; used for migration only

# Default subnets for discovery when Network integration returns none
DEFAULT_SUBNETS = [
    "192.168.1.0/24",
    "192.168.0.0/24",
    "192.168.101.0/24",
    "10.0.0.0/24",
]

# Backend type values
BACKEND_TYPE_HTTP = "http"
BACKEND_TYPE_YAML = "yaml"

# Relative path for YAML state file inside the integration directory
YAML_STATE_FILE_RELATIVE = "data/state.yaml"

# Update intervals
SCAN_INTERVAL = timedelta(seconds=30)

# Simulation mode constants (deprecated; migration only)
SIMULATION_MODE_ENV_VAR = "SIMULATION_MODE"


def get_yaml_state_file_path(integration_dir: Optional[Path] = None) -> Path:
    """Return the full path for the YAML backend state file.

    State file is located in the integration directory under data/state.yaml.
    Used when backend_type is yaml (development / file-based mode).

    Args:
        integration_dir: Base directory of the integration. If None, not set.

    Returns:
        Path to state.yaml. Caller should pass Path(__file__).resolve().parent.
    """
    if integration_dir is None:
        integration_dir = Path(__file__).resolve().parent
    return integration_dir / "data" / "state.yaml"


def make_unique_id(serial_number: str, device_id: int) -> str:
    """Build unique_id for device registry (enables discovery update on IP change).

    Args:
        serial_number: Device serial number from probe/discovery.
        device_id: Device ID (1-255).

    Returns:
        Unique identifier string, e.g. "mi01_00006047_65".
    """
    return f"{serial_number}_{device_id}"


def get_device_identifier(entry: "ConfigEntry") -> str:
    """Return identifier for entities (unique_id prefix). Uses serial_deviceid or entry_id."""
    serial = entry.data.get(CONF_SERIAL_NUMBER)
    device_id = entry.data.get(CONF_DEVICE_ID)
    if serial is not None and device_id is not None:
        return make_unique_id(serial, device_id)
    return entry.entry_id


def get_device_info(entry: "ConfigEntry") -> DeviceInfo:
    """Return DeviceInfo for the heater device.

    Uses unique_id (serial_deviceid) when available for discovery updates on IP change.
    Falls back to entry_id for legacy entries without serial_number.

    Args:
        entry: Config entry for the heater.

    Returns:
        DeviceInfo for the device registry.
    """
    identifier = get_device_identifier(entry)
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name="Kospel Heater",
        manufacturer="Kospel",
        model="Electric Heater",
        translation_key="heater",
    )
