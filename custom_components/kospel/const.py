"""Constants for the Kospel integration."""

from datetime import timedelta
from pathlib import Path
from typing import Optional

from homeassistant.helpers.entity import DeviceInfo

DOMAIN = "kospel"

# Configuration keys
CONF_BACKEND_TYPE = "backend_type"
CONF_HEATER_IP = "heater_ip"
CONF_DEVICE_ID = "device_id"
CONF_SIMULATION_MODE = "simulation_mode"  # Deprecated; used for migration only

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
