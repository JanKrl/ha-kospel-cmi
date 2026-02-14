"""Climate entity for Kospel integration."""

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_device_info
from .coordinator import KospelDataUpdateCoordinator

from kospel_cmi.registers.enums import HeaterMode, PumpStatus
from kospel_cmi.controller.api import HeaterController

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kospel climate platform."""
    coordinator: KospelDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KospelClimateEntity(coordinator)])


class KospelClimateEntity(
    CoordinatorEntity[KospelDataUpdateCoordinator], ClimateEntity
):
    """Representation of a Kospel heater climate entity (main device entity)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "heater"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_preset_modes = [mode.value for mode in HeaterMode]

    def __init__(self, coordinator: KospelDataUpdateCoordinator) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_climate"
        self._attr_device_info = get_device_info(coordinator.entry.entry_id)

        self._preset_mode = self._attr_preset_modes[0]

    @property
    def _heater_mode(self) -> HeaterMode:
        """Current heater mode from the controller."""
        controller: HeaterController = self.coordinator.data
        return getattr(controller, "heater_mode", HeaterMode.OFF)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        controller: HeaterController = self.coordinator.data
        # Use room temperature sensor (register 0b6d) as current temperature
        return getattr(controller, "room_temperature", None)

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        controller: HeaterController = self.coordinator.data
        return getattr(controller, "manual_temperature", None)

    @property
    def hvac_mode(self) -> HVACMode:
        """Current HVAC mode is based on the heater mode (represented in preset)."""
        return HVACMode.HEAT if self._heater_mode != HeaterMode.OFF else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """HVAC action is based on whether or not CO pump is running"""
        controller: HeaterController = self.coordinator.data
        return (
            HVACAction.HEATING
            if getattr(controller, "is_pump_co_running", PumpStatus.IDLE)
            == PumpStatus.RUNNING
            else HVACAction.OFF
        )

    @property
    def preset_mode(self) -> str | None:
        """Current preset mode is the heater mode."""
        return self._heater_mode.value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)
        controller: HeaterController = self.coordinator.data

        controller.heater_mode = (
            HeaterMode.OFF if hvac_mode == HVACMode.OFF else HeaterMode.WINTER
        )
        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        controller: HeaterController = self.coordinator.data
        temperature = kwargs.get("temperature")
        if temperature is not None:
            controller.manual_temperature = temperature
            await controller.save()
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("Setting preset mode to %s", preset_mode)
        controller: HeaterController = self.coordinator.data
        controller.heater_mode = HeaterMode(preset_mode)

        await controller.save()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
