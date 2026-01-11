"""The Kospel Heater integration."""

import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_HEATER_IP,
    CONF_DEVICE_ID,
    CONF_SIMULATION_MODE,
)
from .coordinator import KospelDataUpdateCoordinator
from .controller.api import HeaterController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["climate", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Kospel integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kospel from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get simulation mode from config entry (defaults to False if not set)
    simulation_mode = entry.data.get(CONF_SIMULATION_MODE, False)

    # Use placeholder IP/device ID if in simulation mode
    if simulation_mode:
        heater_ip = entry.data.get(CONF_HEATER_IP, "127.0.0.1")
        device_id = entry.data.get(CONF_DEVICE_ID, "65")
        _LOGGER.info("Kospel integration starting in simulation mode")
    else:
        heater_ip = entry.data[CONF_HEATER_IP]
        device_id = entry.data[CONF_DEVICE_ID]

    api_base_url = f"http://{heater_ip}/api/dev/{device_id}"

    # Create aiohttp session
    session = aiohttp.ClientSession()

    try:
        # Create HeaterController instance with simulation_mode parameter
        heater_controller = HeaterController(
            session, api_base_url, simulation_mode=simulation_mode
        )

        # Create coordinator
        coordinator = KospelDataUpdateCoordinator(
            hass, entry, session, heater_controller
        )

        # Store coordinator in hass.data
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # Fetch initial data so we have data when entities subscribe
        await coordinator.async_config_entry_first_refresh()

    except Exception as err:
        await session.close()
        _LOGGER.error("Error setting up Kospel integration: %s", err)
        raise ConfigEntryNotReady from err

    # Forward the config entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
