"""Diagnostics support for Kospel."""
from typing import Any
import inspect

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import KospelDataUpdateCoordinator

TO_REDACT = {"unique_id", "host", "mac"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data: dict[str, Any] = {
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "kospel_cmi_library": {},
    }

    device = coordinator.data
    if device is not None:
        # Dump raw registers from the device cache
        raw_registers = getattr(device, "_registers", {})
        
        # Dump evaluated properties
        parsed_properties = {}
        for name, member in inspect.getmembers(type(device), predicate=lambda x: isinstance(x, property)):
            try:
                val = getattr(device, name)
                # Format Enums and other types for readability
                if hasattr(val, "name") and hasattr(val, "value"):
                    parsed_properties[name] = f"{type(val).__name__}.{val.name} ('{val.value}')"
                else:
                    parsed_properties[name] = val
            except Exception as e:
                parsed_properties[name] = f"Error: {e}"

        diagnostics_data["kospel_cmi_library"] = {
            "raw_registers": raw_registers,
            "parsed_properties": parsed_properties,
        }
    else:
        diagnostics_data["kospel_cmi_library"] = "Device data not available (coordinator failed)"

    return diagnostics_data
