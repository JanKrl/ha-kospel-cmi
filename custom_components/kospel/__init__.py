"""The Kospel Heater integration."""

import logging
from pathlib import Path

import aiohttp
from kospel_cmi import (
    EkcoM3,
    HttpCmiBackend,
    HttpModbusBackend,
    KospelController,
    Ppe4,
    YamlCmiBackend,
    YamlModbusBackend,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    BACKEND_TYPE_HTTP,
    BACKEND_TYPE_YAML,
    CONF_BACKEND_TYPE,
    CONF_DEVICE_ID,
    CONF_DEVICE_TYPE,
    CONF_HEATER_IP,
    DEVICE_TYPE_EKCO_M3,
    DEVICE_TYPE_PPE4,
    DOMAIN,
    get_yaml_state_file_path,
)
from .coordinator import KospelDataUpdateCoordinator
from .services import async_setup_services

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
    device_type = entry.data.get(CONF_DEVICE_TYPE, DEVICE_TYPE_EKCO_M3)
    session: aiohttp.ClientSession | None = None
    heater_controller: KospelController

    if backend_type == BACKEND_TYPE_YAML:
        integration_dir = Path(__file__).resolve().parent
        state_file_path = get_yaml_state_file_path(integration_dir, device_type)
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        _LOGGER.info(
            "Kospel integration using YAML backend (%s): %s",
            device_type,
            state_file_path,
        )
        if device_type == DEVICE_TYPE_PPE4:
            backend_modbus = YamlModbusBackend(state_file=str(state_file_path))
            heater_controller = Ppe4(backend=backend_modbus, strict_refresh=True)
        else:
            backend_cmi = YamlCmiBackend(state_file=str(state_file_path))
            heater_controller = EkcoM3(backend=backend_cmi, strict_refresh=True)
    else:
        heater_ip = entry.data[CONF_HEATER_IP]
        session = aiohttp.ClientSession()
        if device_type == DEVICE_TYPE_PPE4:
            api_base_url = f"http://{heater_ip}/api"
            backend_modbus_http = HttpModbusBackend(session, api_base_url)
            heater_controller = Ppe4(
                backend=backend_modbus_http, strict_refresh=True
            )
        else:
            device_id = entry.data[CONF_DEVICE_ID]
            api_base_url = f"http://{heater_ip}/api/dev/{device_id}"
            backend_cmi_http = HttpCmiBackend(session, api_base_url)
            heater_controller = EkcoM3(
                backend=backend_cmi_http, strict_refresh=True
            )

    try:
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

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.heater_controller.aclose()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
