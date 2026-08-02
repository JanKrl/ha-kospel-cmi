"""The Kospel Heater integration."""

import logging
from pathlib import Path

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
from .services import async_setup_services
from kospel_cmi.controller.device import EkcoM3
from kospel_cmi.kospel.backend import HttpRegisterBackend, YamlRegisterBackend

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "binary_sensor",
    "climate",
    "number",
    "select",
    "sensor",
    "water_heater",
]


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
        heater_controller = EkcoM3(backend=backend, strict_refresh=True)
        coordinator = KospelDataUpdateCoordinator(hass, entry, heater_controller)
        hass.data[DOMAIN][entry.entry_id] = coordinator
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        if session is not None:
            await session.close()
        _LOGGER.error("Error setting up Kospel integration: %s", err)
        raise ConfigEntryNotReady from err

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async_setup_services(hass)
    await _async_register_frontend_cards(hass)

    return True


async def _async_register_frontend_cards(hass: HomeAssistant) -> None:
    """Register custom Lovelace cards with Home Assistant frontend."""
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if not frontend_dir.exists():
        return

    if hass.data.get(DOMAIN, {}).get("_frontend_registered"):
        return

    try:
        from homeassistant.components.frontend import add_extra_js_url
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    url_path="/kospel_static",
                    path=str(frontend_dir),
                    cache_headers=False,
                )
            ]
        )
        add_extra_js_url(hass, "/kospel_static/kospel-program-card.js")
        add_extra_js_url(hass, "/kospel_static/kospel-weekday-card.js")
        hass.data.setdefault(DOMAIN, {})["_frontend_registered"] = True
    except Exception as err:
        _LOGGER.warning("Failed to register frontend custom cards: %s", err)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.heater_controller.aclose()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
