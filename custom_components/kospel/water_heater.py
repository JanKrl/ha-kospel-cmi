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

from kospel_cmi.registers.enums import CwuMode, WaterHeaterEnabled
from kospel_cmi.controller.api import HeaterController

_LOGGER = logging.getLogger(__name__)

# HA water_heater operation modes (from homeassistant.const)
STATE_ECO = "eco"
STATE_PERFORMANCE = "performance"
STATE_OFF = "off"

OPERATION_LIST = [STATE_ECO, STATE_PERFORMANCE, STATE_OFF]

# CwuMode (0=economy, 1=anti-freeze, 2=comfort) to HA operation mode
_CWU_MODE_TO_HA: dict[int, str] = {
    CwuMode.ECONOMY: STATE_ECO,
    CwuMode.ANTI_FREEZE: STATE_OFF,
    CwuMode.COMFORT: STATE_PERFORMANCE,
}

_HA_TO_CWU_MODE: dict[str, CwuMode] = {
    STATE_ECO: CwuMode.ECONOMY,
    STATE_PERFORMANCE: CwuMode.COMFORT,
    STATE_OFF: CwuMode.ANTI_FREEZE,
}


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
        """Return the target temperature from the active setpoint (mode-dependent)."""
        controller = self._get_controller()
        cwu_mode = getattr(controller, "cwu_mode", 0)
        if cwu_mode == CwuMode.COMFORT:
            return getattr(controller, "cwu_temperature_comfort", None)
        if cwu_mode == CwuMode.ANTI_FREEZE:
            return getattr(controller, "cwu_temperature_economy", None)
        return getattr(controller, "cwu_temperature_economy", None)

    @property
    def current_operation(self) -> str:
        """Return the current operation mode from device cwu_mode."""
        controller = self._get_controller()
        if getattr(controller, "is_water_heater_enabled", WaterHeaterEnabled.DISABLED) == WaterHeaterEnabled.DISABLED:
            return STATE_OFF
        cwu_mode = getattr(controller, "cwu_mode", 0)
        return _CWU_MODE_TO_HA.get(cwu_mode, STATE_ECO)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature using mode-appropriate helper."""
        controller = self._get_controller()
        temperature = kwargs.get("temperature")
        if temperature is not None:
            operation = self.current_operation
            if operation == STATE_PERFORMANCE:
                await controller.set_water_comfort_temperature(temperature)
            else:
                await controller.set_water_economy_temperature(temperature)
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode via set_water_mode."""
        _LOGGER.debug("Setting operation mode to %s", operation_mode)
        if operation_mode in OPERATION_LIST:
            cwu_mode = _HA_TO_CWU_MODE.get(operation_mode)
            if cwu_mode is not None:
                controller = self._get_controller()
                await controller.set_water_mode(cwu_mode)
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()

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
