"""The Kospel Heater integration."""

import logging
from pathlib import Path
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_BACKEND_TYPE,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    BACKEND_TYPE_HTTP,
    BACKEND_TYPE_YAML,
    get_yaml_state_file_path,
)
from .coordinator import KospelDataUpdateCoordinator
from kospel_cmi.controller.api import HeaterController
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["climate", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Kospel integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kospel from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    backend_type = entry.data.get(CONF_BACKEND_TYPE, BACKEND_TYPE_HTTP)
    session: aiohttp.ClientSession | None = None
    backend: HttpRegisterBackend | YamlRegisterBackend

    if backend_type == BACKEND_TYPE_YAML:
        integration_dir = Path(__file__).resolve().parent
        state_file_path = get_yaml_state_file_path(integration_dir)
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        backend = YamlRegisterBackend(state_file=str(state_file_path))
        _LOGGER.info(
            "Kospel integration using YAML backend: %s",
            state_file_path,
        )
    else:
        heater_ip = entry.data[CONF_HEATER_IP]
        device_id = entry.data[CONF_DEVICE_ID]
        api_base_url = f"http://{heater_ip}/api/dev/{device_id}"
        session = aiohttp.ClientSession()
        backend = HttpRegisterBackend(session, api_base_url)

    try:
        heater_controller = HeaterController(backend=backend)
        coordinator = KospelDataUpdateCoordinator(hass, entry, heater_controller)
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        if session is not None:
            await session.close()
        _LOGGER.error("Error setting up Kospel integration: %s", err)
        raise ConfigEntryNotReady from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.heater_controller.aclose()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
