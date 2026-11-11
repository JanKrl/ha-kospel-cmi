"""Constants for the Kospel integration."""

import math
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from homeassistant.helpers.entity import DeviceInfo

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

DOMAIN = "kospel"

# Configuration keys
CONF_BACKEND_TYPE = "backend_type"
CONF_DEVICE_TYPE = "device_type"
CONF_HEATER_IP = "heater_ip"
CONF_DEVICE_ID = "device_id"
CONF_SERIAL_NUMBER = "serial_number"
CONF_SIMULATION_MODE = "simulation_mode"  # Deprecated; used for migration only

# Device types
DEVICE_TYPE_EKCO_M3 = "ekco_m3"
DEVICE_TYPE_PPE4 = "ppe4"

DEVICE_TYPE_MODELS: dict[str, str] = {
    DEVICE_TYPE_EKCO_M3: "EKCO.M3",
    DEVICE_TYPE_PPE4: "PPE.4",
}

MODEL_NAME_TO_DEVICE_TYPE: dict[str, str] = {
    "EKCO.M3": DEVICE_TYPE_EKCO_M3,
    "PPE.4": DEVICE_TYPE_PPE4,
}

# Kospel S.A. MA-S prefix from IEEE registry / vendor lookup (36-bit).
# Normalized format strips separators and uses lowercase hex.
KOSPEL_MAC_PREFIXES = ("70b3d5249",)

# Backend type values
BACKEND_TYPE_HTTP = "http"
BACKEND_TYPE_YAML = "yaml"

# Relative paths for YAML state files inside the integration directory
YAML_EKCOM3_STATE_FILE_RELATIVE = "data/state_ekcom3.yaml"
YAML_PPE4_STATE_FILE_RELATIVE = "data/state_ppe4.yaml"
YAML_STATE_FILE_RELATIVE = YAML_EKCOM3_STATE_FILE_RELATIVE

# Update intervals
SCAN_INTERVAL = timedelta(seconds=15)

# Consecutive failed coordinator polls before entities report unavailable (~90s at default scan).
COMMUNICATION_FAILURE_THRESHOLD = max(
    1, int(math.ceil(90.0 / SCAN_INTERVAL.total_seconds()))
)

# Delay before coordinator refresh after set operations (device needs time to persist).
CONF_REFRESH_DELAY_AFTER_SET = "refresh_delay_after_set"
DEFAULT_REFRESH_DELAY_AFTER_SET = 1.0  # seconds
REFRESH_DELAY_MIN = 0.5
REFRESH_DELAY_MAX = 5.0

# Simulation mode constants (deprecated; migration only)
SIMULATION_MODE_ENV_VAR = "SIMULATION_MODE"


def get_yaml_state_file_path(
    integration_dir: Optional[Path] = None,
    device_type: str = DEVICE_TYPE_EKCO_M3,
) -> Path:
    """Return the full path for the YAML backend state file for the given device type."""
    if integration_dir is None:
        integration_dir = Path(__file__).resolve().parent
    if device_type == DEVICE_TYPE_PPE4:
        return integration_dir / YAML_PPE4_STATE_FILE_RELATIVE
    return integration_dir / YAML_EKCOM3_STATE_FILE_RELATIVE


def make_unique_id(serial_number: str, device_id: int) -> str:
    """Build unique_id for device registry (enables discovery update on IP change)."""
    return f"{serial_number}_{device_id}"


def get_device_identifier(entry: "ConfigEntry") -> str:
    """Return identifier for entities (unique_id prefix). Uses serial_deviceid or entry_id."""
    serial = entry.data.get(CONF_SERIAL_NUMBER)
    device_id = entry.data.get(CONF_DEVICE_ID)
    if serial is not None and device_id is not None:
        return make_unique_id(serial, device_id)
    return entry.entry_id


def get_refresh_delay_after_set(entry: "ConfigEntry") -> float:
    """Return delay (seconds) before coordinator refresh after set operations."""
    options = entry.options or {}
    return options.get(CONF_REFRESH_DELAY_AFTER_SET, DEFAULT_REFRESH_DELAY_AFTER_SET)


def get_device_info(entry: "ConfigEntry") -> DeviceInfo:
    """Return DeviceInfo for the heater device."""
    identifier = get_device_identifier(entry)
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_EKCO_M3)
    model = DEVICE_TYPE_MODELS.get(device_type, "Electric Heater")
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name="Kospel Heater",
        manufacturer="Kospel",
        model=model,
        translation_key="heater",
    )
