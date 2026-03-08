"""Water heater entity for Kospel integration (CWU / DHW)."""

import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info, get_device_identifier
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.registers.enums import WaterHeaterEnabled
from kospel_cmi.controller.api import HeaterController

_LOGGER = logging.getLogger(__name__)

# HA water_heater operation modes (from homeassistant.const)
STATE_ECO = "eco"
STATE_PERFORMANCE = "performance"
STATE_OFF = "off"

OPERATION_LIST = [STATE_ECO, STATE_PERFORMANCE]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel water heater platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KospelWaterHeaterEntity(coordinator)])


class KospelWaterHeaterEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], WaterHeaterEntity
):
    """Representation of a Kospel domestic hot water (CWU/DHW) entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "dhw"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = OPERATION_LIST
    _attr_min_temp = 30.0
    _attr_max_temp = 65.0
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the water heater entity."""
        super().__init__(coordinator)
        device_id = get_device_identifier(coordinator.entry)
        self._attr_unique_id = f"{device_id}_water_heater"
        self._attr_device_info = get_device_info(coordinator.entry)
        # Track operation mode locally (device has no CWU mode register)
        self._current_operation = STATE_ECO

    def _get_controller(self) -> HeaterController:
        """Return the heater controller from coordinator data."""
        return self.coordinator.data

    @property
    def current_temperature(self) -> float | None:
        """Return the current water temperature."""
        controller = self._get_controller()
        return getattr(controller, "water_current_temperature", None)

    @property
    def target_temperature(self) -> float | None:
        """Return the effective CWU target temperature (supply_setpoint)."""
        controller = self._get_controller()
        return getattr(controller, "supply_setpoint", None)

    @property
    def current_operation(self) -> str:
        """Return the current operation mode."""
        controller = self._get_controller()
        if getattr(controller, "is_water_heater_enabled", WaterHeaterEnabled.DISABLED) == WaterHeaterEnabled.DISABLED:
            return STATE_OFF
        return self._current_operation

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        controller = self._get_controller()
        temperature = kwargs.get("temperature")
        if temperature is not None:
            if self._current_operation == STATE_ECO:
                controller.cwu_temperature_economy = temperature
            else:
                controller.cwu_temperature_comfort = temperature
            await controller.save()
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode."""
        _LOGGER.debug("Setting operation mode to %s", operation_mode)
        if operation_mode in OPERATION_LIST:
            self._current_operation = operation_mode
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn water heater on."""
        controller = self._get_controller()
        controller.is_water_heater_enabled = WaterHeaterEnabled.ENABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn water heater off."""
        controller = self._get_controller()
        controller.is_water_heater_enabled = WaterHeaterEnabled.DISABLED
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
